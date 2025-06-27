"""
본문 추출 · 초간단 요약기
"""
from __future__ import annotations
import re, requests, bs4, logging
from .text_utils import clean_text

HEADERS = {"User-Agent": "Mozilla/5.0"}

_LOG = logging.getLogger(__name__)


def extract_with_newspaper(url: str) -> str:
    """Return article body text using ``newspaper`` library."""
    try:
        from newspaper import Article
    except Exception as e:  # ImportError or any failure
        raise RuntimeError("newspaper unavailable") from e

    art = Article(url)
    art.download()
    art.parse()
    return art.text or ""

def _regex_extract(html: str, min_len: int) -> str:
    """Fallback text extraction using regex when BeautifulSoup is unavailable."""
    if not html:
        return ""
    section = html
    m = re.search(r"<article[^>]*>(.*?)</article>", html, re.I | re.S)
    if not m:
        m = re.search(
            r"<div[^>]+(?:id|class)=(?:\"|')?[^>]*(?:content|article|body|entry)[^>]*(?:\"|')?[^>]*>(.*?)</div>",
            html,
            re.I | re.S,
        )
    if m:
        section = m.group(1)
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", section, re.I | re.S)
    lines: list[str] = []
    for p in paragraphs:
        txt = re.sub(r"<[^>]+>", "", p).strip()
        if len(txt) >= max(1, min_len):
            lines.append(txt)
    if not lines:
        lines = [re.sub(r"<[^>]+>", "", section)]
    return clean_text("\n".join(lines))

def _extract_from_html(html: str, min_len: int) -> str:
    """Extract main text from ``html`` using BeautifulSoup when available."""
    Soup = getattr(bs4, "BeautifulSoup", None)
    if Soup is None:
        return _regex_extract(html, min_len)
    try:
        soup = Soup(html or "", "html.parser")
        container = (
            soup.find("article")
            or soup.find("div", id=re.compile(r"(content|article|body)", re.I))
            or soup.find("div", class_=re.compile(r"(content|article|body|entry)", re.I))
        )
        if container:
            parts = [p.get_text(" ", strip=True) for p in container.find_all("p")]
            cleaned = clean_text("\n".join(parts))
            if cleaned:
                return cleaned
        text = []
        for p in soup.get_text("\n").splitlines():
            p = p.strip()
            if len(p) >= max(1, min_len):
                text.append(p)
        return clean_text("\n".join(text))
    except Exception as e:
        _LOG.debug("BeautifulSoup failed: %s", e)
        return _regex_extract(html, min_len)

def extract_main_text(url: str, min_len: int = 10) -> str:
    """Return cleaned main body text from the article page."""
    try:
        text = extract_with_newspaper(url)
        cleaned = clean_text(text)
        if cleaned:
            return cleaned
    except Exception as e:
        _LOG.debug("newspaper failed: %s", e)

    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        response.raise_for_status()
        html = response.text
        return _extract_from_html(html, min_len=min_len)
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
