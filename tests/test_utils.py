import sys
import types
import unittest

# create stub feedparser so that pipeline imports without dependency
if "feedparser" not in sys.modules:
    sys.modules["feedparser"] = types.ModuleType("feedparser")
if "yaml" not in sys.modules:
    dummy_yaml = types.ModuleType("yaml")
    dummy_yaml.safe_load = lambda *a, **k: []
    sys.modules["yaml"] = dummy_yaml
if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")
if "bs4" not in sys.modules:
    sys.modules["bs4"] = types.ModuleType("bs4")

from utubenews.pipeline import sort_articles
from utubenews.text_utils import clean_text


class TestUtils(unittest.TestCase):
    def test_clean_text_strips_ads(self):
        sample = "Hello\n광고 배너\nWorld"
        self.assertEqual(clean_text(sample), "Hello World")

    def test_sort_articles(self):
        arts = [
            {"title": "old", "pubDateISO": "2024-01-01T00:00:00"},
            {"title": "new", "pubDateISO": "2025-01-01T00:00:00"},
        ]
        sorted_arts = sort_articles(arts)
        self.assertEqual(sorted_arts[0]["title"], "new")


if __name__ == "__main__":
    unittest.main()
