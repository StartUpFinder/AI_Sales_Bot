import os
from dotenv import load_dotenv

load_dotenv()

# ── AI ────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ── Mailer ────────────────────────────────────────────────────────────────────
SMTP_EMAIL    = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# ── Your identity (shows up in every email signature) ────────────────────────
SENDER_NAME     = os.getenv("SENDER_NAME", "")
SENDER_TITLE    = os.getenv("SENDER_TITLE", "")
SENDER_EMAIL    = os.getenv("SENDER_EMAIL", "")
SENDER_LINKEDIN = os.getenv("SENDER_LINKEDIN", "")

# ── Search — SerpAPI ──────────────────────────────────────────────────────────
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# ── Email discovery & verification APIs (freemium) ───────────────────────────
HUNTER_API_KEY     = os.getenv("HUNTER_API_KEY", "")
SNOV_CLIENT_ID     = os.getenv("SNOV_CLIENT_ID", "")
SNOV_CLIENT_SECRET = os.getenv("SNOV_CLIENT_SECRET", "")
APOLLO_API_KEY     = os.getenv("APOLLO_API_KEY", "")
ABSTRACT_API_KEY   = os.getenv("ABSTRACT_API_KEY", "")

# ── Search keywords ───────────────────────────────────────────────────────────
#
# BD LOGIC — target companies that:
#   1. Are growing but have no in-house data/AI team yet
#   2. Operate in sectors where AI ROI is fast and easy to demonstrate
#   3. Are small enough that the founder/director makes buying decisions quickly
#   4. Already spend money on tools — meaning they have budget and buy solutions
#
# Product → best-fit sector mapping:
#   AI Feedback Analytics  → ecommerce, hospitality, SaaS with reviews/NPS
#   AI Support Chatbot     → law firms, clinics, SaaS, financial advisors
#   AI Data Dashboard      → logistics, manufacturing, marketing agencies, real estate


# ─────────────────────────────────────────────────────────────────────────────
#  KEYWORD STRATEGY (CRITICAL)
# ─────────────────────────────────────────────────────────────────────────────

# ✅ Apollo için (KISA ve NET keywordler)
APOLLO_KEYWORDS = [
    "ecommerce",
    "agency",
    "saas",
    "b2b saas",
    "startup",
    "scaleup",
    "law firm",
    "legal services",
    "marketing agency",
    "digital marketing",
    "logistics",
    "supply chain",
    "real estate",
    "property management",
    "healthcare",
    "consulting",
    "dental clinic",
]


# ✅ Google için (pain-based, uzun keywordler)

GOOGLE_KEYWORDS = [

    # ── 🇹🇷 AJANS / CONSULTING ───────────────────────────────
    "danışmanlık şirketi istanbul iletişim",
    "consulting firm turkey contact",
    "business consulting istanbul about us",
    "management consulting turkey team",

    # ── 🇹🇷 SAAS / YAZILIM ───────────────────────────────────
    "yazılım şirketi istanbul iletişim",
    "software company turkey contact",
    "b2b yazılım firması istanbul about",
    "saas company turkey team",

    # ── 🇹🇷 HUKUK ────────────────────────────────────────────
    "law firm istanbul contact",
    "hukuk bürosu istanbul iletişim",
    "avukatlık bürosu istanbul team",
    "boutique law firm istanbul contact",

    # ── 🇹🇷 LOJİSTİK ─────────────────────────────────────────
    "lojistik firması istanbul iletişim",
    "logistics company turkey contact",
    "nakliye firması istanbul about us",
    "freight company turkey team",

    # ── 🇹🇷 GAYRİMENKUL ──────────────────────────────────────
    "gayrimenkul danışmanlık istanbul iletişim",
    "real estate agency turkey contact",
    "property management istanbul about",

    # ── 🇪🇺 SAAS / SOFTWARE ─────────────────────────────────
    "b2b saas company europe contact",
    "software company germany about us",
    "saas startup uk team page",
    "software firm netherlands contact",

    # ── 🇪🇺 CONSULTING / AGENCY ─────────────────────────────
    "consulting firm uk contact",
    "management consulting germany impressum",
    "business consulting netherlands team",
    "strategy consulting europe contact",

    # ── 🇪🇺 HUKUK ───────────────────────────────────────────
    "law firm uk contact us",
    "boutique law firm germany impressum",
    "legal firm netherlands team",
    "cabinet avocat paris contact",

    # ── 🇪🇺 LOJİSTİK ────────────────────────────────────────
    "logistics company germany contact",
    "supply chain company europe about",
    "freight company netherlands contact",
    "logistics company poland team",

    # ── 🇪🇺 GAYRİMENKUL ─────────────────────────────────────
    "real estate agency uk contact",
    "property management germany impressum",
    "real estate firm netherlands team",

    # ── 🔥 HIGH QUALITY SIGNAL ─────────────────────────────
    "small company founders team europe",
    "company leadership team about us europe",
    "management team company turkey about",
]


DAILY_LIMIT = int(os.getenv("DAILY_LIMIT"))
MIN_DELAY   = int(os.getenv("MIN_DELAY"))
MAX_DELAY   = int(os.getenv("MAX_DELAY"))