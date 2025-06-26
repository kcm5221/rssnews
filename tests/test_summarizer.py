import sys
import types
import unittest

# stub modules so imports succeed without heavy deps
if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")
if "bs4" not in sys.modules:
    sys.modules["bs4"] = types.ModuleType("bs4")

from utubenews import summarizer
from utubenews.summarizer import (
    simple_summary,
    build_casual_script,
    summarize_blocks,
    build_topic_script,
)
from utubenews.article_extractor import quick_summarize

class TestSummaries(unittest.TestCase):
    def test_simple_summary(self):
        text = "A. Bbbbbbbb. CCCCCCCC."
        self.assertEqual(simple_summary(text, max_sent=2), "Bbbbbbbb. CCCCCCCC.")

    def test_simple_summary_handles_newlines(self):
        text = "A.\nBbbbbbbb.\nCCCCCCCC."
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

    def test_summarize_blocks(self):
        blocks = ["A. Long sentence here.", "Short one. Another longer sentence."]
        sums = summarize_blocks(blocks, max_sent=1)
        self.assertEqual(len(sums), 2)
        self.assertEqual(sums[0], "Long sentence here.")
        self.assertEqual(sums[1], "Another longer sentence.")

    def test_translate_text_splits_large_input(self):
        class DummyTranslator:
            calls = []

            def translate(self, text, dest=None):
                DummyTranslator.calls.append(text)
                return types.SimpleNamespace(text=text.upper())

        gt_mod = types.ModuleType("googletrans")
        gt_mod.Translator = DummyTranslator
        orig_gt = sys.modules.get("googletrans")
        orig_dt = sys.modules.get("deep_translator")
        sys.modules["googletrans"] = gt_mod
        sys.modules["deep_translator"] = types.ModuleType("deep_translator")

        line1 = "a" * 4000
        line2 = "b" * 2000
        raw = line1 + "\n" + line2

        try:
            result = summarizer.translate_text(raw, "en")
        finally:
            if orig_gt is not None:
                sys.modules["googletrans"] = orig_gt
            else:
                del sys.modules["googletrans"]
            if orig_dt is not None:
                sys.modules["deep_translator"] = orig_dt
            else:
                del sys.modules["deep_translator"]

        expected_segments = [line1 + "\n", line2]

        self.assertEqual(DummyTranslator.calls, expected_segments)
        self.assertEqual(result, line1.upper() + "\n" + line2.upper())

    def test_translate_text_partial_failure_falls_back(self):
        class DummyGT:
            calls = []

            def translate(self, text, dest=None):
                DummyGT.calls.append(text)
                if text == "bad":
                    raise RuntimeError("boom")
                return types.SimpleNamespace(text=text.upper())

        class DummyDT:
            calls = []

            def translate(self, text):
                DummyDT.calls.append(text)
                return "DT-" + text

        gt_mod = types.ModuleType("googletrans")
        gt_mod.Translator = DummyGT
        dt_mod = types.ModuleType("deep_translator")
        dt_mod.GoogleTranslator = lambda source="auto", target="en": DummyDT()

        orig_gt = sys.modules.get("googletrans")
        orig_dt = sys.modules.get("deep_translator")
        sys.modules["googletrans"] = gt_mod
        sys.modules["deep_translator"] = dt_mod

        orig_chunk = summarizer._chunk_text
        summarizer._chunk_text = lambda x: ["good", "bad", "last"]

        try:
            result = summarizer.translate_text("irrelevant", "en")
        finally:
            summarizer._chunk_text = orig_chunk
            if orig_gt is not None:
                sys.modules["googletrans"] = orig_gt
            else:
                del sys.modules["googletrans"]
            if orig_dt is not None:
                sys.modules["deep_translator"] = orig_dt
            else:
                del sys.modules["deep_translator"]

        self.assertEqual(DummyGT.calls, ["good", "bad", "last"])
        self.assertEqual(DummyDT.calls, ["bad"])
        self.assertEqual(result, "GOODDT-badLAST")

    def test_build_topic_script_groups_and_transitions(self):
        arts = [
            {"topic": "IT", "script": "메타 AI 모델 발표. 새 기능 공개."},
            {"topic": "보안", "script": "패치 배포. 취약점 고쳤다."},
        ]

        result = build_topic_script(arts)
        self.assertIn("▶ IT", result)
        self.assertIn("▶ 보안", result)
        self.assertIn("다음 소식입니다~", result)
        self.assertTrue(result.strip().endswith("찾아뵐게요!"))

if __name__ == "__main__":
    unittest.main()

