"""
다양한 소스에서 기사 메타데이터를 모아 리스트로 반환
"""
from __future__ import annotations
import feedparser, logging, datetime as dt
from pathlib import Path
import yaml
from .naver_news_client import fetch_naver_articles
from .text_utils import clean_html_text
from .utils import filter_keywords

_LOG = logging.getLogger(__name__)
_ALLOWED_TOPICS = {"IT", "게임", "AI", "보안", "프로그래밍"}

# Keywords used to filter Naver search results.
# 원하는 단어로 변경할 수 있습니다. 예시:
# _INCLUDE_KEYWORDS = ["프로그램", "사이버 보안"]
_INCLUDE_KEYWORDS = [
    "프로그래밍",
    "인공지능",
    "AI",
    "보안",
    "클라우드",
    "반도체",
    "GPU",
    "데이터",
    "IoT",
    "블록체인",
    "로봇",
]
_EXCLUDE_KEYWORDS = [
    "공항",
    "cctv",
    "경비",
    "정치",
    "교육 프로그램",
    "대학일자리",
    "양성", "국정", "정부", "drama", "드라마", "개회", "의원",
    "주식",
    "사건",
    "사고",
]

_MAX_NAVER_ARTICLES = 20

_SRC_PATH = Path("rss_sources.yaml")


def _load_sources() -> list[dict]:
    """YAML 파일에서 수집 소스 목록을 로드합니다."""
    if not _SRC_PATH.exists():
        _LOG.warning("소스 파일 %s이 존재하지 않습니다", _SRC_PATH)
        return []
    with _SRC_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return data



# ✔ RSS ----------------------------------------------------------------------
def _fetch_rss(url: str, topic: str, days: int = 1) -> list[dict]:
    """Fetch RSS items within the given number of days and clean summaries."""
    cutoff = dt.datetime.now() - dt.timedelta(days=days)
    items: list[dict] = []
    for entry in feedparser.parse(url).entries:
        # pubDate → datetime
        pub = entry.get("published_parsed")
        if not pub:
            continue
        pub_dt = dt.datetime(*pub[:6])
        if pub_dt < cutoff:
            continue

        raw_sum = entry.get("summary", entry.get("description", ""))
        items.append(
            {
                "title":       entry.get("title", "").strip(),
                "link":        entry.get("link", ""),
                "summary":     clean_html_text(raw_sum),
                "topic":       topic,
                "pubDateISO":  pub_dt.isoformat(),
                "src":         "rss",
            }
        )
    _LOG.info("✅ %s: %d 개", topic, len(items))
    return items

# -----------------------------------------------------------------------------
def collect_all(days: int = 1, max_naver: int = _MAX_NAVER_ARTICLES) -> list[dict]:
    """Return articles from all configured sources.

    Parameters
    ----------
    days : int, optional
        Only include articles published within the last ``days``.
    max_naver : int, optional
        Maximum number of Naver articles to return after filtering.
    """
    sources = _load_sources()
    collected: list[dict] = []
    for src in sources:
        if src.get("type") == "rss":
            arts = _fetch_rss(src["url"], src.get("topic", ""), days=days)
            collected += arts
        elif src.get("type") == "naver":
            arts = fetch_naver_articles(
                src["query"],
                src.get("topic", ""),
                days=days,
                max_pages=src.get("max_pages", 10),
            )
            for a in arts:
                a["src"] = "naver"
            collected += arts
    filtered = [a for a in collected if a.get("topic") in _ALLOWED_TOPICS]
    _LOG.info("허용된 토픽 %s 기사 %d건", list(_ALLOWED_TOPICS), len(filtered))

    naver_only = [a for a in filtered if a.get("src") == "naver"]
    others = [a for a in filtered if a.get("src") != "naver"]

    naver_only = filter_keywords(
        naver_only,
        include=_INCLUDE_KEYWORDS,
        exclude=_EXCLUDE_KEYWORDS,
    )

    if len(naver_only) > max_naver:
        _LOG.info(
            "네이버 기사 %d건 중 처음 %d건 사용", len(naver_only), max_naver
        )
        naver_only = naver_only[:max_naver]

    filtered = others + naver_only
    _LOG.info("네이버 키워드 필터 후 %d건", len(filtered))
    return filtered
