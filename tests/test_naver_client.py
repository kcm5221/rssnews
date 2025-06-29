import types
import unittest
import os

import utubenews.naver_news_client as nc


class TestFetchNaverArticles(unittest.TestCase):
    def test_returns_partial_on_request_error(self):
        class DummyRequestException(Exception):
            pass

        dummy_req = types.SimpleNamespace(
            RequestException=DummyRequestException,
            exceptions=types.SimpleNamespace(RequestException=DummyRequestException),
        )

        class OkResponse:
            def raise_for_status(self):
                pass
            def json(self):
                return {
                    "items": [
                        {
                            "title": "<b>T1</b>",
                            "link": "L1",
                            "description": "D1",
                            "pubDate": "Mon, 01 Jan 2099 00:00:00 +0900",
                        }
                    ]
                }

        calls = {"count": 0}

        def dummy_get(*args, **kwargs):
            if calls["count"] == 0:
                calls["count"] += 1
                return OkResponse()
            raise DummyRequestException("boom")

        dummy_req.get = dummy_get

        # ensure env vars exist
        orig_id = os.environ.get("NAVER_CLIENT_ID")
        orig_secret = os.environ.get("NAVER_CLIENT_SECRET")
        os.environ["NAVER_CLIENT_ID"] = "id"
        os.environ["NAVER_CLIENT_SECRET"] = "secret"

        orig_requests = nc.requests
        nc.requests = dummy_req
        try:
            articles = nc.fetch_naver_articles("q", "topic", days=1, max_pages=2)
        finally:
            nc.requests = orig_requests
            if orig_id is not None:
                os.environ["NAVER_CLIENT_ID"] = orig_id
            else:
                os.environ.pop("NAVER_CLIENT_ID", None)
            if orig_secret is not None:
                os.environ["NAVER_CLIENT_SECRET"] = orig_secret
            else:
                os.environ.pop("NAVER_CLIENT_SECRET", None)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "T1")

    def test_skips_when_env_missing(self):
        orig_id = os.environ.pop("NAVER_CLIENT_ID", None)
        orig_secret = os.environ.pop("NAVER_CLIENT_SECRET", None)
        try:
            with self.assertLogs(nc._LOG, level="WARNING") as cm:
                arts = nc.fetch_naver_articles("q", "topic")
        finally:
            if orig_id is not None:
                os.environ["NAVER_CLIENT_ID"] = orig_id
            if orig_secret is not None:
                os.environ["NAVER_CLIENT_SECRET"] = orig_secret
        self.assertEqual(arts, [])
        log_output = "\n".join(cm.output)
        self.assertIn("NAVER_CLIENT_ID/SECRET", log_output)


if __name__ == "__main__":
    unittest.main()
