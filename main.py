import json
import os
import argparse

from utubenews.pipeline import run
from utubenews.summarizer import build_casual_script, postprocess_script
from utubenews.utils import setup_logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", help="Translate script to this language")
    args = parser.parse_args()

    setup_logging()
    out = run()
    articles = json.loads(out.read_text())
    lang = args.lang or os.getenv("SCRIPT_LANG")
    script = build_casual_script(articles, target_lang=lang)
    script = postprocess_script(script)
    out.with_suffix(".txt").write_text(script)
    print(script)
