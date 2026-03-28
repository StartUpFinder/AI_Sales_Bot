import re
import requests

def extract_emails(url):
    try:
        res = requests.get(url, timeout=5)
        text = res.text

        emails = re.findall(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text
        )

        return list(set(emails))

    except:
        return []


def guess_email(domain):
    return f"info@{domain}"