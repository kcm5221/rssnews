"""
(1) 수집 → (2) 본문 추출 → (3) 요약·스크립트 생성 → JSON 저장
"""
from __future__ import annotations
import json, logging, datetime as dt
from pathlib import Path
from .collector import collect_all
from .article_extractor import extract_main_text, quick_summarize
from .text_utils import clean_text
from .utils import deduplicate

_LOG = logging.getLogger(__name__)
RAW_DIR = Path("raw_feeds")
RAW_DIR.mkdir(exist_ok=True)


def collect_articles(days: int = 1) -> list[dict]:
    """Collect articles from all configured sources."""
    return collect_all(days=days)


def enrich_articles(articles: list[dict]) -> list[dict]:
    """Attach body text and summary script to each article."""
    for art in articles:
        body = extract_main_text(art["link"])
        body = clean_text(body)
        summary_src = art.get("summary") or body or art["title"]
        summary_src = clean_text(summary_src)
        art["script"] = quick_summarize(art["title"], summary_src)
    return articles


def sort_articles(articles: list[dict]) -> list[dict]:
    """Return articles sorted by publish date (newest first)."""
    return sorted(articles, key=lambda x: x.get("pubDateISO", ""), reverse=True)


def save_articles(articles: list[dict], directory: Path = RAW_DIR) -> Path:
    """Save articles to a timestamped JSON file and return its path."""
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = directory / f"articles_{ts}.json"
    out_path.write_text(json.dumps(articles, ensure_ascii=False, indent=2))
    _LOG.info("총 %d건 저장 → %s", len(articles), out_path)
    return out_path

def run(days: int = 1) -> Path:
    """Run the full pipeline and return the output path."""
    _LOG.info("파이프라인 시작")
    arts = collect_articles(days=days)
    arts = deduplicate(arts)
    arts = enrich_articles(arts)
    arts = sort_articles(arts)
    return save_articles(arts)

if __name__ == "__main__":
    run()
