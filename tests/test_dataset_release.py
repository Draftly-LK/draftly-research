"""Check that the public scoring package matches the paper's frozen metrics."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/dataset-release"))
from evaluate import read_jsonl, score, validate_split  # noqa: E402


class ReleaseTest(unittest.TestCase):
    def test_export_and_reference_scorer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run([sys.executable, str(ROOT / "scripts/dataset-release/build_release.py"),
                            "--out", temp], check=True, capture_output=True, text=True)
            base = Path(temp)
            benchmark = base / "draftly-statutory-retrieval"
            dev = read_jsonl(benchmark / "benchmark_v1/development.jsonl")
            test = read_jsonl(benchmark / "benchmark_v1/test.jsonl")
            validate_split(dev + test)
            self.assertEqual((len(dev), len(test), len({r["benchmark_matter_id"] for r in dev + test})),
                             (10, 40, 40))
            self.assertTrue(all(r["lawyer_validation_status"] == "pending" for r in dev + test))
            self.assertEqual(len(read_jsonl(benchmark / "source_papers/data.jsonl")), 16)
            self.assertEqual(len(read_jsonl(benchmark / "atomic_question_pool/data.jsonl")), 667)

            raw_dir = ROOT / "data/evaluvation/statutory-qa-v1/experiments"
            raw = read_jsonl(raw_dir / "raw-rankings/main-test/S5_hybrid_rerank.jsonl")
            predictions = [{"benchmark_question_id": r["query_id"], "ranked_section_ids": r["ranking"]}
                           for r in raw]
            actual = score(test, predictions)
            expected = json.loads((raw_dir / "metrics/main-test/summary.json").read_text(encoding="utf-8"))
            metrics = expected["systems"]["S5_hybrid_rerank"]["metrics"]
            self.assertAlmostEqual(actual["C@20_matter_macro"], metrics["complete@20"]["matter_macro"])
            self.assertAlmostEqual(actual["Indispensable_Recall@20_matter_macro"],
                                   metrics["recall@20"]["matter_macro"])

            index = read_jsonl(base / "draftly-sri-lanka-act-sources/acts/data.jsonl")
            self.assertEqual(len(index), 112)
            self.assertEqual(sum(bool(r["source_url"]) for r in index), 52)
            self.assertEqual(sum(bool(r["candidate_source_url"]) for r in index), 16)
            self.assertTrue(all("body" not in r and "text" not in r for r in index))

    def test_rejects_split_leakage_and_partial_predictions(self) -> None:
        rows = [{"benchmark_question_id": "a", "benchmark_matter_id": "m", "split": "development",
                 "indispensable_section_ids": ["s1"]},
                {"benchmark_question_id": "b", "benchmark_matter_id": "m", "split": "test",
                 "indispensable_section_ids": ["s2"]}]
        with self.assertRaisesRegex(ValueError, "both splits"):
            validate_split(rows)
        rows[1]["benchmark_matter_id"] = "n"
        with self.assertRaisesRegex(ValueError, "missing predictions"):
            score(rows, [{"benchmark_question_id": "a", "ranked_section_ids": ["s1"]}])


if __name__ == "__main__":
    unittest.main()
