# ═══════════════════════════════════════════════════════════════════════════════
# main.py — AI Sales Bot Ana Orkestratörü
# ───────────────────────────────────────
# GENEL AKIŞ:
#   1. Google Sheets'ten daha önce gönderilmiş emailleri yükle (duplicate önleme)
#   2. Apollo API'den keyword + lokasyon + firma büyüklüğüne göre şirket listesi çek
#   3. Her şirket için:
#       a. Website metnini çek ve küçük işletme mi diye kontrol et
#       b. OpenAI ile şirketi analiz et ve hangi ürünü önereceksin seç
#       c. Şirketin hem info@ adresini hem karar verici kişileri bul
#       d. Her hedefe ayrı kişiselleştirilmiş email üret ve gönder
#       e. Sonucu Google Sheets'e kaydet
#   4. Apollo limiti veya yoksa Google (SerpAPI) ile aynı akış
# ═══════════════════════════════════════════════════════════════════════════════

from lead_generation.scraper import (
    search_apollo_companies,
    search_google,
    extract_company_info,
    extract_full_text,
    is_small_business
)

from enrichment.email_finder import (
    find_all_targets,
    guess_email,
    pick_best_email
)

from ai.analyzer import analyze_company
from ai.offer_selector import select_offer
from ai.email_writer import generate_email

from mailer.sender import send_email, generate_subject
from database.sheets import connect_sheet, save_or_update, get_all_data

from urllib.parse import urlparse
from config import APOLLO_KEYWORDS, GOOGLE_KEYWORDS, DAILY_LIMIT, MIN_DELAY, MAX_DELAY

import datetime
import time
import random
import uuid


# ───────────────────────────────────────────────────────────────────────────────
def get_domain(url):
    """
    URL'den temiz domain adını çıkarır.

    INPUT : url (str) — tam URL, örn. "https://www.firma.com/hakkimizda"
    OUTPUT: str       — temiz domain, örn. "firma.com"

    Örnek:
        get_domain("https://www.acme.co.uk/products") → "acme.co.uk"
    """
    return urlparse(url).netloc.replace("www.", "")


# ───────────────────────────────────────────────────────────────────────────────
def process_company(comp, sheet, sent_emails, sent_count):
    """
    Tek bir şirket için tüm pipeline'ı uçtan uca çalıştırır.
    Bu fonksiyon hem Apollo hem de Google kaynaklı şirketler için aynı şekilde çalışır.

    INPUT:
        comp        (dict) — {"name": str, "website": str, "domain": str (opsiyonel)}
                             Apollo'dan geliyorsa domain de dolu gelir,
                             Google'dan geliyorsa sadece name + website olur.
        sheet       (tuple) — connect_sheet()'ten dönen (workbook, worksheet) ikilisi.
                              save_or_update() fonksiyonuna iletilir.
        sent_emails (dict)  — {email: status} şeklinde daha önce gönderilenlerin haritası.
                              Duplicate gönderimi önlemek için kullanılır.
                              Fonksiyon içinde yeni gönderimler bu dict'e de eklenir.
        sent_count  (int)   — Bu session'da kaç mail gönderildiğinin sayacı.

    OUTPUT:
        int — güncellenmiş sent_count (başarılı her gönderimde +1 artar)

    ADIMLAR:
        1. Website metnini çek → küçük işletme değilse pas geç
        2. OpenAI ile analiz et → hangi ürün önerilecek seç
        3. find_all_targets() ile hem info@ hem kişisel emailleri bul
        4. Her hedef için email üret → gönder → sheets'e kaydet
    """
    link   = comp["website"]
    domain = comp.get("domain", get_domain(link))

    # ── ADIM 1: Website içeriğini çek ─────────────────────────────────────────
    full_text = extract_full_text(link)
    if not full_text or not is_small_business(full_text):
        # İçerik yoksa veya küçük işletme değilse bu şirketi atla
        return sent_count

    # ── ADIM 2: AI Analizi ve Ürün Seçimi ────────────────────────────────────
    # analyze_company() → şirketin sektör, pain point, dil bilgilerini JSON döndürür
    # select_offer()    → sektöre göre "feedback", "chatbot" veya "dashboard" seçer
    analysis = analyze_company(full_text)
    offer    = select_offer(analysis)

    # ── ADIM 3: Email Hedeflerini Bul ─────────────────────────────────────────
    # find_all_targets() hem kişisel (CEO, HR vb.) hem generic (info@) adresleri döndürür
    # Her item: {email, name, position, score, source, verified, type}
    print(f"🔍 Hedefler aranıyor: {comp['name']} ({domain})")
    targets = find_all_targets(link, domain)

    # Hiçbir şey bulunamazsa info@domain ile devam et
    if not targets:
        targets = [{
            "email":    guess_email(domain),
            "name":     "",
            "position": "",
            "score":    0,
            "source":   "guess",
            "verified": False,
            "type":     "generic",
        }]

    print(f"📬 {len(targets)} hedef bulundu → {[t['email'] for t in targets]}")

    # ── ADIM 4: Her Hedefe Ayrı Mail Gönder ──────────────────────────────────
    for target in targets:

        # Günlük limit kontrolü
        if sent_count >= DAILY_LIMIT:
            return sent_count

        email = target["email"]

        # Daha önce gönderilmişse atla
        if sent_emails.get(email) == "sent":
            print(f"⏭️  Zaten gönderilmiş → {email}")
            continue

        contact_name = target.get("name", "")
        target_type  = target.get("type", "generic")

        print(f"  → [{target_type.upper()}] {email} | "
              f"{target.get('position','?')} | skor: {target.get('score', 0)}")

        # Kişiye özel email metni üret (generic hedefler için contact_name boş kalır)
        ai_email    = generate_email(comp["name"], analysis, offer, contact_name)
        tracking_id = str(uuid.uuid4())
        subject     = generate_subject(offer)

        # Gönder
        success = send_email(email, ai_email, tracking_id, subject)
        status  = "sent" if success else "failed"

        # Duplicate önleme dict'ini güncelle
        sent_emails[email] = status

        # Google Sheets'e kaydet
        save_or_update(sheet, [
            comp["name"],
            comp["website"],
            offer,
            email,
            status,
            tracking_id,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "no",   # Opened
            "no",   # Replied
        ])

        if success:
            print(f"  ✅ Gönderildi → {email}")
        else:
            print(f"  ❌ Başarısız  → {email}")

        sent_count += 1
        time.sleep(random.randint(MIN_DELAY, MAX_DELAY))

    return sent_count


# ───────────────────────────────────────────────────────────────────────────────
def run():
    """
    Ana çalıştırıcı fonksiyon. python main.py ile burası tetiklenir.

    INPUT : Yok (konfigürasyon config.py ve .env'den okunur)
    OUTPUT: Yok (sonuçlar Google Sheets'e yazılır, konsola loglanır)

    AKIŞ:
        1. Google Sheets'e bağlan, daha önce gönderilenleri yükle
        2. Apollo ile APOLLO_KEYWORDS listesindeki her keyword için şirket ara
           → Her şirketi process_company() ile işle
        3. Günlük limit dolmadıysa GOOGLE_KEYWORDS ile Google'dan ek lead çek
           → extract_company_info() ile şirket bilgisine çevir
           → Her şirketi process_company() ile işle
    """
    # ── Sheets bağlantısı ve geçmiş veri ──────────────────────────────────────
    sheet         = connect_sheet()
    existing_data = get_all_data(sheet)

    # {email: status} — daha önce gönderilenlerin haritası
    sent_emails = {row["Email"]: row["Status"] for row in existing_data}
    sent_count  = 0

    # Hedef lokasyon ve firma büyüklüğü filtreleri
    target_locations = [
        "Turkey", "Germany", "United Kingdom",
        "Netherlands", "France", "Italy", "Spain"
    ]
    target_size = ["11,50", "51,200"]

    # ─────────────────────────────────────────────────────────────────────────
    # 1️⃣  APOLLO — Ana lead kaynağı
    #     Keyword + lokasyon + büyüklük filtrelemesiyle doğrudan şirket listesi döner.
    #     Her şirket için process_company() çalışır.
    # ─────────────────────────────────────────────────────────────────────────
    for keyword in APOLLO_KEYWORDS:
        if sent_count >= DAILY_LIMIT:
            print("\n🛑 Günlük limit doldu.")
            return

        print(f"\n🚀 [APOLLO] '{keyword}' için şirketler aranıyor...")
        companies_data = search_apollo_companies(
            keyword        = keyword,
            locations      = target_locations,
            employee_ranges= target_size,
        )
        print(f"🏢 [APOLLO] Bulunan şirket sayısı: {len(companies_data)}")

        for comp in companies_data:
            if sent_count >= DAILY_LIMIT:
                return
            sent_count = process_company(comp, sheet, sent_emails, sent_count)

    # ─────────────────────────────────────────────────────────────────────────
    # 2️⃣  GOOGLE (SerpAPI) — Yedek lead kaynağı
    #     Apollo limiti bittiyse veya yeterli şirket bulunamadıysa devreye girer.
    #     Arama sonucu URL listesi döner → extract_company_info() ile şirkete çevrilir.
    # ─────────────────────────────────────────────────────────────────────────
    for keyword in GOOGLE_KEYWORDS:
        if sent_count >= DAILY_LIMIT:
            print("\n🛑 Günlük limit doldu.")
            return

        print(f"\n🌐 [GOOGLE] '{keyword}' için linkler aranıyor...")
        links = search_google(keyword)
        print(f"🔗 [GOOGLE] Bulunan potansiyel link sayısı: {len(links)}")

        companies_data = []
        for link in links:
            info = extract_company_info(link)
            if info:
                companies_data.append(info)

        for comp in companies_data:
            if sent_count >= DAILY_LIMIT:
                return
            sent_count = process_company(comp, sheet, sent_emails, sent_count)

    print("\n🏁 İşlem tamamlandı.")


if __name__ == "__main__":
    run()