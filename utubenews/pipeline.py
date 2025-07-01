"""
(1) 수집 → (2) 본문 추출 → (3) 요약·스크립트 생성 → JSON 저장
"""
from __future__ import annotations
import json, logging, datetime as dt, re
from pathlib import Path
from . import collector
from .collector import collect_all
from .article_extractor import extract_main_text
from .summarizer import llm_summarize, normalize_script
from .text_utils import clean_text
from .utils import deduplicate_fuzzy

_LOG = logging.getLogger(__name__)
RAW_DIR = Path("raw_feeds")
RAW_DIR.mkdir(exist_ok=True)


def collect_articles(
    days: int = 1,
    max_naver: int = collector._MAX_NAVER_ARTICLES,
    max_total: int | None = None,
) -> list[dict]:
    """Collect articles from all configured sources."""
    return collect_all(days=days, max_naver=max_naver, max_total=max_total)


def enrich_articles(articles: list[dict]) -> list[dict]:
    """Attach body text and summary script to each article."""
    for art in articles:
        body = extract_main_text(art["link"])
        body = clean_text(body)
        art["body"] = body
        summary_src = body or art.get("summary") or art["title"]
        summary_src = clean_text(summary_src)
        script = llm_summarize(summary_src)
        normalized = normalize_script(script)
        if len(re.findall(r"[A-Za-z\uAC00-\uD7A3]", normalized)) < 5:
            _LOG.warning("Suspicious script for %s: %r", art.get("link"), normalized)
            normalized = normalize_script(art.get("title", ""))
        elif normalized != script:
            _LOG.warning("Suspicious script for %s: %r", art.get("link"), script)
        art["script"] = normalized
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
    try:
        with out_path.open() as f:
            json.load(f)
    except Exception as exc:
        _LOG.error("Failed to validate JSON %s: %s", out_path, exc)
    return out_path

def run(
    days: int = 1,
    max_naver: int = collector._MAX_NAVER_ARTICLES,
    max_total: int | None = None,
) -> Path:
    """Execute the full pipeline and return the output file path.

    Parameters
    ----------
    days : int, optional
        Range of days to collect articles for. Only articles newer than
        ``days`` are processed.
    max_total : int | None, optional
        If set, limit the total number of articles after filtering.
    """
    _LOG.info("파이프라인 시작")
    arts = collect_articles(days=days, max_naver=max_naver, max_total=max_total)
    arts = deduplicate_fuzzy(arts, similarity_threshold=0.9)
    arts = enrich_articles(arts)
    arts = sort_articles(arts)
    return save_articles(arts)

if __name__ == "__main__":
    run()
