from lead_generation.scraper import (
    search_google,
    extract_company_info,
    extract_text_snippet
)

from enrichment.email_finder import extract_emails, guess_email
from ai.email_writer import generate_email
from email.sender import send_email
from database.sheets import connect_sheet, save_or_update, get_all_data

from urllib.parse import urlparse
from config import SEARCH_KEYWORDS


def get_domain(url):
    return urlparse(url).netloc.replace("www.", "")


def detect_industry(text):

    text = text.lower()

    if "law" in text or "legal" in text:
        return "Law Firm"
    elif "shop" in text:
        return "E-commerce"
    elif "saas" in text or "software" in text:
        return "SaaS"
    elif "agency" in text:
        return "Marketing Agency"
    elif "logistics" in text:
        return "Logistics"

    return "General"


def run():

    sheet = connect_sheet()
    existing_data = get_all_data(sheet)

    sent_emails = {row["Email"]: row["Status"] for row in existing_data}

    for keyword in SEARCH_KEYWORDS:

        print(f"\n🔍 Searching: {keyword}")

        links = search_google(keyword)

        for link in links:

            company = extract_company_info(link)
            if not company:
                continue

            snippet = extract_text_snippet(link)
            industry = detect_industry(snippet)

            emails = extract_emails(link)

            if emails:
                email = emails[0]
            else:
                email = guess_email(get_domain(link))

            # Eğer zaten gönderilmişse SKIP
            if email in sent_emails and sent_emails[email] == "sent":
                print(f"⏭️ Skipped (already sent): {email}")
                continue

            ai_email = generate_email(
                company["name"],
                industry,
                snippet
            )

            success = send_email(email, ai_email)

            status = "sent" if success else "failed"

            result = save_or_update(sheet, [
                company["name"],
                company["website"],
                industry,
                email,
                status
            ])

            print(f"✅ {company['name']} | {email} | {status} | {result}")


if __name__ == "__main__":
    run()