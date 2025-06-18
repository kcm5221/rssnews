from utubenews.pipeline import run
from utubenews.utils import setup_logging

if __name__ == "__main__":
    setup_logging()
    out = run(days=1)
    print(f"saved to {out}")
