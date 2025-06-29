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
    postprocess_script,
    llm_summarize,
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

    def test_llm_summarize_uses_transformers_pipeline(self):
        summarizer._PIPELINE = None
        calls = {}

        def fake_summary(text, max_length=60, min_length=None, do_sample=False, **_k):
            calls["text"] = text
            calls["max"] = max_length
            return [{"summary_text": "LLM"}]

        fake_mod = types.ModuleType("transformers")

        def fake_pipe(name):
            self.assertEqual(name, "summarization")
            return fake_summary

        fake_mod.pipeline = fake_pipe

        orig_trans = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        import utubenews.article_extractor as ae
        orig_qs = ae.quick_summarize
        ae.quick_summarize = lambda *_a, **_k: "BAD"

        try:
            result = llm_summarize("source text", max_tokens=10)
        finally:
            if orig_trans is not None:
                sys.modules["transformers"] = orig_trans
            else:
                del sys.modules["transformers"]
            ae.quick_summarize = orig_qs
            summarizer._PIPELINE = None

        self.assertEqual(result, "LLM")
        self.assertEqual(calls, {"text": "source text", "max": 7})

    def test_llm_summarize_falls_back_without_transformers(self):
        summarizer._PIPELINE = None
        import utubenews.article_extractor as ae
        called = {}

        def fake_qs(title, text, max_sent=3):
            called["text"] = text
            return "FB"

        orig_qs = ae.quick_summarize
        ae.quick_summarize = fake_qs

        orig_trans = sys.modules.get("transformers")
        if "transformers" in sys.modules:
            del sys.modules["transformers"]
        try:
            result = llm_summarize("text here")
        finally:
            if orig_trans is not None:
                sys.modules["transformers"] = orig_trans
            ae.quick_summarize = orig_qs
            summarizer._PIPELINE = None

        self.assertEqual(result, "FB")
        self.assertEqual(called["text"], "text here")

    def test_llm_summarize_returns_empty_on_blank_input(self):
        summarizer._PIPELINE = None

        fake_mod = types.ModuleType("transformers")
        def fake_pipe(name):
            raise AssertionError("pipeline should not be called")
        fake_mod.pipeline = fake_pipe

        orig_trans = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        import utubenews.article_extractor as ae
        orig_qs = ae.quick_summarize
        ae.quick_summarize = lambda *_a, **_k: "BAD"

        try:
            result = llm_summarize("   ")
        finally:
            if orig_trans is not None:
                sys.modules["transformers"] = orig_trans
            else:
                del sys.modules["transformers"]
            ae.quick_summarize = orig_qs
            summarizer._PIPELINE = None

        self.assertEqual(result, "")

    def test_llm_summarize_reuses_pipeline(self):
        summarizer._PIPELINE = None

        calls = {"pipe": 0, "texts": []}

        def fake_summary(text, max_length=60, min_length=None, do_sample=False, **_k):
            calls["texts"].append(text)
            return [{"summary_text": f"OUT-{text}"}]

        fake_mod = types.ModuleType("transformers")

        def fake_pipe(name):
            self.assertEqual(name, "summarization")
            calls["pipe"] += 1
            return fake_summary

        fake_mod.pipeline = fake_pipe

        orig_mod = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        try:
            first = llm_summarize("A", max_tokens=5)
            second = llm_summarize("B", max_tokens=6)
        finally:
            if orig_mod is not None:
                sys.modules["transformers"] = orig_mod
            else:
                del sys.modules["transformers"]
            summarizer._PIPELINE = None

        self.assertEqual(first, "OUT-A")
        self.assertEqual(second, "OUT-B")
        self.assertEqual(calls["pipe"], 1)
        self.assertEqual(calls["texts"], ["A", "B"])

    def test_llm_summarize_short_input_no_warning(self):
        summarizer._PIPELINE = None

        def fake_summary(text, max_length=60, min_length=None, do_sample=False, **_k):
            if max_length > len(text.split()) + 5:
                import warnings

                warnings.warn("too long", UserWarning)
            return [{"summary_text": "OK"}]

        fake_mod = types.ModuleType("transformers")

        def fake_pipe(name):
            self.assertEqual(name, "summarization")
            return fake_summary

        fake_mod.pipeline = fake_pipe

        orig = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        import warnings as _warnings

        try:
            with _warnings.catch_warnings(record=True) as w:
                _warnings.simplefilter("always")
                result = llm_summarize("tiny text", max_tokens=20)
        finally:
            if orig is not None:
                sys.modules["transformers"] = orig
            else:
                del sys.modules["transformers"]
            summarizer._PIPELINE = None

        self.assertEqual(result, "OK")
        self.assertEqual(len(w), 0)

    def test_llm_summarize_sets_min_length(self):
        summarizer._PIPELINE = None

        calls = {}

        def fake_summary(text, max_length=60, min_length=None, do_sample=False, truncation=False):
            calls["max"] = max_length
            calls["min"] = min_length
            return [{"summary_text": "OK"}]

        fake_mod = types.ModuleType("transformers")
        fake_mod.pipeline = lambda name: fake_summary

        orig = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        try:
            llm_summarize("short text", max_tokens=20)
        finally:
            if orig is not None:
                sys.modules["transformers"] = orig
            else:
                del sys.modules["transformers"]
            summarizer._PIPELINE = None

        self.assertIsNotNone(calls.get("min"))
        self.assertLessEqual(calls["min"], calls["max"])

    def test_llm_summarize_blank_then_min_length(self):
        """Calling with blank text returns empty and later sets min_length."""
        summarizer._PIPELINE = None

        calls: list[dict] = []

        def fake_summary(text, max_length=60, min_length=None, do_sample=False, truncation=False):
            calls.append({"text": text, "max": max_length, "min": min_length})
            return [{"summary_text": "OK"}]

        fake_mod = types.ModuleType("transformers")
        fake_mod.pipeline = lambda name: fake_summary

        orig_mod = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        import utubenews.article_extractor as ae
        orig_qs = ae.quick_summarize
        ae.quick_summarize = lambda *_a, **_k: "BAD"

        try:
            empty_result = llm_summarize("")
            self.assertEqual(empty_result, "")
            self.assertEqual(calls, [])

            filled_result = llm_summarize("short text", max_tokens=20)
        finally:
            if orig_mod is not None:
                sys.modules["transformers"] = orig_mod
            else:
                del sys.modules["transformers"]
            ae.quick_summarize = orig_qs
            summarizer._PIPELINE = None

        self.assertEqual(filled_result, "OK")
        self.assertEqual(len(calls), 1)
        self.assertIsNotNone(calls[0].get("min"))
        self.assertLessEqual(calls[0]["min"], calls[0]["max"])

    def test_llm_summarize_truncates_to_model_length_and_passes_flag(self):
        summarizer._PIPELINE = None

        class DummyTokenizer:
            model_max_length = 3

            def encode(self, text, max_length=None, truncation=False, **_k):
                tokens = text.split()
                if truncation and max_length is not None and len(tokens) > max_length:
                    tokens = tokens[:max_length]
                return tokens

            def decode(self, tokens, skip_special_tokens=True):
                return " ".join(tokens)

        calls = {}

        def fake_summary(text, max_length=60, min_length=None, do_sample=False, truncation=False):
            calls["text"] = text
            calls["trunc"] = truncation
            return [{"summary_text": "OK"}]

        fake_summary.tokenizer = DummyTokenizer()

        fake_mod = types.ModuleType("transformers")
        fake_mod.pipeline = lambda name: fake_summary

        orig = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        import utubenews.article_extractor as ae
        orig_qs = ae.quick_summarize
        ae.quick_summarize = lambda *_a, **_k: "BAD"

        try:
            result = llm_summarize("w1 w2 w3 w4 w5")
        finally:
            if orig is not None:
                sys.modules["transformers"] = orig
            else:
                del sys.modules["transformers"]
            ae.quick_summarize = orig_qs
            summarizer._PIPELINE = None

        self.assertEqual(result, "OK")
        self.assertEqual(calls["text"], "w1 w2 w3")
        self.assertTrue(calls["trunc"])

    def test_llm_summarize_handles_more_than_max_input_tokens(self):
        summarizer._PIPELINE = None

        class DummyTokenizer:
            model_max_length = summarizer.MAX_LLM_INPUT_TOKENS

            def encode(self, text, max_length=None, truncation=False, **_k):
                tokens = text.split()
                if truncation and max_length is not None and len(tokens) > max_length:
                    tokens = tokens[:max_length]
                return tokens

            def decode(self, tokens, skip_special_tokens=True):
                return " ".join(tokens)

        calls = {}

        def fake_summary(text, max_length=60, min_length=None, do_sample=False, truncation=False, **_k):
            calls["length"] = len(text.split())
            return [{"summary_text": "OK"}]

        fake_summary.tokenizer = DummyTokenizer()

        fake_mod = types.ModuleType("transformers")
        fake_mod.pipeline = lambda name: fake_summary

        orig = sys.modules.get("transformers")
        sys.modules["transformers"] = fake_mod

        import utubenews.article_extractor as ae
        orig_qs = ae.quick_summarize
        ae.quick_summarize = lambda *_a, **_k: "BAD"

        long_text = " ".join(f"w{i}" for i in range(2000))

        try:
            result = llm_summarize(long_text)
        finally:
            if orig is not None:
                sys.modules["transformers"] = orig
            else:
                del sys.modules["transformers"]
            ae.quick_summarize = orig_qs
            summarizer._PIPELINE = None

        self.assertEqual(result, "OK")
        self.assertLessEqual(calls["length"], summarizer.MAX_LLM_INPUT_TOKENS)

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

    def test_postprocess_script_sections_and_ending(self):
        raw = " ".join(f"S{i}." for i in range(1, 21))
        processed = postprocess_script(raw, max_sent=12)
        blocks = processed.split("\n\n")

        self.assertTrue(processed.strip().endswith("오늘 뉴스는 여기까지입니다."))
        self.assertEqual(len(blocks), 4)
        from utubenews.text_utils import split_sentences

        first_block_sents = split_sentences(blocks[0])
        second_block_sents = split_sentences(blocks[2])
        self.assertEqual(len(first_block_sents), 12)
        self.assertEqual(len(second_block_sents), 8)

if __name__ == "__main__":
    unittest.main()

