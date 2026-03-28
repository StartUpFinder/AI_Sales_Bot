import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean_google_url(href):
    if href.startswith("/url?q="):
        return href.split("/url?q=")[1].split("&")[0]
    return None


def search_google(query):
    url = f"https://www.google.com/search?q={query}"
    res = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(res.text, "html.parser")

    links = []

    for a in soup.select("a"):
        href = a.get("href")
        clean = clean_google_url(href) if href else None

        if clean and not any(x in clean for x in ["google", "youtube"]):
            links.append(clean)

    return list(set(links))[:10]


def extract_company_info(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string if soup.title else url

        return {
            "name": title.strip(),
            "website": url
        }

    except:
        return None


def extract_text_snippet(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs[:5]])

        return text[:1000]

    except:
        return ""