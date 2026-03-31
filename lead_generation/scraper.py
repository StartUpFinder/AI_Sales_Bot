import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


def search_google(query):
    url = f"https://www.google.com/search?q={query}"
    res = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(res.text, "html.parser")

    links = []

    for a in soup.select("a"):
        href = a.get("href")
        if href and "/url?q=" in href:
            clean = href.split("/url?q=")[1].split("&")[0]

            if "google" not in clean and "youtube" not in clean:
                links.append(clean)

    return list(set(links))[:10]


def extract_company_info(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string if soup.title else url

        return {"name": title.strip(), "website": url}

    except:
        return None


def extract_full_text(url):
    try:
        res = requests.get(url, timeout=8, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup(["script", "style"]):
            tag.extract()

        text = soup.get_text(separator=" ")
        return " ".join(text.split())[:5000]

    except:
        return ""


def is_small_business(text):

    keywords = ["about", "team", "agency", "startup", "company"]

    return any(k in text.lower() for k in keywords)