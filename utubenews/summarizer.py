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

