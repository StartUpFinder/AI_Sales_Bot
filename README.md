AI Sales Bot

AI Sales Bot is a Python-based automation tool designed to send highly personalized cold emails to medium-sized companies (5–50 employees) in Europe and Turkey.

The project covers lead generation, email automation, and Google Sheets database management.

⚠️ Web Search API integration is planned but not yet implemented. Currently, a simple Google scraper is used.

🔹 Features

1️⃣ Lead Generation
Currently uses Google scraping, but can be upgraded to a Web Search API (RapidAPI, Bing Search, or Google Programmable Search)
Collects company information and website URLs
Keyword-based searches by industry and location

2️⃣ Lead Enrichment
Extract emails from company website (extract_emails)
Guess email if none found (guess_email)
Collect company name, website, and snippet text

3️⃣ Database
Stores data in Google Sheets
Duplicate checking
Status tracking (sent / failed / updated)

4️⃣ Email Automation
AI-generated personalized emails (generate_email)
SMTP sending via Gmail or Outlook (send_email)
Human-like style with company-specific details

5️⃣ Tracking (PRO+ plan)
Email opens and replies tracking (planned, not yet implemented)


🔹 Project Structure

AI_SALES_BOT/
│
├── main.py                  # Main script
├── config.py                # Settings & keyword lists
├── ai/
│   └── email_writer.py      # AI-powered email generator
├── database/
│   └── sheets.py            # Google Sheets connection & storage
├── email/
│   └── sender.py            # SMTP sending
├── enrichment/
│   └── email_finder.py      # Email extraction / guessing
├── lead_generation/
│   ├── scraper.py           # Google scraper (temporary)
│   └── config.py            # Lead generation settings


🔹 Requirements

Python 3.10+
Google Sheets API enabled & credentials.json for service account
OpenAI API Key
Gmail or Outlook SMTP account

Python packages:

pip install -r requirements.txt

Example requirements.txt:

openai
gspread
oauth2client
requests
beautifulsoup4


🔹 Setup

Clone the project:
git clone https://github.com/username/AI_Sales_Bot.git
cd AI_Sales_Bot
Create & activate a virtual environment:
python -m venv .venv

.venv\Scripts\activate      # Windows
# or

source .venv/bin/activate   # Mac/Linux
Install dependencies:
pip install -r requirements.txt
Add your credentials.json for Google Sheets service account.
Configure config.py with your SMTP credentials and OpenAI API key.
Create a Google Sheet named Leads with these column headers:
Company | Website | Industry | Email | Status

🔹 Running the Bot
python main.py
Currently, the bot uses a simple scraper to find links.
If no links are found, the Sheet will remain empty.
Integration with Web Search API will dramatically improve response rate and reliability.

🔹 Future / PRO+ Upgrades
Web Search API integration → RapidAPI, Bing, or Google Programmable Search
Email open & reply tracking
Advanced AI email generation → using company snippet analysis and demo project references
Response rate optimization → throttling, delays, and A/B testing

🔹 Usage Tips
Test with 5–10 keywords first.
Verify that emails are being sent and data is written to the Sheet before scaling.
PRO+ with Web Search API will increase response rates significantly.