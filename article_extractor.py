"""
본문 추출 · 초간단 요약기
"""
from __future__ import annotations
import re, requests, bs4

_RE_WS = re.compile(r"\s+")

def extract_main_text(url: str, min_len: int = 300) -> str:
    """BeautifulSoup 이용, <p> 태그 모아 대략적인 본문만 반환"""
    try:
        html = requests.get(url, timeout=10).text
        soup = bs4.BeautifulSoup(html, "html.parser")
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = "\n".join(p for p in paragraphs if len(p) > 30)
        return _RE_WS.sub(" ", text).strip()
    except Exception:
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
