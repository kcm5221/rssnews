"""
본문 추출 · 초간단 요약기
"""
from __future__ import annotations
import re, requests, bs4, logging, time
from .text_utils import clean_text
from .utils import REQUEST_HEADERS

_LOG = logging.getLogger(__name__)


def _get_with_retries(url: str, headers: dict[str, str], attempts: int = 3, delay: float = 1.0):
    """Return ``requests.get(url, headers=headers)`` with retry logic."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            last_exc = e
            if i < attempts - 1:
                time.sleep(delay)
    if last_exc:
        raise last_exc


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


def extract_with_readability(html: str) -> str:
    """Return main text using ``readability-lxml`` Document."""
    try:
        from readability import Document
    except Exception as e:
        raise RuntimeError("readability unavailable") from e

    doc = Document(html or "")
    content = doc.summary() or ""
    text = re.sub(r"<[^>]+>", " ", content)
    return clean_text(text)


def extract_with_trafilatura(html: str) -> str:
    """Return main text using ``trafilatura`` library."""
    try:
        import trafilatura
    except Exception as e:
        raise RuntimeError("trafilatura unavailable") from e

    try:
        text = trafilatura.extract(html or "", favor_recall=True)
    except Exception as e:
        raise RuntimeError("trafilatura failed") from e
    return clean_text(text or "")


def fetch_html_selenium(url: str, wait: float = 2.0) -> str:
    """Fetch ``url`` using Selenium for JS-heavy pages."""
    try:
        import chromedriver_autoinstaller
        from selenium import webdriver
    except Exception as e:
        raise RuntimeError("selenium unavailable") from e

    chromedriver_autoinstaller.install()
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(url)
        time.sleep(wait)
        return driver.page_source
    finally:
        driver.quit()

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
        if len(cleaned) >= min_len:
            _LOG.info("extracted with newspaper")
            return cleaned
    except Exception as e:
        _LOG.debug("newspaper failed: %s", e)

    html = ""
    try:
        response = _get_with_retries(url, REQUEST_HEADERS)
        html = response.text
    except requests.exceptions.RequestException as e:
        _LOG.warning("Failed to fetch %s: %s", url, e)
        return ""

    try:
        text = extract_with_readability(html)
        if len(text) >= min_len:
            _LOG.info("extracted with readability")
            return text
    except Exception as e:
        _LOG.debug("readability failed: %s", e)

    try:
        text = extract_with_trafilatura(html)
        if len(text) >= min_len:
            _LOG.info("extracted with trafilatura")
            return text
    except Exception as e:
        _LOG.debug("trafilatura failed: %s", e)

    try:
        text = _extract_from_html(html, min_len=min_len)
        if text:
            _LOG.info("extracted with html parser")
        return text
    except Exception as e:
        _LOG.warning("Failed to parse %s: %s", url, e)
        return ""

def quick_summarize(text: str, max_sent: int = 3) -> str:
    """Return a short summary built from the most frequent sentences.

    The input ``text`` is split by sentence and the top ``max_sent`` sentences
    with the highest word frequency are returned. When the text is shorter than
    200 characters it is returned as-is with an ellipsis.
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
