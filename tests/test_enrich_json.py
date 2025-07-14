import sys
import types
import unittest
import json
import runpy
from pathlib import Path
import tempfile

# stub heavy modules so pipeline imports succeed
for mod in ["feedparser", "yaml", "requests", "bs4", "slugify", "utubenews.screenshot"]:
    if mod not in sys.modules:
        m = types.ModuleType(mod)
        if mod == "slugify":
            m.slugify = lambda s: s
        if mod == "utubenews.screenshot":
            m.capture = lambda *a, **k: None
        sys.modules[mod] = m

from utubenews import pipeline
from utubenews import utils as ut


class TestEnrichJsonCLI(unittest.TestCase):
    def test_cli_calls_enrich_with_flag(self):
        articles = [{"title": "T", "link": "L"}]
        with tempfile.TemporaryDirectory() as td:
            in_path = Path(td) / "in.json"
            in_path.write_text(json.dumps(articles, ensure_ascii=False))

            called = {}

            def fake_enrich(arts, *, with_screenshot=False):
                called["arts"] = arts
                called["with_screenshot"] = with_screenshot
                return [{"done": True}]

            orig_enrich = pipeline.enrich_articles
            orig_log = ut.setup_logging
            pipeline.enrich_articles = fake_enrich
            ut.setup_logging = lambda *a, **k: None

            argv = sys.argv
            sys.argv = [
                "enrich_json.py",
                str(in_path),
                "--with-screenshot",
            ]
            try:
                runpy.run_module("utubenews.enrich_json", run_name="__main__")
            finally:
                pipeline.enrich_articles = orig_enrich
                ut.setup_logging = orig_log
                sys.argv = argv

            out_files = list(Path(td).glob("articles_enriched_*.json"))
            self.assertEqual(len(out_files), 1)
            with open(out_files[0]) as f:
                result = json.load(f)
            self.assertEqual(result, [{"done": True}])
            self.assertEqual(called["arts"], articles)
            self.assertTrue(called["with_screenshot"])

    def test_cli_default_no_screenshot(self):
        articles = [{"title": "T", "link": "L"}]
        with tempfile.TemporaryDirectory() as td:
            in_path = Path(td) / "in.json"
            in_path.write_text(json.dumps(articles, ensure_ascii=False))

            called = {}

            def fake_enrich(arts, *, with_screenshot=False):
                called["with_screenshot"] = with_screenshot
                return arts

            orig_enrich = pipeline.enrich_articles
            orig_log = ut.setup_logging
            pipeline.enrich_articles = fake_enrich
            ut.setup_logging = lambda *a, **k: None

            argv = sys.argv
            sys.argv = ["enrich_json.py", str(in_path)]
            try:
                runpy.run_module("utubenews.enrich_json", run_name="__main__")
            finally:
                pipeline.enrich_articles = orig_enrich
                ut.setup_logging = orig_log
                sys.argv = argv

            self.assertFalse(called["with_screenshot"])


if __name__ == "__main__":
    unittest.main()
