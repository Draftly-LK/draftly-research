"""OpenAI Responses API wrapper with structured outputs.

Three stages, each with its own reasoning effort and its own pydantic schema.
Nothing here parses free-form text, and nothing here reads the gold file.

Validation is the point of this module: a selection may only name candidates that
were supplied, and an answer may only cite provisions that were selected. A
violation triggers exactly one corrective retry; if it persists, the caller gets
a ValidationFailure to record rather than a fabricated result.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Sequence

import smoke_config as config
from schemas import GroundedAnswer, InformationNeeds, ProvisionSelection


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


def render_candidates(candidates: Sequence[dict]) -> str:
    """Candidates as node_id / citation / heading / text, one block each."""
    blocks = []
    for candidate in candidates:
        heading = candidate.get("heading") or "(no heading)"
        blocks.append(
            f"node_id: {candidate['node_id']}\n"
            f"citation: {candidate.get('citation') or ''}\n"
            f"heading: {heading}\n"
            f"text: {candidate.get('text') or ''}"
        )
    return "\n\n---\n\n".join(blocks)


class SmokeTestLLM:
    """The three LLM stages. `client` is injectable so tests can mock it."""

    def __init__(self, client=None, model: str | None = None):
        self._client = client if client is not None else build_client()
        self.model = model or config.model_name()

    # -- transport ------------------------------------------------------ #

    def _parse(self, prompt: str, schema, effort: str):
        response = self._client.responses.parse(
            model=self.model,
            input=prompt,
            text_format=schema,
            reasoning={"effort": effort},
        )
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise ValidationFailure(
                "transport", "model returned no parsed structured output")
        return parsed

    # -- stage 1: query generation -------------------------------------- #

    def generate_information_needs(
        self, background: str, question: str
    ) -> StageResult:
        prompt = config.prompt_text("query_generation").format(
            background=background or "(none)", question=question)
        parsed = self._parse(
            prompt, InformationNeeds, config.REASONING_EFFORT["query_generation"])
        return StageResult(parsed=parsed, attempts=1, prompt=prompt)

    # -- stage 2: provision selection ----------------------------------- #

    def select_provisions(
        self, background: str, question: str, candidates: Sequence[dict]
    ) -> StageResult:
        allowed = {c["node_id"] for c in candidates}
        base_prompt = config.prompt_text("provision_selection").format(
            background=background or "(none)",
            question=question,
            candidates=render_candidates(candidates),
        )
        prompt = base_prompt
        effort = config.REASONING_EFFORT["provision_selection"]

        for attempt in (1, 2):
            parsed = self._parse(prompt, ProvisionSelection, effort)
            invalid = [nid for nid in parsed.selected_node_ids if nid not in allowed]
            if not invalid:
                return StageResult(parsed=parsed, attempts=attempt, prompt=prompt)
            if attempt == 2:
                raise ValidationFailure(
                    "provision_selection",
                    "selected node IDs are not in the candidate set",
                    invalid,
                )
            prompt = (
                f"{base_prompt}\n\n## Correction\n\n"
                f"A previous attempt returned these node IDs, which are not in "
                f"the candidate list above: {json.dumps(invalid)}. "
                "Select only node_id values copied exactly from the candidate "
                "list. Do not construct node IDs."
            )
        raise AssertionError("unreachable")

    # -- stage 3: grounded answering ------------------------------------ #

    def answer(
        self, background: str, question: str, provisions: Sequence[dict]
    ) -> StageResult:
        """Answers from selected provisions only.

        The generated information needs are deliberately not a parameter of this
        method, so they cannot reach the answering prompt.
        """
        allowed = {p["node_id"] for p in provisions}
        base_prompt = config.prompt_text("grounded_answer").format(
            background=background or "(none)",
            question=question,
            provisions=render_candidates(provisions),
        )
        prompt = base_prompt
        effort = config.REASONING_EFFORT["final_answer"]

        for attempt in (1, 2):
            parsed = self._parse(prompt, GroundedAnswer, effort)
            invalid = [nid for nid in parsed.cited_node_ids if nid not in allowed]
            if not invalid:
                return StageResult(parsed=parsed, attempts=attempt, prompt=prompt)
            if attempt == 2:
                raise ValidationFailure(
                    "final_answer",
                    "cited node IDs are not in the selected evidence",
                    invalid,
                )
            prompt = (
                f"{base_prompt}\n\n## Correction\n\n"
                f"A previous attempt cited these node IDs, which are not among "
                f"the provisions supplied above: {json.dumps(invalid)}. "
                "Cite only node_id values from the supplied provisions."
            )
        raise AssertionError("unreachable")
