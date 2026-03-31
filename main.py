
from lead_generation.scraper import (
    search_google,
    extract_company_info,
    extract_full_text,
    is_small_business
)

from enrichment.email_finder import (
    extract_emails,
    guess_email,
    pick_best_email
)

from ai.analyzer import analyze_company
from ai.offer_selector import select_offer
from ai.email_writer import generate_email
from mailer.sender import send_email, generate_subject
from database.sheets import connect_sheet, save_or_update, get_all_data

from urllib.parse import urlparse
from config import SEARCH_KEYWORDS, DAILY_LIMIT, MIN_DELAY, MAX_DELAY

import datetime
import time
import random
import uuid


def get_domain(url):
    return urlparse(url).netloc.replace("www.", "")


def run():

    sheet = connect_sheet()
    existing_data = get_all_data(sheet)

    sent_emails = {row["Email"]: row["Status"] for row in existing_data}

    sent_count = 0

    for keyword in SEARCH_KEYWORDS:

        links = search_google(keyword)
        print(f"Found links for '{keyword}': {links}")  # <--- debug

        for link in links:

            if sent_count >= DAILY_LIMIT:
                print("Daily limit reached")
                return

            company = extract_company_info(link)
            print(f"Company info: {company}")  # <--- debug
            if not company:
                continue

            full_text = extract_full_text(link)
            if not full_text:
                continue

            if not is_small_business(full_text):
                continue

            analysis = analyze_company(full_text)
            offer = select_offer(analysis)

            emails = extract_emails(link)
            email = pick_best_email(emails)

            if not email:
                email = guess_email(get_domain(link))

            if email in sent_emails and sent_emails[email] == "sent":
                continue

            ai_email = generate_email(company["name"], analysis, offer)

            tracking_id = str(uuid.uuid4())
            subject = generate_subject(offer)

            success = send_email(email, ai_email, tracking_id, subject)

            status = "sent" if success else "failed"

            save_or_update(sheet, [
                company["name"],
                company["website"],
                offer,
                email,
                status,
                tracking_id,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                "no",  # Opened
                "no"   # Replied
            ])

            sent_count += 1

            time.sleep(random.randint(MIN_DELAY, MAX_DELAY))


if __name__ == "__main__":
    run()