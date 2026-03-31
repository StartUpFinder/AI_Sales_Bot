from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_company(text):

    prompt = f"""
Analyze this company website.

{text}

Return JSON:

- what_they_do
- target_customer
- industry (ecommerce, saas, agency, law, logistics, other)
- main_problem
- where_they_are_losing_time_or_money
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content