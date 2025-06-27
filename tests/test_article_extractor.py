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

from utubenews.article_extractor import extract_main_text

class TestExtractMainText(unittest.TestCase):
    def test_returns_empty_on_request_error(self):
        self.assertEqual(extract_main_text("http://x"), "")

    def test_short_lines_not_dropped(self):
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

if __name__ == "__main__":
    unittest.main()
