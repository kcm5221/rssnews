import argparse
import json
import logging
from pathlib import Path

import requests
import bs4

from .text_utils import clean_text
from .utils import setup_logging, REQUEST_HEADERS
_LOG = logging.getLogger(__name__)


def extract_body(url: str) -> str:
    """Return cleaned body text from the article page."""
    body = ""
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        resp.raise_for_status()
        Soup = getattr(bs4, "BeautifulSoup", None)
        if Soup is not None:
            soup = Soup(resp.text, "html.parser")
            content = soup.find("article") or soup.find("div", class_="content")
            if content:
                paragraphs = [p.get_text(" ", strip=True) for p in content.find_all("p")]
                body = " ".join(paragraphs)
    except Exception as exc:
        _LOG.warning("Failed to fetch %s: %s", url, exc)
    return clean_text(body)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract article bodies and update JSON")
    parser.add_argument("articles", help="Input JSON file with articles")
    parser.add_argument("output", help="Path to output JSON file")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args(argv)

    setup_logging(level=args.log_level.upper())

    with open(args.articles, encoding="utf-8") as f:
        articles = json.load(f)

    for art in articles:
        link = art.get("link", "")
        art["body"] = extract_body(link)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(articles)} articles to {args.output}")
    return Path(args.output)


if __name__ == "__main__":
    main()
