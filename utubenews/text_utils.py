import re
import bs4

_RE_WS = re.compile(r"\s+")
_AD_PAT = re.compile(r"(?i)advert|sponsor|subscribe|광고|후원")

def clean_text(text: str) -> str:
    """Normalize whitespace and drop ad-like lines."""
    parts: list[str] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or _AD_PAT.search(line):
            continue
        parts.append(line)
    return _RE_WS.sub(" ", " ".join(parts)).strip()


def clean_html_text(html: str, min_len: int = 0) -> str:
    """Extract text from HTML and clean it."""
    soup = bs4.BeautifulSoup(html or "", "html.parser")
    text = []
    for p in soup.get_text("\n").splitlines():
        p = p.strip()
        if len(p) < max(1, min_len):
            continue
        text.append(p)
    return clean_text("\n".join(text))
