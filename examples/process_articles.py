import json
import sys
import requests
from bs4 import BeautifulSoup

from utubenews.text_utils import clean_text
from utubenews.summarizer import translate_text
from utubenews.utils import REQUEST_HEADERS

def fetch_article(link: str) -> tuple[str, str]:
    """Return cleaned title and body text from the article page."""
    title, body = "", ""
    try:
        resp = requests.get(link, headers=REQUEST_HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # attempt to find headline
        title_el = soup.find("h1") or soup.find(class_="headline") or soup.title
        if title_el:
            title = title_el.get_text(strip=True)

        # gather article paragraphs
        content = soup.find("article") or soup.find("div", class_="content")
        if content:
            paragraphs = [p.get_text(" ", strip=True) for p in content.find_all("p")]
            body = " ".join(paragraphs)
    except Exception as exc:
        print(f"Failed to fetch {link}: {exc}")
    return clean_text(title), clean_text(body)

def process_articles(articles: list[dict], target_lang: str) -> list[dict]:
    """Return new list with extracted and translated fields."""
    result = []
    for art in articles:
        link = art.get("link", "")
        title, body = fetch_article(link)
        title_tr = translate_text(title, target_lang)
        body_tr = translate_text(body, target_lang)
        art.update({
            "title": title,
            "body": body,
            "title_translated": title_tr,
            "body_translated": body_tr,
        })
        result.append(art)
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_articles.py input.json [target_lang]")
        sys.exit(1)
    target_lang = sys.argv[2] if len(sys.argv) > 2 else "ko"
    with open(sys.argv[1], encoding="utf-8") as f:
        articles = json.load(f)
    processed = process_articles(articles, target_lang)
    print(json.dumps(processed, ensure_ascii=False, indent=2))
