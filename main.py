import json
import os
import argparse

from utubenews.pipeline import run
from utubenews.summarizer import build_casual_script, postprocess_script
from utubenews.utils import setup_logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", help="Translate script to this language")
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days of articles to collect (default: 1)",
    )
    args = parser.parse_args()

    setup_logging()
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
    print(script)
