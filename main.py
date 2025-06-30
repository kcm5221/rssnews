import json
import os
import argparse

from utubenews.pipeline import run
from utubenews.summarizer import build_casual_script, postprocess_script
from utubenews.utils import setup_logging
import logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", help="Translate script to this language")
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days of articles to collect (default: 1)",
    )
    parser.add_argument(
        "--save-bodies",
        dest="save_bodies",
        action="store_true",
        default=True,
        help="Save article bodies to a text file (default: enabled)",
    )
    parser.add_argument(
        "--no-save-bodies",
        dest="save_bodies",
        action="store_false",
        help="Do not save article bodies",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (e.g. INFO, DEBUG)",
    )
    args = parser.parse_args()

    level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logging(level=level)
    out = run(days=args.days)
    articles = json.loads(out.read_text())
    lang = args.lang or os.getenv("SCRIPT_LANG", "ko")
    # Don't run translation step when script language is already Korean
    if lang == "ko":
        script = build_casual_script(articles, add_closing=False)
    else:
        script = build_casual_script(articles, target_lang=lang, add_closing=False)
    script = postprocess_script(script)
    out.with_suffix(".txt").write_text(script)
    if args.save_bodies:
        bodies_path = out.with_suffix(".bodies.txt")
        with bodies_path.open("w") as bf:
            for art in articles:
                title = art.get("title", "").strip()
                link = art.get("link", "").strip()
                body = art.get("body", "").strip()
                bf.write(f"{title}\n{link}\n{body}\n\n")
        print(f"Saved bodies to {bodies_path}")
    print(script)
