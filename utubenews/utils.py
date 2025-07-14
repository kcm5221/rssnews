"""Generic helper utilities used across the package."""

from __future__ import annotations

import logging
import re
import subprocess
from typing import Sequence

# Default headers used for HTTP requests
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}

_LOG = logging.getLogger(__name__)
from difflib import SequenceMatcher

def setup_logging(level: int = logging.INFO) -> None:
    """Configure basic console logging."""

    fmt = "%(asctime)s %(levelname)-8s %(message)s"
    logging.basicConfig(format=fmt, level=level)



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


def run_as_sudo(cmd: Sequence[str]) -> bool:
    """Run ``cmd`` with sudo after confirming with the user.

    Parameters
    ----------
    cmd : Sequence[str]
        Command and arguments to execute with ``sudo``.

    Returns
    -------
    bool
        ``True`` if the command executed, ``False`` otherwise.
    """

    prompt = "관리자 권한이 필요합니다. 계속하시겠습니까? (y/N): "
    try:
        ans = input(prompt)
    except EOFError:
        ans = ""

    if ans.strip().lower() != "y":
        _LOG.info("사용자가 관리자 권한 승인을 거부했습니다.")
        return False

    try:
        subprocess.run(["sudo", "-E", *cmd], check=True)
        return True
    except Exception as exc:
        _LOG.error("sudo 명령 실패: %s", exc)
        return False
