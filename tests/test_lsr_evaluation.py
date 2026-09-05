from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from draftly.retrieval.index import build_index
from draftly.retrieval.lsr_evaluation import load_lsr_gold, run_lsr_evaluation

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD_BUILDER_PATH = REPO_ROOT / "scripts" / "legal-statute-retrieval" / "00_build_lsr_gold.py"


def _load_gold_builder():
    spec = importlib.util.spec_from_file_location("lsr_gold_builder", GOLD_BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gold_builder = _load_gold_builder()


class NormalizeTests(unittest.TestCase):
    def test_collapses_whitespace(self) -> None:
        self.assertEqual(gold_builder.normalize("a   b\n\nc"), "a b c")

    def test_drops_encoding_artifacts(self) -> None:
        self.assertEqual(gold_builder.normalize("investi�gated"), "investigated")
        self.assertEqual(gold_builder.normalize("investi\xadgated"), "investigated")


class BuildQueryTests(unittest.TestCase):
    def test_masks_citation_within_window_when_locatable(self) -> None:
        text = "Some opening text. Held, that Civil Procedure Code, s. 241 applies here. Closing text."
        quote = "Held, that Civil Procedure Code, s. 241 applies here."
        citation = "Civil Procedure Code, s. 241"
        query_text, construction = gold_builder.build_query(text, quote, citation)
        self.assertEqual(construction, gold_builder.WINDOW_CITATION_MASKED)
        self.assertIn(gold_builder.PLACEHOLDER, query_text)
        self.assertNotIn("241", query_text)

    def test_masks_whole_quote_when_citation_not_separately_found(self) -> None:
        text = "Some opening text. Held, that the claim succeeds under the applicable provision. Closing text."
        quote = "Held, that the claim succeeds under the applicable provision."
        citation = "a citation phrase that never appears in the text"
        query_text, construction = gold_builder.build_query(text, quote, citation)
        self.assertEqual(construction, gold_builder.WINDOW_QUOTE_MASKED)
        self.assertIn(gold_builder.PLACEHOLDER, query_text)

    def test_falls_back_when_quote_not_locatable_at_all(self) -> None:
        text = "This judgment text does not contain the extracted quote anywhere."
        quote = "A quote that drifted away from the stored judgment text."
        citation = "Civil Procedure Code, s. 241"
        query_text, construction = gold_builder.build_query(text, quote, citation)
        self.assertEqual(construction, gold_builder.HELD_SENTENCE_FALLBACK)
        self.assertEqual(query_text, gold_builder.normalize(quote))


class ParseYearTests(unittest.TestCase):
    def test_parses_digit_string(self) -> None:
        self.assertEqual(gold_builder.parse_year("1985"), 1985)

    def test_returns_none_for_blank_or_non_digit(self) -> None:
        self.assertIsNone(gold_builder.parse_year(""))
        self.assertIsNone(gold_builder.parse_year(None))
        self.assertIsNone(gold_builder.parse_year("circa 1900"))


class LsrEvaluationHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build_index(force=True)

    def test_run_lsr_evaluation_reports_overall_and_temporal_buckets(self) -> None:
        fixture_rows = [
            {
                "query_id": "lsr-fixture-1",
                "case_id": "fixture-case-1",
                "source_id": "SRC001",
                "section_number": "2",
                "section_id": "SRC001:s2",
                "query_text": "registration of a deed under the applicable Ordinance",
                "query_construction": "window-citation-masked",
                "case_year": 1990,
                "temporal_status": "applicable",
                "amended_after_judgment": [],
            },
            {
                "query_id": "lsr-fixture-2",
                "case_id": "fixture-case-2",
                "source_id": "SRC034",
                "section_number": "24",
                "section_id": "SRC034:s24",
                "query_text": "a claim under a provision that was later amended",
                "query_construction": "held-sentence-fallback",
                "case_year": 1985,
                "temporal_status": "superseded-since-judgment",
                "amended_after_judgment": [2017],
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            gold_path = Path(tmp) / "lsr_gold.jsonl"
            with gold_path.open("w", encoding="utf-8") as handle:
                for row in fixture_rows:
                    handle.write(json.dumps(row) + "\n")

            gold = load_lsr_gold(gold_path)
            self.assertEqual(len(gold), 2)

            output_dir = Path(tmp) / "run"
            metrics = run_lsr_evaluation(gold_path=gold_path, output_dir=output_dir, rerank=False)

            self.assertIn("overall", metrics)
            self.assertEqual(metrics["overall"]["questions"], 2)
            self.assertIn("applicable", metrics)
            self.assertEqual(metrics["applicable"]["questions"], 1)
            self.assertIn("superseded-since-judgment", metrics)
            self.assertEqual(metrics["superseded-since-judgment"]["questions"], 1)
            self.assertIn("history-unknown", metrics)
            self.assertEqual(metrics["history-unknown"]["questions"], 0)
            self.assertFalse(metrics["rerank_used"])
            self.assertTrue((output_dir / "metrics.json").exists())
            self.assertTrue((output_dir / "predictions.csv").exists())


if __name__ == "__main__":
    unittest.main()
