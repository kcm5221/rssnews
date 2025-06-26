import sys
import types
import unittest

# stub heavy deps so imports work without them
for mod in ["requests", "bs4", "feedparser", "yaml"]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

from utubenews import block_processor

class TestProcessBlocks(unittest.TestCase):
    def test_process_blocks_runs_steps(self):
        blocks = [
            "Title one. Extra details that are long.",
            "Title one. Extra details that are long.",  # duplicate
            "Another article. More info here." ,
        ]
        titles = ["A", "B", "C"]

        called = {}
        def fake_translate(text, lang):
            called["text"] = text
            called["lang"] = lang
            return "번역:" + text

        orig = block_processor.translate_text
        block_processor.translate_text = fake_translate
        try:
            result = block_processor.process_blocks(blocks, titles, target_lang="ko")
        finally:
            block_processor.translate_text = orig

        self.assertIn("번역:", result)
        self.assertEqual(called["lang"], "ko")

if __name__ == "__main__":
    unittest.main()
