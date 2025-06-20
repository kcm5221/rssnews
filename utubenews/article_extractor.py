"""
본문 추출 · 초간단 요약기
"""
from __future__ import annotations
import re, requests, bs4, logging
from .text_utils import clean_html_text, clean_text

_LOG = logging.getLogger(__name__)

def extract_main_text(url: str, min_len: int = 30) -> str:
    """Return cleaned main body text from the article page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
        return clean_html_text(html, min_len=min_len)
    except requests.exceptions.RequestException as e:
        _LOG.warning("Failed to fetch %s: %s", url, e)
        return ""
    except Exception as e:
        _LOG.warning("Failed to parse %s: %s", url, e)
        return ""

def quick_summarize(title: str, text: str, max_sent: int = 3) -> str:
    """
    ▶ 문장 단위로 자르고, 단어 빈도 기준 top-N 문장 선택
    ▶ 너무 짧으면 `text` 처음 200자 정도를 반환
    """
    if len(text) < 200:
        return text[:200] + "..."
    # 문장 분할
    sents = re.split(r"(?<=[.!?。])\s+", text)
    if len(sents) <= max_sent:
        return " ".join(sents)
    # 단어 빈도
    from collections import Counter
    words = Counter(re.findall(r"[A-Za-z가-힣]+", text.lower()))
    scored = sorted(
        ((sum(words[w.lower()] for w in re.findall(r"[A-Za-z가-힣]+", s)), i, s) for i, s in enumerate(sents)),
        reverse=True,
    )
    top = sorted(scored[:max_sent], key=lambda x: x[1])  # 원문 순서 유지
    return " ".join(s for _, _, s in top)
