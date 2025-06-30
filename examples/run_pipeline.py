from utubenews.pipeline import run
from utubenews.utils import setup_logging
import logging

if __name__ == "__main__":
    setup_logging(level=logging.ERROR)
    out = run(days=1)
    print(f"saved to {out}")
