import types
import unittest

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

        orig_requests = nc.requests
        nc.requests = dummy_req
        try:
            articles = nc.fetch_naver_articles("q", "topic", days=1, max_pages=2)
        finally:
            nc.requests = orig_requests

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "T1")


if __name__ == "__main__":
    unittest.main()
