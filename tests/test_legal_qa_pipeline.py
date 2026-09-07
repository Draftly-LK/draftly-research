"""Tests for scripts/legal-qa-pipeline/.

Everything runs on a small synthetic matter written to a temporary directory.
The fixture is a complete, internally consistent bundle (issue map, verified
authorities, legal map, predicates, document specs, ledger, two rendered
documents) built around the real M001 source record, with placeholder
non-legal text everywhere a legal statement would go. Each test breaks one
rule and checks that the right validator refuses it. Nothing here asserts
anything about the law.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "scripts" / "legal-qa-pipeline"
sys.path.insert(0, str(SCRIPT_DIR))

import build_review_packets as BRP  # noqa: E402
import lqa_common as C  # noqa: E402
import run_legal_qa_pipeline as RUN  # noqa: E402
import validate_document_bundles as VDB  # noqa: E402
import validate_legal_maps as VLM  # noqa: E402
import validate_matter_ledgers as VML  # noqa: E402

SOURCE_DIR = ROOT / "data" / "evaluvation" / "parsed-pastpapers" / "benchmark"
MATTER = "M001"
RUN_ID = "test-run"
NOW = "2026-09-05T00:00:00Z"
MARKER = C.SYNTHETIC_MARKER
AUTH_TEXT = "Fixture provision text one. It carries no legal meaning and exists only for tests.\nSecond line of fixture text.\n"
EXCERPT = "Fixture provision text one. It carries no legal meaning and exists only for tests."


def real_m001_record() -> dict:
    for row in C.read_jsonl(SOURCE_DIR / "selected-matters.jsonl"):
        if row["benchmark_matter_id"] == MATTER:
            return row
    raise AssertionError("M001 not found in selected-matters.jsonl")


def real_m001_flat() -> list[dict]:
    return [q for q in C.read_jsonl(SOURCE_DIR / "selected-questions.jsonl") if q["benchmark_matter_id"] == MATTER]


def verification(source_path: str, source_hash: str | None, excerpt: str = EXCERPT, version: str = "current_text_applicable",
                 necessity: str = "indispensable") -> dict:
    return {
        "verifying_agent": "fixture-verifier",
        "source_tier": 2,
        "source_path": source_path,
        "source_hash": source_hash,
        "locator": {"page": 1, "node_id": None, "paragraph": None, "line_range": "1-1", "json_pointer": None},
        "exact_excerpt": excerpt,
        "excerpt_is_verbatim_substring_of_source": True,
        "effective_from": "1900-01-01",
        "effective_to": None,
        "applicable_version_for_matter_date": version,
        "amendment_chain": [],
        "source_status": "fixture",
        "structural_verification_status": None,
        "legal_verification_status": None,
        "supports_claimed_proposition": "yes",
        "holding_classification": None,
        "case_still_applicable": None,
        "necessity_assessed": necessity,
        "omitted_authority_needed": None,
        "notes": "fixture only",
    }


def authority(aid: str, qids: list[str], status: str, verif: dict | None, necessity: str = "indispensable") -> dict:
    return {
        "authority_id": aid,
        "authority_type": "statute_provision",
        "title": "Fixture Ordinance",
        "enactment_number": "Fixture No. 1 of 1900",
        "section": "1",
        "subsection": None,
        "case_citation": None,
        "court": None,
        "decision_date": None,
        "candidate_source_paths": ["fixtures/auth-001.txt"],
        "retrieval_methods": ["manual_corpus_browse"],
        "retrieval_scores": {"bm25": 1.0},
        "candidate_reason": "fixture",
        "proposed_by_agent": "fixture-research",
        "benchmark_question_ids": qids,
        "necessity_claimed": necessity,
        "verification_status": status,
        "verification": verif,
    }


class Fixture:
    """A complete matter directory under a temporary run directory."""

    def __init__(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="lqa-test-"))
        self.root = self.tmp / "repo"
        self.runs_dir = self.root / "runs"
        self.run_dir = self.runs_dir / RUN_ID
        self.matter_dir = self.run_dir / "pilot" / MATTER
        (self.matter_dir / "synthetic-documents").mkdir(parents=True)
        (self.root / "fixtures").mkdir(parents=True)
        self.auth_file = self.root / "fixtures" / "auth-001.txt"
        self.auth_file.write_text(AUTH_TEXT, encoding="utf-8")
        self.auth_hash = C.sha256_file(self.auth_file)
        self.record = real_m001_record()
        self.flat = real_m001_flat()
        self.qids = [q["benchmark_question_id"] for q in self.record["questions"]]
        self.build()

    def cleanup(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- artifacts ---------------------------------------------------------

    def build(self) -> None:
        self.source = RUN.build_source_record(
            self.record, self.flat, "0" * 64, "1" * 64, RUN_ID, "selected-matters.jsonl", "selected-questions.jsonl"
        )
        self.issue_map = {
            "benchmark_matter_id": MATTER, "run_id": RUN_ID, "produced_by_agent": "fixture",
            "matter_summary": "Fixture summary with no legal conclusion.",
            "parties": [{"party_ref": "PTY01", "name_as_in_source": "Gamini Perera", "role": "fixture role", "legal_capacity": "fixture"}],
            "relevant_dates": [{"date_as_in_source": "12th June 1990", "iso_date": "1990-06-12", "event": "fixture event", "legal_significance": "fixture"}],
            "questions": [{
                "benchmark_question_id": q, "primary_issue": "Fixture primary issue text", "secondary_issues": [],
                "legal_domain": "other", "required_legal_conclusion": "fixture", "answer_format": "explanation",
                "relevant_transaction_or_event": "fixture", "relevant_dates": ["1990-06-12"], "authority_type_expected": "statute",
                "answer_depends_on_unresolved_facts": False, "unresolved_fact_dependencies": [],
                "research_queries": [{"query": "fixture query", "corpus": "statutes", "named_in_question": False}],
                "status": "issue_mapped",
            } for q in self.qids],
        }
        a1 = authority("AUTH-M001-001", self.qids, "verified", verification("fixtures/auth-001.txt", self.auth_hash))
        a2 = authority("AUTH-M001-002", self.qids, "verified",
                       verification("https://example.invalid/fixture", None, "Fixture web excerpt two.", necessity="supporting"),
                       necessity="supporting")
        self.candidates = {
            "benchmark_matter_id": MATTER, "run_id": RUN_ID, "stage": "authorities_candidate", "produced_by_agent": "fixture",
            "matter_reference_date": "1995", "matter_reference_date_basis": "fixture",
            "authorities": [dict(a, verification_status="candidate", verification=None) for a in (a1, a2)],
            "negative_retrieval": [],
        }
        self.verified = dict(self.candidates, stage="authorities_verified", authorities=[a1, a2])
        self.legal_map = {
            "benchmark_matter_id": MATTER, "run_id": RUN_ID, "produced_by_agent": "fixture", "status": "authorities_verified",
            "questions": [self.question_map(q) for q in self.qids],
        }
        self.predicates = {
            "benchmark_matter_id": MATTER, "run_id": RUN_ID, "produced_by_agent": "fixture",
            "predicates": [
                {"predicate_id": "PR-M001-001", "benchmark_question_ids": self.qids, "predicate": "fixture_predicate_one",
                 "description": "fixture", "expected_value": True, "predicate_type": "fact", "necessity": "indispensable",
                 "polarity": "positive", "authority_ids": ["AUTH-M001-001"], "supporting_fact_ids": ["FACT-M001-001"],
                 "evidence_document_ids": ["DOC-M001-001"], "status": "observed", "counterfactual_effect": "fixture counterfactual",
                 "potentially_decisive": True, "notes": None},
                {"predicate_id": "PR-M001-002", "benchmark_question_ids": self.qids[:1], "predicate": "fixture_predicate_two",
                 "description": "fixture", "expected_value": None, "predicate_type": "legal_status", "necessity": "supporting",
                 "polarity": "negative", "authority_ids": [], "supporting_fact_ids": [], "evidence_document_ids": [],
                 "status": "unresolved", "counterfactual_effect": "fixture", "potentially_decisive": False, "notes": None},
            ],
        }
        self.ledger = {
            "benchmark_matter_id": MATTER, "run_id": RUN_ID, "produced_by_agent": "fixture",
            "source_facts": [
                self.fact("FACT-M001-001", "parties.PTY01.name", "Gamini Perera", "past_paper", "Gamini Perera was allotted Lot A", "decisive", ["PR-M001-001"]),
                self.fact("FACT-M001-002", "instruments.INS01.number", "515", "past_paper", "Deed of Gift No. 515", "supporting"),
                self.fact("FACT-M001-003", "instruments.INS01.folio", "F-77", "synthetic_neutral", None, "neutral"),
                self.fact("FACT-M001-004", "events.EVT01.date", "12th June 1990", "past_paper", "Gamini Perera died on 12th June 1990", "supporting", iso="1990-06-12"),
                self.fact("FACT-M001-005", "events.EVT02.date", "25th February 1991", "past_paper",
                          "Deed of revocation of life interest bearing No. 525 dated 25th February 1991", "supporting", iso="1991-02-25"),
            ],
            "parties": [{"id": "PTY01", "name": "Gamini Perera", "role": "fixture", "capacity": "fixture", "is_real_person": False,
                         "identity_number_policy": "none_or_obviously_synthetic", "fact_ids": ["FACT-M001-001"]}],
            "properties": [],
            "instruments": [{"id": "INS01", "instrument_type": "deed_of_gift", "number": "515", "date": None, "date_iso": None,
                             "attesting_notary": None, "parties": ["PTY01"], "folio": "F-77", "fact_ids": ["FACT-M001-002", "FACT-M001-003"]}],
            "events": [
                {"id": "EVT01", "event_type": "death", "date": "12th June 1990", "date_iso": "1990-06-12", "sequence": 1, "parties": ["PTY01"], "instrument_id": None, "fact_ids": ["FACT-M001-004"]},
                {"id": "EVT02", "event_type": "revocation", "date": "25th February 1991", "date_iso": "1991-02-25", "sequence": 2, "parties": [], "instrument_id": None, "fact_ids": ["FACT-M001-005"]},
            ],
            "relationships": [], "financial_values": [], "registrations": [], "notices": [], "court_events": [], "fact_conflicts": [],
            "synthetic_additions": [{"fact_id": "FACT-M001-003", "reason": "neutral filing reference", "could_affect": [], "legal_review_required": False}],
            "questions": self.qids,
            "predicates": ["PR-M001-001", "PR-M001-002"],
        }
        self.specs = {
            "benchmark_matter_id": MATTER, "run_id": RUN_ID, "produced_by_agent": "fixture",
            "documents": [
                self.doc_spec("DOC-M001-001", "deed_of_gift", "indispensable", ["explicit"], ["PR-M001-001"], "deed_515.txt", [
                    self.particular("FLD-M001-001", "donor_name", "FACT-M001-001", "decisive", "past_paper", ["PR-M001-001"]),
                    self.particular("FLD-M001-002", "deed_number", "ledger.instruments.INS01.number", "supporting", "past_paper"),
                    self.particular("FLD-M001-003", "folio", "FACT-M001-003", "neutral", "synthetic_neutral"),
                ]),
                self.doc_spec("DOC-M001-002", "receipt", "distractor", ["distractor"], [], "receipt_1991.txt", [
                    self.particular("FLD-M001-004", "receipt_date", "FACT-M001-005", "neutral", "past_paper"),
                    self.particular("FLD-M001-005", "payer_name", "FACT-M001-001", "neutral", "past_paper"),
                ], rationale="fixture distractor rationale"),
            ],
        }
        self.sdocs = {
            "DOC-M001-001": self.synthetic_doc("DOC-M001-001", "deed_of_gift", "deed_515.txt", [
                ("FLD-M001-001", "donor_name", "Gamini Perera", "FACT-M001-001"),
                ("FLD-M001-002", "deed_number", "515", "FACT-M001-002"),
                ("FLD-M001-003", "folio", "F-77", "FACT-M001-003"),
            ]),
            "DOC-M001-002": self.synthetic_doc("DOC-M001-002", "receipt", "receipt_1991.txt", [
                ("FLD-M001-004", "receipt_date", "25th February 1991", "FACT-M001-005"),
                ("FLD-M001-005", "payer_name", "Gamini Perera", "FACT-M001-001"),
            ]),
        }

    def question_map(self, q: str) -> dict:
        qq = C.question_number(q)
        return {
            "benchmark_question_id": q, "issues": ["fixture issue"],
            "indispensable_authority_ids": ["AUTH-M001-001"], "supporting_authority_ids": ["AUTH-M001-002"],
            "legal_hop_count": 1, "hop_count_basis": "fixture",
            "reasoning_chain": [{"step": 1, "text": "fixture step", "authority_ids": ["AUTH-M001-001"], "relies_on_scenario_fact_ids": ["FACT-M001-001"]}],
            "gold_answer_draft": {"issue": "fixture issue", "rule": "fixture rule", "application": "fixture application",
                                  "conclusion": "Fixture conclusion sentence that is deliberately long enough to be checked for leakage."},
            "answer_claims": [
                {"claim_id": f"CL-M001-Q{qq}-001", "claim_text": "fixture rule claim", "claim_type": "rule",
                 "supporting_authority_ids": ["AUTH-M001-001"],
                 "supporting_excerpts": [{"authority_id": "AUTH-M001-001", "excerpt": "Fixture provision   text one.", "locator": None}],
                 "support_strength": "direct", "scenario_fact_basis": None, "verification_status": "verified"},
                {"claim_id": f"CL-M001-Q{qq}-002", "claim_text": "fixture scenario claim", "claim_type": "scenario_inference",
                 "supporting_authority_ids": [], "supporting_excerpts": [], "support_strength": "scenario_fact",
                 "scenario_fact_basis": "FACT-M001-001", "verification_status": "verified"},
            ],
            "confidence": 0.5, "status": "authorities_verified", "blocking_reason": None,
        }

    @staticmethod
    def fact(fid, field, value, origin, quote, relevance, preds=None, iso=None) -> dict:
        return {"fact_id": fid, "field": field, "value": value, "value_iso": iso, "origin": origin,
                "source_atomic_ids": ["P01-Q01-P01"] if origin == "past_paper" else [], "source_quote": quote,
                "legal_relevance": relevance, "supports_predicate_ids": preds or [], "confidence": 0.9, "notes": None}

    @staticmethod
    def particular(fid, name, source, relevance, origin, preds=None) -> dict:
        return {"field_id": fid, "field_name": name, "data_type": "string", "value_source": source, "required": True,
                "legal_relevance": relevance, "supports_predicate_ids": preds or [], "validation_rules": [],
                "source_origin": origin, "generation_allowed": True, "decisive_generation_justification": None}

    def doc_spec(self, did, dtype, necessity, roles, preds, filename, particulars, rationale=None) -> dict:
        return {"document_id": did, "benchmark_matter_id": MATTER, "document_type": dtype, "document_role": roles,
                "required_for_question_ids": self.qids, "supports_predicate_ids": preds, "necessity": necessity,
                "inclusion_reason": "fixture", "issuer_or_executor": "fixture notary", "document_date_fact_id": None,
                "template_source": None, "generation_status": "rendered", "synthetic_label_required": True,
                "public_filename": filename, "distractor_rationale": rationale, "particulars": particulars}

    @staticmethod
    def synthetic_doc(did, dtype, filename, fields) -> dict:
        lines = [MARKER, f"Fixture {dtype}"] + [f"{name}: {value}" for _, name, value, _ in fields]
        text = "\n".join(lines) + "\n"
        return {"document_id": did, "benchmark_matter_id": MATTER, "document_type": dtype, "synthetic_marker": MARKER,
                "template_id": f"fixture-{dtype}", "generator_version": "test-0",
                "fields": [{"field_id": f, "field_name": n, "value": v, "fact_id": fid} for f, n, v, fid in fields],
                "rendered_text": text, "expected_extracted_fields": {n: v for _, n, v, _ in fields},
                "document_hash": C.prefixed_sha256(C.sha256_text(text)), "public_filename": filename,
                "contains_statute_citation": False, "signature_policy": "placeholder_only_no_seal_no_signature_image"}

    # -- writing -------------------------------------------------------------

    def write(self) -> Path:
        m = self.matter_dir
        C.write_json(m / "source.json", self.source)
        C.write_json(m / "issue-map.json", self.issue_map)
        C.write_json(m / "candidate-authorities.json", self.candidates)
        C.write_json(m / "verified-authorities.json", self.verified)
        C.write_json(m / "legal-map.json", self.legal_map)
        C.write_json(m / "predicates.json", self.predicates)
        C.write_json(m / "document-specs.json", self.specs)
        C.write_json(m / "matter-ledger.json", self.ledger)
        for f in (m / "synthetic-documents").glob("*"):
            f.unlink()
        for did, doc in self.sdocs.items():
            C.write_json(m / "synthetic-documents" / f"{did}.json", doc)
        return m

    def rehash(self, did: str) -> None:
        doc = self.sdocs[did]
        doc["document_hash"] = C.prefixed_sha256(C.sha256_text(doc["rendered_text"]))

    # -- a run directory with a manifest ------------------------------------

    def init_run(self, pilots: str = MATTER) -> dict:
        source_dir = self.tmp / "source"
        source_dir.mkdir(exist_ok=True)
        shutil.copyfile(SOURCE_DIR / "selected-matters.jsonl", source_dir / "selected-matters.jsonl")
        shutil.copyfile(SOURCE_DIR / "selected-questions.jsonl", source_dir / "selected-questions.jsonl")
        code = RUN.main([
            "init", "--run-id", RUN_ID, "--runs-dir", str(self.runs_dir), "--root", str(self.root),
            "--source-dir", str(source_dir), "--pilot", pilots, "--reason", f"{MATTER}=fixture reason", "--now", NOW,
        ])
        assert code == 0, code
        return C.read_json(self.run_dir / "manifest.json")

    def cli(self, *argv: str) -> int:
        return RUN.main([argv[0], "--run-id", RUN_ID, "--runs-dir", str(self.runs_dir), "--root", str(self.root), "--now", NOW, *argv[1:]])


class LegalQaPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    # -- helpers ---------------------------------------------------------------

    def legal(self) -> dict:
        return VLM.validate_matter(self.fx.write(), self.fx.root)

    def ledger(self) -> dict:
        return VML.validate_matter(self.fx.write())

    def bundle(self) -> dict:
        return VDB.validate_matter(self.fx.write())

    def assertErrorMatching(self, rep: dict, needle: str) -> None:
        self.assertFalse(rep["passed"], rep)
        self.assertTrue(any(needle in e for e in rep["errors"]), f"{needle!r} not in {rep['errors']}")

    # -- schemas ---------------------------------------------------------------

    def test_happy_path_passes_every_validator(self) -> None:
        for rep in (self.legal(), self.ledger(), self.bundle()):
            self.assertTrue(rep["passed"], rep["errors"])
            self.assertEqual(rep["status"], "unverified")

    def test_schema_validation_pass_and_fail_per_schema(self) -> None:
        good = {
            "issue-map": self.fx.issue_map, "authority": self.fx.verified, "legal-map": self.fx.legal_map,
            "predicate": self.fx.predicates, "document-spec": self.fx.specs, "matter-ledger": self.fx.ledger,
            "synthetic-document": self.fx.sdocs["DOC-M001-001"],
            "lawyer-review": BRP.build_packet(self.fx.write(), self.fx.root)[1],
        }
        for name, obj in good.items():
            self.assertEqual(C.validate_against_schema(obj, name), [], name)
            broken = copy.deepcopy(obj)
            broken["benchmark_matter_id" if "benchmark_matter_id" in broken else "matter_id"] = "not-a-matter"
            self.assertTrue(C.validate_against_schema(broken, name), name)
        manifest = self.fx.init_run()
        self.assertEqual(C.validate_against_schema(manifest, "run-manifest"), [])
        self.assertTrue(C.validate_against_schema({"run_id": "x"}, "run-manifest"))
        self.assertTrue(C.validate_against_schema({}, "gold-question"))

    def test_candidate_authority_must_have_null_verification(self) -> None:
        bad = copy.deepcopy(self.fx.candidates)
        bad["authorities"][0]["verification"] = verification("fixtures/auth-001.txt", None)
        self.assertTrue(C.validate_against_schema(bad, "authority"))

    # -- ids and state machine -------------------------------------------------

    def test_stable_ids(self) -> None:
        ids = C.StableIds(MATTER)
        self.assertEqual([ids.next_authority(), ids.next_authority()], ["AUTH-M001-001", "AUTH-M001-002"])
        self.assertEqual(ids.next_claim("M001-Q02"), "CL-M001-Q02-001")
        self.assertEqual(ids.next_claim("M001-Q01"), "CL-M001-Q01-001")
        self.assertEqual(ids.next_claim("M001-Q02"), "CL-M001-Q02-002")
        self.assertEqual(ids.next_predicate(), "PR-M001-001")
        self.assertEqual(ids.next_document(), "DOC-M001-001")
        self.assertEqual(ids.next_field(), "FLD-M001-001")
        self.assertEqual(ids.next_fact(), "FACT-M001-001")
        self.assertEqual(C.id_sequence("FACT", MATTER, 2), ["FACT-M001-001", "FACT-M001-002"])
        self.assertEqual(C.id_sequence("CL", MATTER, 1, "M001-Q03"), ["CL-M001-Q03-001"])
        self.assertEqual(C.id_sequence("AUTH", MATTER, 3), C.id_sequence("AUTH", MATTER, 3))
        with self.assertRaises(ValueError):
            C.authority_id("M1", 1)

    def test_state_machine_cannot_skip_or_reach_lawyer_validated(self) -> None:
        self.assertTrue(C.can_advance("selected", "issue_mapped"))
        self.assertFalse(C.can_advance("selected", "authorities_candidate"))
        self.assertFalse(C.can_advance("issue_mapped", "issue_mapped"))
        self.assertFalse(C.can_advance("lawyer_review_pending", "lawyer_validated"))
        history = [{"state": "selected"}, {"state": "issue_mapped"}, {"state": "blocked_missing_authority"}]
        self.assertTrue(C.can_advance("blocked_missing_authority", "authorities_candidate", history))
        self.assertFalse(C.can_advance("blocked_missing_authority", "authorities_verified", history))

    def test_cli_validate_refuses_skips_and_lawyer_validated(self) -> None:
        self.fx.init_run()
        self.fx.write()
        self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", "lawyer_validated"), RUN.EXIT_HUMAN_ONLY)
        self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", "authorities_verified"), RUN.EXIT_FAIL)
        manifest = C.read_json(self.fx.run_dir / "manifest.json")
        self.assertEqual(RUN.Run(RUN_ID, self.fx.runs_dir).matter_entry(manifest, MATTER)["state"], "selected")
        self.assertEqual(manifest["events"][-1]["event"], "advance_refused")

    def test_cli_walks_the_state_machine_to_review_pending(self) -> None:
        self.fx.init_run()
        self.fx.write()
        for stage in C.ORDERED_STATES[1:8]:
            self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", stage), 0, stage)
        self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", "lawyer_review_pending"), RUN.EXIT_FAIL)
        self.assertEqual(self.fx.cli("audit", "--matter", MATTER), 0)
        self.assertEqual(self.fx.cli("packet", "--matter", MATTER, "--no-lint"), 0)
        self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", "lawyer_review_pending"), 0)
        manifest = C.read_json(self.fx.run_dir / "manifest.json")
        entry = RUN.Run(RUN_ID, self.fx.runs_dir).matter_entry(manifest, MATTER)
        self.assertEqual(entry["state"], "lawyer_review_pending")
        self.assertEqual([h["state"] for h in entry["state_history"]], C.ORDERED_STATES[:9])
        self.assertTrue(all(h["validated_by"].endswith(".py") for h in entry["state_history"]))
        self.assertEqual(C.validate_against_schema(manifest, "run-manifest"), [])
        self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", "lawyer_validated"), RUN.EXIT_HUMAN_ONLY)

    def test_block_and_event(self) -> None:
        self.fx.init_run()
        self.assertEqual(self.fx.cli("block", "--matter", MATTER, "--state", "blocked_missing_authority", "--detail", "fixture"), 0)
        self.assertEqual(self.fx.cli("event", "--matter", MATTER, "--event", "retry", "--detail", "fixture retry"), 0)
        manifest = C.read_json(self.fx.run_dir / "manifest.json")
        entry = RUN.Run(RUN_ID, self.fx.runs_dir).matter_entry(manifest, MATTER)
        self.assertEqual(entry["state"], "blocked_missing_authority")
        self.assertEqual([e["event"] for e in manifest["events"]], ["init", "blocked", "retry"])
        self.assertNotEqual(self.fx.cli("block", "--matter", MATTER, "--state", "issue_mapped", "--detail", "x"), 0)

    # -- source provenance -----------------------------------------------------

    def test_init_source_json_matches_selected_record(self) -> None:
        manifest = self.fx.init_run()
        self.assertEqual(len(manifest["matters"]), 44)
        self.assertEqual(manifest["source_dataset"]["question_count"], 84)
        entry = RUN.Run(RUN_ID, self.fx.runs_dir).matter_entry(manifest, MATTER)
        self.assertEqual((entry["role"], entry["state"], entry["selection_reason"]), ("pilot", "selected", "fixture reason"))
        self.assertTrue(all(m["state"] == "selected" for m in manifest["matters"]))
        self.assertEqual(sum(m["role"] == "pilot" for m in manifest["matters"]), 1)
        source = C.read_json(self.fx.matter_dir / "source.json")
        record = real_m001_record()
        for key, value in record.items():
            self.assertEqual(source[key], value, key)
        self.assertEqual(len(source["flat_questions"]), len(record["questions"]))
        self.assertEqual(source["source_sha256"]["selected_matters_jsonl"], manifest["source_dataset"]["selected_matters_sha256"])
        self.assertEqual(source["source_sha256"]["matter_record"], C.sha256_text(C.canonical_json(record)))
        self.assertEqual(set(manifest["schema_versions"]), set(C.SCHEMA_FILES))
        self.assertTrue((self.fx.run_dir / "schemas" / "authority.schema.json").exists())

    def test_past_paper_fact_quote_must_be_substring(self) -> None:
        self.assertTrue(self.ledger()["passed"])
        self.fx.ledger["source_facts"][0]["source_quote"] = "Words that are not in the past paper at all"
        self.assertErrorMatching(self.ledger(), "source_quote is not found")

    # -- authorities -----------------------------------------------------------

    def test_authority_locator_missing_file_and_wrong_hash(self) -> None:
        self.fx.verified["authorities"][0]["verification"]["source_path"] = "fixtures/nope.txt"
        self.assertErrorMatching(self.legal(), "does not exist")
        self.fx.verified["authorities"][0]["verification"]["source_path"] = "fixtures/auth-001.txt"
        self.fx.verified["authorities"][0]["verification"]["source_hash"] = "0" * 64
        self.assertErrorMatching(self.legal(), "source_hash mismatch")
        self.fx.verified["authorities"][0]["verification"]["source_hash"] = "sha256:" + self.fx.auth_hash
        self.assertTrue(self.legal()["passed"])
        self.fx.verified["authorities"][0]["verification"]["exact_excerpt"] = "Text that is not in the file"
        self.assertErrorMatching(self.legal(), "exact_excerpt is not a whitespace-normalised substring")

    def test_indispensable_authority_must_be_verified(self) -> None:
        for status in ("partially_verified", "unresolved", "rejected"):
            self.fx.verified["authorities"][0]["verification_status"] = status
            self.assertErrorMatching(self.legal(), "matter cannot advance")

    def test_temporal_applicability_warning_is_surfaced_not_fatal(self) -> None:
        self.fx.verified["authorities"][0]["verification"]["applicable_version_for_matter_date"] = "history_unknown"
        rep = self.legal()
        self.assertTrue(rep["passed"], rep["errors"])
        self.assertEqual(len(rep["temporal_warnings"]), 1)
        self.assertIn("history_unknown", rep["temporal_warnings"][0])
        self.assertIn(rep["temporal_warnings"][0], rep["warnings"])
        self.fx.verified["authorities"][1]["verification"]["applicable_version_for_matter_date"] = "current_text_superseded_since_event"
        self.assertEqual(len(self.legal()["temporal_warnings"]), 1, "supporting authorities do not trigger temporal warnings")

    def test_claim_to_authority_completeness(self) -> None:
        q = self.fx.legal_map["questions"][0]
        q["answer_claims"][0]["supporting_excerpts"][0]["excerpt"] = "An excerpt the verifier never saw"
        self.assertErrorMatching(self.legal(), "no supporting excerpt matches")
        q["answer_claims"][0]["supporting_excerpts"][0]["excerpt"] = EXCERPT + " and then some extra words"
        self.assertTrue(self.legal()["passed"], "verifier excerpt inside the claim excerpt is accepted")
        q["supporting_authority_ids"] = ["AUTH-M001-099"]
        self.assertErrorMatching(self.legal(), "not in verified-authorities.json")

    def test_every_source_question_must_be_mapped_and_hop_count_positive(self) -> None:
        dropped = self.fx.legal_map["questions"].pop()
        self.assertErrorMatching(self.legal(), "is not mapped")
        self.fx.legal_map["questions"].append(dropped)
        self.fx.legal_map["questions"][0]["legal_hop_count"] = 0
        self.assertErrorMatching(self.legal(), "legal_hop_count must be >= 1")

    def test_stage_validators_for_issue_map_and_candidates(self) -> None:
        m = self.fx.write()
        self.assertTrue(VLM.validate_issue_map(m)["passed"])
        self.assertTrue(VLM.validate_candidate_authorities(m)["passed"])
        self.fx.issue_map["questions"].pop()
        self.fx.candidates["authorities"][0]["benchmark_question_ids"] = ["M001-Q99"]
        m = self.fx.write()
        self.assertFalse(VLM.validate_issue_map(m)["passed"])
        self.assertErrorMatching(VLM.validate_candidate_authorities(m), "unknown question")

    # -- predicates and documents -----------------------------------------------

    def test_predicate_to_authority_completeness(self) -> None:
        m = self.fx.write()
        self.assertTrue(RUN.validate_predicates(m, None)["passed"])
        self.fx.predicates["predicates"][0]["authority_ids"] = ["AUTH-M001-042"]
        self.assertErrorMatching(RUN.validate_predicates(self.fx.write(), None), "not in verified-authorities.json")
        self.fx.predicates["predicates"][0]["authority_ids"] = []
        self.assertErrorMatching(RUN.validate_predicates(self.fx.write(), None), "[predicate]")

    def test_predicate_to_document_completeness(self) -> None:
        self.fx.predicates["predicates"][0]["evidence_document_ids"] = ["DOC-M001-009"]
        rep = self.bundle()
        self.assertErrorMatching(rep, "no evidence document present")
        self.assertErrorMatching(RUN.validate_document_specs(self.fx.matter_dir, None), "no evidence document")
        self.fx.predicates["predicates"][0]["evidence_document_ids"] = ["DOC-M001-001"]
        self.fx.specs["documents"][0]["supports_predicate_ids"] = ["PR-M001-002"]
        self.assertErrorMatching(self.bundle(), "supports no indispensable predicate")

    def test_document_field_to_ledger_resolution(self) -> None:
        self.fx.specs["documents"][0]["particulars"][1]["value_source"] = "ledger.instruments.INS01.nonexistent"
        self.assertErrorMatching(self.bundle(), "has no attribute")
        self.fx.specs["documents"][0]["particulars"][1]["value_source"] = "ledger.instruments.INS01.number"
        self.fx.specs["documents"][0]["particulars"][0]["value_source"] = "FACT-M001-099"
        self.assertErrorMatching(self.bundle(), "not in ledger")
        self.fx.specs["documents"][0]["particulars"][0]["value_source"] = "FACT-M001-001"
        self.fx.sdocs["DOC-M001-001"]["fields"][0]["value"] = "Somebody Else"
        self.fx.rehash("DOC-M001-001")
        self.assertErrorMatching(self.bundle(), "!= ledger FACT-M001-001")

    def test_cross_document_consistency(self) -> None:
        doc = self.fx.sdocs["DOC-M001-002"]
        doc["fields"][1]["value"] = "Gamini  Perera"
        self.fx.rehash("DOC-M001-002")
        rep = self.bundle()
        self.assertErrorMatching(rep, "different values across documents")

    def test_chronological_consistency(self) -> None:
        self.fx.ledger["events"][1]["date_iso"] = "1989"
        self.assertErrorMatching(self.ledger(), "is dated before")
        self.fx.ledger["events"][1]["date_iso"] = "1990"
        self.assertTrue(self.ledger()["passed"], "year-only date compatible with a full date in the same year")
        self.assertTrue(C.dates_non_decreasing("1990", "1990-06-12"))
        self.assertFalse(C.dates_non_decreasing("1990-06-12", "1990-05"))

    def test_no_unsupported_decisive_synthetic_facts(self) -> None:
        self.fx.ledger["source_facts"][2]["origin"] = "synthetic_decisive"
        self.fx.ledger["source_facts"][2]["legal_relevance"] = "decisive"
        self.fx.ledger["synthetic_additions"][0]["could_affect"] = ["ownership"]
        self.assertErrorMatching(self.ledger(), "requires legal_review_required: true")
        self.fx.ledger["synthetic_additions"][0]["legal_review_required"] = True
        self.assertTrue(self.ledger()["passed"])
        self.fx.ledger["source_facts"][2]["origin"] = "synthetic_neutral"
        self.fx.ledger["source_facts"][2]["legal_relevance"] = "neutral"
        self.assertErrorMatching(self.ledger(), "synthetic_neutral fact claims could_affect")
        self.fx.ledger["synthetic_additions"] = []
        self.assertErrorMatching(self.ledger(), "not listed in synthetic_additions")

    def test_no_real_pii(self) -> None:
        self.fx.ledger["parties"][0]["name"] = "Gamini Perera NIC 851234567V"
        self.assertErrorMatching(self.ledger(), "nic_old:851234567V")
        self.fx.ledger["parties"][0]["name"] = "Gamini Perera"
        self.fx.ledger["instruments"][0]["number"] = "0771234567"
        self.assertErrorMatching(self.ledger(), "phone:0771234567")
        self.fx.ledger["instruments"][0]["number"] = "515"
        self.fx.ledger["parties"][0]["is_real_person"] = True
        self.assertErrorMatching(self.ledger(), "is_real_person")
        self.fx.ledger["parties"][0]["is_real_person"] = False
        self.fx.ledger["predicates"] = ["PR-M001-077"]
        self.assertErrorMatching(self.ledger(), "not in predicates.json")

    def test_synthetic_watermark_and_hash(self) -> None:
        doc = self.fx.sdocs["DOC-M001-001"]
        doc["rendered_text"] = doc["rendered_text"].replace(MARKER, "no marker here")
        self.fx.rehash("DOC-M001-001")
        self.assertErrorMatching(self.bundle(), "synthetic marker")
        self.fx.build()
        self.fx.sdocs["DOC-M001-001"]["document_hash"] = "sha256:" + "0" * 64
        self.assertErrorMatching(self.bundle(), "document_hash")

    def test_no_gold_answer_or_private_id_leakage(self) -> None:
        doc = self.fx.sdocs["DOC-M001-001"]
        conclusion = self.fx.legal_map["questions"][0]["gold_answer_draft"]["conclusion"]
        doc["rendered_text"] += conclusion + "\n"
        self.fx.rehash("DOC-M001-001")
        self.assertErrorMatching(self.bundle(), "gold conclusion sentence appears verbatim in DOC-M001-001")
        self.fx.build()
        self.fx.sdocs["DOC-M001-001"]["rendered_text"] += "see AUTH-M001-001 and PR-M001-001\n"
        self.fx.rehash("DOC-M001-001")
        self.assertErrorMatching(self.bundle(), "leaks private id AUTH-M001-001")
        self.fx.build()
        self.fx.specs["documents"][1]["public_filename"] = "distractor_receipt.txt"
        self.fx.sdocs["DOC-M001-002"]["public_filename"] = "distractor_receipt.txt"
        self.assertErrorMatching(self.bundle(), "leaks a label word")
        self.fx.build()
        self.fx.specs["documents"][1]["public_filename"] = "deed_515.txt"
        self.fx.sdocs["DOC-M001-002"]["public_filename"] = "deed_515.txt"
        self.assertErrorMatching(self.bundle(), "is also used by")

    # -- packets, render, merge ---------------------------------------------------

    def test_review_packet_is_deterministic_blank_and_lint_shaped(self) -> None:
        self.fx.init_run()
        m = self.fx.write()
        first = BRP.write_packet(m, self.fx.root, self.fx.run_dir, lint=False)
        packet_a = (m / BRP.PACKET_NAME).read_bytes()
        approval_a = (m / BRP.APPROVAL_NAME).read_bytes()
        BRP.write_packet(m, self.fx.root, self.fx.run_dir, lint=False)
        self.assertEqual(packet_a, (m / BRP.PACKET_NAME).read_bytes())
        self.assertEqual(approval_a, (m / BRP.APPROVAL_NAME).read_bytes())
        self.assertTrue(first["passed"])
        copy_dir = self.fx.run_dir / "review-packets" / MATTER
        self.assertEqual(packet_a, (copy_dir / BRP.PACKET_NAME).read_bytes())
        approval = json.loads(approval_a)
        self.assertEqual(C.validate_against_schema(approval, "lawyer-review"), [])
        self.assertIsNone(approval["reviewer_id"])
        self.assertEqual(approval["overall_status"], "pending")
        self.assertFalse(any(v is True for v in approval.values()))
        text = packet_a.decode("utf-8")
        self.assertTrue(text.startswith("# Lawyer review packet: M001\n\n"))
        self.assertIn(EXCERPT, text)
        self.assertIn("fixtures/auth-001.txt", text)
        self.assertIn("CL-M001-Q01-001", text)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#"):
                self.assertTrue(i == 0 or lines[i - 1] == "", f"heading without blank line before: {line}")
                self.assertEqual(lines[i + 1], "", f"heading without blank line after: {line}")
            self.assertFalse(line.endswith(" "), f"trailing space: {line!r}")
            self.assertFalse(line.startswith("<"), f"inline HTML: {line!r}")
        self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))
        # A human-started approval copy is never overwritten by code.
        human = dict(approval, reviewer_id="lawyer-1", review_date="2026-09-06")
        C.write_json(copy_dir / BRP.APPROVAL_NAME, human)
        BRP.write_packet(m, self.fx.root, self.fx.run_dir, lint=False)
        self.assertEqual(C.read_json(copy_dir / BRP.APPROVAL_NAME)["reviewer_id"], "lawyer-1")

    def test_render_writes_txt_and_checks_hash(self) -> None:
        self.fx.init_run()
        self.fx.write()
        self.assertEqual(self.fx.cli("render", "--matter", MATTER), 0)
        txt = self.fx.matter_dir / "synthetic-documents" / "DOC-M001-001.txt"
        self.assertEqual(txt.read_text(encoding="utf-8"), self.fx.sdocs["DOC-M001-001"]["rendered_text"])
        first = txt.read_bytes()
        self.fx.cli("render", "--matter", MATTER)
        self.assertEqual(first, txt.read_bytes())
        self.fx.sdocs["DOC-M001-001"]["document_hash"] = "sha256:" + "1" * 64
        self.fx.write()
        self.assertEqual(self.fx.cli("render", "--matter", MATTER), RUN.EXIT_FAIL)

    def advance_to_review(self) -> None:
        self.fx.init_run()
        self.fx.write()
        for stage in C.ORDERED_STATES[1:8]:
            self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", stage), 0, stage)
        self.assertEqual(self.fx.cli("audit", "--matter", MATTER), 0)
        self.assertEqual(self.fx.cli("packet", "--matter", MATTER, "--no-lint"), 0)
        self.assertEqual(self.fx.cli("validate", "--matter", MATTER, "--stage", "lawyer_review_pending"), 0)

    def test_merge_groups_by_matter_and_separates_public_private(self) -> None:
        self.advance_to_review()
        self.assertEqual(self.fx.cli("merge"), 0)
        gold = C.read_jsonl(self.fx.run_dir / "private" / "gold" / "gold-questions.jsonl")
        public = C.read_jsonl(self.fx.run_dir / "public" / "input" / "questions.jsonl")
        self.assertEqual(len(gold), len(self.fx.qids))
        self.assertEqual(len(public), len(self.fx.qids))
        self.assertEqual({g["public_input"]["matter_group"] for g in gold}, {MATTER})
        self.assertEqual({p["matter_group"] for p in public}, {MATTER})
        for g in gold:
            self.assertEqual(C.validate_against_schema(g, "gold-question"), [])
            self.assertEqual(g["pipeline_state"], "lawyer_review_pending")
            self.assertEqual(g["lawyer_validation_status"], "pending")
            self.assertEqual(g["private_gold"]["authority_ids"], ["AUTH-M001-001", "AUTH-M001-002"])
            self.assertEqual(g["private_gold"]["indispensable_document_ids"], ["DOC-M001-001"])
            self.assertEqual(g["public_input"]["document_filenames"], ["deed_515.txt", "receipt_1991.txt"])
            flat = next(q for q in self.fx.flat if q["benchmark_question_id"] == g["benchmark_question_id"])
            self.assertEqual(g["private_gold"]["provenance"]["source_quote"], flat["source_quote"])
            self.assertEqual(g["private_gold"]["provenance"]["part_uid"], flat["provenance"]["part_uid"])
        public_text = (self.fx.run_dir / "public" / "input" / "questions.jsonl").read_text(encoding="utf-8")
        for forbidden in ("authority_id", "predicate", "gold_answer", "claim_id", "AUTH-M001", "private_gold"):
            self.assertNotIn(forbidden, public_text)
        self.assertEqual(sorted(p["benchmark_question_id"] for p in public), sorted(self.fx.qids))
        docs_dir = self.fx.run_dir / "public" / "input" / "documents" / MATTER
        self.assertEqual(sorted(p.name for p in docs_dir.iterdir()), ["deed_515.txt", "receipt_1991.txt"])
        self.assertEqual((docs_dir / "deed_515.txt").read_text(encoding="utf-8"), self.fx.sdocs["DOC-M001-001"]["rendered_text"])
        for name in ("run-manifest.json", "source-coverage.json", "unresolved-authorities.json", "pipeline-summary.json"):
            self.assertTrue((self.fx.run_dir / "audits" / name).exists(), name)
        summary = C.read_json(self.fx.run_dir / "audits" / "pipeline-summary.json")
        self.assertEqual(summary["state_counts"]["selected"], 43)
        self.assertEqual(summary["state_counts"]["lawyer_review_pending"], 1)
        self.assertEqual(summary["matters"][MATTER]["authorities"], 2)
        self.assertEqual(summary["merged_matters"], [MATTER])
        coverage = C.read_json(self.fx.run_dir / "audits" / "source-coverage.json")
        self.assertEqual(coverage["matters"][MATTER]["by_status"], {"verified": 2})

    def test_merge_is_deterministic_and_skips_unready_matters(self) -> None:
        self.advance_to_review()
        self.assertEqual(self.fx.cli("merge"), 0)
        gold_a = (self.fx.run_dir / "private" / "gold" / "gold-questions.jsonl").read_bytes()
        public_a = (self.fx.run_dir / "public" / "input" / "questions.jsonl").read_bytes()
        self.assertEqual(self.fx.cli("merge"), 0)
        self.assertEqual(gold_a, (self.fx.run_dir / "private" / "gold" / "gold-questions.jsonl").read_bytes())
        self.assertEqual(public_a, (self.fx.run_dir / "public" / "input" / "questions.jsonl").read_bytes())
        self.assertEqual(self.fx.cli("block", "--matter", MATTER, "--state", "needs_legal_review", "--detail", "fixture"), 0)
        self.assertEqual(self.fx.cli("merge"), 0)
        self.assertEqual(C.read_jsonl(self.fx.run_dir / "private" / "gold" / "gold-questions.jsonl"), [])

    def test_validators_run_from_the_command_line(self) -> None:
        m = self.fx.write()
        for script in ("validate_legal_maps.py", "validate_matter_ledgers.py", "validate_document_bundles.py"):
            argv = [sys.executable, str(SCRIPT_DIR / script), "--matter-dir", str(m), "--report", str(self.fx.tmp / f"{script}.json")]
            if script == "validate_legal_maps.py":
                argv += ["--root", str(self.fx.root)]
            proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["passed"])
            self.assertTrue((self.fx.tmp / f"{script}.json").exists())
        self.fx.ledger["source_facts"][0]["source_quote"] = "not in source"
        m = self.fx.write()
        proc = subprocess.run([sys.executable, str(SCRIPT_DIR / "validate_matter_ledgers.py"), "--matter-dir", str(m)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
