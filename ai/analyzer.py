from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_company(text):

    prompt = f"""
You are a sharp B2B analyst. Analyze this company website text and return ONLY a valid JSON object — no markdown, no backticks, no explanation.

Website text:
{text}

Return this exact JSON structure:
{{
  "company_summary": "1 sentence describing what they do",
  "industry": "one of: ecommerce, saas, agency, law, logistics, manufacturing, healthcare, finance, consulting, other",
  "target_customer": "who they serve",
  "team_size_guess": "small / medium / large",
  "main_pain": "the single biggest operational pain this type of business faces — be specific",
  "time_or_money_loss": "where they are visibly losing time or money based on their industry",
  "tone": "formal / semi-formal / casual — based on their website language",
  "language": "tr / en / de / fr / es / it / nl / other — the primary language of the website",
  "specific_detail": "one specific thing you noticed about THIS company from the text — a service, a client type, a location, a claim they make — something unique to them"
}}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return res.choices[0].message.content