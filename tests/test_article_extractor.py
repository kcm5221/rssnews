import sys
import types
import unittest

# provide stub requests module raising a RequestException
class DummyRequestException(Exception):
    pass

dummy_requests = types.ModuleType("requests")
dummy_requests.exceptions = types.SimpleNamespace(RequestException=DummyRequestException)

class DummyResponse:
    def raise_for_status(self):
        raise DummyRequestException("boom")
    @property
    def text(self):
        return "<html></html>"

def dummy_get(*args, **kwargs):
    return DummyResponse()

dummy_requests.get = dummy_get
sys.modules["requests"] = dummy_requests

# stub bs4 to avoid heavy dependency
if "bs4" not in sys.modules:
    sys.modules["bs4"] = types.ModuleType("bs4")

# provide stub newspaper module used by extract_with_newspaper
dummy_newspaper = types.ModuleType("newspaper")
sys.modules["newspaper"] = dummy_newspaper

import utubenews.article_extractor as ae
from utubenews.article_extractor import extract_main_text

class TestExtractMainText(unittest.TestCase):
    def test_returns_empty_on_request_error(self):
        if hasattr(dummy_newspaper, "Article"):
            del dummy_newspaper.Article
        self.assertEqual(extract_main_text("http://x"), "")

    def test_short_lines_not_dropped(self):
        if hasattr(dummy_newspaper, "Article"):
            del dummy_newspaper.Article
        html = "<html><article><p>Short line.</p><p>Another one.</p></article></html>"

        class OkResponse:
            def raise_for_status(self):
                pass

            @property
            def text(self):
                return html

        def ok_get(*a, **k):
            return OkResponse()

        dummy_requests.get = ok_get
        try:
            text = extract_main_text("http://ok")
        finally:
            dummy_requests.get = dummy_get

        self.assertIn("Short line.", text)
        self.assertIn("Another one.", text)

    def test_newspaper_success_used_first(self):
        class GoodArticle:
            def __init__(self, url):
                self.url = url
            def download(self):
                pass
            def parse(self):
                self.text = "NP text"

        dummy_newspaper.Article = GoodArticle
        try:
            text = extract_main_text("http://np")
        finally:
            del dummy_newspaper.Article
        self.assertEqual(text, "NP text")

    def test_newspaper_failure_falls_back(self):
        class BadArticle:
            def __init__(self, url):
                pass
            def download(self):
                raise RuntimeError("boom")
            def parse(self):
                pass

        dummy_newspaper.Article = BadArticle

        html = "<html><article><p>Fallback.</p></article></html>"

        class OkResponse:
            def raise_for_status(self):
                pass
            @property
            def text(self):
                return html

        def ok_get(*a, **k):
            return OkResponse()

        dummy_requests.get = ok_get
        try:
            text = extract_main_text("http://fb")
        finally:
            dummy_requests.get = dummy_get
            del dummy_newspaper.Article

        self.assertEqual(text, "Fallback.")

    def test_retries_until_success(self):
        if hasattr(dummy_newspaper, "Article"):
            del dummy_newspaper.Article

        html = "<html><article><p>Retry.</p></article></html>"

        class FailResponse:
            def raise_for_status(self):
                raise DummyRequestException("boom")

        class OkResponse:
            def raise_for_status(self):
                pass

            @property
            def text(self):
                return html

        calls = {"n": 0}

        def flaky_get(*args, **kwargs):
            if calls["n"] == 0:
                calls["n"] += 1
                return FailResponse()
            return OkResponse()

        dummy_requests.get = flaky_get
        orig_sleep = ae.time.sleep
        ae.time.sleep = lambda s: None
        try:
            text = extract_main_text("http://retry")
        finally:
            dummy_requests.get = dummy_get
            ae.time.sleep = orig_sleep

        self.assertEqual(text, "Retry.")

if __name__ == "__main__":
    unittest.main()
