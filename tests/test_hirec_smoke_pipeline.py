"""Validation for the HiREC-inspired retrieval experiment.

Entirely offline. The loop is exercised through a fake OpenAI client, so no paid
API call is ever made and no key is needed.

    uv run pytest tests/test_hirec_smoke_pipeline.py -q
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "HiREC-inspired-retrieval"
KOBLEX = ROOT / "experiments" / "koblex-inspired-retrieval"
sys.path.insert(0, str(EXPERIMENT))

import hirec_config as config  # noqa: E402
import hirec_evaluate as evaluate_module  # noqa: E402
import hirec_hierarchy as hierarchy  # noqa: E402
import hirec_index  # noqa: E402
import hirec_llm as llm_client  # noqa: E402
import hirec_schemas as schemas  # noqa: E402
import run_hierarchy_ceiling  # noqa: E402
import run_hirec  # noqa: E402

import pydantic  # noqa: E402

GOLD_FILENAME = "smoke_test_20_gold.jsonl"
GOLD_PATH = config.SHARED_DATA_DIR / GOLD_FILENAME

# The modules allowed to know the gold file exists. hirec_evaluate.py scores
# against it; validate_dataset.py checks it is well-formed. Nothing else may
# name it, which is what keeps the runtime/evaluation split structural.
GOLD_AWARE_MODULES = {"hirec_evaluate.py", "validate_dataset.py"}

# Every module that runs at inference time.
RUNTIME_MODULES = [
    "hirec_config.py", "hirec_index.py", "hirec_hierarchy.py",
    "hirec_schemas.py", "hirec_llm.py", "hirec_build_index.py",
    "run_hierarchy_ceiling.py", "run_hirec.py", "pastpaper_triage.py",
]

# A section with a large subtree, for expansion tests.
BIG_SECTION = "7-2007/section-529"
# The corpus records whose section_id is null; they must expand to themselves.
NULL_SECTION_NODES = [
    "17-2002/schedule-1", "2-1958/schedule-1",
    "21-1931/schedule-1/item-1", "21-1931/schedule-1/item-2",
]

SENTINEL_REFINED_QUERY = "zzz-sentinel-refinement-query-zzz"


def build_temp_index(tmp: Path) -> Path:
    db = tmp / "index.sqlite3"
    hirec_index.build_index(config.CORPUS_PATH, db)
    return db


def default_args(**overrides) -> argparse.Namespace:
    args = argparse.Namespace(
        seed_top_k=config.DEFAULT_SEED_TOP_K,
        max_iterations=config.DEFAULT_MAX_ITERATIONS,
        max_relevant_ids=config.DEFAULT_MAX_RELEVANT_IDS,
        max_acts=config.DEFAULT_MAX_ACTS,
        max_pool_records=config.DEFAULT_MAX_POOL_RECORDS,
        max_pool_chars=config.DEFAULT_MAX_POOL_CHARS,
        act_selector="derived",
        gate_on="derived",
        curation_effort=None,
        expand=True,
        negative_prior=False,
        xref_precheck=False,
        freeze_evidence=False,
    )
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


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

    def count_for(self, schema_name: str) -> int:
        return sum(1 for c in self.calls if c["schema"] == schema_name)


def scripted(responses):
    """A factory that returns each canned response once, in order.

    Raises if the pipeline asks for more responses than were scripted, which is
    what turns a runaway loop into a test failure rather than a hang.
    """
    remaining = list(responses)

    def factory(prompt):
        if not remaining:
            raise AssertionError(
                "the pipeline asked for more responses than were scripted")
        value = remaining.pop(0)
        return value(prompt) if callable(value) else value

    return factory


def pool_ids_in(prompt: str, candidates: list[str], count: int) -> list[str]:
    return [nid for nid in candidates if nid in prompt][:count]


def curation(*, complete: bool, node_ids, status=None, missing=None,
             refined=SENTINEL_REFINED_QUERY, xrefs=()) -> schemas.EvidenceCuration:
    node_ids = list(node_ids)
    if status is None:
        status = schemas.COVERED if node_ids else schemas.NOT_COVERED
    if status == schemas.NOT_COVERED:
        covering = []
    else:
        covering = node_ids
    return schemas.EvidenceCuration(
        sub_questions=[schemas.SubQuestionCoverage(
            sub_question="What does the Act require?",
            covering_node_ids=covering,
            status=status,
            gap="" if status == schemas.COVERED else "the enforcement rule")],
        unresolved_cross_references=list(xrefs),
        sibling_accounting="Siblings were considered.",
        relevant_node_ids=node_ids,
        model_claimed_complete=complete,
        missing_evidence=[] if complete else (missing or ["the enforcement rule"]),
        refined_query="" if complete else refined,
    )


def answer_factory(prompt):
    cited = [line.split("node_id: ")[1].strip()
             for line in prompt.splitlines() if line.startswith("node_id: ")][:1]
    return schemas.GroundedAnswer(
        answerable=True,
        answer="The statutory rule applies to these facts.",
        cited_node_ids=cited,
        missing_evidence=[])


def refined_query_factory(_prompt):
    return schemas.RefinedQuery(
        search_query=SENTINEL_REFINED_QUERY,
        targets="Find the enforcement rule.")


# --------------------------------------------------------------------------- #
# isolation from the koblex experiment
# --------------------------------------------------------------------------- #

class IsolationTests(unittest.TestCase):
    """Both experiments put their directory on sys.path in the same pytest run.

    Unprefixed module names would let `import schemas` resolve to whichever
    directory landed first -- a silent wrong-module import, not an error. These
    tests are what make that impossible to introduce unnoticed.
    """

    def test_every_module_resolves_inside_this_experiment(self):
        modules = [config, hirec_index, hierarchy, schemas, llm_client,
                   evaluate_module, run_hirec, run_hierarchy_ceiling]
        offenders = [
            m.__name__ for m in modules
            if EXPERIMENT not in Path(m.__file__).resolve().parents
        ]
        self.assertEqual(offenders, [],
                         f"module(s) resolved outside {EXPERIMENT}: {offenders}")

    def test_no_module_name_collides_with_the_koblex_experiment(self):
        mine = {p.name for p in EXPERIMENT.glob("*.py")}
        theirs = {p.name for p in KOBLEX.glob("*.py")}
        self.assertEqual(mine & theirs, set(),
                         "module names shared with the koblex experiment would "
                         "shadow each other on sys.path")

    def test_answering_prompt_is_byte_identical_to_the_koblex_one(self):
        """The answer stage is shared so its metrics stay comparable."""
        mine = (EXPERIMENT / "prompts" / "grounded_answer.md").read_bytes()
        theirs = (KOBLEX / "prompts" / "grounded_answer.md").read_bytes()
        self.assertEqual(hashlib.sha256(mine).hexdigest(),
                         hashlib.sha256(theirs).hexdigest())

    def test_index_database_is_private_to_this_experiment(self):
        self.assertIn(EXPERIMENT, config.INDEX_DB_PATH.parents)

    def test_corpus_and_questions_are_shared_read_only_inputs(self):
        self.assertIn(KOBLEX, config.CORPUS_PATH.parents)
        self.assertIn(KOBLEX, config.QUESTIONS_PATH.parents)
        self.assertTrue(config.CORPUS_PATH.is_file())
        self.assertTrue(config.QUESTIONS_PATH.is_file())


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #

class DataTests(unittest.TestCase):

    def test_all_twenty_questions_load(self):
        questions = config.load_jsonl(config.QUESTIONS_PATH)
        self.assertEqual(len(questions), 20)
        for item in questions:
            self.assertIn("question_id", item)
            self.assertTrue(item["question"].strip())

    def test_gold_provisions_all_resolve_against_the_corpus(self):
        corpus_ids = {json.loads(line)["node_id"]
                      for line in config.CORPUS_PATH.read_text(
                          encoding="utf-8").splitlines() if line.strip()}
        missing = []
        for record in config.load_jsonl(GOLD_PATH):
            for node_id in record["relevant_provisions"]:
                if node_id not in corpus_ids:
                    missing.append(node_id)
        self.assertEqual(missing, [])


# --------------------------------------------------------------------------- #
# index and hierarchy
# --------------------------------------------------------------------------- #

class HierarchyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = build_temp_index(Path(cls._tmp.name))
        cls.index = hirec_index.Bm25Index(cls.db)
        cls.corpus = config.load_jsonl(config.CORPUS_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.index.close()
        cls._tmp.cleanup()

    def _corpus_subtree(self, section_id: str) -> set[str]:
        return {r["node_id"] for r in self.corpus
                if (r.get("section_id") or r["node_id"]) == section_id}

    def test_acts_table_covers_every_act_with_a_long_title(self):
        """Derived from the corpus, never a fixed count: the corpus gains
        statutes as sources are ingested."""
        acts = self.index.acts()
        self.assertEqual({a["act_id"] for a in acts},
                         {r["act_id"] for r in self.corpus})
        for act in acts:
            self.assertTrue(act["long_title"].strip(),
                            f"{act['act_id']} has no long title")
            self.assertGreater(act["record_count"], 0)
            self.assertGreater(act["section_count"], 0)

    def test_section_expansion_admits_every_record_of_a_seeded_section(self):
        expected = self._corpus_subtree(BIG_SECTION)
        self.assertGreater(len(expected), 100, "fixture section should be large")
        child = sorted(expected - {BIG_SECTION})[0]
        pool = hierarchy.section_pool(
            self.index, [{"node_id": child, "rank": 1}],
            max_records=10_000, max_chars=10**9)
        self.assertEqual(set(pool.node_ids), expected)

    def test_expanded_records_are_in_ascending_document_order(self):
        pool = hierarchy.section_pool(
            self.index, [{"node_id": BIG_SECTION, "rank": 1}],
            max_records=10_000, max_chars=10**9)
        ordinals = [r["ordinal"] for r in pool.records]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_section_expansion_is_idempotent_and_deduplicates(self):
        expected = self._corpus_subtree(BIG_SECTION)
        seeds = [{"node_id": nid, "rank": i}
                 for i, nid in enumerate(sorted(expected)[:5], start=1)]
        pool = hierarchy.section_pool(
            self.index, seeds, max_records=10_000, max_chars=10**9)
        self.assertEqual(set(pool.node_ids), expected)
        self.assertEqual(len(pool.node_ids), len(set(pool.node_ids)))

    def test_records_without_a_section_id_expand_to_themselves(self):
        for node_id in NULL_SECTION_NODES:
            with self.subTest(node_id=node_id):
                pool = hierarchy.section_pool(
                    self.index, [{"node_id": node_id, "rank": 1}],
                    max_records=10_000, max_chars=10**9)
                self.assertEqual(pool.node_ids, [node_id])

    def test_act_scoped_search_returns_only_the_requested_acts(self):
        results = self.index.search("registration of title", 25,
                                    act_ids=["21-1998"])
        self.assertTrue(results)
        self.assertEqual({r["act_id"] for r in results}, {"21-1998"})

    def test_empty_act_list_is_unscoped_not_empty(self):
        """An empty IN () would silently return nothing."""
        scoped = self.index.search("registration of title", 10, act_ids=[])
        unscoped = self.index.search("registration of title", 10, act_ids=None)
        self.assertTrue(scoped)
        self.assertEqual([r["node_id"] for r in scoped],
                         [r["node_id"] for r in unscoped])

    def test_pool_respects_max_records_and_drops_whole_sections(self):
        hits = self.index.search("registration of title parcel", 20)
        pool = hierarchy.section_pool(
            self.index, hits, max_records=30, max_chars=10**9)
        self.assertTrue(pool.truncated)
        self.assertTrue(pool.dropped_section_ids)
        # No section may be partially present: a half section would make the
        # sibling rule in the curation prompt a lie.
        for section_id in pool.section_ids:
            self.assertEqual(
                {r["node_id"] for r in pool.records
                 if r["section_id"] == section_id},
                self._corpus_subtree(section_id))
        for section_id in pool.dropped_section_ids:
            self.assertNotIn(section_id, pool.section_ids)

    def test_pool_respects_max_chars(self):
        hits = self.index.search("registration of title parcel", 20)
        pool = hierarchy.section_pool(
            self.index, hits, max_records=10_000, max_chars=3_000)
        self.assertTrue(pool.truncated)
        self.assertLessEqual(pool.char_count, 3_000 + 0)

    def test_pool_order_is_section_rank_then_document_order(self):
        hits = self.index.search("registration of title parcel", 20)
        pool = hierarchy.section_pool(
            self.index, hits, max_records=10_000, max_chars=10**9)
        keys = [(pool.section_rank[r["section_id"]], r["ordinal"])
                for r in pool.records]
        self.assertEqual(keys, sorted(keys))

    def test_merge_keeps_carried_evidence_even_when_truncating(self):
        hits = self.index.search("registration of title parcel", 20)
        new = hierarchy.section_pool(
            self.index, hits, max_records=10_000, max_chars=10**9)
        carried = hierarchy.carried_pool(new.records[-3:])
        merged = hierarchy.merge_pools(carried, new, max_records=5,
                                      max_chars=10**9)
        for record in carried.records:
            self.assertIn(record["node_id"], merged.node_ids)

    def test_merge_sorts_the_carried_section_first(self):
        """Carried evidence leads, but its section stays whole and in document
        order -- a retained paragraph does not get torn out ahead of its own
        section."""
        hits = self.index.search("registration of title parcel", 20)
        new = hierarchy.section_pool(
            self.index, hits, max_records=10_000, max_chars=10**9)
        retained = new.records[-1]
        carried = hierarchy.carried_pool([retained])
        merged = hierarchy.merge_pools(carried, new, max_records=10_000,
                                       max_chars=10**9)
        leading = [r for r in merged.records
                   if r["section_id"] == retained["section_id"]]
        self.assertEqual(merged.records[:len(leading)], leading)
        self.assertIn(retained["node_id"], [r["node_id"] for r in leading])

    def test_render_pool_groups_by_section(self):
        hits = self.index.search("registration of title parcel", 5)
        pool = hierarchy.section_pool(
            self.index, hits, max_records=10_000, max_chars=10**9)
        rendered = hierarchy.render_pool(pool)
        for section_id in pool.section_ids:
            self.assertIn(f"### Section group: {section_id}", rendered)
        for node_id in pool.node_ids:
            self.assertIn(f"node_id: {node_id}", rendered)

    def test_query_text_uses_background_and_question(self):
        text = hirec_index.question_query_text("Background facts.", "The question?")
        self.assertEqual(text, "Background facts. The question?")

    def test_long_title_extraction_skips_a_provision_heading(self):
        self.assertEqual(
            hirec_index.long_title_of("An Act No. 1 of 1900 | Section 1 - Short title."),
            "")
        self.assertEqual(
            hirec_index.long_title_of("An Act No. 1 of 1900 | AN ORDINANCE TO DO X. | Section 1"),
            "AN ORDINANCE TO DO X.")


# --------------------------------------------------------------------------- #
# schemas
# --------------------------------------------------------------------------- #

class SchemaBoundaryTests(unittest.TestCase):

    def test_curation_schema_has_no_unsupported_keywords(self):
        """minItems/maxItems are rejected by OpenAI strict structured outputs."""
        for model in (schemas.EvidenceCuration, schemas.ActSelection,
                      schemas.RefinedQuery, schemas.GroundedAnswer):
            with self.subTest(model=model.__name__):
                text = json.dumps(model.model_json_schema())
                self.assertNotIn("minItems", text)
                self.assertNotIn("maxItems", text)

    def test_coverage_table_precedes_the_boolean_in_the_schema(self):
        """Strict outputs are generated in field order, so the analysis must
        come before the verdict it is supposed to justify."""
        fields = list(schemas.EvidenceCuration.model_fields)
        self.assertLess(fields.index("sub_questions"),
                        fields.index("model_claimed_complete"))
        self.assertLess(fields.index("unresolved_cross_references"),
                        fields.index("model_claimed_complete"))
        self.assertLess(fields.index("sibling_accounting"),
                        fields.index("model_claimed_complete"))

    def test_curation_rejects_complete_with_a_stated_gap(self):
        with self.assertRaises(pydantic.ValidationError):
            curation(complete=True, node_ids=["a"]).model_copy(
                update={"missing_evidence": ["something"]}).model_validate(
                    {"x": 1})

    def test_complete_with_missing_evidence_is_rejected(self):
        with self.assertRaises(pydantic.ValidationError):
            schemas.EvidenceCuration(
                sub_questions=[{"sub_question": "q", "covering_node_ids": ["a"],
                                "status": schemas.COVERED, "gap": ""}],
                unresolved_cross_references=[],
                sibling_accounting="",
                relevant_node_ids=["a"],
                model_claimed_complete=True,
                missing_evidence=["still missing something"],
                refined_query="")

    def test_incomplete_with_no_gap_stated_is_rejected(self):
        with self.assertRaises(pydantic.ValidationError):
            schemas.EvidenceCuration(
                sub_questions=[{"sub_question": "q", "covering_node_ids": [],
                                "status": schemas.NOT_COVERED, "gap": "x"}],
                unresolved_cross_references=[],
                sibling_accounting="",
                relevant_node_ids=[],
                model_claimed_complete=False,
                missing_evidence=[],
                refined_query="")

    def test_relevant_ids_bounded_by_validator(self):
        with self.assertRaises(pydantic.ValidationError):
            curation(complete=True,
                     node_ids=[f"n-{i}" for i in
                               range(schemas.MAX_RELEVANT_IDS + 1)])

    def test_relevant_ids_must_not_repeat(self):
        with self.assertRaises(pydantic.ValidationError):
            curation(complete=True, node_ids=["a", "a"])

    def test_sub_question_count_is_bounded(self):
        entry = {"sub_question": "q", "covering_node_ids": ["a"],
                 "status": schemas.COVERED, "gap": ""}
        for count in (0, schemas.MAX_SUB_QUESTIONS + 1):
            with self.subTest(count=count):
                with self.assertRaises(pydantic.ValidationError):
                    schemas.EvidenceCuration(
                        sub_questions=[entry] * count,
                        unresolved_cross_references=[],
                        sibling_accounting="",
                        relevant_node_ids=["a"],
                        model_claimed_complete=True,
                        missing_evidence=[],
                        refined_query="")

    def test_covered_point_must_name_a_provision(self):
        with self.assertRaises(pydantic.ValidationError):
            schemas.SubQuestionCoverage(
                sub_question="q", covering_node_ids=[],
                status=schemas.COVERED, gap="")

    def test_not_covered_point_must_not_name_a_provision(self):
        with self.assertRaises(pydantic.ValidationError):
            schemas.SubQuestionCoverage(
                sub_question="q", covering_node_ids=["a"],
                status=schemas.NOT_COVERED, gap="x")

    def test_derived_completeness_overrides_the_model_boolean(self):
        """The measurement this variant exists to make."""
        partial = schemas.EvidenceCuration(
            sub_questions=[
                {"sub_question": "a", "covering_node_ids": ["n-1"],
                 "status": schemas.COVERED, "gap": ""},
                {"sub_question": "b", "covering_node_ids": [],
                 "status": schemas.NOT_COVERED, "gap": "the penalty"}],
            unresolved_cross_references=[],
            sibling_accounting="",
            relevant_node_ids=["n-1"],
            model_claimed_complete=True,
            missing_evidence=[],
            refined_query="")
        self.assertTrue(partial.model_claimed_complete)
        self.assertFalse(schemas.derive_completeness(partial))

    def test_unresolved_cross_reference_defeats_derived_completeness(self):
        record = curation(complete=True, node_ids=["n-1"], xrefs=["section 47"])
        self.assertFalse(schemas.derive_completeness(record))

    def test_saturation_hatch_fires_at_the_threshold(self):
        ids = [f"n-{i}" for i in range(schemas.MAX_RELEVANT_IDS)]
        complete, forced = schemas.apply_saturation_hatch(
            False, ids, schemas.MAX_RELEVANT_IDS)
        self.assertTrue(complete)
        self.assertTrue(forced)

    def test_saturation_hatch_does_not_fire_below_the_threshold(self):
        ids = [f"n-{i}" for i in range(schemas.MAX_RELEVANT_IDS - 1)]
        complete, forced = schemas.apply_saturation_hatch(
            False, ids, schemas.MAX_RELEVANT_IDS)
        self.assertFalse(complete)
        self.assertFalse(forced)

    def test_saturation_hatch_does_not_mark_an_already_complete_set_forced(self):
        complete, forced = schemas.apply_saturation_hatch(
            True, [f"n-{i}" for i in range(30)], schemas.MAX_RELEVANT_IDS)
        self.assertTrue(complete)
        self.assertFalse(forced)


# --------------------------------------------------------------------------- #
# id guards
# --------------------------------------------------------------------------- #

class IdGuardTests(unittest.TestCase):

    def _pool(self) -> hierarchy.Pool:
        return hierarchy.Pool(
            records=[{"node_id": "a-1", "citation": "Act, s 1", "heading": "H",
                      "text": "Text one.", "section_id": "a-1", "ordinal": 0},
                     {"node_id": "a-2", "citation": "Act, s 2", "heading": "H",
                      "text": "Text two.", "section_id": "a-2", "ordinal": 1}],
            section_rank={"a-1": 1, "a-2": 2})

    def test_curation_cannot_name_node_ids_outside_the_pool(self):
        attempts = [curation(complete=True, node_ids=["fabricated-1"]),
                    curation(complete=True, node_ids=["fabricated-2"])]
        client = FakeOpenAI({"EvidenceCuration": scripted(attempts)})
        llm = llm_client.HirecLLM(client=client, model="test-model")
        with self.assertRaises(llm_client.ValidationFailure) as caught:
            llm.curate_evidence("bg", "q", self._pool(), 1)
        self.assertEqual(caught.exception.stage, "evidence_curation")
        self.assertEqual(caught.exception.offending, ["fabricated-2"],
                         "the failure is raised on the second attempt, so it "
                         "reports that attempt's offending ids, deduplicated")
        self.assertEqual(client.count_for("EvidenceCuration"), 2)
        self.assertIn("## Correction", client.prompts_for("EvidenceCuration")[1])

    def test_curation_retry_succeeds_when_the_second_attempt_is_valid(self):
        attempts = [curation(complete=True, node_ids=["fabricated-1"]),
                    curation(complete=True, node_ids=["a-1"])]
        client = FakeOpenAI({"EvidenceCuration": scripted(attempts)})
        llm = llm_client.HirecLLM(client=client, model="test-model")
        result = llm.curate_evidence("bg", "q", self._pool(), 1)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.parsed.relevant_node_ids, ["a-1"])

    def test_coverage_table_ids_are_guarded_too(self):
        """A fabricated id in the coverage table is as bad as one in the
        selection: the derived completeness flag is computed from it."""
        bad = schemas.EvidenceCuration(
            sub_questions=[{"sub_question": "q",
                            "covering_node_ids": ["fabricated-9"],
                            "status": schemas.COVERED, "gap": ""}],
            unresolved_cross_references=[], sibling_accounting="",
            relevant_node_ids=["a-1"], model_claimed_complete=True,
            missing_evidence=[], refined_query="")
        client = FakeOpenAI({"EvidenceCuration": scripted([bad, bad])})
        llm = llm_client.HirecLLM(client=client, model="test-model")
        with self.assertRaises(llm_client.ValidationFailure) as caught:
            llm.curate_evidence("bg", "q", self._pool(), 1)
        self.assertEqual(caught.exception.offending, ["fabricated-9"])

    def test_answer_cannot_cite_unsupplied_nodes(self):
        bad = schemas.GroundedAnswer(
            answerable=True, answer="x", cited_node_ids=["fabricated-1"],
            missing_evidence=[])
        client = FakeOpenAI({"GroundedAnswer": scripted([bad, bad])})
        llm = llm_client.HirecLLM(client=client, model="test-model")
        with self.assertRaises(llm_client.ValidationFailure) as caught:
            llm.answer("bg", "q", self._pool().records)
        self.assertEqual(caught.exception.stage, "final_answer")

    def test_act_selection_cannot_name_unsupplied_acts(self):
        bad = schemas.ActSelection(selected_act_ids=["99-9999"], reasoning="r")
        client = FakeOpenAI({"ActSelection": scripted([bad, bad])})
        llm = llm_client.HirecLLM(client=client, model="test-model")
        with self.assertRaises(llm_client.ValidationFailure) as caught:
            llm.select_acts("bg", "q", [{"act_id": "21-1998",
                                         "act_title": "T", "long_title": "L",
                                         "record_count": 1}], 3)
        self.assertEqual(caught.exception.stage, "act_selection")

    def test_reasoning_effort_per_stage(self):
        pool = self._pool()
        client = FakeOpenAI({
            "EvidenceCuration": scripted([curation(complete=True,
                                                   node_ids=["a-1"])]),
            "GroundedAnswer": scripted([schemas.GroundedAnswer(
                answerable=True, answer="x", cited_node_ids=["a-1"],
                missing_evidence=[])]),
            "RefinedQuery": scripted([refined_query_factory]),
        })
        llm = llm_client.HirecLLM(client=client, model="test-model")
        llm.curate_evidence("bg", "q", pool, 1)
        llm.answer("bg", "q", pool.records)
        llm.transform_query("bg", "q", ["gap"], [])
        efforts = {c["schema"]: c["reasoning"]["effort"] for c in client.calls}
        self.assertEqual(efforts["EvidenceCuration"],
                         config.REASONING_EFFORT["evidence_curation"])
        self.assertEqual(efforts["GroundedAnswer"],
                         config.REASONING_EFFORT["final_answer"])
        self.assertEqual(efforts["RefinedQuery"],
                         config.REASONING_EFFORT["query_transform"])

    def test_curation_effort_is_overridable(self):
        client = FakeOpenAI({"EvidenceCuration": scripted(
            [curation(complete=True, node_ids=["a-1"])])})
        llm = llm_client.HirecLLM(client=client, model="test-model",
                                  curation_effort="high")
        llm.curate_evidence("bg", "q", self._pool(), 1)
        self.assertEqual(client.calls[0]["reasoning"]["effort"], "high")

    def test_negative_prior_is_off_unless_asked_for(self):
        pool = self._pool()
        for negative_prior in (False, True):
            with self.subTest(negative_prior=negative_prior):
                client = FakeOpenAI({"EvidenceCuration": scripted(
                    [curation(complete=True, node_ids=["a-1"])])})
                llm = llm_client.HirecLLM(client=client, model="test-model",
                                          negative_prior=negative_prior)
                llm.curate_evidence("bg", "q", pool, 1)
                prompt = client.prompts_for("EvidenceCuration")[0]
                self.assertEqual(
                    config.NEGATIVE_PRIOR_BLOCK.strip() in prompt,
                    negative_prior)


# --------------------------------------------------------------------------- #
# the loop
# --------------------------------------------------------------------------- #

class LoopTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = build_temp_index(Path(cls._tmp.name))
        cls.index = hirec_index.Bm25Index(cls.db)
        cls.question = config.load_jsonl(config.QUESTIONS_PATH)[0]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.index.close()
        cls._tmp.cleanup()

    def _run(self, curations, *, args=None, refinements=None):
        client = FakeOpenAI({
            "EvidenceCuration": scripted(curations),
            "RefinedQuery": scripted(refinements
                                     or [refined_query_factory] * len(curations)),
            "GroundedAnswer": scripted([answer_factory]),
        })
        llm = llm_client.HirecLLM(client=client, model="test-model")
        trace = run_hirec.Trace()
        run_hirec.run_question(self.question, self.index, llm,
                               args or default_args(), trace)
        return client, trace

    @staticmethod
    def _first_pool_ids(client) -> list[str]:
        prompt = client.prompts_for("EvidenceCuration")[0]
        return [line.split("node_id: ")[1].strip()
                for line in prompt.splitlines() if line.startswith("node_id: ")]

    def test_loop_stops_when_evidence_is_complete(self):
        def complete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:2]
            return curation(complete=True, node_ids=ids)

        client, trace = self._run([complete])
        self.assertEqual(client.count_for("EvidenceCuration"), 1)
        self.assertEqual(client.count_for("RefinedQuery"), 0,
                         "no query rewrite should happen on a first-pass stop")
        self.assertEqual(len(trace.answers), 1)
        self.assertEqual(trace.answers[0]["stopped_by"],
                         run_hirec.STOPPED_COMPLETE)
        self.assertEqual(trace.answers[0]["iterations"], 1)
        self.assertEqual(trace.errors, [])

    def test_no_query_transform_on_the_first_iteration(self):
        """The koblex b1 run measured that generating queries up front cost 4
        points of recall@20, so the base question is used as-is first."""
        def incomplete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        client, _trace = self._run([incomplete, incomplete, incomplete],
                                   args=default_args(max_iterations=3))
        first_query = client.prompts_for("EvidenceCuration")[0]
        self.assertNotIn(SENTINEL_REFINED_QUERY, first_query)
        # Two rewrites for three iterations: none before the first.
        self.assertEqual(client.count_for("RefinedQuery"), 2)

    def test_loop_terminates_at_max_iterations_and_still_answers(self):
        def incomplete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        client, trace = self._run([incomplete] * 3,
                                  args=default_args(max_iterations=3))
        self.assertEqual(client.count_for("EvidenceCuration"), 3)
        self.assertEqual(len(trace.answers), 1)
        self.assertEqual(trace.answers[0]["stopped_by"],
                         run_hirec.STOPPED_BUDGET)
        self.assertEqual(trace.answers[0]["iterations"], 3)
        self.assertTrue(trace.answers[0]["unmet_evidence_at_stop"])
        labels = [p["label"] for p in trace.pools]
        self.assertIn("last_resort_retrieval", labels,
                      "budget exhaustion must record the uncurated last-resort "
                      "retrieval HiREC performs")

    def test_saturation_hatch_stops_the_loop_and_is_recorded(self):
        def saturated(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:schemas.MAX_RELEVANT_IDS]
            self.assertEqual(len(ids), schemas.MAX_RELEVANT_IDS)
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        client, trace = self._run([saturated], args=default_args(max_iterations=3))
        self.assertEqual(client.count_for("EvidenceCuration"), 1)
        self.assertEqual(trace.answers[0]["stopped_by"],
                         run_hirec.STOPPED_SATURATION)
        self.assertTrue(trace.curations[0]["forced_answerable"])
        self.assertEqual(len(trace.answers), 1)

    def test_gate_on_model_uses_the_models_own_boolean(self):
        """The faithful HiREC behaviour: a claim of completeness stops the loop
        even when the coverage table contradicts it."""
        def claims_complete_but_isnt(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return schemas.EvidenceCuration(
                sub_questions=[
                    {"sub_question": "a", "covering_node_ids": ids,
                     "status": schemas.COVERED, "gap": ""},
                    {"sub_question": "b", "covering_node_ids": [],
                     "status": schemas.NOT_COVERED, "gap": "the penalty"}],
                unresolved_cross_references=[], sibling_accounting="",
                relevant_node_ids=ids, model_claimed_complete=True,
                missing_evidence=[], refined_query="")

        client, trace = self._run([claims_complete_but_isnt],
                                  args=default_args(gate_on="model"))
        self.assertEqual(client.count_for("EvidenceCuration"), 1)
        self.assertTrue(trace.curations[0]["model_claimed_complete"])
        self.assertFalse(trace.curations[0]["derived_complete"])
        self.assertEqual(trace.answers[0]["stopped_by"],
                         run_hirec.STOPPED_COMPLETE)

    def test_derived_gate_keeps_iterating_where_the_model_would_stop(self):
        def claims_complete_but_isnt(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return schemas.EvidenceCuration(
                sub_questions=[
                    {"sub_question": "a", "covering_node_ids": ids,
                     "status": schemas.COVERED, "gap": ""},
                    {"sub_question": "b", "covering_node_ids": [],
                     "status": schemas.NOT_COVERED, "gap": "the penalty"}],
                unresolved_cross_references=[], sibling_accounting="",
                relevant_node_ids=ids, model_claimed_complete=True,
                missing_evidence=[], refined_query="")

        client, trace = self._run([claims_complete_but_isnt] * 2,
                                  args=default_args(max_iterations=2))
        self.assertEqual(client.count_for("EvidenceCuration"), 2)
        self.assertEqual(trace.answers[0]["stopped_by"],
                         run_hirec.STOPPED_BUDGET)

    def test_refined_query_never_reaches_the_curation_or_answer_prompt(self):
        def incomplete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        client, _trace = self._run([incomplete] * 3,
                                   args=default_args(max_iterations=3))
        offenders = []
        for schema in ("EvidenceCuration", "GroundedAnswer"):
            for prompt in client.prompts_for(schema):
                if SENTINEL_REFINED_QUERY in prompt:
                    offenders.append(schema)
        self.assertEqual(
            offenders, [],
            "the refined query is a retrieval hypothesis and must never reach "
            "a prompt that judges or cites evidence")

    def test_the_original_question_reaches_every_judging_prompt(self):
        def incomplete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        client, _trace = self._run([incomplete] * 2,
                                   args=default_args(max_iterations=2))
        prompts = (client.prompts_for("EvidenceCuration")
                   + client.prompts_for("GroundedAnswer"))
        self.assertTrue(prompts)
        for prompt in prompts:
            self.assertIn(self.question["question"], prompt)

    def test_tried_queries_go_to_the_rewriter_and_not_the_curator(self):
        """The tried-query list is retrieval hygiene, so it belongs in the
        rewriting stage. Withholding it from the curator is what makes the
        no-generated-text-in-a-judging-prompt property total."""
        def incomplete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        client, _trace = self._run([incomplete] * 3,
                                   args=default_args(max_iterations=3))
        for prompt in client.prompts_for("EvidenceCuration"):
            self.assertNotIn("Already tried", prompt)
        self.assertIn(SENTINEL_REFINED_QUERY,
                      client.prompts_for("RefinedQuery")[1])

    def test_evidence_shrinkage_is_recorded_per_iteration(self):
        """HiREC re-filters rather than freezing, so a provision kept at one
        iteration can be dropped at the next. Both sets must survive into the
        trace or gold_lost cannot be computed."""
        state = {}

        def keep_two(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:2]
            state["first"] = ids
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        def keep_one(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        _client, trace = self._run([keep_two, keep_one],
                                   args=default_args(max_iterations=2))
        self.assertEqual(len(trace.curations), 2)
        self.assertEqual(len(trace.curations[0]["retained_node_ids"]), 2)
        self.assertEqual(len(trace.curations[1]["retained_node_ids"]), 1)

    def test_freeze_evidence_never_drops_a_curated_provision(self):
        def keep_two(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:2]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        def keep_one(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=False, node_ids=ids,
                            status=schemas.PARTIALLY_COVERED)

        _client, trace = self._run(
            [keep_two, keep_one],
            args=default_args(max_iterations=2, freeze_evidence=True))
        first = set(trace.curations[0]["retained_node_ids"])
        second = set(trace.curations[1]["retained_node_ids"])
        self.assertTrue(first.issubset(second))

    def test_answers_only_cite_curated_nodes(self):
        def complete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:2]
            return curation(complete=True, node_ids=ids)

        _client, trace = self._run([complete])
        answer = trace.answers[0]
        curated = set(answer["curated_node_ids"])
        for node_id in answer["cited_node_ids"]:
            self.assertIn(node_id, curated)

    def test_derived_act_selection_costs_no_llm_call(self):
        def complete(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=True, node_ids=ids)

        client, trace = self._run([complete])
        self.assertEqual(client.count_for("ActSelection"), 0)
        self.assertEqual(trace.acts[0]["selector"], "derived")
        self.assertTrue(trace.acts[0]["selected_act_ids"])

    def test_xref_precheck_can_force_incompleteness(self):
        """Off by default so the calibration finding stays a statement about the
        model's own judgement."""
        def complete_with_a_dangling_reference(prompt):
            ids = [line.split("node_id: ")[1].strip()
                   for line in prompt.splitlines()
                   if line.startswith("node_id: ")][:1]
            return curation(complete=True, node_ids=ids)

        client = FakeOpenAI({
            "EvidenceCuration": scripted(
                [complete_with_a_dangling_reference] * 2),
            "RefinedQuery": scripted([refined_query_factory] * 2),
            "GroundedAnswer": scripted([answer_factory]),
        })
        llm = llm_client.HirecLLM(client=client, model="test-model")
        trace = run_hirec.Trace()
        run_hirec.run_question(
            self.question, self.index, llm,
            default_args(max_iterations=1, xref_precheck=True), trace)
        self.assertIn("xref_precheck_findings", trace.curations[0])


# --------------------------------------------------------------------------- #
# gold isolation
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

    def test_runtime_module_list_covers_every_module_but_the_gold_aware_ones(self):
        """A new runtime module must not escape the gold-isolation guarantee by
        being absent from the list above."""
        on_disk = {p.name for p in EXPERIMENT.glob("*.py")}
        self.assertEqual(on_disk - set(RUNTIME_MODULES), GOLD_AWARE_MODULES)

    def test_gold_aware_modules_are_the_only_ones_naming_the_gold_file(self):
        for name in GOLD_AWARE_MODULES:
            with self.subTest(module=name):
                source = (EXPERIMENT / name).read_text(encoding="utf-8")
                self.assertIn(GOLD_FILENAME, source)

    def test_ceiling_run_completes_with_the_gold_path_booby_trapped(self):
        """Open the gold file during a free run and the run must fail loudly."""
        import builtins

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
            sys.argv = ["run_hierarchy_ceiling.py", "--run-name",
                        "test-gold-isolation", "--limit", "2", "--db", str(db)]
            builtins.open = guarded_open
            try:
                exit_code = run_hierarchy_ceiling.main()
            finally:
                builtins.open = real_open
                sys.argv = argv
                run_dir = config.RUNS_DIR / "test-gold-isolation"
                pool_written = (run_dir / "hierarchy_pool.jsonl").is_file()
                written = json.loads(
                    (run_dir / "run_config.json").read_text(encoding="utf-8"))
                config.RUNS_DIR = runs_dir

        self.assertEqual(exit_code, 0)
        self.assertEqual(touched, [])
        self.assertTrue(pool_written)
        self.assertNotIn("OPENAI_API_KEY", json.dumps(written))
        self.assertIsNone(written["model"])

    def test_run_config_records_the_fidelity_ledger(self):
        ledger = config.fidelity_ledger(
            negative_prior=True, xref_precheck=True, freeze_evidence=True,
            gate_on="model", act_selector="llm")
        self.assertTrue(ledger["faithful"])
        joined = " ".join(ledger["divergent"])
        for flag in ("--negative-prior", "--xref-precheck",
                     "--freeze-evidence", "--gate-on model",
                     "--act-selector llm"):
            self.assertIn(flag, joined)

    def test_fidelity_ledger_omits_flags_that_are_off(self):
        ledger = config.fidelity_ledger(
            negative_prior=False, xref_precheck=False, freeze_evidence=False,
            gate_on="derived", act_selector="derived")
        joined = " ".join(ledger["divergent"])
        for flag in ("--negative-prior", "--xref-precheck", "--freeze-evidence"):
            self.assertNotIn(flag, joined)


# --------------------------------------------------------------------------- #
# evaluation maths
# --------------------------------------------------------------------------- #

class EvaluationTests(unittest.TestCase):

    def test_pool_recall_cutoffs_extend_beyond_twenty(self):
        order = [f"n-{i}" for i in range(200)]
        scored = evaluate_module.score_ranked(
            {"q1": order}, {"q1": {"n-150"}},
            evaluate_module.RECALL_CUTOFFS_POOL)
        self.assertEqual(scored["summary"]["recall@100"], 0.0)
        self.assertEqual(scored["summary"]["recall@200"], 1.0)
        self.assertTrue(scored["per_question"]["q1"]["complete_in_candidates"])

    def test_calibration_confusion_matrix(self):
        claims = {
            "q1": (True, {"a"}),          # claimed, and complete
            "q2": (True, {"a"}),          # claimed, but incomplete
            "q3": (False, {"a"}),         # not claimed, but complete
            "q4": (False, {"a"}),         # not claimed, and incomplete
        }
        gold = {"q1": {"a"}, "q2": {"a", "b"}, "q3": {"a"}, "q4": {"a", "b"}}
        block = evaluate_module.score_calibration(claims, gold)
        self.assertEqual(block["confusion"], {
            "claimed_complete_and_complete": 1,
            "claimed_complete_but_incomplete": 1,
            "claimed_incomplete_but_complete": 1,
            "claimed_incomplete_and_incomplete": 1,
        })
        self.assertEqual(block["accuracy"], 0.5)
        self.assertEqual(block["false_complete_rate"], 0.5)
        self.assertEqual(block["per_question"]["q2"]["missing"], ["b"])

    def test_calibration_flags_a_degenerate_ground_truth(self):
        """When the evidence was complete everywhere there is nothing for the
        claim to be wrong about, and a null rate must say so rather than read
        like a pass."""
        claims = {"q1": (True, {"a"}), "q2": (False, {"a"})}
        block = evaluate_module.score_calibration(
            claims, {"q1": {"a"}, "q2": {"a"}})
        self.assertIsNone(block["false_complete_rate"])
        self.assertIsNotNone(block["degenerate"])
        self.assertIn("unmeasurable", block["degenerate"])

    def test_calibration_is_not_flagged_degenerate_when_measurable(self):
        claims = {"q1": (True, {"a"}), "q2": (True, {"a"})}
        block = evaluate_module.score_calibration(
            claims, {"q1": {"a"}, "q2": {"a", "b"}})
        self.assertIsNone(block["degenerate"])

    def test_calibration_of_an_always_complete_claim(self):
        """The degenerate case the koblex baseline actually produced."""
        claims = {"q1": (True, {"a"}), "q2": (True, {"a"})}
        gold = {"q1": {"a"}, "q2": {"a", "b"}}
        block = evaluate_module.score_calibration(claims, gold)
        self.assertEqual(block["false_complete_rate"], 1.0)
        self.assertEqual(block["recall_of_incomplete"], 0.0)
        self.assertEqual(block["mcc"], 0.0)

    def test_iteration_growth_detects_added_and_lost_gold(self):
        curations = [
            {"question_id": "q1", "iteration": 1, "pool_size": 10,
             "relevant_node_ids": ["a"], "retained_node_ids": ["a"],
             "evidence_complete": False, "forced_answerable": False,
             "sub_questions": []},
            {"question_id": "q1", "iteration": 2, "pool_size": 20,
             "relevant_node_ids": ["b"], "retained_node_ids": ["b"],
             "evidence_complete": True, "forced_answerable": False,
             "sub_questions": []},
        ]
        answers = [{"question_id": "q1", "iterations": 2,
                    "stopped_by": "complete"}]
        block = evaluate_module.score_iterations(
            curations, answers, {"q1": {"a", "b"}})
        self.assertEqual(block["per_iteration"]["2"]["new_gold_found"], 1)
        self.assertEqual(block["per_iteration"]["2"]["gold_lost"], 1)
        self.assertEqual(block["mean_iterations"], 2.0)
        self.assertEqual(block["stopped_by"], {"complete": 1})
        self.assertEqual(
            block["questions_where_iteration_lost_gold"][0]["node_ids"], ["a"])

    def test_act_scoring_counts_only_reachable_excluded_gold(self):
        gold = {"q1": {"21-1998/section-10", "7-2007/section-73"}}
        # The act filter kept only one of the two gold acts, and the seed could
        # reach both.
        block = evaluate_module.score_act_selection(
            {"q1": ["21-1998"]}, gold, {"q1": {"21-1998", "7-2007"}})
        self.assertEqual(
            block["summary"]["gold_provisions_excluded_by_act_filter"], 1)
        self.assertEqual(block["summary"]["act_recall"], 0.5)
        self.assertFalse(block["per_question"]["q1"]["act_set_complete"])

    def test_act_scoring_ignores_gold_the_seed_never_reached(self):
        gold = {"q1": {"21-1998/section-10", "7-2007/section-73"}}
        block = evaluate_module.score_act_selection(
            {"q1": ["21-1998"]}, gold, {"q1": {"21-1998"}})
        self.assertEqual(
            block["summary"]["gold_provisions_excluded_by_act_filter"], 0)

    def test_set_metrics(self):
        block = evaluate_module.score_sets(
            {"q1": {"a", "b"}}, {"q1": {"a", "c"}}, "curated")
        entry = block["per_question"]["q1"]
        self.assertEqual(entry["precision"], 0.5)
        self.assertEqual(entry["recall"], 0.5)
        self.assertFalse(entry["complete_evidence"])
        self.assertFalse(entry["exact_set"])

    def test_superset_is_complete_but_not_exact(self):
        block = evaluate_module.score_sets(
            {"q1": {"a", "b", "c"}}, {"q1": {"a", "b"}}, "curated")
        entry = block["per_question"]["q1"]
        self.assertTrue(entry["complete_evidence"])
        self.assertFalse(entry["exact_set"])
        self.assertEqual(entry["recall"], 1.0)

    def test_sub_question_coverage_calibration(self):
        curations = [{
            "question_id": "q1",
            "pool": [{"node_id": "a"}, {"node_id": "b"}],
            "sub_questions": [
                {"status": "covered", "covering_node_ids": ["a"]},
                {"status": "covered", "covering_node_ids": ["b"]},
                {"status": "not_covered", "covering_node_ids": []},
            ],
        }]
        block = evaluate_module.score_sub_question_coverage(
            curations, {"q1": {"a"}})
        self.assertEqual(block["points_marked_covered"], 2)
        self.assertEqual(block["covered_points_naming_gold"], 1)
        self.assertEqual(block["covered_precision"], 0.5)
        self.assertEqual(block["points_marked_not_covered"], 1)

    def test_selection_block_reports_no_rank_aware_metric(self):
        block = evaluate_module.score_sets(
            {"q1": {"a"}}, {"q1": {"a"}}, "curated")
        self.assertNotIn("mrr", block["summary"])
        self.assertNotIn("recall@5", block["summary"])


if __name__ == "__main__":
    unittest.main()
