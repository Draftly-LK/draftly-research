"""Tests for scripts/pastpaper-dataset/build_selected_matters.py.

Everything runs on small synthetic atomic records, so each rule (selection,
grouping, context order, dedup, shared-vs-specific split, integrity failures,
deterministic IDs, JSONL validity) is exercised in isolation rather than hoped
for in the 667-record corpus. A final test runs the real corpus end to end.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "scripts" / "pastpaper-dataset"
sys.path.insert(0, str(SCRIPT_DIR))

import build_selected_matters as bsm  # noqa: E402

SHARED = "Gamini owned Lot A in Plan 2525."
GROUP = "Kanthi is a Notary in Colombo."
OWN_B = "After execution she lacked the Yearly Certificate."


def question(atomic_id, *, paper=1, qno=1, part="i", item=None, matter="P01-Q01-M00",
             shared=None, group=None, prior=(), own=None, group_lead=None, stem=None,
             text="What is the position?"):
    return {
        "atomic_id": atomic_id,
        "part_uid": f"paper-{paper:02d}/q{qno}/{part}" + (f"/{item}" if item else ""),
        "paper_no": paper,
        "question_no": qno,
        "part_id": part,
        "item_id": item,
        "matter_id": matter,
        "compulsory": False,
        "stem": stem,
        "shared_background": shared,
        "shared_background_origin": "fact_pattern" if shared else None,
        "group_background": group,
        "group_lead": group_lead,
        "prior_background": list(prior),
        "own_background": own,
        "question": text,
        "question_kind": "question",
        "marks": 5,
        "part_marks": None,
        "pdf_page": 1,
        "source_quote": f"({part}) {text}",
        "split_method": "none",
        "needs_review": [],
    }


def classification(atomic_id, sources=("shared",), *, dep="required", rich="detailed",
                   quality="clean", action="keep", conf=0.9, flags=()):
    return {
        "atomic_id": atomic_id,
        "context_sources": list(sources),
        "context_dependency": dep,
        "scenario_richness": rich,
        "extraction_quality": quality,
        "candidate_action": action,
        "decision_reason": "",
        "background_evidence": "",
        "question_evidence": "",
        "missing_fact_types": [],
        "confidence": conf,
        "flags": list(flags),
    }


def run(questions, classifications, exp_q=None, exp_m=None):
    return bsm.build(questions, classifications, exp_q, exp_m)


class SelectionPredicateTests(unittest.TestCase):
    def test_all_five_clauses_are_required(self):
        base = classification("X")
        self.assertTrue(bsm.is_selected(base))
        for field, bad in [
            ("candidate_action", "enrich"),
            ("scenario_richness", "minimal"),
            ("extraction_quality", "review"),
            ("context_dependency", "none"),
            ("confidence", 0.79),
        ]:
            c = dict(base, **{field: bad})
            self.assertFalse(bsm.is_selected(c), field)
            self.assertEqual(len(bsm.failed_predicates(c)), 1, field)

    def test_boundary_confidence_and_partial_dependency_are_kept(self):
        self.assertTrue(bsm.is_selected(classification("X", conf=0.80, dep="partial")))

    def test_unselected_records_never_reach_the_output(self):
        qs = [question("A", shared=SHARED), question("B", part="ii", shared=SHARED)]
        cs = [classification("A"), classification("B", action="drop_candidate", dep="none")]
        matters, flat, _ = run(qs, cs)
        self.assertEqual([f["atomic_id"] for f in flat], ["A"])
        self.assertEqual(len(matters[0]["questions"]), 1)


class GroupingTests(unittest.TestCase):
    def test_matter_id_groups_and_missing_matter_id_becomes_singleton(self):
        qs = [
            question("P01-Q01-P01", part="i", shared=SHARED),
            question("P01-Q01-P02", part="ii", shared=SHARED),
            question("P01-Q02-P01", qno=2, matter=None, own=OWN_B),
            question("P01-Q03-P01", qno=3, matter="", own=OWN_B),
        ]
        cs = [
            classification("P01-Q01-P01"), classification("P01-Q01-P02"),
            classification("P01-Q02-P01", ["local"]), classification("P01-Q03-P01", ["local"]),
        ]
        matters, flat, audit = run(qs, cs)
        self.assertEqual(len(matters), 3)
        self.assertEqual(len(flat), 4)
        keys = [m["grouping_key"] for m in matters]
        self.assertEqual(keys, ["P01-Q01-M00", "atomic:P01-Q02-P01", "atomic:P01-Q03-P01"])
        self.assertIsNone(matters[1]["source_matter_id"])
        self.assertEqual(matters[0]["source_matter_id"], "P01-Q01-M00")
        self.assertEqual(audit["questions_per_matter_distribution"], {"1": 2, "2": 1})


class ContextOrderingTests(unittest.TestCase):
    def test_effective_background_follows_shared_group_prior_own(self):
        q = question("A", shared="S.", group="G.", prior=["P1.", "P2."], own="O.")
        segs = bsm.context_segments(q, ["local", "prior", "group", "shared"])
        self.assertEqual([s.original for s in segs], ["S.", "G.", "P1.", "P2.", "O."])

    def test_only_listed_sources_are_used(self):
        q = question("A", shared="S.", group="G.", prior=["P1."], own="O.")
        segs = bsm.context_segments(q, ["prior", "local"])
        self.assertEqual([s.original for s in segs], ["P1.", "O."])
        self.assertEqual(bsm.context_segments(q, []), [])

    def test_prior_background_array_is_expanded_in_order(self):
        q = question("A", prior=["First.", "Second.", "Third."])
        segs = bsm.context_segments(q, ["prior"])
        self.assertEqual([s.index for s in segs], [0, 1, 2])
        self.assertEqual([s.field_label for s in segs],
                         ["prior_background[0]", "prior_background[1]", "prior_background[2]"])


class ContextDeduplicationTests(unittest.TestCase):
    def test_identical_segment_appears_once(self):
        q = question("A", group=GROUP, prior=[GROUP, "New fact."])
        segs = bsm.context_segments(q, ["group", "prior"])
        self.assertEqual([s.original for s in segs], [GROUP, "New fact."])

    def test_dedup_compares_normalized_text(self):
        q = question("A", shared="A  fact.", prior=["A fact."])
        segs = bsm.context_segments(q, ["shared", "prior"])
        self.assertEqual(len(segs), 1)

    def test_superset_segment_is_kept_and_reported(self):
        qs = [question("A", group=GROUP, prior=[GROUP + " " + OWN_B])]
        cs = [classification("A", ["group", "prior"])]
        _, flat, audit = run(qs, cs)
        self.assertIn(OWN_B, flat[0]["background_original"])
        self.assertEqual(audit["overlapping_context_segments"][0]["within"], "prior_background[0]")


class SharedVersusSpecificContextTests(unittest.TestCase):
    def test_shared_goes_to_matter_and_own_stays_with_question(self):
        qs = [
            question("A", part="i", shared=SHARED),
            question("B", part="ii", shared=SHARED, own=OWN_B),
        ]
        cs = [classification("A"), classification("B", ["shared", "local"])]
        matters, flat, _ = run(qs, cs)
        m = matters[0]
        self.assertEqual(m["matter_background"]["original"], SHARED)
        self.assertEqual(m["matter_background"]["source_fields"],
                         [{"segment_index": 0, "field": "shared_background", "atomic_ids": ["A", "B"]}])
        qa, qb = m["questions"]
        self.assertIsNone(qa["question_specific_context"]["own_background"])
        self.assertEqual(qb["question_specific_context"]["own_background"], OWN_B)
        self.assertEqual(qa["effective_background_original"], SHARED)
        self.assertEqual(qb["effective_background_original"], SHARED + "\n\n" + OWN_B)
        self.assertEqual(flat[1]["background_original"], qb["effective_background_original"])

    def test_common_fact_across_own_and_prior_fields_is_promoted(self):
        # Part 1 states the facts locally; part 2 inherits them as prior and adds its own.
        qs = [
            question("A", part="1", own=SHARED),
            question("B", part="2", prior=[SHARED], own=OWN_B),
        ]
        cs = [classification("A", ["local"]), classification("B", ["prior", "local"])]
        matters, _, _ = run(qs, cs)
        m = matters[0]
        self.assertEqual(m["matter_background"]["original"], SHARED)
        fields = {(f["field"], tuple(f["atomic_ids"])) for f in m["matter_background"]["source_fields"]}
        self.assertEqual(fields, {("own_background", ("A",)), ("prior_background", ("B",))})
        self.assertEqual(m["questions"][1]["question_specific_context"]["prior_background"], [])
        self.assertEqual(m["questions"][1]["question_specific_context"]["own_background"], OWN_B)

    def test_group_fact_not_shared_by_every_question_stays_specific(self):
        qs = [
            question("A", part="1", own=SHARED),
            question("B", part="2", item="a", group="Loan of Rs.3,000,000/-.", prior=[SHARED]),
        ]
        cs = [classification("A", ["local"]), classification("B", ["group", "prior"])]
        matters, _, _ = run(qs, cs)
        m = matters[0]
        self.assertEqual(m["matter_background"]["original"], SHARED)
        self.assertEqual(m["questions"][1]["question_specific_context"]["group_background"],
                         "Loan of Rs.3,000,000/-.")

    def test_instructional_group_lead_is_ignored_and_factual_one_is_flagged(self):
        qs = [
            question("A", part="1", shared=SHARED, group_lead="Write notes on the following."),
            question("B", part="2", shared=SHARED, group_lead="Nimal owns Lot B and leases it."),
        ]
        cs = [classification("A"), classification("B")]
        _, flat, audit = run(qs, cs)
        self.assertNotIn("Write notes", flat[0]["background_original"])
        self.assertNotIn("Nimal owns", flat[1]["background_original"])
        self.assertEqual([r["atomic_id"] for r in audit["group_lead_factual_context_review"]], ["B"])

    def test_listed_source_with_empty_field_quarantines_the_matter(self):
        qs = [question("A", shared=None)]
        cs = [classification("A", ["shared"])]
        with self.assertRaises(bsm.ValidationError) as ctx:
            run(qs, cs)
        self.assertEqual(ctx.exception.report["quarantined_records"][0]["atomic_ids"], ["A"])
        self.assertFalse(ctx.exception.report["validation_passed"])

    def test_conflicting_shared_background_quarantines_the_matter(self):
        qs = [question("A", part="i", shared=SHARED), question("B", part="ii", shared="Different.")]
        cs = [classification("A"), classification("B")]
        with self.assertRaises(bsm.ValidationError) as ctx:
            run(qs, cs)
        self.assertEqual(len(ctx.exception.report["background_conflicts"]), 1)


class IntegrityTests(unittest.TestCase):
    def test_duplicate_atomic_id_is_rejected(self):
        qs = [question("A", shared=SHARED), question("A", shared=SHARED)]
        cs = [classification("A")]
        with self.assertRaises(bsm.ValidationError) as ctx:
            run(qs, cs)
        self.assertEqual(ctx.exception.report["duplicate_atomic_ids"], ["A"])

    def test_duplicate_classification_id_is_rejected(self):
        qs = [question("A", shared=SHARED)]
        cs = [classification("A"), classification("A")]
        with self.assertRaises(bsm.ValidationError):
            run(qs, cs)

    def test_classification_without_question_is_rejected(self):
        qs = [question("A", shared=SHARED)]
        cs = [classification("A"), classification("GHOST")]
        with self.assertRaises(bsm.ValidationError) as ctx:
            run(qs, cs)
        self.assertEqual(ctx.exception.report["missing_join_ids"], ["GHOST"])

    def test_question_without_classification_is_reported_not_fatal(self):
        qs = [question("A", shared=SHARED), question("B", part="ii", shared=SHARED)]
        cs = [classification("A")]
        _, flat, audit = run(qs, cs)
        self.assertEqual(audit["missing_join_ids"], ["B"])
        self.assertEqual(len(flat), 1)

    def test_bad_enum_and_bad_confidence_are_rejected(self):
        qs = [question("A", shared=SHARED)]
        with self.assertRaises(bsm.ValidationError):
            run(qs, [classification("A", dep="sometimes")])
        with self.assertRaises(bsm.ValidationError):
            run(qs, [classification("A", conf=1.5)])
        with self.assertRaises(bsm.ValidationError):
            run(qs, [classification("A", conf="0.9")])

    def test_missing_required_field_is_rejected(self):
        q = question("A", shared=SHARED)
        del q["source_quote"]
        with self.assertRaises(bsm.ValidationError):
            run([q], [classification("A")])

    def test_invalid_jsonl_line_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.jsonl"
            p.write_text('{"atomic_id": "A"}\n{not json}\n', encoding="utf-8")
            with self.assertRaises(bsm.ValidationError):
                bsm.read_jsonl(p)


class ExpectedCountTests(unittest.TestCase):
    def test_wrong_question_count_fails_with_diagnostic(self):
        qs = [question("A", shared=SHARED), question("B", part="ii", shared=SHARED)]
        cs = [classification("A"), classification("B", conf=0.5)]
        with self.assertRaises(bsm.ValidationError) as ctx:
            run(qs, cs, exp_q=2, exp_m=1)
        rep = ctx.exception.report
        self.assertEqual(rep["selected_atomic_question_count"], 1)
        self.assertEqual(rep["selected_atomic_ids"], ["A"])
        self.assertEqual(rep["near_miss_records"][0]["atomic_id"], "B")
        self.assertEqual(rep["near_miss_records"][0]["failed"], ["confidence=0.5"])

    def test_wrong_matter_count_fails_with_grouping(self):
        qs = [question("A", shared=SHARED), question("B", qno=2, matter="P01-Q02-M00", shared=SHARED)]
        cs = [classification("A"), classification("B")]
        with self.assertRaises(bsm.ValidationError) as ctx:
            run(qs, cs, exp_q=2, exp_m=1)
        self.assertEqual(sorted(ctx.exception.report["grouping"]), ["P01-Q01-M00", "P01-Q02-M00"])

    def test_matching_counts_pass(self):
        qs = [question("A", shared=SHARED)]
        _, _, audit = run(qs, [classification("A")], exp_q=1, exp_m=1)
        self.assertTrue(audit["validation_passed"])


class DeterministicIdTests(unittest.TestCase):
    def fixture(self):
        qs = [
            question("P02-Q01-P01", paper=2, matter="P02-Q01-M00", shared=SHARED),
            question("P01-Q03-P01", qno=3, matter="P01-Q03-M00", own=OWN_B),
            question("P01-Q01-P10", part="x", shared=SHARED),
            question("P01-Q01-P02", part="ii", shared=SHARED),
            question("P01-Q01-P09", part="ix", shared=SHARED),
        ]
        cs = [classification(q["atomic_id"], ["local"] if q["own_background"] else ["shared"]) for q in qs]
        return qs, cs

    def test_ids_follow_paper_question_and_part_order(self):
        matters, flat, _ = run(*self.fixture())
        self.assertEqual([m["benchmark_matter_id"] for m in matters], ["M001", "M002", "M003"])
        self.assertEqual([m["grouping_key"] for m in matters], ["P01-Q01-M00", "P01-Q03-M00", "P02-Q01-M00"])
        first = matters[0]["questions"]
        # Roman numerals sort by value, not lexically: ii < ix < x.
        self.assertEqual([q["atomic_id"] for q in first], ["P01-Q01-P02", "P01-Q01-P09", "P01-Q01-P10"])
        self.assertEqual([q["benchmark_question_id"] for q in first], ["M001-Q01", "M001-Q02", "M001-Q03"])
        self.assertEqual(flat[0]["benchmark_question_id"], "M001-Q01")

    def test_input_order_does_not_change_output(self):
        qs, cs = self.fixture()
        a = run(qs, cs)
        b = run(list(reversed(copy.deepcopy(qs))), list(reversed(copy.deepcopy(cs))))
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_label_sort_key_families(self):
        keys = [bsm.label_sort_key(x) for x in ["2", "10", "ii", "iv", "ix", "a", "b"]]
        self.assertEqual(keys, sorted(keys))
        self.assertLess(bsm.label_sort_key(None), bsm.label_sort_key("1"))


class NormalizationTests(unittest.TestCase):
    def test_whitespace_only_changes(self):
        text = "Deed  No. 515\r\ndated 10th March 1986 , attested ?"
        norm, kinds = bsm.normalize_text(text)
        self.assertEqual(norm, "Deed No. 515 dated 10th March 1986, attested?")
        self.assertEqual(kinds, ["line_endings", "collapsed_whitespace", "space_before_punctuation"])

    def test_glued_punctuation_is_left_alone_and_reported(self):
        text = "Notary in Colombo .Her friend Rupa"
        norm, _ = bsm.normalize_text(text)
        self.assertEqual(norm, text)
        self.assertEqual(len(bsm.ambiguous_punctuation(text)), 1)

    def test_numbers_and_unicode_are_preserved(self):
        text = "Rs. 3,000,000/= on 2nd February 1981 — “Waters Edge” No.400A"
        self.assertEqual(bsm.normalize_text(text)[0], text)

    def test_originals_are_stored_beside_normalized(self):
        qs = [question("A", shared="Two  spaces.", text="Why ?")]
        matters, flat, audit = run(qs, [classification("A")])
        q = matters[0]["questions"][0]
        self.assertEqual(q["question_original"], "Why ?")
        self.assertEqual(q["question_normalized"], "Why?")
        self.assertEqual(matters[0]["matter_background"]["original"], "Two  spaces.")
        self.assertEqual(matters[0]["matter_background"]["normalized"], "Two spaces.")
        self.assertEqual({c["field"] for c in audit["normalization_changes"]},
                         {"shared_background", "question"})


class JsonlOutputTests(unittest.TestCase):
    def test_cli_writes_valid_jsonl_and_is_idempotent(self):
        import tempfile
        qs = [
            question("A", part="i", shared="Unicode – “quotes” – ශ්‍රී"),
            question("B", part="ii", shared="Unicode – “quotes” – ශ්‍රී", own=OWN_B),
        ]
        cs = [classification("A"), classification("B", ["shared", "local"])]
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "q.jsonl").write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in qs), encoding="utf-8")
            (d / "c.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cs), encoding="utf-8")
            argv = ["--questions", str(d / "q.jsonl"), "--classifications", str(d / "c.jsonl"),
                    "--out-dir", str(d / "out"), "--expected-questions", "2", "--expected-matters", "1"]
            self.assertEqual(bsm.main(argv), 0)
            first = {p.name: p.read_bytes() for p in (d / "out").iterdir()}
            self.assertEqual(bsm.main(argv), 0)
            second = {p.name: p.read_bytes() for p in (d / "out").iterdir()}
            self.assertEqual(first, second)
            self.assertEqual(set(first), {"selected-matters.jsonl", "selected-questions.jsonl",
                                          "selected-matters-audit.json"})
            lines = (d / "out" / "selected-questions.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            for line in lines:
                rec = json.loads(line)
                self.assertIn("ශ්‍රී", rec["background_original"])
            self.assertIn("ශ්‍රී", (d / "out" / "selected-matters.jsonl").read_text(encoding="utf-8"))
            # Source files untouched.
            self.assertEqual((d / "q.jsonl").read_text(encoding="utf-8").count("\n"), 2)

    def test_cli_returns_nonzero_on_count_mismatch(self):
        import tempfile
        qs = [question("A", shared=SHARED)]
        cs = [classification("A")]
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "q.jsonl").write_text(json.dumps(qs[0]) + "\n", encoding="utf-8")
            (d / "c.jsonl").write_text(json.dumps(cs[0]) + "\n", encoding="utf-8")
            argv = ["--questions", str(d / "q.jsonl"), "--classifications", str(d / "c.jsonl"),
                    "--out-dir", str(d / "out"), "--expected-questions", "5", "--expected-matters", "1"]
            self.assertEqual(bsm.main(argv), 2)
            audit = json.loads((d / "out" / "selected-matters-audit.json").read_text(encoding="utf-8"))
            self.assertFalse(audit["validation_passed"])
            self.assertFalse((d / "out" / "selected-matters.jsonl").exists())


@unittest.skipUnless(bsm.DEFAULT_QUESTIONS.exists() and bsm.DEFAULT_CLASSIFICATIONS.exists(),
                     "atomic corpus not present")
class RealCorpusTests(unittest.TestCase):
    def test_current_corpus_yields_84_questions_in_44_matters(self):
        qs = bsm.read_jsonl(bsm.DEFAULT_QUESTIONS)
        cs = bsm.read_jsonl(bsm.DEFAULT_CLASSIFICATIONS)
        matters, flat, audit = bsm.build(qs, cs, 84, 44)
        self.assertEqual(len(matters), 44)
        self.assertEqual(len(flat), 84)
        self.assertTrue(audit["validation_passed"])
        self.assertEqual(audit["quarantined_records"], [])
        by_q = {q["atomic_id"]: q for q in qs}
        by_c = {c["atomic_id"]: c for c in cs}
        for f in flat:
            self.assertTrue(f["background_normalized"])
            self.assertTrue(f["question_normalized"])
            self.assertEqual(f["question_original"], by_q[f["atomic_id"]]["question"])
            self.assertEqual(f["source_quote"], by_q[f["atomic_id"]]["source_quote"])
            self.assertTrue(bsm.is_selected(by_c[f["atomic_id"]]))
        self.assertEqual(len({f["atomic_id"] for f in flat}), 84)
        self.assertEqual({f["benchmark_matter_id"] for f in flat},
                         {m["benchmark_matter_id"] for m in matters})

    def test_cli_runs_against_the_corpus(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "build_selected_matters.py"), "--out-dir", d],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            n = sum(1 for _ in open(Path(d) / "selected-questions.jsonl", encoding="utf-8"))
            self.assertEqual(n, 84)


if __name__ == "__main__":
    unittest.main()
