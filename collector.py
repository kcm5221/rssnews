"""
다양한 소스에서 기사 메타데이터를 모아 리스트로 반환
"""
from __future__ import annotations
import feedparser, logging, datetime as dt
from pathlib import Path
import yaml
from naver_news_client import fetch_naver_articles
from text_utils import clean_html_text

_LOG = logging.getLogger(__name__)
_ALLOWED_TOPICS = {"IT", "게임", "AI"}

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
            }
        )
    _LOG.info("✅ %s: %d 개", topic, len(items))
    return items

# -----------------------------------------------------------------------------
def collect_all(days: int = 1) -> list[dict]:
    """모든 소스에서 기사를 수집합니다."""
    sources = _load_sources()
    collected: list[dict] = []
    for src in sources:
        if src.get("type") == "rss":
            collected += _fetch_rss(src["url"], src.get("topic", ""), days=days)
        elif src.get("type") == "naver":
            collected += fetch_naver_articles(src["query"], src.get("topic", ""), days=days)
    filtered = [a for a in collected if a.get("topic") in _ALLOWED_TOPICS]
    _LOG.info("허용된 토픽 %s 기사 %d건", list(_ALLOWED_TOPICS), len(filtered))
    return filtered
