# naver_client.py
"""Simplified wrapper around the Naver Search API."""

from __future__ import annotations

import datetime
import logging
import os
import requests

NAVER_URL = "https://openapi.naver.com/v1/search/news.json"
HEADERS = {
    "X-Naver-Client-Id":  os.getenv("NAVER_CLIENT_ID"),
    "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET"),
    "User-Agent": "utubenews/1.0",
}

log = logging.getLogger(__name__)
TODAY = datetime.date.today()

def search_today(query: str, max_pages: int = 10, page_size: int = 100) -> list[dict]:
    """Return articles from the past two days for ``query``."""

    results: list[dict] = []
    for page in range(max_pages):
        start = page * page_size + 1          # 1-based
        params = {
            "query": query,
            "display": page_size,
            "start": start,
            "sort": "date",                   # 최신순
        }
        resp = requests.get(NAVER_URL, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            break

        for it in items:
            # 날짜 파싱
            pub_dt = datetime.datetime.strptime(it["pubDate"],
                                                "%a, %d %b %Y %H:%M:%S %z")
            pub_date = pub_dt.date()
            if pub_date < TODAY - datetime.timedelta(days=1):
                return results   # 더 내려갈 필요 없음
            results.append({
                "title": it["title"],
                "url":   it["originallink"] or it["link"],
                "summary": it["description"],
                "source": "Naver News",
                "license": "출처 표기·변형 사용 (뉴스저작권 예외조항)",
                "pub_date": str(pub_date)
            })
    return results
