"""Generic helper utilities used across the package."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
import email.utils

def setup_logging(level: int = logging.INFO) -> None:
    """Configure basic console logging."""

    fmt = "%(asctime)s %(levelname)-8s %(message)s"
    logging.basicConfig(format=fmt, level=level)

def filter_recent(articles: list[dict], days: int = 7) -> list[dict]:
    """Return only articles published within ``days`` from now."""

    # Naver pubDate 예: "Tue, 13 May 2025 09:30:00 +0900"
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=days)

    recent: list[dict] = []
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

def filter_topic(articles: list[dict], keywords: list[str]) -> list[dict]:
    """Return articles whose title or description contains ``keywords``."""
    out: list[dict] = []
    for art in articles:
        text = (art.get("title","") + " " + art.get("description","")).lower()
        if any(kw.lower() in text for kw in keywords):
            out.append(art)
    return out


def filter_keywords(
    articles: list[dict],
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[dict]:
    """Filter ``articles`` by include and exclude keyword lists.

    The check is case-insensitive and looks for keywords in the article title
    and description. Articles must contain at least one ``include`` keyword
    (when provided) and none of the ``exclude`` keywords.
    """

    include = [kw.lower() for kw in include or []]
    exclude = [kw.lower() for kw in exclude or []]

    result: list[dict] = []
    for art in articles:
        text = (art.get("title", "") + " " + art.get("description", "")).lower()

        if include and not any(kw in text for kw in include):
            continue
        if exclude and any(kw in text for kw in exclude):
            continue

        result.append(art)

    return result
