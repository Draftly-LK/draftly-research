"""Validation for the KoBLEX-inspired retrieval smoke test.

Entirely offline. The B1 pipeline is exercised through a fake OpenAI client, so
no paid API call is ever made and no key is needed.

    uv run pytest tests/test_koblex_smoke_pipeline.py -q
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "koblex-inspired-retrieval"
sys.path.insert(0, str(EXPERIMENT))

import smoke_config as config  # noqa: E402
import corpus_index  # noqa: E402
import evaluate as evaluate_module  # noqa: E402
import smoke_llm as llm_client  # noqa: E402
import run_koblex_inspired  # noqa: E402
from schemas import GroundedAnswer, InformationNeeds, ProvisionSelection  # noqa: E402

import pydantic  # noqa: E402

GOLD_FILENAME = "smoke_test_20_gold.jsonl"
GOLD_PATH = config.DATA_DIR / GOLD_FILENAME

RUNTIME_MODULES = [
    "smoke_config.py", "corpus_index.py", "smoke_llm.py",
    "build_index.py", "run_bm25.py", "run_koblex_inspired.py",
]


def build_temp_index(tmp: Path) -> Path:
    db = tmp / "index.sqlite3"
    corpus_index.build_index(config.CORPUS_PATH, db)
    return db


# --------------------------------------------------------------------------- #
# fake OpenAI client
# --------------------------------------------------------------------------- #

class FakeParsed:
    def __init__(self, parsed):
        self.output_parsed = parsed


class FakeResponses:
    """Returns a canned parsed object per schema type. Records every call."""

    def __init__(self, owner):
        self.owner = owner

    def parse(self, *, model, input, text_format, reasoning):  # noqa: A002
        self.owner.calls.append({
            "model": model, "prompt": input,
            "schema": text_format.__name__, "reasoning": reasoning,
        })
        factory = self.owner.factories[text_format.__name__]
        return FakeParsed(factory(input))


class FakeOpenAI:
    def __init__(self, factories):
        self.factories = factories
        self.calls: list[dict] = []
        self.responses = FakeResponses(self)

    def prompts_for(self, schema_name: str) -> list[str]:
        return [c["prompt"] for c in self.calls if c["schema"] == schema_name]


GENERATED_QUERIES = [
    "cadastral map requirement for registration of title",
    "investigation of claims to land parcel",
]


def default_factories(first_candidate_ids: list[str]):
    """Canned responses that stay inside the supplied candidate set."""

    def needs(_prompt):
        return InformationNeeds(information_needs=[
            {"id": f"need-{i}", "purpose": f"Find rule {i}.", "search_query": q}
            for i, q in enumerate(GENERATED_QUERIES, start=1)
        ])

    def selection(prompt):
        chosen = [nid for nid in first_candidate_ids if nid in prompt][:2]
        return ProvisionSelection(
            selected_node_ids=chosen, evidence_complete=True, missing_evidence=[])

    def answer(prompt):
        cited = [nid for nid in first_candidate_ids if nid in prompt][:1]
        return GroundedAnswer(
            answerable=True,
            answer="The statutory rule applies to these facts.",
            cited_node_ids=cited,
            missing_evidence=[])

    return {
        "InformationNeeds": needs,
        "ProvisionSelection": selection,
        "GroundedAnswer": answer,
    }


# --------------------------------------------------------------------------- #
# 1, 2, 8 -- data
# --------------------------------------------------------------------------- #

class DataTests(unittest.TestCase):

    def test_all_twenty_questions_load(self):
        questions = config.load_jsonl(config.QUESTIONS_PATH)
        self.assertEqual(len(questions), 20)
        ids = [q["question_id"] for q in questions]
        self.assertEqual(len(set(ids)), 20)
        for question in questions:
            self.assertTrue(question["question"].strip())
            self.assertIn("background", question)

    def test_statute_node_ids_are_unique(self):
        records = config.load_jsonl(config.CORPUS_PATH)
        ids = [r["node_id"] for r in records]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(r.get("search_text") for r in records))

    def test_gold_provisions_all_resolve_against_the_corpus(self):
        corpus_ids = {r["node_id"] for r in config.load_jsonl(config.CORPUS_PATH)}
        gold = config.load_jsonl(GOLD_PATH)
        self.assertEqual(len(gold), 20)
        unresolved = [
            f"{g['question_id']}:{nid}"
            for g in gold for nid in g["relevant_provisions"]
            if nid not in corpus_ids
        ]
        self.assertEqual(unresolved, [], f"gold IDs missing from corpus: {unresolved}")
        question_ids = [q["question_id"] for q in config.load_jsonl(config.QUESTIONS_PATH)]
        self.assertEqual([g["question_id"] for g in gold], question_ids)


# --------------------------------------------------------------------------- #
# 3 -- BM25
# --------------------------------------------------------------------------- #

class Bm25Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = build_temp_index(Path(cls._tmp.name))
        cls.index = corpus_index.Bm25Index(cls.db)
        cls.corpus_ids = cls.index.node_ids()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.index.close()
        cls._tmp.cleanup()

    def test_results_are_valid_node_ids_ranked_by_descending_score(self):
        questions = config.load_jsonl(config.QUESTIONS_PATH)
        offenders = []
        for item in questions:
            query = corpus_index.question_query_text(
                item.get("background", ""), item["question"])
            results = self.index.search(query, 20)
            if not results:
                offenders.append(f"{item['question_id']}: no results")
                continue
            for result in results:
                if result["node_id"] not in self.corpus_ids:
                    offenders.append(f"{item['question_id']}: {result['node_id']}")
            scores = [r["bm25_score"] for r in results]
            if scores != sorted(scores, reverse=True):
                offenders.append(f"{item['question_id']}: scores not descending")
            ranks = [r["rank"] for r in results]
            if ranks != list(range(1, len(ranks) + 1)):
                offenders.append(f"{item['question_id']}: ranks not sequential")
        self.assertEqual(offenders, [])

    def test_query_text_uses_background_and_question(self):
        query = corpus_index.question_query_text("Facts about a notary.",
                                                 "What is the rule?")
        self.assertIn("facts about a notary", query.casefold())
        self.assertIn("what is the rule", query.casefold())

    def test_stopwords_dropped_but_legal_and_numeric_tokens_kept(self):
        tokens = corpus_index.content_tokens(
            "the acquisition of an interest in section 20C of the "
            "Registration of Title Act 1998 by a notary")
        self.assertNotIn("the", tokens)
        self.assertNotIn("of", tokens)
        self.assertNotIn("by", tokens)
        for kept in ("acquisition", "interest", "section", "20c",
                     "registration", "title", "act", "1998", "notary"):
            self.assertIn(kept, tokens, f"{kept} should survive stopword filtering")

    def test_match_expression_quotes_tokens_and_survives_punctuation(self):
        expression = corpus_index.match_expression('s. 20(2)(a) -- "title" OR NEAR/')
        self.assertTrue(expression)
        self.assertNotIn("(", expression)
        # The dangerous input must still execute against FTS5 without raising.
        self.index.search('s. 20(2)(a) -- "title" OR NEAR/', 5)

    def test_empty_query_returns_no_results(self):
        self.assertEqual(self.index.search("", 5), [])
        self.assertEqual(corpus_index.match_expression("!!! ???"), "")

    def test_merge_deduplicates_and_respects_max_candidates(self):
        first = self.index.search("cadastral map registration of title", 20)
        second = self.index.search("investigation of claims to land", 20)
        merged = corpus_index.merge_candidates(
            [("base", first), ("need-1", second)], max_candidates=25)
        ids = [c["node_id"] for c in merged]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertLessEqual(len(ids), 25)
        self.assertEqual([c["merged_rank"] for c in merged],
                         list(range(1, len(merged) + 1)))


# --------------------------------------------------------------------------- #
# 4, 5, 6 -- schema and validation boundaries
# --------------------------------------------------------------------------- #

class SchemaBoundaryTests(unittest.TestCase):

    def _needs(self, count: int) -> InformationNeeds:
        return InformationNeeds(information_needs=[
            {"id": f"need-{i}", "purpose": "p", "search_query": "q"}
            for i in range(1, count + 1)
        ])

    def test_between_one_and_three_information_needs_accepted(self):
        for count in (1, 2, 3):
            self.assertEqual(len(self._needs(count).information_needs), count)

    def test_zero_or_four_information_needs_rejected(self):
        for count in (0, 4):
            with self.assertRaises(pydantic.ValidationError):
                self._needs(count)

    def test_information_needs_schema_has_no_unsupported_keywords(self):
        """minItems/maxItems would break OpenAI strict structured outputs."""
        schema = json.dumps(InformationNeeds.model_json_schema())
        self.assertNotIn("minItems", schema)
        self.assertNotIn("maxItems", schema)

    def test_selection_cannot_return_unsupplied_candidate_ids(self):
        candidates = [{"node_id": "a/section-1", "citation": "c", "heading": "h",
                       "text": "t"}]

        def bad_selection(_prompt):
            return ProvisionSelection(
                selected_node_ids=["a/section-1", "fabricated/section-99"],
                evidence_complete=True, missing_evidence=[])

        factories = default_factories(["a/section-1"])
        factories["ProvisionSelection"] = bad_selection
        client = FakeOpenAI(factories)
        llm = llm_client.SmokeTestLLM(client=client, model="test-model")

        with self.assertRaises(llm_client.ValidationFailure) as caught:
            llm.select_provisions("bg", "q", candidates)
        self.assertIn("fabricated/section-99", caught.exception.offending)
        # exactly one corrective retry, then give up
        self.assertEqual(len(client.prompts_for("ProvisionSelection")), 2)
        self.assertIn("## Correction", client.prompts_for("ProvisionSelection")[1])

    def test_selection_retry_succeeds_when_second_attempt_is_valid(self):
        candidates = [{"node_id": "a/section-1", "citation": "c", "heading": "h",
                       "text": "t"}]
        attempts = {"n": 0}

        def flaky(_prompt):
            attempts["n"] += 1
            ids = (["ghost/section-1"] if attempts["n"] == 1 else ["a/section-1"])
            return ProvisionSelection(selected_node_ids=ids,
                                      evidence_complete=True, missing_evidence=[])

        factories = default_factories(["a/section-1"])
        factories["ProvisionSelection"] = flaky
        llm = llm_client.SmokeTestLLM(client=FakeOpenAI(factories), model="m")
        result = llm.select_provisions("bg", "q", candidates)
        self.assertEqual(result.parsed.selected_node_ids, ["a/section-1"])
        self.assertEqual(result.attempts, 2)

    def test_answer_cannot_cite_unselected_nodes(self):
        provisions = [{"node_id": "a/section-1", "citation": "c", "heading": "h",
                       "text": "t"}]

        def bad_answer(_prompt):
            return GroundedAnswer(
                answerable=True, answer="x",
                cited_node_ids=["a/section-1", "never/selected-1"],
                missing_evidence=[])

        factories = default_factories(["a/section-1"])
        factories["GroundedAnswer"] = bad_answer
        client = FakeOpenAI(factories)
        llm = llm_client.SmokeTestLLM(client=client, model="m")

        with self.assertRaises(llm_client.ValidationFailure) as caught:
            llm.answer("bg", "q", provisions)
        self.assertIn("never/selected-1", caught.exception.offending)
        self.assertEqual(len(client.prompts_for("GroundedAnswer")), 2)

    def test_reasoning_effort_per_stage(self):
        candidates = [{"node_id": "a/section-1", "citation": "c", "heading": "h",
                       "text": "t"}]
        client = FakeOpenAI(default_factories(["a/section-1"]))
        llm = llm_client.SmokeTestLLM(client=client, model="m")
        llm.generate_information_needs("bg", "q")
        llm.select_provisions("bg", "q", candidates)
        llm.answer("bg", "q", candidates)
        efforts = {c["schema"]: c["reasoning"]["effort"] for c in client.calls}
        self.assertEqual(efforts["InformationNeeds"], "low")
        self.assertEqual(efforts["ProvisionSelection"], "low")
        self.assertEqual(efforts["GroundedAnswer"], "medium")


# --------------------------------------------------------------------------- #
# 7 -- gold isolation
# --------------------------------------------------------------------------- #

class GoldIsolationTests(unittest.TestCase):

    def test_runtime_modules_never_name_the_gold_file(self):
        offenders = []
        for name in RUNTIME_MODULES:
            source = (EXPERIMENT / name).read_text(encoding="utf-8")
            if GOLD_FILENAME in source:
                offenders.append(name)
        self.assertEqual(offenders, [],
                         f"gold filename referenced in runtime module(s): {offenders}")

    def test_only_evaluate_references_the_gold_file(self):
        source = (EXPERIMENT / "evaluate.py").read_text(encoding="utf-8")
        self.assertIn(GOLD_FILENAME, source)

    def test_run_bm25_completes_with_the_gold_path_booby_trapped(self):
        """Open the gold file during a B0 run and the run must fail loudly."""
        import builtins
        import run_bm25

        real_open = builtins.open
        touched: list[str] = []

        def guarded_open(file, *args, **kwargs):
            if GOLD_FILENAME in str(file):
                touched.append(str(file))
                raise AssertionError("runtime must not open the gold file")
            return real_open(file, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            db = build_temp_index(Path(tmp))
            argv = sys.argv
            runs_dir = config.RUNS_DIR
            # Keep the run output inside the temp dir so the test leaves no
            # artefacts in the repository.
            config.RUNS_DIR = Path(tmp) / "runs"
            sys.argv = ["run_bm25.py", "--run-name", "test-gold-isolation",
                        "--limit", "2", "--db", str(db)]
            builtins.open = guarded_open
            try:
                exit_code = run_bm25.main()
            finally:
                builtins.open = real_open
                sys.argv = argv
                run_dir = config.RUNS_DIR / "test-gold-isolation"
                predictions = (run_dir / "bm25_predictions.jsonl").is_file()
                written = json.loads(
                    (run_dir / "run_config.json").read_text(encoding="utf-8"))
                config.RUNS_DIR = runs_dir

        self.assertEqual(exit_code, 0)
        self.assertEqual(touched, [])
        self.assertTrue(predictions)
        self.assertNotIn("OPENAI_API_KEY", json.dumps(written))
        self.assertIsNone(written["model"])


# --------------------------------------------------------------------------- #
# 9, 10 -- full mocked pipeline
# --------------------------------------------------------------------------- #

class MockedPipelineTests(unittest.TestCase):

    def _run(self, tmp: Path):
        db = build_temp_index(tmp)
        index = corpus_index.Bm25Index(db)
        questions = config.load_jsonl(config.QUESTIONS_PATH)[:3]

        base = corpus_index.question_query_text(
            questions[0].get("background", ""), questions[0]["question"])
        candidate_ids = [r["node_id"] for r in index.search(base, 20)]

        client = FakeOpenAI(default_factories(candidate_ids))
        llm = llm_client.SmokeTestLLM(client=client, model="test-model")
        with index:
            traces = run_koblex_inspired.run_pipeline(
                questions, index, llm, top_k=20, max_candidates=40)
        return client, questions, traces

    def test_mocked_client_drives_the_whole_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            client, questions, traces = self._run(Path(tmp))
        queries, candidates, selections, answers, errors = traces

        self.assertEqual(len(queries), len(questions))
        self.assertEqual(len(candidates), len(questions))
        self.assertEqual(errors, [], f"unexpected errors: {errors}")
        self.assertEqual(len(selections), len(questions))
        self.assertEqual(len(answers), len(questions))

        for trace in (queries, candidates, selections, answers):
            for record in trace:
                self.assertIn("question_id", record)

        # all three stages were called for every question
        schemas = [c["schema"] for c in client.calls]
        self.assertEqual(schemas.count("InformationNeeds"), len(questions))
        self.assertEqual(schemas.count("ProvisionSelection"), len(questions))
        self.assertEqual(schemas.count("GroundedAnswer"), len(questions))

        # generated queries actually reached retrieval
        for record in candidates:
            self.assertEqual(record["generated_queries"], GENERATED_QUERIES)
            self.assertTrue(record["candidate_count"] > 0)

    def test_generated_queries_never_reach_the_answering_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            client, _questions, _traces = self._run(Path(tmp))

        answer_prompts = client.prompts_for("GroundedAnswer")
        selection_prompts = client.prompts_for("ProvisionSelection")
        self.assertTrue(answer_prompts)
        offenders = []
        for label, prompts in (("answer", answer_prompts),
                               ("selection", selection_prompts)):
            for prompt in prompts:
                for generated in GENERATED_QUERIES:
                    if generated in prompt:
                        offenders.append(f"{label}: {generated!r} leaked")
        self.assertEqual(offenders, [])

    def test_answers_only_cite_selected_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _client, _questions, traces = self._run(Path(tmp))
        _queries, _candidates, selections, answers, _errors = traces
        selected_by_q = {s["question_id"]: set(s["selected_node_ids"])
                         for s in selections}
        offenders = [
            f"{a['question_id']}: {nid}"
            for a in answers for nid in a["cited_node_ids"]
            if nid not in selected_by_q[a["question_id"]]
        ]
        self.assertEqual(offenders, [])


# --------------------------------------------------------------------------- #
# evaluation maths
# --------------------------------------------------------------------------- #

class EvaluationTests(unittest.TestCase):

    def test_ranked_metrics(self):
        gold = {"q1": {"a", "b"}}
        scored = evaluate_module.score_ranked({"q1": ["x", "a", "y", "b"]}, gold)
        entry = scored["per_question"]["q1"]
        self.assertEqual(entry["recall@5"], 1.0)
        self.assertEqual(entry["reciprocal_rank"], 0.5)
        self.assertTrue(entry["complete_in_candidates"])

    def test_ranked_metrics_with_no_hit(self):
        scored = evaluate_module.score_ranked({"q1": ["x", "y"]}, {"q1": {"a"}})
        entry = scored["per_question"]["q1"]
        self.assertEqual(entry["reciprocal_rank"], 0.0)
        self.assertEqual(entry["recall@5"], 0.0)
        self.assertFalse(entry["complete_in_candidates"])

    def test_set_metrics(self):
        gold = {"q1": {"a", "b"}}
        scored = evaluate_module.score_sets({"q1": {"a", "c"}}, gold, "selected")
        entry = scored["per_question"]["q1"]
        self.assertEqual(entry["precision"], 0.5)
        self.assertEqual(entry["recall"], 0.5)
        self.assertEqual(entry["f1"], 0.5)
        self.assertFalse(entry["complete_evidence"])
        self.assertFalse(entry["exact_set"])

    def test_exact_set_and_completeness(self):
        scored = evaluate_module.score_sets({"q1": {"a", "b"}}, {"q1": {"a", "b"}},
                                           "selected")
        entry = scored["per_question"]["q1"]
        self.assertTrue(entry["exact_set"])
        self.assertTrue(entry["complete_evidence"])
        self.assertEqual(entry["f1"], 1.0)

    def test_superset_is_complete_but_not_exact(self):
        scored = evaluate_module.score_sets({"q1": {"a", "b", "c"}}, {"q1": {"a", "b"}},
                                            "selected")
        entry = scored["per_question"]["q1"]
        self.assertTrue(entry["complete_evidence"])
        self.assertFalse(entry["exact_set"])
        self.assertEqual(entry["recall"], 1.0)

    def test_selection_block_reports_no_rank_aware_metric(self):
        scored = evaluate_module.score_sets({"q1": {"a"}}, {"q1": {"a"}}, "selected")
        keys = set(scored["summary"])
        self.assertFalse({"mrr", "recall@5", "recall@10", "recall@20"} & keys)


if __name__ == "__main__":
    unittest.main()
