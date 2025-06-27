import types
import sys
import unittest
from pathlib import Path

# ensure heavy deps are stubbed
for mod in ["feedparser", "yaml", "requests", "bs4"]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

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
            result = collector.collect_all(days=1)
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
            result = collector.collect_all(days=1)
        finally:
            collector._load_sources = orig_load
            collector.fetch_naver_articles = orig_naver

        expected = [dict(good, src="naver")]
        self.assertEqual(result, expected)

class TestEnrichArticles(unittest.TestCase):
    def test_enrich_articles_uses_summary_or_body(self):
        art_with_sum = {"title": "T1", "link": "L1", "summary": "SUM"}
        art_no_sum = {"title": "T2", "link": "L2"}
        arts = [art_with_sum, art_no_sum]

        def fake_extract(link):
            return f"BODY-{link}"

        def fake_clean(text):
            return text

        def fake_sum(title, src):
            return f"SCRIPT-{src}"

        orig = {
            "ext": pipeline.extract_main_text,
            "clean": pipeline.clean_text,
            "qs": pipeline.quick_summarize,
        }
        pipeline.extract_main_text = fake_extract
        pipeline.clean_text = fake_clean
        pipeline.quick_summarize = fake_sum
        try:
            out = pipeline.enrich_articles(arts)
        finally:
            pipeline.extract_main_text = orig["ext"]
            pipeline.clean_text = orig["clean"]
            pipeline.quick_summarize = orig["qs"]

        self.assertEqual(out[0]["script"], "SCRIPT-SUM")
        self.assertEqual(out[1]["script"], "SCRIPT-BODY-L2")
        self.assertEqual(out[0]["body"], "BODY-L1")
        self.assertEqual(out[1]["body"], "BODY-L2")

class TestRun(unittest.TestCase):
    def test_run_calls_steps_and_returns_path(self):
        collected = [{"title": "A"}]
        order = []

        def fake_collect(days=1):
            order.append("collect")
            self.assertEqual(days, 2)
            return collected

        def fake_dedup(arts):
            order.append("dedup")
            self.assertIs(arts, collected)
            return arts

        def fake_enrich(arts):
            order.append("enrich")
            return arts

        def fake_sort(arts):
            order.append("sort")
            return arts

        def fake_save(arts, directory=pipeline.RAW_DIR):
            order.append("save")
            self.assertIs(arts, collected)
            return Path("out.json")

        orig = {
            "collect": pipeline.collect_articles,
            "dedup": pipeline.deduplicate,
            "enrich": pipeline.enrich_articles,
            "sort": pipeline.sort_articles,
            "save": pipeline.save_articles,
        }
        pipeline.collect_articles = fake_collect
        pipeline.deduplicate = fake_dedup
        pipeline.enrich_articles = fake_enrich
        pipeline.sort_articles = fake_sort
        pipeline.save_articles = fake_save
        try:
            path = pipeline.run(days=2)
        finally:
            pipeline.collect_articles = orig["collect"]
            pipeline.deduplicate = orig["dedup"]
            pipeline.enrich_articles = orig["enrich"]
            pipeline.sort_articles = orig["sort"]
            pipeline.save_articles = orig["save"]

        self.assertEqual(path, Path("out.json"))
        self.assertEqual(order, ["collect", "dedup", "enrich", "sort", "save"])

if __name__ == "__main__":
    unittest.main()
