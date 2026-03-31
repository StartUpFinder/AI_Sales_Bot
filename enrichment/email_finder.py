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


def pick_best_email(emails):

    if not emails:
        return None

    priority = ["ceo", "founder", "owner", "hello", "contact", "info"]

    for p in priority:
        for e in emails:
            if p in e.lower():
                return e

    return emails[0]


def guess_email(domain):
    return f"info@{domain}"