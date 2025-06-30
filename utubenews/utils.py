"""Generic helper utilities used across the package."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
import email.utils
import re
from difflib import SequenceMatcher

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
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[dict]:
    """Return ``articles`` filtered by ``include`` and ``exclude`` keywords.

    The search is case-insensitive and looks for keywords in the article title,
    description, or summary. Articles containing any ``exclude`` keyword are
    removed. When ``include`` is given, only articles containing at least one of
    the ``include`` keywords are kept.
    """

    include = [kw.lower() for kw in include or []]
    exclude = [kw.lower() for kw in exclude or []]

    result: list[dict] = []
    for art in articles:
        text = (
            art.get("title", "")
            + " "
            + art.get("description", "")
            + " "
            + art.get("summary", "")
        ).lower()

        if exclude and any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in exclude):
            continue
        if include and not any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in include):
            continue

        result.append(art)

    return result


def deduplicate(
    articles: list[dict], *, similarity_threshold: float = 1.0
) -> list[dict]:
    """Return new list with duplicate entries removed.

    Articles with the same ``link`` or the same ``title`` are considered
    duplicates. When ``similarity_threshold`` is below ``1.0`` the check
    becomes fuzzy and also compares how similar titles (or available text)
    are using :class:`difflib.SequenceMatcher`.
    The first occurrence is kept while later ones are dropped.
    """

    if not 0 < similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be in (0, 1]")

    seen_links: set[str] = set()
    seen_titles: list[str] = []  # stored in lowercase for fuzzy comparison
    seen_texts: list[str] = []
    unique: list[dict] = []

    for art in articles:
        link = (art.get("link") or "").strip().lower()
        title = (art.get("title") or "").strip()
        title_key = title.lower()
        text = (art.get("summary") or art.get("body") or "").strip()
        text_key = text.lower()

        if link in seen_links or title_key in seen_titles:
            continue

        is_dup = False
        if similarity_threshold < 1.0:
            for t in seen_titles:
                if SequenceMatcher(None, title_key, t).ratio() >= similarity_threshold:
                    is_dup = True
                    break
            if not is_dup and text_key:
                for txt in seen_texts:
                    if SequenceMatcher(None, text_key, txt).ratio() >= similarity_threshold:
                        is_dup = True
                        break

        if is_dup:
            continue

        seen_links.add(link)
        seen_titles.append(title_key)
        if text_key:
            seen_texts.append(text_key)
        unique.append(art)

    return unique


def deduplicate_fuzzy(
    articles: list[dict], *, similarity_threshold: float = 0.9
) -> list[dict]:
    """Wrapper around :func:`deduplicate` with fuzzy matching enabled."""

    return deduplicate(articles, similarity_threshold=similarity_threshold)
