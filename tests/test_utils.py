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
from utubenews.utils import filter_keywords, deduplicate


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

    def test_filter_keywords(self):
        arts = [
            {"title": "새 보안 프로그램 출시", "description": "사이버 보안 기능"},
            {"title": "공항 보안 강화", "description": "경비"},
            {"title": "게임 업데이트", "description": "신규 맵"},
        ]
        result = filter_keywords(
            arts,
            include=["프로그램", "사이버 보안"],
            exclude=["보안 카메라", "공항 보안", "국가 안보"],
        )
        self.assertEqual(len(result), 1)
        self.assertIn("프로그램", result[0]["title"])

    def test_deduplicate(self):
        arts = [
            {"title": "t1", "link": "a"},
            {"title": "t1", "link": "b"},
            {"title": "t2", "link": "a"},
            {"title": "t3", "link": "c"},
        ]
        result = deduplicate(arts)
        self.assertEqual(len(result), 2)
        titles = {a["title"] for a in result}
        self.assertIn("t1", titles)
        self.assertIn("t3", titles)


if __name__ == "__main__":
    unittest.main()
