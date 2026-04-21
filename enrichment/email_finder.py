# ═══════════════════════════════════════════════════════════════════════════════
# enrichment/email_finder.py — Email Bulma ve Doğrulama Modülü
# ─────────────────────────────────────────────────────────────
# GÖREV:
#   Bir şirket için hem kişisel (karar verici) hem de generic (info@) email
#   adreslerini bulmak, doğrulamak ve skorlamak.
#
# KATMAN MİMARİSİ:
#   ┌─────────────────────────────────────────────────────────────────────────┐
#   │  find_all_targets(url, domain)  ← main.py'nin çağırdığı tek fonksiyon  │
#   │       ↓                                                                 │
#   │  ┌─── KİŞİSEL EMAİLLER ──────────────────────────────────────────┐    │
#   │  │  find_and_verify_emails(url)                                    │    │
#   │  │    ├── Apollo + Snov PARALEL  (confidence ≥ 60 → erken çıkış) │    │
#   │  │    ├── Hunter (yedek, confidence 40)                           │    │
#   │  │    └── HTML scraper (son çare, confidence 20)                  │    │
#   │  │  Her adayı _verify_email() ile doğrula → skora göre sırala    │    │
#   │  └────────────────────────────────────────────────────────────────┘    │
#   │       ↓                                                                 │
#   │  ┌─── GENERİC EMAİL ──────────────────────────────────────────────┐   │
#   │  │  Önce siteden (mailto: / regex) gerçek info@ bul               │   │
#   │  │  Bulunamazsa info@domain tahmin et                              │   │
#   │  └────────────────────────────────────────────────────────────────┘    │
#   │       ↓                                                                 │
#   │  Tüm liste döner: [{email, name, position, score, source, type}, ...]  │
#   └─────────────────────────────────────────────────────────────────────────┘
#
# DOĞRULAMA:
#   _verify_email() → önce Hunter (50 free/mo), bittiyse Abstract API (100 free/mo)
#
# KREDİ MALİYETİ (aylık free tier):
#   Apollo domain search : 100 export
#   Snov domain search   : 50 kredi
#   Hunter verification  : 50 doğrulama + 25 domain search
#   Abstract API         : 100 doğrulama
# ═══════════════════════════════════════════════════════════════════════════════

import re
import time
import logging
import requests
import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from config import (
    HUNTER_API_KEY,
    SNOV_CLIENT_ID,
    SNOV_CLIENT_SECRET,
    APOLLO_API_KEY,
    ABSTRACT_API_KEY,
)

logger = logging.getLogger(__name__)

HUNTER_BASE   = "https://api.hunter.io/v2"
SNOV_BASE     = "https://api.snov.io/v1"
APOLLO_BASE   = "https://api.apollo.io/api/v1"
ABSTRACT_BASE = "https://emailreputation.abstractapi.com/v1"

REQUEST_TIMEOUT = 10  # saniye

# Genel/rol email adresleri (info@, support@ vb.) — kişisel listeden çıkarılır,
# generic listede tutulur
ROLE_BLACKLIST = {
    "support", "info", "contact", "hello", "mail", "admin",
    "noreply", "no-reply", "webmaster", "office", "team",
    "newsletter", "billing", "sales",
}

# Email tahmin kalıpları — en yaygından en az yaygına sıralı
EMAIL_PATTERNS = [
    "{first}.{last}",
    "{first}{last}",
    "{f}{last}",
    "{first}",
    "{first}_{last}",
    "{last}.{first}",
]


# ═══════════════════════════════════════════════════════════════════════════════
# KATMAN 1 — HTML Scraper (Her zaman ücretsiz, yedek kaynak)
# ═══════════════════════════════════════════════════════════════════════════════

def extract_emails(url: str) -> list:
    """
    Bir website'in HTML içeriğinden email adreslerini toplar.
    İki yöntem kullanır: mailto: linkleri ve regex tarama.
    API katmanları başarısız olduğunda veya generic email ararken kullanılır.

    INPUT:
        url (str) — Website URL'si, örn. "https://firma.com/iletisim"

    OUTPUT:
        list[str] — Bulunan email adresleri listesi, tekrarlar temizlenmiş,
                    sıra korunmuş (dict.fromkeys ile).
                    Her email küçük harf ve geçerli format.
        Hata durumunda boş liste döner.

    ÖRNEK:
        extract_emails("https://firma.com") → ["info@firma.com", "ceo@firma.com"]
    """
    emails = []
    try:
        res = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Yöntem 1: <a href="mailto:..."> linkleri
        for a in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
            addr = a["href"].replace("mailto:", "").split("?")[0].strip().lower()
            if _is_valid_email(addr):
                emails.append(addr)

        # Yöntem 2: Tüm metinde regex ile email tarama
        raw_text = soup.get_text(" ")
        for match in re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", raw_text):
            if _is_valid_email(match):
                emails.append(match.lower())

    except Exception as e:
        logger.warning("extract_emails failed for %s: %s", url, e)

    return list(dict.fromkeys(emails))  # Tekrarı kaldır, sırayı koru


# ═══════════════════════════════════════════════════════════════════════════════
# KATMAN 2 — Apollo People Search (confidence: 70)
# ═══════════════════════════════════════════════════════════════════════════════

def _apollo_domain_search(domain: str) -> list:
    """
    Apollo mixed_people/search API'si ile bir domain'deki karar verici kişileri arar.
    Yalnızca belirli kıdemlilikleri hedefler: kurucu, CEO, VP, direktör, yönetici.

    INPUT:
        domain (str) — Temiz domain adı, örn. "firma.com"
                       www. olmadan, protocol olmadan.

    OUTPUT:
        list[dict] — Bulunan kişiler listesi. Her eleman:
            {
                "email":      str,  # kişinin email adresi
                "first_name": str,
                "last_name":  str,
                "position":   str,  # iş unvanı, örn. "CEO"
                "confidence": int,  # 70 (Apollo yüksek güvenilirlik)
                "source":     str,  # "apollo"
            }
        Hata veya API key yoksa boş liste döner.

    NOT:
        API key header'da "x-api-key" olarak gönderilir.
        person_seniorities filtresi yalnızca karar vericileri getirir,
        tüm çalışanları değil.
    """
    if not APOLLO_API_KEY:
        return []
    try:
        resp = requests.post(
            f"{APOLLO_BASE}/mixed_people/search",
            headers={"x-api-key": APOLLO_API_KEY, "Content-Type": "application/json"},
            json={
                "q_organization_domains": [domain],
                "page":     1,
                "per_page": 10,
                "person_seniorities": [
                    "owner", "founder", "c_suite",
                    "partner", "vp", "director", "manager",
                ],
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return []

        people  = resp.json().get("people", [])
        results = []
        for p in people:
            email = (p.get("email") or "").lower()
            if email and _is_valid_email(email):
                results.append({
                    "email":      email,
                    "first_name": p.get("first_name", ""),
                    "last_name":  p.get("last_name", ""),
                    "position":   p.get("title", ""),
                    "confidence": 70,
                    "source":     "apollo",
                })
        return results

    except Exception as e:
        logger.warning("Apollo domain search error for %s: %s", domain, e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# KATMAN 3 — Snov.io Domain Search (confidence: 60)
# ═══════════════════════════════════════════════════════════════════════════════

_snov_token_cache: dict = {}


def _snov_get_token() -> str:
    """
    Snov.io OAuth2 client_credentials token'ı alır veya cache'den döndürür.
    Token süresi dolmadan 60 saniye önce yenilenir.

    INPUT : Yok (config'den SNOV_CLIENT_ID ve SNOV_CLIENT_SECRET okunur)
    OUTPUT: str — geçerli access token, veya hata durumunda boş string ("")
    """
    global _snov_token_cache
    if _snov_token_cache.get("expires_at", 0) > time.time():
        return _snov_token_cache["access_token"]
    if not SNOV_CLIENT_ID or not SNOV_CLIENT_SECRET:
        return ""
    try:
        resp = requests.post(
            f"{SNOV_BASE}/oauth/access_token",
            json={
                "grant_type":    "client_credentials",
                "client_id":     SNOV_CLIENT_ID,
                "client_secret": SNOV_CLIENT_SECRET,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return ""
        data = resp.json()
        _snov_token_cache = {
            "access_token": data["access_token"],
            "expires_at":   time.time() + data.get("expires_in", 3600) - 60,
        }
        return _snov_token_cache["access_token"]
    except:
        return ""


def _snov_domain_search(domain: str) -> list:
    """
    Snov.io get-domain-emails-with-info endpoint'i ile domain'deki kişisel
    email adreslerini ve kişi bilgilerini getirir.

    INPUT:
        domain (str) — Temiz domain adı, örn. "firma.com"

    OUTPUT:
        list[dict] — Bulunan kişiler listesi. Her eleman:
            {
                "email":      str,
                "first_name": str,
                "last_name":  str,
                "position":   str,  # mevcut iş unvanı
                "confidence": int,  # 60 (Apollo'dan biraz düşük)
                "source":     str,  # "snov"
            }
        Token alınamazsa veya hata durumunda boş liste döner.

    NOT:
        "type": "personal" parametresi yalnızca kişisel emailları getirir,
        info@ gibi generic adresleri hariç tutar.
        1 kredi = 1 bulunan email (aylık 50 ücretsiz kredi).
    """
    token = _snov_get_token()
    if not token:
        return []
    try:
        resp = requests.get(
            f"{SNOV_BASE}/get-domain-emails-with-info",
            params={"domain": domain, "type": "personal", "limit": 5},
            headers={"Authorization": f"Bearer {token}"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return []

        entries = resp.json().get("emails", [])
        results = []
        for e in entries:
            jobs  = e.get("currentJob") or []
            title = jobs[0].get("title", "") if jobs else ""
            results.append({
                "email":      e.get("email", "").lower(),
                "first_name": e.get("firstName", ""),
                "last_name":  e.get("lastName", ""),
                "position":   title,
                "confidence": 60,
                "source":     "snov",
            })
        return [r for r in results if r["email"]]

    except Exception as e:
        logger.warning("Snov domain search error for %s: %s", domain, e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# KATMAN 4 — Hunter.io Domain Search (confidence: 40, yedek)
# ═══════════════════════════════════════════════════════════════════════════════

def _hunter_domain_search(domain: str) -> list:
    """
    Hunter.io domain-search endpoint'i ile bir domain'deki email adreslerini arar.
    Apollo ve Snov'dan sonuç gelmediğinde devreye giren 3. API katmanıdır.

    INPUT:
        domain (str) — Temiz domain adı, örn. "firma.com"

    OUTPUT:
        list[dict] — Bulunan emailler listesi. Her eleman:
            {
                "email":      str,
                "first_name": str,
                "last_name":  str,
                "position":   str,
                "confidence": int,  # 40 (diğerlerine göre daha düşük güvenilirlik)
                "source":     str,  # "hunter"
            }
        API key yoksa veya hata durumunda boş liste döner.

    NOT:
        Hunter ayda 25 ücretsiz domain search verir.
        confidence 40 olarak ayarlanmıştır çünkü Hunter veritabanı
        bazen eski veya tahmine dayalı emailler içerebilir.
    """
    if not HUNTER_API_KEY:
        return []
    try:
        resp = requests.get(
            f"{HUNTER_BASE}/domain-search",
            params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 5},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return []

        entries = resp.json().get("data", {}).get("emails", [])
        return [
            {
                "email":      e.get("value", "").lower(),
                "first_name": e.get("first_name", ""),
                "last_name":  e.get("last_name", ""),
                "position":   e.get("position", ""),
                "confidence": 40,
                "source":     "hunter",
            }
            for e in entries if e.get("value")
        ]

    except Exception as e:
        logger.warning("Hunter domain search error for %s: %s", domain, e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# DOĞRULAMA KATMANI
# ═══════════════════════════════════════════════════════════════════════════════

def _hunter_verify(email: str) -> dict:
    """
    Hunter.io email-verifier endpoint'i ile tek bir emaili doğrular.
    Birincil doğrulama kaynağı olarak kullanılır.

    INPUT:
        email (str) — Doğrulanacak email adresi, örn. "ceo@firma.com"

    OUTPUT:
        dict — {
            "status":     str,   # "valid" | "invalid" | "accept_all" | "unknown"
            "score":      int,   # 0-100 arası güven puanı
            "disposable": bool,  # Geçici/tek kullanımlık email mi?
            "webmail":    bool,  # Gmail/Hotmail gibi kişisel mi?
        }
        API key yoksa veya hata durumunda {"status": "unknown", "score": 0} döner.

    NOT:
        "accept_all" durumu: domain tüm emailleri kabul ediyor demektir (catch-all).
        Bu durum _is_deliverable()'da score ≥ 60 koşuluyla kabul edilir.
        Ayda 50 ücretsiz doğrulama.
    """
    if not HUNTER_API_KEY:
        return {"status": "unknown", "score": 0}
    try:
        resp = requests.get(
            f"{HUNTER_BASE}/email-verifier",
            params={"email": email, "api_key": HUNTER_API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return {"status": "unknown", "score": 0}

        d = resp.json().get("data", {})
        return {
            "status":     d.get("status", "unknown"),
            "score":      d.get("score", 0),
            "disposable": d.get("disposable", False),
            "webmail":    d.get("webmail", False),
        }
    except Exception:
        return {"status": "unknown", "score": 0}


def _abstract_verify(email: str) -> dict:
    """
    Abstract API Email Reputation endpoint'i ile email doğrular.
    Hunter'ın "unknown" döndürdüğü durumlarda yedek olarak devreye girer.

    INPUT:
        email (str) — Doğrulanacak email adresi

    OUTPUT:
        dict — {
            "status":     str,   # "valid" veya "unknown"
            "score":      int,   # quality_score × 100
            "disposable": bool,
            "webmail":    bool,
        }
        API key yoksa veya hata durumunda {"status": "unknown", "score": 0} döner.

    NOT:
        deliverability değerleri: DELIVERABLE, UNDELIVERABLE, RISKY, UNKNOWN
        Sadece DELIVERABLE → "valid" olarak map edilir.
        Ayda 100 ücretsiz doğrulama.
    """
    if not ABSTRACT_API_KEY:
        return {"status": "unknown", "score": 0}
    try:
        resp = requests.get(
            ABSTRACT_BASE,
            params={"api_key": ABSTRACT_API_KEY, "email": email},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return {"status": "unknown", "score": 0}

        d            = resp.json()
        deliverable  = d.get("deliverability", "")
        quality      = d.get("quality_score", "0") or "0"
        score        = int(float(quality) * 100)

        return {
            "status":     "valid" if deliverable == "DELIVERABLE" else "unknown",
            "score":      score,
            "disposable": d.get("is_disposable_email", {}).get("value", False),
            "webmail":    d.get("is_free_email", {}).get("value", False),
        }

    except Exception as e:
        logger.warning("Abstract verify error for %s: %s", email, e)
        return {"status": "unknown", "score": 0}


def _verify_email(email: str) -> dict:
    """
    Doğrulama router'ı: Önce Hunter dener, "unknown" gelirse Abstract'a geçer.

    INPUT:
        email (str) — Doğrulanacak email adresi

    OUTPUT:
        dict — _hunter_verify() veya _abstract_verify() formatında sonuç
               {"status", "score", "disposable", "webmail"}

    NOT:
        İki API'nin free kredisi bittiyse her ikisi de "unknown" döndürür.
        Bu durumda _is_deliverable() False döndüreceği için email atlanır.
    """
    result = _hunter_verify(email)
    if result["status"] == "unknown" and ABSTRACT_API_KEY:
        result = _abstract_verify(email)
    return result


def _is_deliverable(vr: dict) -> bool:
    """
    Doğrulama sonucunu yorumlar: bu emaile mail gönderilmeli mi?

    INPUT:
        vr (dict) — _verify_email() çıktısı

    OUTPUT:
        bool — True  → email gönderilmeye uygun
               False → geçersiz, disposable veya bilinmeyen, gönderme

    KURAL:
        - disposable email → her zaman False (spam trap riski)
        - status "valid" → True
        - status "accept_all" VE score ≥ 60 → True (makul güvenle gönder)
        - diğerleri → False
    """
    if vr.get("disposable"):
        return False
    if vr["status"] == "valid":
        return True
    if vr["status"] == "accept_all" and vr.get("score", 0) >= 60:
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# ANA ORKESTRATÖRLEr
# ═══════════════════════════════════════════════════════════════════════════════

def find_and_verify_emails(url: str) -> list:
    """
    Bir şirket URL'si için kişisel email adreslerini çok katmanlı arama ile bulur.
    Tüm adayları doğrular ve skora göre sıralar.
    find_all_targets() tarafından çağrılır, doğrudan main.py'den çağrılmaz.

    INPUT:
        url (str) — Şirketin website URL'si, örn. "https://firma.com"

    OUTPUT:
        list[dict] — Doğrulanmış ve sıralanmış kişisel email listesi. Her eleman:
            {
                "email":    str,
                "name":     str,   # "Ad Soyad" formatında
                "position": str,
                "score":    int,   # _priority_score() + confidence (0-170 arası)
                "source":   str,   # "apollo" | "snov" | "hunter" | "scrape"
                "verified": bool,  # Her zaman True (doğrulanmayanlar çıkarıldı)
            }
        Boş liste döner eğer hiçbir doğrulanabilir kişisel email bulunamazsa.

    AKIŞ:
        1. Apollo + Snov PARALEL çalıştırılır (ThreadPoolExecutor)
        2. İyi aday yoksa Hunter eklenir
        3. Hala yoksa HTML scraper çalıştırılır
        4. Tüm adaylar doğrulanır, düşük kaliteliler çıkarılır
        5. Final skor = _priority_score(unvan) + confidence(kaynak)
    """
    domain     = _extract_domain(url)
    candidates = []

    # ADIM 1: Apollo ve Snov paralel çalıştır (hız için)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_apollo = executor.submit(_apollo_domain_search, domain)
        future_snov   = executor.submit(_snov_domain_search, domain)
        candidates.extend(future_apollo.result())
        candidates.extend(future_snov.result())

    # ADIM 2: Yüksek güvenilir aday yoksa Hunter dene
    if not _has_good_candidate(candidates):
        candidates.extend(_hunter_domain_search(domain))

    # ADIM 3: Hala boşsa HTML scrape et
    if not _has_good_candidate(candidates):
        for addr in extract_emails(url):
            candidates.append({
                "email": addr, "first_name": "", "last_name": "",
                "position": "", "confidence": 20, "source": "scrape",
            })

    # Aynı email'i en yüksek confidence ile tut
    unique_candidates = {}
    for c in candidates:
        email = c["email"]
        if email not in unique_candidates or c["confidence"] > unique_candidates[email]["confidence"]:
            unique_candidates[email] = c

    # Doğrula, skora göre sırala
    verified = []
    for email, c in unique_candidates.items():
        vr = _verify_email(email)
        if not _is_deliverable(vr):
            continue
        final_score = _priority_score(c) + c["confidence"]
        verified.append({
            "email":    email,
            "name":     f"{c['first_name']} {c['last_name']}".strip(),
            "position": c.get("position") or "",
            "score":    final_score,
            "source":   c["source"],
            "verified": True,
        })

    verified.sort(key=lambda x: x["score"], reverse=True)
    return verified


def find_all_targets(url: str, domain: str = "") -> list:
    """
    Bir şirket için HEM kişisel (karar verici) HEM generic (info@) email
    adreslerini tek listede toplar. main.py'nin doğrudan çağırdığı tek fonksiyon.

    INPUT:
        url    (str) — Şirketin website URL'si
        domain (str) — Opsiyonel. Verilirse URL'den çıkarma yapılmaz.
                       Apollo'dan gelen şirketlerde domain zaten hazır gelir,
                       buraya pass etmek gereksiz HTTP parse işlemini önler.

    OUTPUT:
        list[dict] — Tüm hedefler listesi. Her eleman:
            {
                "email":    str,
                "name":     str,   # Kişisel emaillerde dolu, generic'te boş
                "position": str,   # Kişisel emaillerde dolu, generic'te boş
                "score":    int,
                "source":   str,
                "verified": bool,
                "type":     str,   # "personal" veya "generic"
            }
        List en az 1 eleman içerir (en kötü durumda info@domain guess ile).

    ÖRNEK ÇIKTI:
        [
            {"email": "ceo@firma.com",  "name": "Ali Yılmaz", "type": "personal", ...},
            {"email": "hr@firma.com",   "name": "Ayşe Kaya",  "type": "personal", ...},
            {"email": "info@firma.com", "name": "",            "type": "generic",  ...},
        ]
        main.py bu listedeki HER birine ayrı mail gönderir.

    AKIŞ:
        1. find_and_verify_emails() ile kişisel emailler → type="personal"
        2. Siteden generic email ara (info@, contact@) → type="generic"
        3. Bulunamazsa info@domain tahmin et → type="generic"
    """
    if not domain:
        domain = _extract_domain(url)

    all_targets  = []
    seen_emails  = set()

    # ── 1. Kişisel emailler ────────────────────────────────────────────────────
    personal_contacts = find_and_verify_emails(url)
    for c in personal_contacts:
        email = c["email"]
        local = email.split("@")[0].lower()

        # ROLE_BLACKLIST'tekileri personal listesinden çıkar (generic kısmında işlenecek)
        if any(r in local for r in ROLE_BLACKLIST):
            continue

        if email not in seen_emails:
            seen_emails.add(email)
            all_targets.append({**c, "type": "personal"})

    # ── 2. Generic email (info@, contact@ vb.) ────────────────────────────────
    scraped       = extract_emails(url)
    generic_found = False

    for addr in scraped:
        local = addr.split("@")[0].lower()
        # Sadece ROLE_BLACKLIST'teki adresleri generic olarak al
        if any(r in local for r in ROLE_BLACKLIST) and addr not in seen_emails:
            vr = _verify_email(addr)
            if _is_deliverable(vr):
                seen_emails.add(addr)
                all_targets.append({
                    "email":    addr,
                    "name":     "",
                    "position": "",
                    "score":    20,
                    "source":   "scrape_generic",
                    "verified": True,
                    "type":     "generic",
                })
                generic_found = True
                break   # İlk geçerli generic email yeterli

    # ── 3. Fallback: info@domain tahmini ─────────────────────────────────────
    if not generic_found:
        fallback = f"info@{domain}"
        if fallback not in seen_emails:
            seen_emails.add(fallback)
            all_targets.append({
                "email":    fallback,
                "name":     "",
                "position": "",
                "score":    10,
                "source":   "guess",
                "verified": False,   # Doğrulanmadı, tahmin
                "type":     "generic",
            })

    return all_targets


# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def pick_best_email(emails_or_contacts) -> str:
    """
    Email listesinden en iyi tek emaili seçer.
    Hem ham string listesi hem de dict listesi desteklenir.
    find_all_targets() yerine kullanılan eski kod için geriye dönük uyumluluk sağlar.

    INPUT:
        emails_or_contacts — list[str] veya list[dict]
            list[str]:  ["info@firma.com", "ceo@firma.com"]
            list[dict]: find_all_targets() veya find_and_verify_emails() çıktısı

    OUTPUT:
        str  — Seçilen tek email adresi
        None — Liste boşsa

    NOT:
        Dict listesi verildiğinde ilk elemanı döndürür (zaten skora göre sıralı).
        String listesi verildiğinde CEO/founder/owner öncelikli seçim yapar.
    """
    if not emails_or_contacts:
        return None

    if isinstance(emails_or_contacts[0], dict):
        return emails_or_contacts[0]["email"]

    priority_kw = ["ceo", "founder", "owner", "hello", "contact", "info"]
    for kw in priority_kw:
        for e in emails_or_contacts:
            if kw in e.lower():
                return e
    return emails_or_contacts[0]


def guess_email(domain: str, first_name: str = "", last_name: str = "") -> str:
    """
    Bir domain için olası email adresini tahmin eder.
    Tüm API'ler ve scraper başarısız olduğunda son çare olarak kullanılır.

    INPUT:
        domain     (str) — Temiz domain, örn. "firma.com"
        first_name (str) — Kişi adı (opsiyonel)
        last_name  (str) — Kişi soyadı (opsiyonel)

    OUTPUT:
        str — Tahmin edilen email:
              - İsim verilmişse: "ad.soyad@domain.com" (EMAIL_PATTERNS[0])
              - İsim yoksa:      "info@domain.com"

    NOT:
        Bu fonksiyon kesinlikle doğru olmayan bir tahmindir.
        verified=False olarak işaretlenir, ancak yine de gönderilir
        çünkü info@ adresi çoğu şirkette gerçekten mevcuttur.
    """
    if not first_name or not last_name:
        return f"info@{domain}"
    first = first_name.lower().strip()
    last  = last_name.lower().strip()
    f     = first[0] if first else ""
    return EMAIL_PATTERNS[0].format(first=first, last=last, f=f) + f"@{domain}"


def _extract_domain(url: str) -> str:
    """
    URL'den temiz domain çıkarır.

    INPUT : url (str) — "https://www.firma.com/sayfa" veya "firma.com"
    OUTPUT: str       — "firma.com"
    """
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    return parsed.netloc.replace("www.", "")


def _is_valid_email(email: str) -> bool:
    """
    Email adresinin geçerli format kontrolü (regex ile).

    INPUT : email (str)
    OUTPUT: bool — True = geçerli format, False = geçersiz
    """
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))


def _has_good_candidate(candidates: list) -> bool:
    """
    Listedeki adaylar arasında yüksek güvenilirlikli (Apollo/Snov kalitesinde)
    isimli bir contact var mı kontrol eder.
    Bu kontrol bir sonraki API katmanının çağrılıp çağrılmayacağına karar verir.

    INPUT:
        candidates (list[dict]) — Email aday listesi

    OUTPUT:
        bool — True  = confidence ≥ 60 ve first_name dolu olan en az 1 aday var
               False = daha fazla API çağrısı gerekiyor
    """
    return any(c.get("confidence", 0) >= 60 and c.get("first_name") for c in candidates)


def _priority_score(contact: dict) -> int:
    """
    Kişinin iş unvanına göre öncelik skoru hesaplar.
    find_and_verify_emails()'deki final skor hesabında confidence ile toplanır.

    INPUT:
        contact (dict) — "position" (iş unvanı) alanı içeren dict

    OUTPUT:
        int — 0-100 arası skor:
              100 → CEO, Founder, Owner, President
               90 → CTO, COO, CMO, Co-Founder
               75 → Director, VP, Head of
               60 → Manager, Lead, Principal
               10 → Scrape'den gelen ROLE_BLACKLIST emaili
               40 → Diğer tüm durumlar

    NOT:
        Yüksek skor → kişi find_all_targets() listesinde üstte çıkar
        → generate_email() bu kişi için kişiselleştirilmiş selamlama kullanır.
    """
    title = (contact.get("position") or "").lower()
    if any(k in title for k in ("ceo", "founder", "owner", "president")):
        return 100
    if any(k in title for k in ("cto", "coo", "cmo", "co-founder")):
        return 90
    if any(k in title for k in ("director", "vp", "vice president", "head of")):
        return 75
    if any(k in title for k in ("manager", "lead", "principal")):
        return 60
    if contact.get("source") == "scrape":
        if any(r in contact["email"].split("@")[0].lower() for r in ROLE_BLACKLIST):
            return 10
    return 40