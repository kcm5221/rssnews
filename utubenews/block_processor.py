"""Utility to clean, summarize, split and translate text blocks."""

from __future__ import annotations

from typing import List, Optional

from .summarizer import summarize_blocks, translate_text
from .text_utils import clean_text, split_sentences


def process_blocks(
    blocks: List[str],
    titles: Optional[List[str]] | None = None,
    target_lang: str = "ko",
) -> str:
    """Return a translated script built from ``blocks``.

    Parameters
    ----------
    blocks:
        Raw text blocks from various sources.
    titles:
        Optional titles for each block. When provided, the cleaned block is
        prefixed with ``"## {title}"`` before summarizing.
    target_lang:
        Language code to translate the final script into.
    """

    titles = titles or []
    cleaned: List[str] = []
    seen: set[str] = set()
    for idx, raw in enumerate(blocks):
        text = clean_text(raw)
        if not text or text in seen:
            continue
        seen.add(text)
        if idx < len(titles):
            cleaned.append(f"## {titles[idx].strip()}\n{text}")
        else:
            cleaned.append(text)

    summaries = summarize_blocks(cleaned, max_sent=2)

    sentences: List[str] = []
    for summary in summaries:
        sentences.extend(split_sentences(summary))

    script = "\n".join(sentences)
    translated = translate_text(script, target_lang) if target_lang else script
    return clean_text(translated)
