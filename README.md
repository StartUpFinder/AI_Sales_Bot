# 🚀 AI Sales Bot

AI Sales Bot is a Python-based automation system designed to generate leads and send highly personalized cold emails to medium-sized companies (5–50 employees) across Europe and Turkey.

It combines lead generation, data enrichment, AI-powered email writing, and automated outreach, all integrated with Google Sheets for tracking and management.

> ⚠️ Note: Web Search API integration is planned but not yet implemented. The current version uses a basic Google scraper, which may return limited results.

---

## ✨ Features

### 🔎 Lead Generation

* Keyword-based company discovery by industry and region
* Extracts company websites and basic metadata
* Currently uses a simple scraper (upgradeable to APIs like RapidAPI, Bing, or Google Programmable Search)

### 🧠 Lead Enrichment

* Extracts emails directly from company websites
* Fallback email generation (info@domain) when none found
* Collects company name, website, and content snippets

### 📊 Database (Google Sheets)

* Stores all leads in Google Sheets
* Prevents duplicates
* Tracks email status (sent / failed / updated)

### ✉️ Email Automation

* AI-generated, human-like personalized emails
* Tailored based on company content and industry
* SMTP-based delivery via Gmail or Outlook

### 📈 Tracking (Planned - PRO+)

* Email open tracking
* Reply detection
* Performance analytics

---

## 🏗️ Project Structure

AI_SALES_BOT/
│
├── main.py
├── config.py
│
├── ai/
│   └── email_writer.py
│   └── analyzer.py
│   └── offer_selector.py
│
├── database/
│   └── sheets.py
│
├── mailer/
│   └── sender.py
│
├── enrichment/
│   └── email_finder.py
│
├── lead_generation/
│   ├── scraper.py
│   └── config.py

---

## ⚙️ Requirements

* Python 3.10+
* Google Sheets API enabled
* credentials.json (service account)
* OpenAI API key
* SMTP email account

---

## 📦 Installation

git clone https://github.com/username/AI_Sales_Bot.git
cd AI_SALES_BOT

python -m venv .venv
.venv\Scripts\activate (Windows)
source .venv/bin/activate (Mac/Linux)

pip install -r requirements.txt

---

## 🔑 Configuration

Create a Google Sheet named **Leads** with:

Company | Website | Industry | Email | Status

Add service account as editor and place credentials.json in root.

Update config.py:

OPENAI_API_KEY = "your-openai-key"
SMTP_EMAIL = "[your-email@gmail.com](mailto:your-email@gmail.com)"
SMTP_PASSWORD = "your-app-password"

---

## ▶️ Run

python main.py

---

## 🧠 Roadmap

* Web Search API integration
* Email tracking
* Advanced AI personalization
* Analytics dashboard

---

## ⚠️ Disclaimer

For educational and legitimate outreach use only.
