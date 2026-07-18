from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from draftly.retrieval import StatuteQuery, answer, search
from draftly.retrieval.answering import (
    build_prompt,
    sanitize_answer_payload,
    validate_answer_payload,
    verify_claims,
)
from draftly.retrieval.models import AnswerClaim, StatuteAnswer, StatuteHit
from draftly.retrieval.qa_evaluation import run_qa_evaluation
from draftly.retrieval.question_analysis import analyze_question, known_corpus_gaps, parse_question_file


def hit(section_id: str, text: str = "A supported rule.") -> StatuteHit:
    source_id = section_id.split(":", 1)[0]
    return StatuteHit(
        source_id=source_id,
        section_id=section_id,
        title="Example Act",
        act_number="1",
        year="2026",
        document_type="statute",
        topics=(),
        heading="Example rule",
        excerpt=text,
        score=1.0,
        public_source_url="",
        extraction_confidence="parsed",
        text=text,
    )


class QuestionAnalysisTests(unittest.TestCase):
    def test_exam_file_parses_all_questions_and_subquestions(self) -> None:
        questions = parse_question_file("src/questions.md")

        self.assertEqual(len(questions), 18)
        self.assertEqual(sum(len(question.subquestions) for question in questions), 73)
        self.assertEqual(questions[0].question_id, "2026-april-q01")

    def test_full_question_is_decomposed_and_routed(self) -> None:
        question = parse_question_file("src/questions.md")[0]
        analysis = analyze_question(question.text)

        self.assertEqual(len(analysis.subqueries), 4)
        self.assertTrue({"SRC004", "SRC021", "SRC022"}.issubset({hint.source_id for hint in analysis.source_hints}))

    def test_known_missing_authority_is_explicit(self) -> None:
        gaps = known_corpus_gaps("Which approval is required for development in the coastal zone?")
        self.assertTrue(gaps)
        self.assertIn("coastal-zone", gaps[0])


class RetrievalRobustnessTests(unittest.TestCase):
    def test_lay_deed_query_returns_the_operating_provision_first(self) -> None:
        hits = search(StatuteQuery(text="What makes a deed of transfer valid?", limit=5))
        self.assertEqual(hits[0].section_id, "SRC001:s2")

    def test_multi_part_question_covers_both_inheritance_and_foreign_land_rules(self) -> None:
        question = parse_question_file("src/questions.md")[0]
        section_ids = {item.section_id for item in search(StatuteQuery(text=question.text, limit=12))}

        self.assertTrue({f"SRC004:s{number}" for number in range(22, 27)}.issubset(section_ids))
        self.assertIn("SRC021:s2", section_ids)
        self.assertTrue({"SRC022:s2", "SRC022:s3"} & section_ids)

    def test_missing_coastal_source_abstains_without_irrelevant_evidence(self) -> None:
        response = answer("Which authority approves development in the coastal zone?")
        self.assertEqual(response.outcome, "insufficient_authority")
        self.assertFalse(response.hits)
        self.assertEqual(response.fallback_reason, "known_corpus_gap")


class AnswerContractTests(unittest.TestCase):
    def test_answer_serialization_can_include_raw_model_output(self) -> None:
        response = StatuteAnswer(
            question="Question",
            hits=(hit("SRC001:s2"),),
            claims=(AnswerClaim(part="1", text="Rule", citations=("SRC001:s2",), verified=True),),
            raw_response='{"outcome":"answered"}',
            outcome="answered",
        )

        public = response.to_dict()
        internal = response.to_dict(include_raw=True)

        self.assertNotIn("raw_response", public)
        self.assertEqual(internal["raw_response"], '{"outcome":"answered"}')
        self.assertEqual(public["claims"][0]["text"], "Rule")

    def test_prompt_citation_allowlist_matches_included_evidence(self) -> None:
        prompt, citations = build_prompt("Question", (hit("SRC001:s2"), hit("SRC005:s7")), ("Question",))
        self.assertEqual(citations, {"SRC001:s2", "SRC005:s7"})
        self.assertIn("ID: SRC001:s2", prompt)

    def test_structured_payload_rejects_unknown_citations(self) -> None:
        payload = {
            "outcome": "answered",
            "claims": [{"part": "1", "text": "Rule", "citations": ["SRC999:s1"]}],
            "limitations": [],
            "missing_information": [],
        }
        self.assertIn("unknown_citation", validate_answer_payload(payload, {"SRC001:s2"}) or "")

    def test_uncited_claim_is_removed_without_discarding_valid_claims(self) -> None:
        payload = {
            "outcome": "answered",
            "claims": [
                {"part": "1", "text": "Supported", "citations": ["SRC001:s2"]},
                {"part": "2", "text": "Unsupported", "citations": []},
            ],
            "limitations": [],
            "missing_information": [],
        }

        cleaned, rejected = sanitize_answer_payload(payload, {"SRC001:s2"})

        self.assertEqual(len(cleaned["claims"]), 1)
        self.assertEqual(len(rejected), 1)
        self.assertIsNone(validate_answer_payload(cleaned, {"SRC001:s2"}))

    def test_subsection_citation_is_canonicalized_to_the_retrieved_parent(self) -> None:
        payload = {
            "outcome": "answered",
            "claims": [{"part": "1", "text": "Supported", "citations": ["SRC005:s7(1)"]}],
            "limitations": [],
            "missing_information": [],
        }

        cleaned, rejected = sanitize_answer_payload(payload, {"SRC005:s7"})

        self.assertFalse(rejected)
        self.assertEqual(cleaned["claims"][0]["citations"], ["SRC005:S7"])

    def test_abstained_payload_with_grounded_claims_becomes_partial(self) -> None:
        payload = {
            "outcome": "abstained",
            "claims": [{"part": "1", "text": "Supported", "citations": ["SRC001:s2"]}],
            "limitations": [],
            "missing_information": ["Part 2 lacks authority."],
        }

        cleaned, rejected = sanitize_answer_payload(payload, {"SRC001:s2"})

        self.assertFalse(rejected)
        self.assertEqual(cleaned["outcome"], "partial")
        self.assertIsNone(validate_answer_payload(cleaned, {"SRC001:s2"}))

    @patch("draftly.retrieval.answering.generate_json")
    def test_claim_verifier_drops_unsupported_claims(self, generate_json) -> None:
        generate_json.return_value = (
            {
                "verdicts": [
                    {"claim_index": 0, "supported": True, "answers_part": True, "reason": "supported"},
                    {"claim_index": 1, "supported": False, "answers_part": False, "reason": "not in section"},
                ]
            },
            "{}",
            None,
        )
        claims = [
            AnswerClaim(part="1", text="Supported", citations=("SRC001:s2",)),
            AnswerClaim(part="2", text="Unsupported", citations=("SRC001:s2",)),
        ]

        accepted, rejected, error = verify_claims("key", "model", "Question facts", claims, (hit("SRC001:s2"),))

        self.assertIsNone(error)
        self.assertEqual([claim.text for claim in accepted], ["Supported"])
        self.assertTrue(accepted[0].verified)
        self.assertEqual(len(rejected), 1)

    @patch("draftly.retrieval.answering.generate_json")
    def test_claim_verifier_drops_supported_but_irrelevant_claims(self, generate_json) -> None:
        generate_json.return_value = (
            {
                "verdicts": [
                    {
                        "claim_index": 0,
                        "supported": True,
                        "answers_part": False,
                        "reason": "the provision is narrower than the question",
                    }
                ]
            },
            "{}",
            None,
        )

        accepted, rejected, error = verify_claims(
            "key",
            "model",
            "Question facts",
            [AnswerClaim(part="1", text="Too broad", citations=("SRC001:s2",))],
            (hit("SRC001:s2"),),
        )

        self.assertIsNone(error)
        self.assertFalse(accepted)
        self.assertEqual(len(rejected), 1)

    def test_interleaved_inheritance_evidence_is_excluded_from_prompt(self) -> None:
        unsafe = StatuteHit(
            **{
                **hit("SRC004:s25").__dict__,
                "extraction_confidence": "interleaved_columns",
            }
        )

        prompt, citations = build_prompt("Calculate the shares", (unsafe, hit("SRC004:s22")), ("shares",))

        self.assertNotIn("SRC004:s25", citations)
        self.assertIn("SRC004:s22", citations)
        self.assertNotIn("ID: SRC004:s25", prompt)


class QuestionEvaluationTests(unittest.TestCase):
    def test_runner_is_explicit_when_legal_gold_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metrics = run_qa_evaluation(
                ["What makes a deed valid?"],
                Path(directory),
                retrieve=lambda _: [hit("SRC001:s2")],
            )

        self.assertEqual(metrics["questions"], 1)
        self.assertEqual(metrics["legal_correctness"]["status"], "not_evaluated")
        self.assertEqual(metrics["answer_quality"]["status"], "machine_checks_only")

    def test_runner_reports_verified_claim_coverage_without_calling_it_correctness(self) -> None:
        response = {
            "outcome": "partial",
            "claims": [{"part": "1", "text": "Rule", "citations": ["SRC001:s2"], "verified": True}],
            "fallback_reason": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            metrics = run_qa_evaluation(
                [{"question_id": "q1", "question": "1. What makes a deed valid?"}],
                Path(directory),
                retrieve=lambda _: [hit("SRC001:s2")],
                answer=lambda _: response,
            )

        self.assertEqual(metrics["answer_quality"]["outcomes"], {"partial": 1})
        self.assertEqual(metrics["answer_quality"]["verified_claims"], 1)
        self.assertEqual(metrics["legal_correctness"]["status"], "not_evaluated")


if __name__ == "__main__":
    unittest.main()
