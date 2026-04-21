# ═══════════════════════════════════════════════════════════════════════════════
# lead_generation/scraper.py — Lead Bulma Modülü
# ───────────────────────────────────────────────
# GÖREV:
#   Şirket listesi üretmek ve şirket websitelerinden içerik çekmek.
#   İki farklı lead kaynağı vardır:
#
#   1. Apollo API  (search_apollo_companies)
#      → Keyword + lokasyon + çalışan sayısı filtresiyle doğrudan şirket DB'si
#      → Her sonuçta name, website, domain bilgisi gelir
#      → Avantajı: Yapılandırılmış veri, domain bilgisi hazır
#
#   2. Google / SerpAPI  (search_google)
#      → Keyword ile Google'da arama yapar, website URL'leri döndürür
#      → extract_company_info() ile title ve URL'den şirket bilgisi çıkarılır
#      → Avantajı: Apollo'da olmayan küçük yerel firmaları bulabilir
# ═══════════════════════════════════════════════════════════════════════════════

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HEADERS        = {"User-Agent": "Mozilla/5.0"}
SERPAPI_KEY    = os.getenv("SERPAPI_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

# Google sonuçlarından filtrelenmesi gereken büyük platformlar ve bloglar.
# Bunlar gerçek şirket sayfası değil, iş ilanı veya e-ticaret platformlarıdır.
BLOCKLIST = [
    "instagram.com", "facebook.com", "linkedin.com", "twitter.com",
    "youtube.com", "medium.com", "shopify.com", "amazon.com",
    "trendyol.com", "hepsiburada.com", "apps.shopify.com", "hulkapps.com",
]


# ───────────────────────────────────────────────────────────────────────────────
def search_apollo_companies(keyword, locations, employee_ranges):
    """
    Apollo organizations/search API'si ile kurumsal B2B şirketleri arar.
    Ana lead kaynağı olarak kullanılır.

    INPUT:
        keyword         (str)       — Arama terimi, örn. "saas", "law firm", "manufacturing"
                                      Apollo bunu şirket açıklaması ve keyword tag'lerinde arar.
        locations       (list[str]) — Hedef ülke/şehir listesi,
                                      örn. ["Turkey", "Germany", "United Kingdom"]
        employee_ranges (list[str]) — Çalışan sayısı aralıkları,
                                      örn. ["11,50", "51,200"]
                                      Format: "min,max" — her iki uç dahildir.

    OUTPUT:
        list[dict] — Bulunan şirket listesi. Her eleman:
            {
                "name":    str,  # Şirket adı, örn. "Acme Software"
                "website": str,  # Tam URL, örn. "https://acme.com"
                "domain":  str   # Temiz domain, örn. "acme.com"
                                 # email_finder'ın domain araması için kullanılır
            }
        Hata durumunda veya API anahtarı yoksa boş liste döner.

    NOT:
        Endpoint: POST https://api.apollo.io/v1/organizations/search
        API key header'da "x-api-key" olarak gönderilir (body'de değil).
        Free tier: Aylık 10.000 API çağrısı, 100 email export.
        *** Sadece info@ ve benzeri emailleri cekebiliyor.***
        *** v1/mixed/search endpoint'i ile kişi emailleri sağlıklı şekilde çekilebilir. (35$ / ay) **********
    """
    if not APOLLO_API_KEY:
        print("UYARI: APOLLO_API_KEY bulunamadı!")
        return []

    if locations is None:
        locations = ["Turkey"]
    if employee_ranges is None:
        employee_ranges = ["1,10", "11,50", "51,200"]

    try:
        resp = requests.post(
            "https://api.apollo.io/v1/organizations/search",  # 🔥 ENDPOINT GÜNCELLENDİ
            headers={
                "x-api-key":     APOLLO_API_KEY,   # ← Key MUTLAKA header'da
                "Content-Type":  "application/json",
                "Cache-Control": "no-cache",
            },
            json={
                "q_organization_keyword_tags":       [keyword],
                "organization_locations":            locations,
                "organization_num_employees_ranges": employee_ranges,
                "page":     1,
                "per_page": 10,
            },
            timeout=15,
        )

        if resp.status_code != 200:
            print(f"❌ [APOLLO] {resp.status_code}: {resp.text}")
            return []

        organizations = resp.json().get("organizations", [])
        companies = []

        for org in organizations:
            website = org.get("website_url", "") or ""
            name    = org.get("name", "")
            domain  = org.get("primary_domain", "") or ""

            # Website URL yoksa domain'den türet
            if not website and domain:
                website = f"https://{domain}"

            if name and (website or domain):
                companies.append({
                    "name":    name,
                    "website": website,
                    "domain":  domain,
                })

        return companies

    except Exception as e:
        print(f"Apollo company search error: {e}")
        return []


# ───────────────────────────────────────────────────────────────────────────────
def search_google(query):
    """
    SerpAPI üzerinden Google arama yapar ve şirket website URL'lerini döndürür.
    Apollo çalışmadığında veya limit bittiğinde yedek lead kaynağı olarak devreye girer.

    INPUT:
        query (str) — Google arama sorgusu,
                      örn. "B2B SaaS startup Turkey 5-50 employees"

    OUTPUT:
        list[str] — Filtrelenmiş website URL'leri listesi, maksimum 10 eleman.
                    BLOCKLIST'teki platformlar (LinkedIn, Shopify vb.) çıkarılmıştır.
                    Bu URL'ler extract_company_info() ile şirkete çevrilir.
        Hata veya SERPAPI_KEY yoksa boş liste döner.

    NOT:
        SerpAPI free tier: Aylık 100 arama.
    """
    if not SERPAPI_KEY:
        return []
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={"api_key": SERPAPI_KEY, "engine": "google", "q": query, "num": 15},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("organic_results", [])
        links   = []

        for r in results:
            url = r.get("link", "")
            # Kara listede olmayan URL'leri ekle
            if url and not any(b in url for b in BLOCKLIST):
                links.append(url)

        return links[:10]

    except Exception as e:
        print(f"search_google error: {e}")
        return []


# ───────────────────────────────────────────────────────────────────────────────
def extract_company_info(url):
    """
    Bir website URL'sinden temel şirket bilgisini çıkarır.
    Sadece Google kaynaklı URL'ler için kullanılır.
    Apollo sonuçlarında şirket bilgisi zaten yapılandırılmış gelir.

    INPUT:
        url (str) — Website URL'si, örn. "https://firma.com"

    OUTPUT:
        dict veya None — Başarılıysa: {"name": str, "website": str}
            name    → <title> tag'inden alınır, yoksa URL kullanılır
            website → verilen URL
        Bağlantı hatası veya timeout durumunda None döner.

    NOT:
        Apollo'dan gelen şirketlerde "domain" alanı da bulunur,
        bu fonksiyondan dönen dict'te domain yoktur.
        main.py'deki get_domain() ile URL'den türetilir.
    """
    try:
        res  = requests.get(url, timeout=5, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.title.string if soup.title else url
        return {"name": title.strip(), "website": url}
    except:
        return None


# ───────────────────────────────────────────────────────────────────────────────
def extract_full_text(url):
    """
    Bir website'in tüm görünür metin içeriğini çeker.
    OpenAI analizi ve is_small_business() kontrolü için ham metin sağlar.

    INPUT:
        url (str) — Website URL'si

    OUTPUT:
        str — Sayfanın temizlenmiş metin içeriği, maksimum 5000 karakter.
              Script ve style tag'leri çıkarılmış, boşluklar normalize edilmiş.
        Hata durumunda boş string ("") döner.

    NOT:
        5000 karakter limiti OpenAI token maliyetini kontrol altında tutar.
        Çoğu şirketin "hakkımızda" bilgisi bu limitin içinde kalır.
    """
    try:
        res  = requests.get(url, timeout=8, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        # JavaScript ve CSS içeriğini çıkar
        for tag in soup(["script", "style"]):
            tag.extract()

        text = soup.get_text(separator=" ")
        return " ".join(text.split())[:5000]
    except:
        return ""


# ───────────────────────────────────────────────────────────────────────────────
def is_small_business(text):
    """
    Website metninden şirketin hedef profilde olup olmadığını kontrol eder.
    Sadece gerçek şirket sitelerini pipeline'a almak için basit bir filtredir.

    INPUT:
        text (str) — extract_full_text() çıktısı, şirketin website metni

    OUTPUT:
        bool — True  → şirket pipeline'a alınır (mail gönderilecek)
               False → şirket atlanır (Google'dan gelen blog/platform vb. temizler)

    NOT:
        Kontrol çok basit tutulmuştur: sadece temel şirket kelimelerini arar.
        Bu fonksiyon "büyük" / "küçük" ayırt etmez, adına rağmen;
        asıl amacı gerçek bir şirket sayfası olup olmadığını doğrulamaktır.
        İleride çalışan sayısı veya gelir filtresi eklenebilir.
    """
    keywords = ["about", "team", "agency", "startup", "company", "hakkımızda", "iletişim"]
    return any(k in text.lower() for k in keywords)