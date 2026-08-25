"""Structured-output schemas for the three LLM stages.

The 1-3 bound on information needs is enforced by a model validator rather than
Field(min_length=..., max_length=...) on purpose: Field constraints emit
minItems/maxItems into the JSON schema, which OpenAI strict structured outputs
rejects. A model validator enforces the same rule at parse time while keeping the
emitted schema strict-compatible.

All fields are required and have no defaults, as strict mode requires.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

MIN_INFORMATION_NEEDS = 1
MAX_INFORMATION_NEEDS = 3


class InformationNeed(BaseModel):
    """One distinct statutory rule that must be found to answer the question."""

    id: str = Field(
        description="Stable identifier for this information need, such as 'need-1'.")
    purpose: str = Field(
        description=(
            "One English sentence naming the legal rule this query is meant to "
            "find. Describe the rule sought; do not state the rule itself and do "
            "not answer the question."))
    search_query: str = Field(
        description=(
            "A concise retrieval query using terminology likely to appear in "
            "legislation. No section numbers, no citations, no quoted statutory "
            "text."))


class InformationNeeds(BaseModel):
    """Between one and three retrieval hypotheses. Never statutory evidence."""

    information_needs: list[InformationNeed] = Field(
        description=(
            "One to three distinct information needs, one per separate legal "
            "issue raised by the question."))

    @model_validator(mode="after")
    def _bound_count(self) -> "InformationNeeds":
        count = len(self.information_needs)
        if not MIN_INFORMATION_NEEDS <= count <= MAX_INFORMATION_NEEDS:
            raise ValueError(
                f"expected between {MIN_INFORMATION_NEEDS} and "
                f"{MAX_INFORMATION_NEEDS} information needs, got {count}")
        return self

    def search_queries(self) -> list[str]:
        return [need.search_query for need in self.information_needs]


class ProvisionSelection(BaseModel):
    """The candidate provisions the model judges necessary to answer."""

    selected_node_ids: list[str] = Field(
        description=(
            "Every candidate node_id required to answer the question. Use only "
            "node_id values that appear in the supplied candidate list."))
    evidence_complete: bool = Field(
        description=(
            "True when the supplied candidates contain every rule needed to "
            "answer the question; false when something necessary is absent."))
    missing_evidence: list[str] = Field(
        description=(
            "Short English descriptions of any rule that is needed but absent "
            "from the candidates. Empty when evidence_complete is true."))


class GroundedAnswer(BaseModel):
    """The final answer, grounded only in the selected statutory provisions."""

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
