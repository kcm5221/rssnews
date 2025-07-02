import os
import argparse

from utubenews.pipeline import run
from utubenews import collector
from utubenews.utils import setup_logging
import logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days of articles to collect (default: 1)",
    )
    parser.add_argument(
        "--max-naver",
        type=int,
        default=collector._MAX_NAVER_ARTICLES,
        help="Maximum number of Naver articles to include",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=30,
        help="Maximum total number of articles to include",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (e.g. INFO, DEBUG)",
    )
    args = parser.parse_args()

    level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logging(level=level)
    out = run(days=args.days, max_naver=args.max_naver, max_total=args.max_total)
    print(f"Saved articles to {out}")
