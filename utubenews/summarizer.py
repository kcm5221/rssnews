"""Utilities for building a short script from an article."""

from __future__ import annotations

import re
import textwrap

BULLET = "\u2022"


def simple_summary(text: str, max_sent: int = 3) -> str:
    """Return the ``max_sent`` longest sentences from ``text``."""

    sentences = re.split(r"(?<=[.!?]) +", text)
    sentences = sorted(sentences, key=len, reverse=True)[:max_sent]
    return " ".join(sentences)


def build_script(title: str, body: str, source: str, license: str) -> str:
    """Return a short markdown script summarizing the article."""

    summary = simple_summary(body)
    return textwrap.dedent(
        f"""
        \u25B6 \uc624\ub298\uc758 \uae00\uc0c1: {title}

        {BULLET} \uc694\uc57d
        {summary}

        {BULLET} \ud574\uc124
        - (\uc5ec\uae30\uc5d0 \ub2f9\uc2e0\uc758 \uc758\uacac/\ubc30\uacbd \uc124\uba85 \ucd94\uac00)

        \ucd9c\ucc98: {source} / \ub77c\uc774\uc13c\uc2a4: {license}
        """
    ).strip()


def build_casual_script(articles: list[dict]) -> str:
    """Return a casual one-person news script from ``articles``.

    Each article dict is expected to contain a ``"script"`` field holding a
    short summary. The first sentence becomes a hook line and up to the next
    two sentences are used as brief details. Articles are separated by a blank
    line and the script ends with a friendly closing line.
    """

    parts: list[str] = []
    for art in articles:
        text = art.get("script", "").strip()
        if not text:
            continue
        sents = re.split(r"(?<=[.!?])\s+", text)
        if not sents:
            continue
        hook = sents[0].strip()
        extras = [s.strip() for s in sents[1:3] if s.strip()]
        if extras:
            part = "\n".join([hook] + extras)
        else:
            part = hook
        parts.append(part)

    parts.append("오늘 뉴스 여기까지! 좋은 하루 보내세요 😊")
    return "\n\n".join(parts)
