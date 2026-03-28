from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_email(company, industry, snippet):

    prompt = f"""
Write a highly personalized cold email.

Company: {company}
Industry: {industry}

Website Info:
{snippet}

Rules:
- Mention something specific about the company
- Suggest a relevant AI automation idea
- Keep it human and natural
- Max 100 words
- No generic phrases

Examples:
- Law → client intake automation
- Ecom → support chatbot
- SaaS → onboarding automation

End with a question.
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content