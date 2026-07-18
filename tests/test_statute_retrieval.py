from __future__ import annotations

import unittest

from draftly.retrieval import StatuteQuery, build_index, search
from draftly.retrieval.answering import parse_model_json, validate_answer_payload
from draftly.retrieval.evaluation import run_evaluation
from draftly.retrieval.index import connect
from draftly.retrieval.paths import EVAL_DIR


class StatuteRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stats = build_index(force=True)

    def test_index_scope_is_statutes_and_amendments_only(self) -> None:
        self.assertEqual(self.stats.documents, 75)
        self.assertEqual(self.stats.statutes, 57)
        self.assertEqual(self.stats.amendments, 18)
        with connect() as conn:
            kinds = {row["kind"] for row in conn.execute("SELECT DISTINCT kind FROM sections").fetchall()}
        self.assertEqual(kinds, {"statute", "amendment"})

    def test_required_sections_are_recovered(self) -> None:
        with connect() as conn:
            for section_id in ["SRC001:s2", "SRC005:s7", "SRC034:s24", "SRC071:s3"]:
                row = conn.execute("SELECT section_id FROM sections WHERE section_id = ?", (section_id,)).fetchone()
                self.assertIsNotNone(row, section_id)

    def test_direct_section_lookup(self) -> None:
        hits = search(StatuteQuery(text="SRC001:s2", limit=3))
        self.assertTrue(hits)
        self.assertEqual(hits[0].section_id, "SRC001:s2")

    def test_topic_and_kind_filters(self) -> None:
        hits = search(
            StatuteQuery(
                text="registration of deed",
                topic_slug="02-registration-of-documents",
                kinds=("statute",),
                limit=5,
            )
        )
        self.assertTrue(hits)
        self.assertTrue(all(hit.document_type == "statute" for hit in hits))
        self.assertTrue(all("02-registration-of-documents" in hit.topics for hit in hits))

    def test_empty_query_returns_no_hits(self) -> None:
        self.assertEqual(search(StatuteQuery(text="   ")), [])

    def test_gemini_validation_accepts_only_retrieved_citations(self) -> None:
        payload, error = parse_model_json(
            '{"abstained": false, "claims": [{"text": "A deed must be written.", "citations": ["SRC001:s2"]}], "limitations": []}'
        )
        self.assertIsNone(error)
        self.assertIsNone(validate_answer_payload(payload, {"SRC001:s2"}))
        self.assertIn("unknown_citation", validate_answer_payload(payload, {"SRC005:s7"}) or "")

    def test_evaluation_outputs_metrics(self) -> None:
        metrics = run_evaluation(EVAL_DIR)
        self.assertEqual(metrics["questions"], 10)
        self.assertIn("recall_at_10", metrics)


class StreamlitAppSmokeTests(unittest.TestCase):
    def test_streamlit_app_loads(self) -> None:
        try:
            from streamlit.testing.v1 import AppTest
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"Streamlit AppTest unavailable: {exc}")

        app = AppTest.from_file("apps/statute-retrieval/app.py")
        app.run(timeout=60)
        self.assertFalse(app.exception)
        self.assertIn("Draftly Statute Q&A", app.title[0].value)


if __name__ == "__main__":
    unittest.main()

