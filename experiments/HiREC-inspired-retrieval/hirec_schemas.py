"""Structured-output schemas for the HiREC stages.

Bounds are enforced by model validators rather than Field(min_length=...) /
Field(max_length=...) on purpose: Field constraints emit minItems/maxItems into
the JSON schema, which OpenAI strict structured outputs rejects. A model
validator enforces the same rule at parse time while keeping the emitted schema
strict-compatible. All fields are required and have no defaults, as strict mode
requires.

The declaration order of EvidenceCuration is load-bearing, not cosmetic. Strict
structured outputs are generated autoregressively in field order, so the model
must emit the coverage table, the cross-reference list and the sibling
accounting before it can emit the completeness boolean. The comparable koblex
schema put its boolean second of three fields with nothing forcing analysis in
front of it, and it came back "complete" on all 20 questions including the three
where the evidence was not.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

MIN_SUB_QUESTIONS = 1
MAX_SUB_QUESTIONS = 5

# HiREC ships 10. Gold evidence sets here reach 9 provisions and pools reach 179
# records, so a threshold of 10 would fire the saturation hatch on nearly every
# question and silently decide the result.
MAX_RELEVANT_IDS = 25

COVERED = "covered"
PARTIALLY_COVERED = "partially_covered"
NOT_COVERED = "not_covered"
COVERAGE_STATUS = (COVERED, PARTIALLY_COVERED, NOT_COVERED)

MAX_ACTS = 18


class ActSelection(BaseModel):
    """The Acts worth retrieving from. The document stage of the hierarchy."""

    selected_act_ids: list[str] = Field(
        description=(
            "The act_id of every Act whose text could contain a rule needed to "
            "answer, most relevant first. Use only act_id values from the "
            "supplied list."))
    reasoning: str = Field(
        description=(
            "One or two sentences on why these Acts and not the others. Not "
            "used as evidence and never cited."))

    @model_validator(mode="after")
    def _bound_count(self) -> "ActSelection":
        if not 1 <= len(self.selected_act_ids) <= MAX_ACTS:
            raise ValueError(
                f"expected between 1 and {MAX_ACTS} acts, got "
                f"{len(self.selected_act_ids)}")
        if len(set(self.selected_act_ids)) != len(self.selected_act_ids):
            raise ValueError("act_id values must not repeat")
        return self


class RefinedQuery(BaseModel):
    """A retrieval query for evidence the pool is missing. Never evidence."""

    search_query: str = Field(
        description=(
            "A concise retrieval query using terminology likely to appear in "
            "legislation. No section numbers, no citations, no quoted statutory "
            "text."))
    targets: str = Field(
        description=(
            "One sentence naming the missing rule this query is meant to find. "
            "Describe the rule sought; do not state the rule itself."))


class SubQuestionCoverage(BaseModel):
    """One point the question requires, and what in the pool establishes it."""

    sub_question: str = Field(
        description=(
            "One thing that must be established to answer. Phrase it as a "
            "question about the law, not about the facts."))
    covering_node_ids: list[str] = Field(
        description=(
            "The pool node_id values whose text establishes this point. Copy "
            "them exactly. Empty when nothing in the pool establishes it."))
    status: str = Field(
        description=(
            "covered when the listed provisions fully establish the point; "
            "partially_covered when they establish only part of it; "
            "not_covered when nothing in the pool establishes it."))
    gap: str = Field(
        description=(
            "What is missing, in the terminology legislation uses. Empty "
            "string when the status is covered."))

    @model_validator(mode="after")
    def _check_status(self) -> "SubQuestionCoverage":
        if self.status not in COVERAGE_STATUS:
            raise ValueError(
                f"status must be one of {COVERAGE_STATUS}, got {self.status!r}")
        if self.status == NOT_COVERED and self.covering_node_ids:
            raise ValueError(
                "a not_covered point must not name covering provisions")
        if self.status == COVERED and not self.covering_node_ids:
            raise ValueError(
                "a covered point must name at least one covering provision")
        return self


class EvidenceCuration(BaseModel):
    """Filter, answerability, missing information and refinement, in one call.

    HiREC's evidence curator does all four in a single inference; that is the
    property being ported. What differs is that the analysis is a structured
    field rather than free text, and that completeness is derived from it by
    derive_completeness() rather than being taken on the model's word.
    """

    sub_questions: list[SubQuestionCoverage] = Field(
        description=(
            "The distinct legal points the question requires, one entry each, "
            "between one and five."))
    unresolved_cross_references: list[str] = Field(
        description=(
            "Provisions referred to by the text you selected that are not in "
            "the pool, for example 'section 47 of the same Act, referred to in "
            "s 12(2)'. Empty when the selected text is self-contained."))
    sibling_accounting: str = Field(
        description=(
            "Section by section over the sections you drew from: why the other "
            "subsections, paragraphs and provisos of that section shown in the "
            "pool are or are not needed."))
    relevant_node_ids: list[str] = Field(
        description=(
            "Every pool provision needed to answer the question. Use only "
            "node_id values copied exactly from the pool."))
    model_claimed_complete: bool = Field(
        description=(
            "True when the pool contains every rule the question needs. Decide "
            "this only after completing the coverage table above."))
    missing_evidence: list[str] = Field(
        description=(
            "Short descriptions of any rule that is needed but absent from the "
            "pool. Empty when nothing is missing."))
    refined_query: str = Field(
        description=(
            "A retrieval query in statutory terminology for the largest gap. "
            "Empty string when nothing is missing. Never a repeat of the "
            "original question or of a query already tried."))

    @model_validator(mode="after")
    def _bound_sub_questions(self) -> "EvidenceCuration":
        count = len(self.sub_questions)
        if not MIN_SUB_QUESTIONS <= count <= MAX_SUB_QUESTIONS:
            raise ValueError(
                f"expected between {MIN_SUB_QUESTIONS} and {MAX_SUB_QUESTIONS} "
                f"sub-questions, got {count}")
        return self

    @model_validator(mode="after")
    def _bound_relevant_ids(self) -> "EvidenceCuration":
        if len(self.relevant_node_ids) > MAX_RELEVANT_IDS:
            raise ValueError(
                f"at most {MAX_RELEVANT_IDS} relevant node IDs, got "
                f"{len(self.relevant_node_ids)}")
        if len(set(self.relevant_node_ids)) != len(self.relevant_node_ids):
            raise ValueError("relevant node IDs must not repeat")
        return self

    @model_validator(mode="after")
    def _consistency(self) -> "EvidenceCuration":
        """A claim of completeness and a stated gap cannot both stand.

        HiREC tolerates the combination: it parses the literal string "None" out
        of a hash-delimited blob and never cross-checks the fields. Enforcing it
        here turns a silent inconsistency into one corrective retry.
        """
        if self.model_claimed_complete:
            if self.missing_evidence or self.refined_query.strip():
                raise ValueError(
                    "model_claimed_complete is true, so missing_evidence must "
                    "be empty and refined_query must be an empty string")
        else:
            if not self.missing_evidence or not self.refined_query.strip():
                raise ValueError(
                    "model_claimed_complete is false, so missing_evidence and "
                    "refined_query must both be filled")
        return self


class GroundedAnswer(BaseModel):
    """The final answer, grounded only in the curated statutory provisions.

    Copied unchanged from the koblex experiment's schemas.py so the answering
    stage stays comparable to that experiment's b1 run.
    """

    answerable: bool = Field(
        description=(
            "True when the selected provisions are sufficient to answer. False "
            "means abstain rather than answer from outside knowledge."))
    answer: str = Field(
        description=(
            "The answer in English: state the statutory rule, then apply it to "
            "the facts. Show arithmetic explicitly for calculation questions. "
            "Empty string when answerable is false."))
    cited_node_ids: list[str] = Field(
        description=(
            "The node_id values supporting the answer. Every one must come from "
            "the supplied provisions, and each must genuinely support a claim "
            "made in the answer."))
    missing_evidence: list[str] = Field(
        description=(
            "When answerable is false, what evidence would be required. Empty "
            "otherwise."))


# --------------------------------------------------------------------------- #
# derived signals
# --------------------------------------------------------------------------- #

def derive_completeness(curation: EvidenceCuration) -> bool:
    """Completeness as an arithmetic consequence of the coverage table.

    The model's own boolean is kept alongside this rather than replaced, because
    the disagreement between the two is the measurement of interest.
    """
    return (all(sq.status == COVERED for sq in curation.sub_questions)
            and not curation.unresolved_cross_references)


def apply_saturation_hatch(complete: bool, relevant_ids, max_relevant_ids: int
                           ) -> tuple[bool, bool]:
    """HiREC's saturation guard. Returns (evidence_complete, forced).

    Faithful to finrag's
        if not is_answerable and len(ids) >= max_relevant_ids: is_answerable = True
    An incomplete verdict that nonetheless marks the maximum number of
    provisions relevant is treated as saturated: there is no room to add more,
    so iterating again cannot help.
    """
    if complete:
        return True, False
    if len(relevant_ids) >= max_relevant_ids:
        return True, True
    return False, False
