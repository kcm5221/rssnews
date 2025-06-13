"""
(1) 수집 → (2) 본문 추출 → (3) 요약·스크립트 생성 → JSON 저장
"""
from __future__ import annotations
import json, logging, datetime as dt
from pathlib import Path
from collector import collect_all
from article_extractor import extract_main_text, quick_summarize

_LOG = logging.getLogger(__name__)
RAW_DIR = Path("raw_feeds")
RAW_DIR.mkdir(exist_ok=True)

def run():
    # ① 수집
    arts = collect_all()

    # ② 본문·요약
    for art in arts:
        body = extract_main_text(art["link"])
        # summary 필드가 비어 있으면 본문(또는 제목)으로 대체
        summary_src = art.get("summary") or body or art["title"]
        art["script"] = quick_summarize(art["title"], summary_src)

    # ③ 저장
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RAW_DIR / f"articles_{ts}.json"
    out_path.write_text(json.dumps(arts, ensure_ascii=False, indent=2))
    _LOG.info("총 %d건 저장 → %s", len(arts), out_path)

if __name__ == "__main__":
    run()
