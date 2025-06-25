"""Utilities for building a short script from an article."""

from __future__ import annotations

import re
import textwrap
from typing import Optional, List
import logging

_LOG = logging.getLogger(__name__)

# maximum characters allowed in a single translation request
MAX_TRANSLATE_CHARS = 5000


def _chunk_text(text: str) -> List[str]:
    """Split ``text`` into <= ``MAX_TRANSLATE_CHARS`` sized chunks."""
    if len(text) <= MAX_TRANSLATE_CHARS:
        return [text]

    parts: List[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > MAX_TRANSLATE_CHARS and current:
            parts.append(current)
            current = line
        else:
            current += line
    if current:
        parts.append(current)

    # Fallback in case a single line is extremely long
    result: List[str] = []
    for part in parts:
        if len(part) <= MAX_TRANSLATE_CHARS:
            result.append(part)
        else:
            for i in range(0, len(part), MAX_TRANSLATE_CHARS):
                result.append(part[i : i + MAX_TRANSLATE_CHARS])
    return result


def translate_text(text: str, target_lang: str) -> str:
    """Translate ``text`` into ``target_lang`` if possible.

    This uses :mod:`googletrans` or :mod:`deep_translator` if available.
    If translation fails for any reason, the original ``text`` is returned.
    """

    parts = _chunk_text(text)

    try:
        from googletrans import Translator  # type: ignore

        translator = Translator()
        if len(parts) == 1:
            return translator.translate(parts[0], dest=target_lang).text
        result = translator.translate(parts, dest=target_lang)
        if not isinstance(result, list):
            result = [result]
        return "".join(r.text for r in result)
    except Exception as exc:
        _LOG.warning(
            "googletrans failed to translate to %s: %s", target_lang, exc
        )

    try:
        from deep_translator import GoogleTranslator  # type: ignore

        translator = GoogleTranslator(source="auto", target=target_lang)
        if len(parts) == 1:
            return translator.translate(parts[0])
        translated = [translator.translate(p) for p in parts]
        return "".join(translated)
    except Exception as exc:
        _LOG.warning(
            "deep_translator failed to translate to %s: %s", target_lang, exc
        )
        return text

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


def build_casual_script(articles: list[dict], target_lang: Optional[str] = None) -> str:
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
    script = "\n\n".join(parts)
    if target_lang:
        return translate_text(script, target_lang)
    return script
