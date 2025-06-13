"""
다양한 소스에서 기사 메타데이터를 모아 리스트로 반환
"""
from __future__ import annotations
import feedparser, logging, datetime as dt
from pathlib import Path
from naver_news_client import fetch_naver_articles

_LOG = logging.getLogger(__name__)

# ✔ 필요한 RSS·검색 소스 정의 -----------------------------------------------
SOURCES = [
    # 정책브리핑
    {
        "type": "rss",
        "url":  "https://www.korea.kr/rss/policy.xml",
        "topic": "정책",
    },
    # VOA Science & Tech
    {
        "type": "rss",
        "url":  "https://www.voakorea.com/api/zgyqeqe%24qm",
        "topic": "국제과학",
    },
    # 네이버 IT/보안 키워드
    {
        "type":  "naver",
        "query": "AI 칩셋 보안",
        "topic": "IT",
    },
]

# ✔ RSS ----------------------------------------------------------------------
def _fetch_rss(url: str, topic: str, days: int = 7) -> list[dict]:
    cutoff = dt.datetime.now() - dt.timedelta(days=days)
    items: list[dict] = []
    for entry in feedparser.parse(url).entries:
        # pubDate → datetime
        pub = entry.get("published_parsed")
        if not pub:
            continue
        pub_dt = dt.datetime(*pub[:6])
        if pub_dt < cutoff:
            continue

        items.append(
            {
                "title":       entry.get("title", "").strip(),
                "link":        entry.get("link", ""),
                "summary":     entry.get("summary", entry.get("description", "")).strip(),
                "topic":       topic,
                "pubDateISO":  pub_dt.isoformat(),
            }
        )
    _LOG.info("✅ %s: %d 개", topic, len(items))
    return items

# -----------------------------------------------------------------------------
def collect_all() -> list[dict]:
    collected: list[dict] = []
    for src in SOURCES:
        if src["type"] == "rss":
            collected += _fetch_rss(src["url"], src["topic"])
        elif src["type"] == "naver":
            collected += fetch_naver_articles(src["query"], src["topic"])
    return collected
