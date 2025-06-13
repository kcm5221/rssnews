"""
다양한 소스에서 기사 메타데이터를 모아 리스트로 반환
"""
from __future__ import annotations
import feedparser, logging, datetime as dt
from pathlib import Path
import yaml
from naver_news_client import fetch_naver_articles

_LOG = logging.getLogger(__name__)

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
def _fetch_rss(url: str, topic: str, days: int = 7) -> list[dict]:
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

        items.append(
            {
                "title":       entry.get("title", "").strip(),
                "link":        entry.get("link", ""),
                "summary":     entry.get("summary", entry.get("description", "")).strip(),
                "topic":       topic,
                "pubDateISO":  pub_dt.isoformat(),
            }
        )
    _LOG.info("✅ %s: %d 개", topic, len(items))
    return items

# -----------------------------------------------------------------------------
def collect_all() -> list[dict]:
    """모든 소스에서 기사를 수집합니다."""
    sources = _load_sources()
    collected: list[dict] = []
    for src in sources:
        if src.get("type") == "rss":
            collected += _fetch_rss(src["url"], src.get("topic", ""))
        elif src.get("type") == "naver":
            collected += fetch_naver_articles(src["query"], src.get("topic", ""))
    return collected
