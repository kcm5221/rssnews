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


def merge_text_blocks(texts: list[str], titles: list[str] | None = None) -> str:
    """Return a single cleaned script from ``texts``.

    Each item in ``texts`` is cleaned using :func:`clean_text`. Duplicate
    blocks are skipped. When ``titles`` are provided, each cleaned block is
    prefixed with ``"## {title}"`` using the matching title.
    Blocks are separated by a blank line.
    """

    titles = titles or []
    seen: set[str] = set()
    out_parts: list[str] = []
    for idx, raw in enumerate(texts):
        cleaned = clean_text(raw)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        if idx < len(titles):
            block = f"## {titles[idx].strip()}\n{cleaned}"
        else:
            block = cleaned
        out_parts.append(block)
    return "\n\n".join(out_parts)


def split_sentences(text: str, filler: str = "입니다.") -> list[str]:
    """Return cleaned short sentences from ``text``.

    The input is normalized using :func:`clean_text` and then split on
    punctuation. Fragments that lack terminal punctuation are finalized with a
    period. When a fragment ends with a Hangul character, ``filler`` is
    appended to clarify the predicate.
    """

    cleaned = clean_text(text)
    if not cleaned:
        return []

    raw_sents = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    sentences: list[str] = []
    for frag in raw_sents:
        frag = frag.strip()
        if not frag:
            continue
        if frag.endswith(('.', '!', '?')):
            sentences.append(frag)
            continue
        if re.search(r"[\uAC00-\uD7A3]$", frag):
            sentences.append(frag + filler)
        else:
            sentences.append(frag + '.')
    return sentences
