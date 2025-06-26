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
        translated_parts = []
        for idx, part in enumerate(parts):
            try:
                translated_parts.append(
                    translator.translate(part, dest=target_lang).text
                )
            except Exception as exc:  # pragma: no cover - log only
                _LOG.warning(
                    "googletrans failed for chunk %d: %s", idx, exc
                )
                translated_parts.append(part)

        return "".join(translated_parts)
    except Exception as exc:
        _LOG.warning(
            "googletrans failed to translate to %s: %s", target_lang, exc
        )

    try:
        from deep_translator import GoogleTranslator  # type: ignore

        translator = GoogleTranslator(source="auto", target=target_lang)
        translated_parts = []
        for idx, part in enumerate(parts):
            try:
                translated_parts.append(translator.translate(part))
            except Exception as exc:  # pragma: no cover - log only
                _LOG.warning(
                    "deep_translator failed for chunk %d: %s", idx, exc
                )
                translated_parts.append(part)

        return "".join(translated_parts)
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


def summarize_blocks(blocks: List[str], max_sent: int = 1) -> List[str]:
    """Return a short summary for each text block in ``blocks``.

    Each block is cleaned using :func:`text_utils.clean_text` and summarized
    with :func:`simple_summary`. Empty blocks after cleaning are skipped.
    """

    from .text_utils import clean_text

    summaries: List[str] = []
    for raw in blocks:
        cleaned = clean_text(raw)
        if not cleaned:
            continue
        summaries.append(simple_summary(cleaned, max_sent=max_sent))
    return summaries


def _annotate_terms(text: str) -> str:
    """Return ``text`` with English terms duplicated in parentheses."""
    import re

    def repl(match: re.Match) -> str:
        eng = match.group(2)
        if f"({eng})" in match.group(0):
            return match.group(0)
        return f"{match.group(1)} {eng}({eng})"

    return re.sub(r"([\uAC00-\uD7A3]+)\s+([A-Za-z][A-Za-z0-9\- ]*)", repl, text)


def build_topic_script(articles: List[dict], target_lang: Optional[str] = None) -> str:
    """Return a topic-grouped broadcast script from ``articles``.

    Articles are grouped by the ``"topic"`` field. Each article summary is
    trimmed to two sentences with up to 40 characters per sentence. Short
    transition phrases are inserted between articles and the script ends with
    a friendly closing line.
    """
    from collections import defaultdict
    from .text_utils import split_sentences, clean_text

    topic_map: defaultdict[str, list[dict]] = defaultdict(list)
    for art in articles:
        topic = art.get("topic") or "기타"
        topic_map[topic].append(art)

    base_order = ["IT", "보안", "게임", "AI"]
    topics = [t for t in base_order if t in topic_map] + [
        t for t in topic_map.keys() if t not in base_order
    ]

    transitions = ["다음 소식입니다~", "이어서 볼까요?", "계속해서 전하겠습니다."]
    trans_idx = 0
    lines: list[str] = []

    for ti, topic in enumerate(topics):
        lines.append(f"▶ {topic}")
        arts = topic_map[topic]
        for ai, art in enumerate(arts):
            raw = art.get("script") or art.get("title", "")
            sents = split_sentences(raw)[:2]
            trimmed = []
            for s in sents:
                s = s.strip()
                if len(s) > 40:
                    s = s[:40]
                trimmed.append(s)
            summary = _annotate_terms(" ".join(trimmed))
            lines.append(clean_text(summary))
            last_topic = ti == len(topics) - 1
            last_art = ai == len(arts) - 1
            if not (last_topic and last_art):
                lines.append(transitions[trans_idx % len(transitions)])
                trans_idx += 1

    lines.append("오늘 소식은 여기까지입니다. 내일도 알찬 뉴스로 찾아뵐게요!")
    script = "\n".join(lines)
    if target_lang:
        script = translate_text(script, target_lang)
    return clean_text(script)
