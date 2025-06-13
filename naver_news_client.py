"""
네이버 검색 API 기사 수집 (최근 7일 이내)
"""
from __future__ import annotations
import os, requests, datetime as dt, html, re, logging

NAVER_URL = "https://openapi.naver.com/v1/search/news.json"
HEADERS = {
    "X-Naver-Client-Id":     os.getenv("NAVER_CLIENT_ID", ""),
    "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET", ""),
}

_DISPLAY = 100
_TAG = re.compile(r"<[^>]+>")
_LOG = logging.getLogger(__name__)

def _clean(txt: str) -> str:
    return html.unescape(_TAG.sub("", txt)).strip()

def _parse(s: str) -> dt.datetime:
    return dt.datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %z")

def fetch_naver_articles(query: str, topic: str, days: int = 7, max_pages: int = 10) -> list[dict]:
    now = dt.datetime.now()
    cutoff = now - dt.timedelta(days=days)
    articles: list[dict] = []

    for p in range(max_pages):
        start = p * _DISPLAY + 1
        params = {"query": query, "display": _DISPLAY, "start": start, "sort": "date"}
        r = requests.get(NAVER_URL, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        for a in r.json().get("items", []):
            pub = _parse(a["pubDate"]).replace(tzinfo=None)
            if pub < cutoff:
                _LOG.info("� 7일 이전 기사 도달, 조기 종료")
                return articles
            articles.append(
                {
                    "title":       _clean(a["title"]),
                    "link":        a["link"],
                    "summary":     _clean(a["description"]),
                    "topic":       topic,
                    "pubDateISO":  pub.isoformat(),
                }
            )
    _LOG.info("✅ 네이버(%s): %d 개", query, len(articles))
    return articles
