import sys
import types
import unittest

# stub modules so imports succeed without heavy deps
if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")
if "bs4" not in sys.modules:
    sys.modules["bs4"] = types.ModuleType("bs4")

from utubenews import summarizer
from utubenews.summarizer import simple_summary, build_casual_script
from utubenews.article_extractor import quick_summarize

class TestSummaries(unittest.TestCase):
    def test_simple_summary(self):
        text = "A. Bbbbbbbb. CCCCCCCC."
        self.assertEqual(simple_summary(text, max_sent=2), "Bbbbbbbb. CCCCCCCC.")

    def test_quick_summarize_short(self):
        t = "Title"
        short = "short text"
        self.assertTrue(quick_summarize(t, short).startswith(short))

    def test_build_casual_script(self):
        arts = [{"script": "A. B. C."}, {"script": "D! E. F. G."}]
        result = build_casual_script(arts)
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("D!", result)
        self.assertTrue(result.strip().endswith("😊"))

    def test_build_casual_script_translates_when_lang(self):
        arts = [{"script": "A. B."}]
        called = {}

        def fake_translate(text, lang):
            called["text"] = text
            called["lang"] = lang
            return "X"  # return marker

        orig = summarizer.translate_text
        summarizer.translate_text = fake_translate
        try:
            result = build_casual_script(arts, target_lang="en")
        finally:
            summarizer.translate_text = orig

        expected_raw = "A.\nB.\n\n오늘 뉴스 여기까지! 좋은 하루 보내세요 😊"
        self.assertEqual(called["text"], expected_raw)
        self.assertEqual(called["lang"], "en")
        self.assertEqual(result, "X")

if __name__ == "__main__":
    unittest.main()

