from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class IndexStats:
    db_path: str
    fingerprint: str
    documents: int
    statutes: int
    amendments: int
    sections: int
    fallbacks: int
    reused: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StatuteQuery:
    text: str
    topic_slug: str | None = None
    kinds: tuple[str, ...] | None = None
    source_id: str | None = None
    limit: int = 8


@dataclass(frozen=True)
class StatuteHit:
    source_id: str
    section_id: str
    title: str
    act_number: str
    year: str
    document_type: str
    topics: tuple[str, ...]
    heading: str
    excerpt: str
    score: float
    public_source_url: str
    extraction_confidence: str
    text: str = ""
    matched_queries: tuple[str, ...] = ()
    citation_note: str = ""
    target_section: str = ""

    def to_dict(self, include_text: bool = True) -> dict[str, Any]:
        data = asdict(self)
        data["topics"] = list(self.topics)
        data["matched_queries"] = list(self.matched_queries)
        if not include_text:
            data.pop("text", None)
        return data


@dataclass(frozen=True)
class AnswerClaim:
    text: str
    citations: tuple[str, ...]
    part: str = ""
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "part": self.part,
            "text": self.text,
            "citations": list(self.citations),
            "verified": self.verified,
        }


@dataclass(frozen=True)
class StatuteAnswer:
    question: str
    hits: tuple[StatuteHit, ...]
    claims: tuple[AnswerClaim, ...] = ()
    limitations: tuple[str, ...] = ()
    abstained: bool = False
    fallback_reason: str | None = None
    model: str | None = None
    raw_response: str | None = None
    invalid_reason: str | None = None
    outcome: str = "abstained"
    missing_information: tuple[str, ...] = ()
    retrieval_queries: tuple[str, ...] = ()
    corpus_fingerprint: str | None = None
    trace_id: str | None = None
    verifier_model: str | None = None

    @property
    def is_generated(self) -> bool:
        return bool(self.claims) and self.outcome in {"answered", "partial"} and not self.fallback_reason

    def to_dict(self, include_raw: bool = False) -> dict[str, Any]:
        data = {
            "question": self.question,
            "outcome": self.outcome,
            "abstained": self.abstained,
            "fallback_reason": self.fallback_reason,
            "invalid_reason": self.invalid_reason,
            "model": self.model,
            "claims": [claim.to_dict() for claim in self.claims],
            "limitations": list(self.limitations),
            "missing_information": list(self.missing_information),
            "retrieval_queries": list(self.retrieval_queries),
            "corpus_fingerprint": self.corpus_fingerprint,
            "trace_id": self.trace_id,
            "verifier_model": self.verifier_model,
            "hits": [hit.to_dict(include_text=False) for hit in self.hits],
        }
        if include_raw:
            data["raw_response"] = self.raw_response
        return data


@dataclass(frozen=True)
class SectionNode:
    section_id: str
    source_id: str
    doc_id: str
    kind: str
    title: str
    act_number: str
    year: str
    topics: tuple[str, ...]
    heading: str
    text: str
    public_source_url: str
    extraction_confidence: str
    source_sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)
