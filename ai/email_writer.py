from openai import OpenAI
from config import OPENAI_API_KEY
from ai.offer_selector import get_project
import json

client = OpenAI(api_key=OPENAI_API_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse_analysis(analysis: str) -> dict:
    try:
        clean = analysis.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except:
        return {}


def _detect_language(data: dict) -> str:
    lang = data.get("language", "")
    if lang in ["tr", "en"]:
        return lang

    text = (data.get("main_pain", "") + data.get("specific_detail", "")).lower()

    if any(w in text for w in [" ve ", " için ", " ile ", "şirket", "müşteri"]):
        return "tr"

    return "en"


def _clean(text: str) -> str:
    return text.strip().replace("\n", " ")


def format_html(text: str) -> str:
    return text.replace("\n", "<br>")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def generate_email(company: str, analysis: str, offer: str, contact_name: str = "") -> str:

    data = _parse_analysis(analysis)
    project = get_project(offer)
    language = _detect_language(data)

    specific_detail = _clean(data.get("specific_detail", ""))
    main_pain = _clean(data.get("main_pain", ""))

    # İsmi düzeltme (Örn: "Ahmet Yılmaz" -> Sadece "Ahmet" alır ve baş harfini büyütür)
    greeting_name = contact_name.strip().split()[0].capitalize() if contact_name else ""

    # fallback (çok önemli)
    if not specific_detail:
        specific_detail = f"I came across {company} and your work caught my attention."

    if not main_pain:
        main_pain = "Many growing teams struggle with manual processes slowing them down."

    project_name = project.get("name", "AI Çözümü")
    one_liner = project.get("one_liner", "süreçleri otomatikleştirir")

    # ─────────────────────────────────────────────────────────────────────────
    # PROMPTS (Ürün Adı ve Yeteneği Eklendi)
    # ─────────────────────────────────────────────────────────────────────────

    if language == "tr":
        prompt = f"""
Şirket: {company}

KURALLAR:
- Sadece Türkçe yaz
- Maksimum 60 kelime
- Kesinlikle satış yapar gibi yazma (doğal, b2b sohbeti gibi yaz)
- "Selam", "Merhaba", "Saygılar" gibi giriş/çıkış kelimelerini KULLANMA. Sadece ana metni ver.

ZORUNLU KULLANIM:
- Şu detayı doğal şekilde cümleye yedir: "{specific_detail}"
- Şirketin yaşadığı şu problemi belirt: "{main_pain}"
- Kendi geliştirdiğin "{project_name}" isimli araçtan bahset.
- Bu aracın "{one_liner}" yeteneği ile şirketin yukarıda belirttiğin problemini nasıl tam olarak çözeceğini net ve etkili bir şekilde açıkla.
"""
    else:
        prompt = f"""
Company: {company}

RULES:
- Max 60 words
- Natural tone (not salesy)
- DO NOT write greetings ("Hi", "Hello") or sign-offs ("Best", "Cheers"). Output ONLY the body paragraphs.

MANDATORY:
- Use this detail naturally: "{specific_detail}"
- Highlight this pain point naturally: "{main_pain}"
- Introduce your custom tool called "{project_name}".
- Explain clearly how this tool's ability to "{one_liner}" directly solves the exact pain point you mentioned.
"""

    # ─────────────────────────────────────────────────────────────────────────
    # OPENAI CALL 
    # ─────────────────────────────────────────────────────────────────────────

    res = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    body_text = res.choices[0].message.content.strip()

    # ─────────────────────────────────────────────────────────────────────────
    # ASSEMBLE EMAIL (Link ve İsim %100 Hatasız Ekleniyor)
    # ─────────────────────────────────────────────────────────────────────────

    if language == "tr":
        greeting = f"Selam {greeting_name}," if greeting_name else "Selam,"
        final_email = f"{greeting}\n\n{body_text}\n\nDemo: {project['demo']}\n\nKısa bir görüşmeye açık olur musunuz?"
    else:
        greeting = f"Hi {greeting_name}," if greeting_name else "Hi,"
        final_email = f"{greeting}\n\n{body_text}\n\nDemo: {project['demo']}\n\nWould you be open to a quick chat?"

    return format_html(final_email)