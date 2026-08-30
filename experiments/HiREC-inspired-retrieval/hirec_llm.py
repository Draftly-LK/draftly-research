"""OpenAI Responses API wrapper with structured outputs.

Four stages, each with its own reasoning effort and its own pydantic schema.
Nothing here parses free-form text, and nothing here reads the gold file.

Validation is the point of this module: an act selection may only name Acts that
were supplied, a curation may only name provisions that were in the pool, and an
answer may only cite provisions that were curated. A violation triggers exactly
one corrective retry; if it persists, the caller gets a ValidationFailure to
record rather than a fabricated result. The retry loop is written once and shared
by every ID-guarded stage.

The refined query is never a parameter of curate_evidence or answer, so it
cannot reach either prompt. HiREC has the same property -- the curator and the
generator always see original_question -- and here it is structural rather than
a discipline someone has to maintain.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Sequence

import hirec_config as config
import hirec_hierarchy as hierarchy
from hirec_schemas import (
    ActSelection,
    EvidenceCuration,
    GroundedAnswer,
    RefinedQuery,
)


class ValidationFailure(RuntimeError):
    """Raised when a stage still returns invalid IDs after one retry."""

    def __init__(self, stage: str, detail: str, offending: Sequence[str] = ()):
        super().__init__(f"{stage}: {detail}")
        self.stage = stage
        self.detail = detail
        self.offending = list(offending)


@dataclass
class StageResult:
    parsed: Any
    attempts: int
    prompt: str


def build_client():
    """Construct the OpenAI client. Import is local so tests need no key."""
    from openai import OpenAI

    config.load_dotenv_if_present()
    return OpenAI()


def render_provisions(provisions: Sequence[dict]) -> str:
    """Curated provisions as node_id / citation / heading / text blocks.

    Matches the koblex rendering exactly, because the answering prompt is shared
    with that experiment and its evidence must look the same.
    """
    blocks = []
    for provision in provisions:
        heading = provision.get("heading") or "(no heading)"
        blocks.append(
            f"node_id: {provision['node_id']}\n"
            f"citation: {provision.get('citation') or ''}\n"
            f"heading: {heading}\n"
            f"text: {provision.get('text') or ''}"
        )
    return "\n\n---\n\n".join(blocks)


def render_tried(tried: Sequence[str]) -> str:
    if not tried:
        return "(nothing tried yet)"
    return "\n".join(f"- {query}" for query in tried)


class HirecLLM:
    """The four LLM stages. `client` is injectable so tests can mock it."""

    def __init__(self, client=None, model: str | None = None,
                 curation_effort: str | None = None,
                 negative_prior: bool = False):
        self._client = client if client is not None else build_client()
        self.model = model or config.model_name()
        self.curation_effort = (
            curation_effort or config.REASONING_EFFORT["evidence_curation"])
        self.negative_prior = negative_prior
        # One record per API call: stage, wall-clock, tokens. Latency and cost
        # are reported from this, so they are measured rather than estimated.
        self.calls: list[dict] = []
        self._question_id: str | None = None

    def for_question(self, question_id: str) -> None:
        """Tag subsequent call records, so usage can be attributed per question."""
        self._question_id = question_id

    # -- transport ------------------------------------------------------ #

    @staticmethod
    def _usage(response) -> dict:
        """Token counts, defensively.

        A mocked client in the tests has no usage object, and a live response
        could in principle omit one. Missing counts are recorded as None rather
        than 0, because a silent zero would understate a cost report.
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            return {"input_tokens": None, "output_tokens": None,
                    "reasoning_tokens": None}
        details = getattr(usage, "output_tokens_details", None)
        return {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "reasoning_tokens": getattr(details, "reasoning_tokens", None),
        }

    def _parse(self, prompt: str, schema, effort: str, stage: str = "unknown"):
        started = time.perf_counter()
        error = None
        try:
            response = self._client.responses.parse(
                model=self.model,
                input=prompt,
                text_format=schema,
                reasoning={"effort": effort},
            )
        except Exception as exc:  # noqa: BLE001 - recorded, then re-raised
            error = type(exc).__name__
            raise
        finally:
            record = {
                "question_id": self._question_id,
                "stage": stage,
                "schema": getattr(schema, "__name__", str(schema)),
                "effort": effort,
                "elapsed_s": round(time.perf_counter() - started, 3),
                "prompt_chars": len(prompt),
                "error": error,
            }
            if error is None:
                record.update(self._usage(response))
            self.calls.append(record)

        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise ValidationFailure(
                "transport", "model returned no parsed structured output")
        return parsed

    def _parse_with_id_guard(
        self,
        base_prompt: str,
        schema,
        effort: str,
        allowed: set[str],
        extract_ids: Callable[[Any], Sequence[str]],
        stage: str,
        detail: str,
        correction_hint: str,
    ) -> StageResult:
        """Parse, then check every ID against `allowed`, retrying once.

        One retry, not a loop: a model that cannot copy an identifier from the
        list in front of it twice is not going to succeed on the fifth attempt,
        and an unbounded retry turns a bad prompt into an unbounded bill.
        """
        prompt = base_prompt
        for attempt in (1, 2):
            parsed = self._parse(prompt, schema, effort, stage)
            invalid = [i for i in extract_ids(parsed) if i not in allowed]
            if not invalid:
                return StageResult(parsed=parsed, attempts=attempt, prompt=prompt)
            if attempt == 2:
                raise ValidationFailure(stage, detail, invalid)
            prompt = (
                f"{base_prompt}\n\n## Correction\n\n"
                f"A previous attempt returned these identifiers, which are not "
                f"available: {json.dumps(invalid)}. {correction_hint}"
            )
        raise AssertionError("unreachable")

    # -- stage 1: act selection ----------------------------------------- #

    def select_acts(self, background: str, question: str,
                    acts: Sequence[dict], max_acts: int) -> StageResult:
        allowed = {a["act_id"] for a in acts}
        prompt = config.prompt_text("act_selection").format(
            background=background or "(none)",
            question=question,
            acts=hierarchy.render_acts(acts),
            max_acts=max_acts,
        )
        return self._parse_with_id_guard(
            prompt, ActSelection, config.REASONING_EFFORT["act_selection"],
            allowed, lambda p: p.selected_act_ids, "act_selection",
            "selected act IDs are not in the supplied list",
            "Select only act_id values copied exactly from the list above.",
        )

    # -- stage 2: refinement query -------------------------------------- #

    def transform_query(self, background: str, question: str,
                        missing_evidence: Sequence[str],
                        tried_queries: Sequence[str]) -> StageResult:
        """Rewrites a described gap into a retrieval query.

        Never called on the first iteration. The koblex b1 run measured that
        generating queries up front cost 4 points of recall@20, so the base
        question is used as-is until there is a specific gap to chase.
        """
        missing = "\n".join(f"- {m}" for m in missing_evidence) or "(none stated)"
        prompt = config.prompt_text("query_transform").format(
            background=background or "(none)",
            question=question,
            missing_evidence=missing,
            tried_queries=render_tried(tried_queries),
        )
        parsed = self._parse(
            prompt, RefinedQuery, config.REASONING_EFFORT["query_transform"],
            "query_transform")
        return StageResult(parsed=parsed, attempts=1, prompt=prompt)

    # -- stage 3: evidence curation ------------------------------------- #

    def curate_evidence(self, background: str, question: str,
                        pool: hierarchy.Pool, iteration: int) -> StageResult:
        """One inference: filter, answerability, missing information, refinement.

        `question` is always the original question, and neither the refined query
        nor the list of queries already tried is a parameter of this method. That
        is deliberate and is what the structure buys: a generated string cannot
        reach a prompt that judges or cites evidence, because there is no
        argument to pass it in through. The rewriting stage, which is pure
        retrieval, is where the tried-query list belongs.
        """
        allowed = set(pool.node_ids)
        prompt = config.prompt_text("evidence_curation").format(
            background=background or "(none)",
            question=question,
            pool=hierarchy.render_pool(pool),
            iteration=iteration,
        )
        if self.negative_prior:
            prompt += config.NEGATIVE_PRIOR_BLOCK

        def ids(parsed: EvidenceCuration) -> list[str]:
            out = list(parsed.relevant_node_ids)
            for sub_question in parsed.sub_questions:
                out.extend(sub_question.covering_node_ids)
            return list(dict.fromkeys(out))

        return self._parse_with_id_guard(
            prompt, EvidenceCuration, self.curation_effort, allowed, ids,
            "evidence_curation",
            "node IDs are not in the supplied provision pool",
            "Use only node_id values copied exactly from the pool above. Do "
            "not construct node IDs.",
        )

    # -- stage 4: grounded answering ------------------------------------ #

    def answer(self, background: str, question: str,
               provisions: Sequence[dict]) -> StageResult:
        """Answers from curated provisions only.

        The refined query is deliberately not a parameter of this method, so it
        cannot reach the answering prompt.
        """
        allowed = {p["node_id"] for p in provisions}
        prompt = config.prompt_text("grounded_answer").format(
            background=background or "(none)",
            question=question,
            provisions=render_provisions(provisions),
        )
        return self._parse_with_id_guard(
            prompt, GroundedAnswer, config.REASONING_EFFORT["final_answer"],
            allowed, lambda p: p.cited_node_ids, "final_answer",
            "cited node IDs are not in the curated evidence",
            "Cite only node_id values from the supplied provisions.",
        )
