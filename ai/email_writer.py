from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_email(company, analysis, offer):

    prompt = f"""
Write a cold email.

Company: {company}

Insights:
{analysis}

Offer type:
{offer}

Context:
I built small AI systems for businesses like this.

Solutions:
- feedback → customer feedback analytics
- chatbot → AI support chatbot
- dashboard → AI data dashboard

Instructions:
- Start with real observation
- Identify ONE problem
- Suggest ONE solution
- Mention demo
- 60-80 words
- human tone
- no sales language
- end with question

Before writing:
Think about the company's pain point.
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content