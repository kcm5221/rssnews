"""Utilities for building a short script from an article."""

from __future__ import annotations

import re
import textwrap
from typing import Optional, List
import logging

from .text_utils import clean_text

_LOG = logging.getLogger(__name__)

# cache for the transformers summarization pipeline
_PIPELINE = None

# safety limit for model input tokens (DistilBART is 1024)
MAX_LLM_INPUT_TOKENS = 1024

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

    gt = None
    dt = None
    try:  # pragma: no cover - optional dependency
        from googletrans import Translator  # type: ignore

        gt = Translator()
    except Exception as exc:
        _LOG.warning("googletrans unavailable: %s", exc)

    if gt is None:
        try:  # pragma: no cover - optional dependency
            from deep_translator import GoogleTranslator  # type: ignore

            dt = GoogleTranslator(source="auto", target=target_lang)
        except Exception as exc:
            _LOG.warning(
                "deep_translator failed to translate to %s: %s", target_lang, exc
            )
            return text

    translated_parts = []
    for idx, part in enumerate(parts):
        translated = None
        if gt is not None:
            try:
                translated = gt.translate(part, dest=target_lang).text
            except Exception as exc:  # pragma: no cover - log only
                _LOG.warning("googletrans failed for chunk %d: %s", idx, exc)
        if translated is None and dt is None:
            try:  # pragma: no cover - optional dependency
                from deep_translator import GoogleTranslator  # type: ignore

                dt = GoogleTranslator(source="auto", target=target_lang)
            except Exception as exc:
                _LOG.warning(
                    "deep_translator failed to translate to %s: %s", target_lang, exc
                )
        if translated is None and dt is not None:
            try:
                translated = dt.translate(part)
            except Exception as exc:  # pragma: no cover - log only
                _LOG.warning("deep_translator failed for chunk %d: %s", idx, exc)

        translated_parts.append(translated if translated is not None else part)

    return "".join(translated_parts)

BULLET = "\u2022"


def simple_summary(text: str, max_sent: int = 3) -> str:
    """Return the ``max_sent`` longest sentences from ``text``."""

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = sorted(sentences, key=len, reverse=True)[:max_sent]
    return " ".join(sentences)


def llm_summarize(text: str, max_tokens: int = 180) -> str:
    """Summarize ``text`` using a local language model if available.

    The function attempts to load :func:`transformers.pipeline` with the
    ``"summarization"`` task. If the library or model is unavailable, it
    falls back to :func:`quick_summarize` for a simple heuristic summary. The
    default ``max_tokens`` value is large enough to keep most of the original
    content so the result reads more like a cleaned version than a short
    abstract.
    """

    if not text or not text.strip():
        return ""

    global _PIPELINE
    try:  # pragma: no cover - optional heavy dependency
        from transformers import pipeline  # type: ignore

        if _PIPELINE is None:
            try:
                _PIPELINE = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-12-6",
                    revision="a4f8f3e",
                )
            except TypeError:
                # older or stub pipelines may not accept these kwargs
                _PIPELINE = pipeline("summarization")

        if hasattr(_PIPELINE, "tokenizer"):
            tokenizer = _PIPELINE.tokenizer
            max_in = getattr(tokenizer, "model_max_length", MAX_LLM_INPUT_TOKENS)
            input_ids = tokenizer.encode(text, max_length=max_in, truncation=True)
            text = tokenizer.decode(input_ids, skip_special_tokens=True)
        else:
            words = text.split()
            if len(words) > MAX_LLM_INPUT_TOKENS:
                text = " ".join(words[:MAX_LLM_INPUT_TOKENS])
                words = words[:MAX_LLM_INPUT_TOKENS]
        words = text.split()
        max_length = min(max_tokens, len(words) + 5)
        min_length = min(len(words), max_length)
        result = _PIPELINE(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False,
            truncation=True,
        )
        if isinstance(result, list):
            data = result[0]
        else:
            data = result
        if isinstance(data, dict):
            out = data.get("summary_text") or data.get("generated_text")
        else:
            out = str(data)
        if out:
            return out.strip()
    except Exception as exc:
        _LOG.warning("llm_summarize failed: %s", exc)

    from .article_extractor import quick_summarize

    return quick_summarize("", text)


def normalize_script(text: str) -> str:
    """Return ``text`` with balanced quotes and closing punctuation."""

    trimmed = (text or "").strip()

    if (
        trimmed.count('"') % 2 == 1
        or trimmed.count('“') != trimmed.count('”')
        or trimmed.count("'") % 2 == 1
        or trimmed.count('‘') != trimmed.count('’')
    ):
        if trimmed.endswith(('"', '“', "'", '‘')):
            trimmed = trimmed[:-1]
        elif trimmed.count('“') > trimmed.count('”'):
            trimmed += '”'
        elif trimmed.count('‘') > trimmed.count('’'):
            trimmed += '’'

    if trimmed and trimmed[-1] not in '.!?':
        trimmed = trimmed.rstrip("\"”'’") + '…'

    return trimmed


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


def build_casual_script(
    articles: list[dict],
    target_lang: Optional[str] = None,
    add_closing: bool = True,
) -> str:
    """Return a casual one-person news script from ``articles``.

    Each article dict is expected to contain a ``"script"`` field holding a
    short summary. The first sentence becomes a hook line and up to the next
    two sentences are used as brief details. Articles are separated by a blank
    line. When ``add_closing`` is ``True`` a friendly closing line is appended.
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

    if add_closing:
        parts.append("오늘 뉴스는 여기까지입니다.")
    script = "\n\n".join(parts)
    if target_lang:
        script = translate_text(script, target_lang)
    cleaned_lines = [clean_text(line) for line in script.splitlines()]
    return "\n".join([l for l in cleaned_lines if l])


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


def postprocess_script(text: str, max_sent: int = 12) -> str:
    """Return ``text`` split into TTS-friendly sections.

    The input is broken into short sentences using :func:`split_sentences` and
    then grouped into blocks of ``max_sent`` sentences. A transition phrase is
    inserted between blocks and a closing line is appended.
    """

    from .text_utils import split_sentences

    sents = split_sentences(text)
    if not sents:
        return "오늘 뉴스는 여기까지입니다."

    transitions = ["계속해서 전하겠습니다.", "이어서 볼까요?", "다음 소식입니다~"]
    trans_idx = 0
    blocks: list[str] = []
    for i in range(0, len(sents), max_sent):
        blocks.append(" ".join(sents[i : i + max_sent]))

    lines: list[str] = []
    for idx, block in enumerate(blocks):
        lines.append(block)
        if idx < len(blocks) - 1:
            lines.append(transitions[trans_idx % len(transitions)])
            trans_idx += 1

    lines.append("오늘 뉴스는 여기까지입니다.")
    return "\n\n".join(lines)
