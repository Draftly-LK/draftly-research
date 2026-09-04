from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CaseIndexStats:
    db_path: str
    fingerprint: str
    cases: int
    reused: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaseQuery:
    text: str
    limit: int = 8


@dataclass(frozen=True)
class CaseHit:
    case_id: str
    citation: str
    title: str
    court: str
    year: str
    url: str
    excerpt: str
    score: float
    matched_signals: tuple[str, ...] = ()
    text: str = ""

    def to_dict(self, include_text: bool = True) -> dict[str, Any]:
        data = asdict(self)
        data["matched_signals"] = list(self.matched_signals)
        if not include_text:
            data.pop("text", None)
        return data


@dataclass(frozen=True)
class SimilarCaseResult:
    query: str
    hits: tuple[CaseHit, ...]
    outcome: str  # "similar_cases_found" | "no_similar_cases"
    reason: str = ""
    corpus_fingerprint: str | None = None

    def to_dict(self, include_text: bool = False) -> dict[str, Any]:
        return {
            "query": self.query,
            "outcome": self.outcome,
            "reason": self.reason,
            "corpus_fingerprint": self.corpus_fingerprint,
            "hits": [hit.to_dict(include_text=include_text) for hit in self.hits],
        }


@dataclass(frozen=True)
class CaseDoc:
    case_id: str
    citation: str
    title: str
    court: str
    year: str
    url: str
    text: str
    text_sha256: str
    rule_statement: str = ""
    statute_links: tuple[tuple[str, str, str], ...] = ()  # (source_id, section_number, band)
    topic_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
