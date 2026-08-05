from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from draftly.retrieval.api import app
from draftly.retrieval.index import build_index


class StatuteApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build_index(force=True)
        cls.client = TestClient(app)

    def test_health_reports_ready_index(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["index"]["statutes"], 57)
        self.assertEqual(body["index"]["amendments"], 18)

    def test_topics_endpoint_returns_named_topics(self) -> None:
        response = self.client.get("/topics")

        self.assertEqual(response.status_code, 200)
        topics = response.json()
        self.assertTrue(topics)
        self.assertTrue(all({"topic_id", "slug", "name"}.issubset(topic) for topic in topics))

    def test_sources_endpoint_returns_registered_sources(self) -> None:
        response = self.client.get("/sources")

        self.assertEqual(response.status_code, 200)
        sources = response.json()
        self.assertTrue(sources)
        self.assertIn("SRC001", {source["source_id"] for source in sources})
        self.assertTrue(all({"source_id", "title", "kind"}.issubset(source) for source in sources))

    def test_search_endpoint_direct_section_lookup(self) -> None:
        response = self.client.get("/search", params={"q": "SRC001:s2", "limit": 3})

        self.assertEqual(response.status_code, 200)
        hits = response.json()
        self.assertTrue(hits)
        self.assertEqual(hits[0]["section_id"], "SRC001:s2")
        self.assertNotIn("text", hits[0])

    def test_search_endpoint_topic_and_kind_filters(self) -> None:
        response = self.client.get(
            "/search",
            params={
                "q": "registration of deed",
                "topic_slug": "02-registration-of-documents",
                "kind": "statute",
                "limit": 5,
            },
        )

        self.assertEqual(response.status_code, 200)
        hits = response.json()
        self.assertTrue(hits)
        self.assertTrue(all(hit["document_type"] == "statute" for hit in hits))
        self.assertTrue(all("02-registration-of-documents" in hit["topics"] for hit in hits))

    def test_search_endpoint_rejects_unknown_kind(self) -> None:
        response = self.client.get("/search", params={"q": "deed", "kind": "case-law"})

        self.assertEqual(response.status_code, 422)
        self.assertIn("case-law", response.json()["detail"])

    def test_search_endpoint_requires_a_query(self) -> None:
        response = self.client.get("/search")

        self.assertEqual(response.status_code, 422)

    def test_search_endpoint_rejects_limit_above_maximum(self) -> None:
        response = self.client.get("/search", params={"q": "deed", "limit": 500})

        self.assertEqual(response.status_code, 422)

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_answer_endpoint_without_api_key_returns_evidence_only(self) -> None:
        response = self.client.get("/answer", params={"q": "What makes a deed of transfer valid?"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["outcome"], "evidence_only")
        self.assertEqual(body["fallback_reason"], "missing_gemini_api_key")
        self.assertTrue(body["hits"])
        self.assertNotIn("raw_response", body)

    def test_answer_endpoint_abstains_on_known_corpus_gap(self) -> None:
        response = self.client.get(
            "/answer", params={"q": "Which authority approves development in the coastal zone?"}
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["outcome"], "insufficient_authority")
        self.assertEqual(body["fallback_reason"], "known_corpus_gap")
        self.assertFalse(body["hits"])


if __name__ == "__main__":
    unittest.main()
