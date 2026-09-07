"""Focused tests for the statutory-qa-v1 pipeline. Offline; no model download
is needed (the dense channel and reranker are not exercised here).

    uv run pytest tests/test_statutory_qa.py -q
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "statutory-qa"
sys.path.insert(0, str(SCRIPTS))

import sq_common as C  # noqa: E402
import sq_retrieval as R  # noqa: E402
import evaluate as E  # noqa: E402
import validate_legal_map as V  # noqa: E402

CORPUS_READY = (C.CORPUS_DIR / "sections.jsonl").exists()


class CommonTests(unittest.TestCase):
    def test_excerpt_match_normalises_whitespace_and_quotes(self):
        body = "the  “Registrar-General”\nshall   keep a register"
        self.assertTrue(C.excerpt_in('the "Registrar-General" shall keep', body))
        self.assertFalse(C.excerpt_in("shall not keep", body))

    def test_paper_sessions_take_earliest_session(self):
        s = C.paper_sessions()
        self.assertEqual(s[9]["date"], "2021-10")  # "OCTOBER 2021 / APRIL 2022"
        self.assertEqual(s[1]["date"], "2026-04")


@unittest.skipUnless(CORPUS_READY, "corpus not built")
class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = C.read_jsonl(C.CORPUS_DIR / "sections.jsonl")
        cls.by_id = {s["section_id"]: s for s in cls.sections}
        cls.manifest = C.read_json(C.CORPUS_DIR / "manifest.json")

    def test_section_ids_unique_and_shaped(self):
        ids = [s["section_id"] for s in self.sections]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(re.match(r"^\d+-\d{4}/s[0-9A-Za-z-]+(-\d+)?$", i) for i in ids))

    def test_known_sections_present(self):
        for sid in ("1-1907/s31", "7-1840/s2", "38-2014/s2", "38-2014/s3", "23-1927/s7"):
            self.assertIn(sid, self.by_id)

    def test_manifest_counts_match_files(self):
        self.assertEqual(self.manifest["sections"], len(self.sections))
        edges = C.read_jsonl(C.CORPUS_DIR / "edges.jsonl")
        self.assertEqual(sum(self.manifest["edges"].values()), len(edges))
        rels = {e["relation"] for e in edges}
        self.assertTrue(rels <= {"defines", "excepts", "qualifies", "amends", "cross_references", "procedurally_requires"})

    def test_exception_edge_is_typed(self):
        edges = C.read_jsonl(C.CORPUS_DIR / "edges.jsonl")
        self.assertTrue(any(e["src"] == "38-2014/s3" and e["dst"] == "38-2014/s2" and e["relation"] == "excepts" for e in edges))

    def test_bm25_finds_two_notary_rule(self):
        corpus = R.Corpus()
        idx = R.BM25F(corpus, None)
        ranking = R.ranked(idx.scores("deed executed before more than one notary"), corpus.ids, 5)
        self.assertIn("1-1907/s31", ranking)

    def test_field_weights_change_ranking_not_ids(self):
        corpus = R.Corpus()
        plain = R.BM25F(corpus, None)
        weighted = R.BM25F(corpus, R.DEFAULT_FIELD_WEIGHTS)
        q = "restriction on transfer of land to a foreigner"
        a = R.ranked(plain.scores(q), corpus.ids, 20)
        b = R.ranked(weighted.scores(q), corpus.ids, 20)
        self.assertIn("38-2014/s2", a[:5])
        self.assertIn("38-2014/s2", b[:5])

    def test_temporal_in_force(self):
        corpus = R.Corpus()
        self.assertTrue(corpus.in_force("7-1840/s2", 1900))
        # an amending Act from 2022 is not in force for a 2019 matter
        amend = next(a for a in corpus.acts.values() if a["kind"] == "amendment" and a.get("year") == 2022)
        sid = corpus.sections_by_act[amend["act_id"]][0]
        self.assertFalse(corpus.in_force(sid, 2019))
        self.assertTrue(corpus.in_force(sid, 2024))


class FusionAndMetricTests(unittest.TestCase):
    def test_rrf_orders_shared_items_first(self):
        fused = R.rrf([["a", "b", "c"], ["b", "a", "d"]], k=60)
        self.assertEqual(R.top(fused, 2), ["a", "b"])

    def test_per_question_metrics(self):
        secs = {"x/s1": {"act_id": "x", "in_force_from_year": 1900}, "x/s2": {"act_id": "x", "in_force_from_year": 1900},
                "y/s1": {"act_id": "y", "in_force_from_year": 2030}}
        acts = {"x": {"kind": "principal"}, "y": {"kind": "principal"}}
        gold = {"indispensable_section_ids": ["x/s1", "x/s2"], "supporting_section_ids": [], "gold_act_ids": ["x"], "matter_reference_date": "2020-04"}
        row = {"query_id": "q", "matter_id": "m", "ranking": ["y/s1", "x/s1", "z/s9", "x/s2"]}
        m = E.per_question(row, gold, secs, acts)
        self.assertAlmostEqual(m["recall@5"], 1.0)
        self.assertEqual(m["complete@5"], 1.0)
        self.assertAlmostEqual(m["mrr"], 0.5)
        self.assertEqual(m["act_acc@5"], 1.0)
        self.assertAlmostEqual(m["temporal_viol@10"], 0.25)
        self.assertEqual(m["missed_ind"], [])

    def test_bootstrap_ci_contains_mean(self):
        import numpy as np
        mean, lo, hi = E.bootstrap({"a": 0.2, "b": 0.6, "c": 1.0, "d": 0.4}, np.random.default_rng(1))
        self.assertTrue(lo <= mean <= hi)


class GuardTests(unittest.TestCase):
    def test_runtime_modules_never_name_gold(self):
        for name in ("sq_retrieval.py", "run_retrieval.py", "search_corpus.py", "build_corpus.py"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            self.assertNotIn("private-gold", text.replace("never the gold file", ""), name)

    def test_validator_rejects_non_verbatim_excerpt(self):
        if not CORPUS_READY:
            self.skipTest("corpus not built")
        s = V.sections()["7-1840/s2"]
        self.assertTrue(C.excerpt_in("No sale, purchase, transfer", s["body"]))
        self.assertFalse(C.excerpt_in("No sale, purchase, transfer of chattels", s["body"]))

    def test_schema_forbids_lawyer_validated_flag(self):
        schema = C.read_json(C.SCHEMAS_DIR / "legal-map.schema.json")
        self.assertEqual(schema["$defs"]["question"]["properties"]["lawyer_validation_status"], {"const": "pending"})


if __name__ == "__main__":
    unittest.main()
