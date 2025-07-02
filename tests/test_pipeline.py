import types
import sys
import unittest
from pathlib import Path

# ensure heavy deps are stubbed
for mod in ["feedparser", "yaml", "requests", "bs4", "slugify", "screenshot"]:
    if mod not in sys.modules:
        m = types.ModuleType(mod)
        if mod == "slugify":
            m.slugify = lambda s: s
        if mod == "screenshot":
            m.capture = lambda *a, **k: None
        sys.modules[mod] = m

from utubenews import collector, pipeline

class TestCollectAll(unittest.TestCase):
    def test_collect_all_mixes_sources(self):
        rss_item = {"title": "r1", "link": "rl", "summary": "s", "topic": "IT", "pubDateISO": "2025", "src": "rss"}
        naver_item = {"title": "n1", "link": "nl", "summary": "s2", "topic": "보안", "pubDateISO": "2025"}

        def fake_load():
            return [
                {"type": "rss", "url": "u", "topic": "IT"},
                {"type": "naver", "query": "q", "topic": "보안"},
            ]

        def fake_rss(url, topic, days=1):
            self.assertEqual(topic, "IT")
            return [rss_item]

        def fake_naver(query, topic, days=1, max_pages=10):
            self.assertEqual(topic, "보안")
            return [naver_item]

        def fake_filter(arts, include=None, exclude=None):
            return arts

        orig = {
            "load": collector._load_sources,
            "rss": collector._fetch_rss,
            "naver": collector.fetch_naver_articles,
            "filter": collector.filter_keywords,
        }
        collector._load_sources = fake_load
        collector._fetch_rss = fake_rss
        collector.fetch_naver_articles = fake_naver
        collector.filter_keywords = fake_filter
        try:
            result = collector.collect_all(days=1, max_naver=5)
        finally:
            collector._load_sources = orig["load"]
            collector._fetch_rss = orig["rss"]
            collector.fetch_naver_articles = orig["naver"]
            collector.filter_keywords = orig["filter"]
        self.assertEqual(len(result), 2)
        self.assertIn(rss_item, result)
        naver_item_with_src = dict(naver_item, src="naver")
        self.assertIn(naver_item_with_src, result)

    def test_collect_all_filters_naver_by_keywords(self):
        good = {
            "title": "새 보안 프로그램 출시",
            "link": "l1",
            "summary": "",
            "topic": "IT",
            "pubDateISO": "2025",
        }
        bad = {
            "title": "게임 업데이트",
            "link": "l2",
            "summary": "",
            "topic": "IT",
            "pubDateISO": "2025",
        }

        def fake_load():
            return [{"type": "naver", "query": "q", "topic": "IT"}]

        def fake_naver(query, topic, days=1, max_pages=10):
            return [good, bad]

        orig_load = collector._load_sources
        orig_naver = collector.fetch_naver_articles
        collector._load_sources = fake_load
        collector.fetch_naver_articles = fake_naver
        try:
            result = collector.collect_all(days=1, max_naver=5)
        finally:
            collector._load_sources = orig_load
            collector.fetch_naver_articles = orig_naver

        expected = [dict(good, src="naver")]
        self.assertEqual(result, expected)

    def test_collect_all_limits_naver_articles(self):
        items = [
            {"title": f"t{i}", "link": f"l{i}", "summary": "", "topic": "IT", "pubDateISO": "2025"}
            for i in range(30)
        ]

        def fake_load():
            return [{"type": "naver", "query": "q", "topic": "IT"}]

        def fake_naver(query, topic, days=1, max_pages=10):
            return items

        orig = {
            "load": collector._load_sources,
            "naver": collector.fetch_naver_articles,
            "filter": collector.filter_keywords,
        }
        collector._load_sources = fake_load
        collector.fetch_naver_articles = fake_naver
        collector.filter_keywords = lambda arts, include=None, exclude=None: arts
        try:
            result = collector.collect_all(days=1, max_naver=5)
        finally:
            collector._load_sources = orig["load"]
            collector.fetch_naver_articles = orig["naver"]
            collector.filter_keywords = orig["filter"]

        self.assertEqual(len(result), 5)

    def test_collect_all_dedupes_before_limit(self):
        items = [
            {"title": "dup", "link": "l1", "summary": "", "topic": "IT", "pubDateISO": "2025"},
            {"title": "dup", "link": "l1b", "summary": "", "topic": "IT", "pubDateISO": "2025"},
        ] + [
            {"title": f"t{i}", "link": f"l{i}", "summary": "", "topic": "IT", "pubDateISO": "2025"}
            for i in range(2,7)
        ]

        def fake_load():
            return [{"type": "naver", "query": "q", "topic": "IT"}]

        def fake_naver(query, topic, days=1, max_pages=10):
            return items

        orig = {
            "load": collector._load_sources,
            "naver": collector.fetch_naver_articles,
            "filter": collector.filter_keywords,
        }
        collector._load_sources = fake_load
        collector.fetch_naver_articles = fake_naver
        collector.filter_keywords = lambda arts, include=None, exclude=None: arts
        try:
            result = collector.collect_all(days=1, max_naver=5)
        finally:
            collector._load_sources = orig["load"]
            collector.fetch_naver_articles = orig["naver"]
            collector.filter_keywords = orig["filter"]

        titles = [a["title"] for a in result]
        self.assertEqual(titles, ["dup", "t2", "t3", "t4", "t5"])

    def test_collect_all_limits_total_articles(self):
        items = [
            {"title": f"t{i}", "link": f"l{i}", "summary": "", "topic": "IT", "pubDateISO": "2025", "src": "rss"}
            for i in range(50)
        ]

        def fake_load():
            return [{"type": "rss", "url": "u", "topic": "IT"}]

        def fake_rss(url, topic, days=1):
            return items

        orig = {
            "load": collector._load_sources,
            "rss": collector._fetch_rss,
            "filter": collector.filter_keywords,
        }
        collector._load_sources = fake_load
        collector._fetch_rss = fake_rss
        collector.filter_keywords = lambda arts, include=None, exclude=None: arts
        try:
            result = collector.collect_all(days=1, max_naver=20, max_total=30)
        finally:
            collector._load_sources = orig["load"]
            collector._fetch_rss = orig["rss"]
            collector.filter_keywords = orig["filter"]

        self.assertEqual(len(result), 10)

    def test_collect_all_reserves_naver_quota(self):
        rss_items = [
            {"title": f"r{i}", "link": f"rl{i}", "summary": "", "topic": "IT", "pubDateISO": "2025", "src": "rss"}
            for i in range(50)
        ]
        naver_items = [
            {"title": f"n{i}", "link": f"nl{i}", "summary": "", "topic": "IT", "pubDateISO": "2025"}
            for i in range(20)
        ]

        def fake_load():
            return [
                {"type": "rss", "url": "u", "topic": "IT"},
                {"type": "naver", "query": "q", "topic": "IT"},
            ]

        def fake_rss(url, topic, days=1):
            return rss_items

        def fake_naver(query, topic, days=1, max_pages=10):
            return naver_items

        orig = {
            "load": collector._load_sources,
            "rss": collector._fetch_rss,
            "naver": collector.fetch_naver_articles,
            "filter": collector.filter_keywords,
        }
        collector._load_sources = fake_load
        collector._fetch_rss = fake_rss
        collector.fetch_naver_articles = fake_naver
        collector.filter_keywords = lambda arts, include=None, exclude=None: arts
        try:
            result = collector.collect_all(days=1, max_naver=10, max_total=30)
        finally:
            collector._load_sources = orig["load"]
            collector._fetch_rss = orig["rss"]
            collector.fetch_naver_articles = orig["naver"]
            collector.filter_keywords = orig["filter"]

        naver_count = len([a for a in result if a.get("src") == "naver"])
        self.assertEqual(len(result), 30)
        self.assertGreaterEqual(naver_count, 10)

class TestEnrichArticles(unittest.TestCase):
    def test_enrich_articles_uses_summary_or_body(self):
        art_with_sum = {"title": "T1", "link": "L1", "summary": "SUM"}
        art_no_sum = {"title": "T2", "link": "L2"}
        arts = [art_with_sum, art_no_sum]

        def fake_extract(link):
            return f"BODY-{link}"

        def fake_clean(text):
            return text

        def fake_sum(src):
            return f"SCRIPT-{src}"

        orig = {
            "ext": pipeline.extract_main_text,
            "clean": pipeline.clean_text,
            "llm": pipeline.llm_summarize,
        }
        pipeline.extract_main_text = fake_extract
        pipeline.clean_text = fake_clean
        pipeline.llm_summarize = fake_sum
        try:
            out = pipeline.enrich_articles(arts)
        finally:
            pipeline.extract_main_text = orig["ext"]
            pipeline.clean_text = orig["clean"]
            pipeline.llm_summarize = orig["llm"]

        self.assertEqual(out[0]["script"], "SCRIPT-BODY-L1…")
        self.assertEqual(out[1]["script"], "SCRIPT-BODY-L2…")
        self.assertEqual(out[0]["body"], "BODY-L1")
        self.assertEqual(out[1]["body"], "BODY-L2")

    def test_enrich_articles_warns_on_short_script(self):
        art = {"title": "T", "link": "L"}

        def fake_extract(link):
            return ""

        def fake_clean(text):
            return text

        def fake_sum(src):
            return "short"

        orig = {
            "ext": pipeline.extract_main_text,
            "clean": pipeline.clean_text,
            "llm": pipeline.llm_summarize,
        }
        pipeline.extract_main_text = fake_extract
        pipeline.clean_text = fake_clean
        pipeline.llm_summarize = fake_sum
        try:
            with self.assertLogs(pipeline._LOG, level="WARNING") as log:
                out = pipeline.enrich_articles([art])
        finally:
            pipeline.extract_main_text = orig["ext"]
            pipeline.clean_text = orig["clean"]
            pipeline.llm_summarize = orig["llm"]

        self.assertEqual(out[0]["script"], "short…")
        self.assertTrue(any("Suspicious script" in m for m in log.output))

        import tempfile, json
        with tempfile.TemporaryDirectory() as td:
            path = pipeline.save_articles(out, Path(td))
            with open(path) as f:
                loaded = json.load(f)

        self.assertEqual(loaded, [{"title": "T", "link": "L"}])

    def test_enrich_articles_warns_on_unbalanced_quote(self):
        art = {"title": "T", "link": "L"}

        def fake_extract(link):
            return ""

        def fake_clean(text):
            return text

        def fake_sum(src):
            return "Bad text\""

        orig = {
            "ext": pipeline.extract_main_text,
            "clean": pipeline.clean_text,
            "llm": pipeline.llm_summarize,
        }
        pipeline.extract_main_text = fake_extract
        pipeline.clean_text = fake_clean
        pipeline.llm_summarize = fake_sum
        try:
            with self.assertLogs(pipeline._LOG, level="WARNING") as log:
                out = pipeline.enrich_articles([art])
        finally:
            pipeline.extract_main_text = orig["ext"]
            pipeline.clean_text = orig["clean"]
            pipeline.llm_summarize = orig["llm"]

        self.assertEqual(out[0]["script"], "Bad text…")
        self.assertTrue(any("Suspicious script" in m for m in log.output))

        import tempfile, json
        with tempfile.TemporaryDirectory() as td:
            path = pipeline.save_articles(out, Path(td))
            with open(path) as f:
                loaded = json.load(f)

        self.assertEqual(loaded, [{"title": "T", "link": "L"}])

    def test_enrich_articles_falls_back_on_non_text_script(self):
        art = {"title": "T", "link": "L"}

        def fake_extract(link):
            return ""

        def fake_clean(text):
            return text

        def fake_sum(src):
            return "?!"

        orig = {
            "ext": pipeline.extract_main_text,
            "clean": pipeline.clean_text,
            "llm": pipeline.llm_summarize,
        }
        pipeline.extract_main_text = fake_extract
        pipeline.clean_text = fake_clean
        pipeline.llm_summarize = fake_sum
        try:
            with self.assertLogs(pipeline._LOG, level="WARNING") as log:
                out = pipeline.enrich_articles([art])
        finally:
            pipeline.extract_main_text = orig["ext"]
            pipeline.clean_text = orig["clean"]
            pipeline.llm_summarize = orig["llm"]

        self.assertEqual(out[0]["script"], "T…")
        self.assertTrue(any("Suspicious script" in m for m in log.output))

    def test_enrich_articles_adds_screenshot(self):
        art = {"title": "T", "link": "L"}

        called = {}

        def fake_capture(url, fname, **kwargs):
            called["fname"] = fname

        orig_cap = pipeline.capture
        pipeline.capture = fake_capture
        try:
            out = pipeline.enrich_articles([art], with_screenshot=True)
        finally:
            pipeline.capture = orig_cap

        self.assertIn("screenshot", out[0])
        self.assertTrue(called["fname"].startswith("screens/"))


class TestNormalizeScript(unittest.TestCase):
    def test_normalize_script_fixes_trailing_quote(self):
        from utubenews.summarizer import normalize_script

        self.assertEqual(normalize_script("Bad summary\""), "Bad summary…")

    def test_normalize_script_handles_single_quotes(self):
        from utubenews.summarizer import normalize_script

        self.assertEqual(normalize_script("Bad summary'"), "Bad summary…")

    def test_normalize_script_handles_opening_quote(self):
        from utubenews.summarizer import normalize_script

        self.assertEqual(normalize_script("“Bad summary"), "“Bad summary…")

class TestRun(unittest.TestCase):
    def test_run_calls_steps_and_returns_path(self):
        collected = [{"title": "A"}]
        order = []

        def fake_collect(days=1, max_naver=collector._MAX_NAVER_ARTICLES, max_total=None):
            order.append("collect")
            self.assertEqual(days, 2)
            self.assertEqual(max_naver, 8)
            self.assertIsNone(max_total)
            return collected

        def fake_dedup(arts, **kwargs):
            order.append("dedup")
            self.assertIs(arts, collected)
            self.assertIn("similarity_threshold", kwargs)
            return arts

        def fake_sort(arts):
            order.append("sort")
            return arts

        def fake_save(arts, directory=pipeline.RAW_DIR):
            order.append("save")
            self.assertIs(arts, collected)
            return Path("out.json")

        def fake_enrich(arts, *, with_screenshot=False):
            order.append("enrich")
            self.assertIs(arts, collected)
            self.assertTrue(with_screenshot)
            return arts

        orig = {
            "collect": pipeline.collect_articles,
            "dedup": pipeline.deduplicate_fuzzy,
            "sort": pipeline.sort_articles,
            "save": pipeline.save_articles,
            "enrich": pipeline.enrich_articles,
        }
        pipeline.collect_articles = fake_collect
        pipeline.deduplicate_fuzzy = fake_dedup
        pipeline.sort_articles = fake_sort
        pipeline.save_articles = fake_save
        pipeline.enrich_articles = fake_enrich
        try:
            path = pipeline.run(days=2, max_naver=8, with_screenshot=True)
        finally:
            pipeline.collect_articles = orig["collect"]
            pipeline.deduplicate_fuzzy = orig["dedup"]
            pipeline.sort_articles = orig["sort"]
            pipeline.save_articles = orig["save"]
            pipeline.enrich_articles = orig["enrich"]

        self.assertEqual(path, Path("out.json"))
        self.assertEqual(order, ["collect", "dedup", "sort", "enrich", "save"])


class TestMainCLI(unittest.TestCase):
    def test_main_passes_days_argument(self):
        import runpy, tempfile, sys
        from utubenews import pipeline as pl
        from utubenews import utils as ut

        called = {}

        def fake_run(days=1, max_naver=collector._MAX_NAVER_ARTICLES, max_total=None, *, with_screenshot=False):
            called["days"] = days
            called["max_naver"] = max_naver
            called["max_total"] = max_total
            called["with_screenshot"] = with_screenshot
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            tmp.write(b"[]")
            tmp.close()
            return Path(tmp.name)

        orig_run = pl.run
        orig_log = ut.setup_logging
        pl.run = fake_run
        ut.setup_logging = lambda *a, **k: None

        argv = sys.argv
        sys.argv = [
            "main.py",
            "--days",
            "3",
            "--max-naver",
            "7",
            "--max-total",
            "15",
        ]
        try:
            runpy.run_module("main", run_name="__main__")
        finally:
            pl.run = orig_run
            ut.setup_logging = orig_log
            sys.argv = argv

        self.assertEqual(called.get("days"), 3)
        self.assertEqual(called.get("max_naver"), 7)
        self.assertEqual(called.get("max_total"), 15)
        self.assertTrue(called.get("with_screenshot"))

    def test_main_no_screenshot_flag(self):
        import runpy, tempfile, sys
        from utubenews import pipeline as pl
        from utubenews import utils as ut

        called = {}

        def fake_run(days=1, max_naver=collector._MAX_NAVER_ARTICLES, max_total=None, *, with_screenshot=False):
            called["with_screenshot"] = with_screenshot
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            tmp.write(b"[]")
            tmp.close()
            return Path(tmp.name)

        orig_run = pl.run
        orig_log = ut.setup_logging
        pl.run = fake_run
        ut.setup_logging = lambda *a, **k: None

        argv = sys.argv
        sys.argv = [
            "main.py",
            "--no-screenshot",
        ]
        try:
            runpy.run_module("main", run_name="__main__")
        finally:
            pl.run = orig_run
            ut.setup_logging = orig_log
            sys.argv = argv

        self.assertFalse(called.get("with_screenshot"))


class TestScreenshotDependency(unittest.TestCase):
    def test_capture_requires_firefox(self):
        import importlib
        import types
        from unittest import mock

        stub = sys.modules["screenshot"]
        # provide minimal selenium stubs so screenshot can import
        selenium = types.ModuleType("selenium")
        webdriver_mod = types.ModuleType("selenium.webdriver")
        firefox_mod = types.ModuleType("selenium.webdriver.firefox")
        prof_mod = types.ModuleType("selenium.webdriver.firefox.firefox_profile")
        opts_mod = types.ModuleType("selenium.webdriver.firefox.options")

        class DummyOptions:
            def __init__(self):
                self.headless = False
                self.profile = None

        prof_mod.FirefoxProfile = lambda profile_directory=None: object()
        opts_mod.Options = DummyOptions
        webdriver_mod.Firefox = lambda *a, **k: None
        webdriver_mod.firefox = firefox_mod
        firefox_mod.firefox_profile = prof_mod
        firefox_mod.options = opts_mod
        selenium.webdriver = webdriver_mod

        sys.modules.update({
            "selenium": selenium,
            "selenium.webdriver": webdriver_mod,
            "selenium.webdriver.firefox": firefox_mod,
            "selenium.webdriver.firefox.firefox_profile": prof_mod,
            "selenium.webdriver.firefox.options": opts_mod,
        })
        fake_auto = types.ModuleType("geckodriver_autoinstaller")
        fake_auto.install = lambda: None
        sys.modules["geckodriver_autoinstaller"] = fake_auto

        del sys.modules["screenshot"]
        screenshot = importlib.import_module("screenshot")

        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(RuntimeError):
                screenshot.capture("http://example.com", Path("tmp.png"))

        del sys.modules["screenshot"]
        sys.modules["screenshot"] = stub
        del sys.modules["geckodriver_autoinstaller"]
        for name in [
            "selenium",
            "selenium.webdriver",
            "selenium.webdriver.firefox",
            "selenium.webdriver.firefox.firefox_profile",
            "selenium.webdriver.firefox.options",
        ]:
            del sys.modules[name]

if __name__ == "__main__":
    unittest.main()
