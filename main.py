import json

from utubenews.pipeline import run
from utubenews.summarizer import build_casual_script
from utubenews.utils import setup_logging

if __name__ == "__main__":
    setup_logging()
    out = run()
    articles = json.loads(out.read_text())
    script = build_casual_script(articles)
    out.with_suffix(".txt").write_text(script)
    print(script)
