import sys
import types
import unittest

# stub modules so imports succeed without heavy deps
if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")
if "bs4" not in sys.modules:
    sys.modules["bs4"] = types.ModuleType("bs4")

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

if __name__ == "__main__":
    unittest.main()

