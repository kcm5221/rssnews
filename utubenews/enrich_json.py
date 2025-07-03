import argparse
import json
from pathlib import Path
from datetime import datetime

from . import pipeline
from .utils import setup_logging


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Enrich articles stored in a JSON file"
    )
    parser.add_argument("input_json", help="Path to JSON file with articles")
    parser.add_argument(
        "--with-screenshot",
        action="store_true",
        help="Capture article pages as screenshots",
    )
    parser.add_argument(
        "--log-level", default="INFO", help="Logging level (default: INFO)"
    )
    args = parser.parse_args(argv)

    level = args.log_level.upper()
    setup_logging(level=level)

    with open(args.input_json, encoding="utf-8") as f:
        articles = json.load(f)

    enriched = pipeline.enrich_articles(
        articles, with_screenshot=args.with_screenshot
    )

    date_str = datetime.now().strftime("%Y%m%d")
    out_path = Path(args.input_json).with_name(
        f"articles_enriched_{date_str}.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(enriched)} articles to {out_path}")
    return out_path


if __name__ == "__main__":
    main()
