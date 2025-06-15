# utils.py
import logging
from datetime import datetime, timedelta, timezone
import email.utils

def setup_logging(level=logging.INFO):
    fmt = "%(asctime)s %(levelname)-8s %(message)s"
    logging.basicConfig(format=fmt, level=level)

def filter_recent(articles, days=7):
    """
    pubDate가 days 이내인 기사만 반환합니다.
    Naver pubDate 예: "Tue, 13 May 2025 09:30:00 +0900"
    """
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=days)

    recent = []
    for art in articles:
        pub = art.get("pubDate")
        if not pub:
            continue
        try:
            dt = email.utils.parsedate_to_datetime(pub)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
        except Exception:
            continue
        if dt_utc >= cutoff:
            recent.append(art)
    return recent

def filter_topic(articles, keywords):
    """
    제목 또는 description에 keywords 중 하나라도 포함된 기사만 반환.
    keywords 예: ["IT","프로그래밍","기술"]
    """
    out = []
    for art in articles:
        text = (art.get("title","") + " " + art.get("description","")).lower()
        if any(kw.lower() in text for kw in keywords):
            out.append(art)
    return out
