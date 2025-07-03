import sys
import types
import unittest
import json
import tempfile
from pathlib import Path

# stub modules so import succeeds
for mod in ["requests", "bs4"]:
    if mod not in sys.modules:
        m = types.ModuleType(mod)
        if mod == "bs4":
            m.BeautifulSoup = lambda *a, **k: None
        if mod == "requests":
            m.get = lambda *a, **k: None
            m.exceptions = types.SimpleNamespace(RequestException=Exception)
        sys.modules[mod] = m

import utubenews.body_extractor as be
from utubenews import utils as ut


class TestBodyExtractorCLI(unittest.TestCase):
    def test_cli_updates_json_with_body(self):
        articles = [{"link": "L"}]
        with tempfile.TemporaryDirectory() as td:
            inp = Path(td) / "in.json"
            outp = Path(td) / "out.json"
            inp.write_text(json.dumps(articles, ensure_ascii=False))

            called = {}

            def fake_extract(url):
                called["url"] = url
                return "BODY"

            orig_extract = be.extract_body
            orig_log = ut.setup_logging
            be.extract_body = fake_extract
            ut.setup_logging = lambda *a, **k: None
            try:
                be.main([str(inp), str(outp)])
            finally:
                be.extract_body = orig_extract
                ut.setup_logging = orig_log

            with open(outp, encoding="utf-8") as f:
                result = json.load(f)
            self.assertEqual(result[0]["body"], "BODY")
            self.assertEqual(called["url"], "L")


if __name__ == "__main__":
    unittest.main()
