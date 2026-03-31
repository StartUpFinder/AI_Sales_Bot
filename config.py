import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

# Lead generation keywords
SEARCH_KEYWORDS = [

    # 🇹🇷 LAW FIRMS
    "hukuk bürosu İstanbul küçük hukuk firması 5-50 çalışan",
    "avukatlık şirketi Türkiye boutique law firm",
    "İstanbul legal consultancy small team",

    # 🇹🇷 E-COMMERCE
    "e-ticaret markası Türkiye Shopify mağaza 5-50 çalışan",
    "online mağaza Türkiye DTC brand orta ölçekli",
    "Türkiye ecommerce startup small business",

    # 🇹🇷 MARKETING / AGENCIES
    "dijital pazarlama ajansı İstanbul küçük ekip 5-50 kişi",
    "Türkiye performance marketing agency small team",
    "creative agency Turkey boutique team",

    # 🇹🇷 SOFTWARE / SAAS
    "yazılım startup Türkiye SaaS 5-50 çalışan",
    "B2B SaaS company Turkey small business",
    "AI startup Turkey early stage team",

    # 🇹🇷 OTHER B2B
    "lojistik şirketi Türkiye KOBİ 5-50 çalışan",
    "imalat firması Türkiye orta ölçekli ihracat",
    
    # 🇪🇺 LAW
    "small law firm Germany legal consultancy 5-50 employees",
    "boutique law firm Netherlands legal small team",
    "legal consultancy Europe medium size firm",

    # 🇪🇺 E-COMMERCE
    "shopify store Europe small brand 5-50 employees",
    "DTC ecommerce company Europe medium business",
    "online retail startup Europe small team",

    # 🇪🇺 MARKETING / AGENCIES
    "digital marketing agency UK small business team",
    "performance marketing agency Europe boutique agency",
    "creative marketing company Europe medium team",

    # 🇪🇺 SOFTWARE / SAAS
    "B2B SaaS startup Europe 5-50 employees",
    "AI startup Europe small team",
    "software company Europe early stage 5-50",

    # 🔥 HIGH VALUE B2B
    "logistics company Europe SME medium size",
    "manufacturing company Turkey export SME",
    "supply chain company Europe 5-50 employees"
]


DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", 40))
MIN_DELAY = int(os.getenv("MIN_DELAY", 20))
MAX_DELAY = int(os.getenv("MAX_DELAY", 45))