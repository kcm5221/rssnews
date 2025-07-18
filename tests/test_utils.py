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
from utubenews.text_utils import clean_text, merge_text_blocks, split_sentences
from utubenews.utils import filter_keywords, deduplicate, deduplicate_fuzzy


class TestUtils(unittest.TestCase):
    def test_clean_text_strips_ads(self):
        sample = "Hello\n광고 배너\nWorld"
        self.assertEqual(clean_text(sample), "Hello World")

    def test_clean_text_strips_toc_markers(self):
        sample = "Intro\nTable of Contents\n[hide]\n목차\nContent"
        self.assertEqual(clean_text(sample), "Intro Content")

    def test_clean_text_strips_translation_warning(self):
        raw = "(It is assumed that there may be errors in the English translation.) Actual content"
        self.assertEqual(clean_text(raw), "Actual content")

    def test_clean_text_strips_korean_translation_label(self):
        raw = "번역결과\n내용입니다"
        self.assertEqual(clean_text(raw), "내용입니다")

    def test_clean_text_strips_control_chars(self):
        sample = "A\uFFFD\nB\x07\x0cC"
        self.assertEqual(clean_text(sample), "A BC")

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
            exclude=["공항", "cctv", "경비"],
        )
        self.assertEqual(len(result), 1)
        titles = {a["title"] for a in result}
        self.assertIn("새 보안 프로그램 출시", titles)

    def test_filter_keywords_summary_only(self):
        arts = [
            {"summary": "사이버 보안 기능 포함"},
            {"summary": "다른 내용"},
        ]
        result = filter_keywords(arts, include=["보안"])
        self.assertEqual(len(result), 1)
        self.assertIn("사이버 보안 기능 포함", result[0].get("summary"))

    def test_filter_keywords_does_not_match_substrings(self):
        arts = [
            {"title": "보안프로그램 출시"},
            {"title": "프로그램 업데이트"},
        ]
        result = filter_keywords(arts, include=["프로그램"])
        # Only the standalone word should match
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "프로그램 업데이트")

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

    def test_deduplicate_case_whitespace(self):
        arts = [
            {"title": "Title1", "link": "http://a.com "},
            {"title": " title1 ", "link": "HTTP://A.COM"},
            {"title": "Title2 ", "link": "http://b.com"},
            {"title": "TITLE2", "link": " http://b.com"},
            {"title": "Title3", "link": "http://c.com"},
        ]
        result = deduplicate(arts)
        self.assertEqual(len(result), 3)
        titles = [a["title"] for a in result]
        self.assertEqual(titles[0], "Title1")
        self.assertEqual(titles[1], "Title2 ")
        self.assertEqual(titles[2], "Title3")

    def test_deduplicate_fuzzy_titles(self):
        arts = [
            {"title": "A사 신제품 발표", "link": "l1"},
            {"title": "A사의 신제품 발표", "link": "l2"},
        ]
        result = deduplicate_fuzzy(arts, similarity_threshold=0.9)
        self.assertEqual(len(result), 1)

    def test_merge_text_blocks(self):
        texts = ["Title\n광고", "Title", "Another news"]
        titles = ["뉴스1", "뉴스2", "뉴스3"]
        result = merge_text_blocks(texts, titles)
        self.assertIn("## 뉴스1", result)
        self.assertIn("## 뉴스3", result)
        # "Title" should appear once after cleaning and deduplication
        self.assertEqual(result.count("Title"), 1)

    def test_split_sentences_adds_period(self):
        result = split_sentences("Hello world")
        self.assertEqual(result, ["Hello world."])

    def test_split_sentences_appends_filler_for_hangul(self):
        result = split_sentences("인공지능 기술")
        self.assertEqual(result, ["인공지능 기술입니다."])

if __name__ == "__main__":
    unittest.main()
