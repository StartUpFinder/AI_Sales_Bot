import json

PROJECTS = {
    "feedback": {
        "name": "AI Customer Feedback Analytics",
        "github": "https://github.com/Brkozshn/ai-customer-feedback-analytics",
        "demo": "https://streamable.com/be1utv?t=2&src=player-page-share",
        "one_liner": "automatically analyses customer feedback and turns it into actionable reports",
    },
    "chatbot": {
        "name": "AI SaaS Support Chatbot",
        "github": "https://github.com/Brkozshn/ai-saas-support-chatbot",
        "demo": "https://streamable.com/13jlsp?t=2&src=player-page-share",
        "one_liner": "handles repetitive customer queries automatically",
    },
    "dashboard": {
        "name": "AI Data Dashboard",
        "github": "https://github.com/Brkozshn/ai-data-dashboard",
        "demo": "https://streamable.com/13jlsp?t=2&src=player-page-share",  # 🔥 BURAYA DEMO EKLE (Eklenen link chatbot'a ait)
        "one_liner": "turns raw data into clear visual insights",
    },
}


SECTOR_MAP = {
    "ecommerce": ["feedback", "dashboard"],
    "saas": ["chatbot", "feedback"],
    "agency": ["dashboard", "feedback"],
    "law": ["chatbot"],
    "logistics": ["dashboard"],
    "manufacturing": ["dashboard"],
    "healthcare": ["chatbot"],
    "finance": ["dashboard"],
    "consulting": ["chatbot"],
    "other": ["dashboard"],
}


def _extract_industry(analysis: str) -> str:
    try:
        clean = analysis.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
        return data.get("industry", "other").lower()
    except:
        a = analysis.lower()

        if "ecommerce" in a:
            return "ecommerce"
        if "saas" in a:
            return "saas"
        if "law" in a:
            return "law"
        if "logistics" in a:
            return "logistics"
        if "agency" in a:
            return "agency"

        return "other"


def select_offer(analysis: str) -> str:

    industry = _extract_industry(analysis)

    ranked = SECTOR_MAP.get(industry, SECTOR_MAP["other"])

    return ranked[0]


def get_project(offer: str) -> dict:
    return PROJECTS.get(offer, PROJECTS["dashboard"])