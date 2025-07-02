"""뉴스 수집 파이프라인.

기본 동작은 다음 단계를 수행합니다.

1. **수집** – RSS 및 네이버 검색에서 기사 메타데이터 수집
2. **중복 제거** – 비슷한 제목의 기사를 걸러냄
3. **정렬** – 발행일 기준으로 최신순 정렬
4. **저장** – 제목과 링크만을 JSON 파일로 저장

``enrich_articles()`` 함수는 본문 추출과 요약을 수행하지만 기본 파이프라인
(``run()``)에서는 사용하지 않습니다.
"""
from __future__ import annotations
import json, logging, datetime as dt, re
from pathlib import Path
from datetime import datetime
from slugify import slugify
from screenshot import capture
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


def enrich_articles(articles: list[dict], *, with_screenshot: bool = False) -> list[dict]:
    """Attach body text, summary script, and optionally a screenshot."""
    date_str = datetime.now().strftime("%Y%m%d") if with_screenshot else ""

    for idx, art in enumerate(articles, 1):
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

        if with_screenshot:
            fname = f"screens/{date_str}_{idx:03d}_{slugify(art.get('title', '') or '')}.png"
            try:
                capture(art["link"], fname)
                art["screenshot"] = fname
            except Exception as e:
                _LOG.warning("스크린샷 실패: %s (%s)", art.get("title"), e)
    return articles


def sort_articles(articles: list[dict]) -> list[dict]:
    """Return articles sorted by publish date (newest first)."""
    return sorted(articles, key=lambda x: x.get("pubDateISO", ""), reverse=True)


def save_articles(articles: list[dict], directory: Path = RAW_DIR) -> Path:
    """Save article titles and links to a timestamped JSON file."""
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = directory / f"articles_{ts}.json"
    simple = [{"title": a.get("title", ""), "link": a.get("link", "")} for a in articles]
    out_path.write_text(json.dumps(simple, ensure_ascii=False, indent=2))
    _LOG.info("총 %d건 저장 → %s", len(simple), out_path)
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
    *,
    with_screenshot: bool = False,
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
    arts = sort_articles(arts)
    if with_screenshot:
        arts = enrich_articles(arts, with_screenshot=True)
    return save_articles(arts)

if __name__ == "__main__":
    run()
