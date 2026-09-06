from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LawchainSection:
    section_id: str
    source_id: str
    title: str
    number: str
    heading: str
    text: str
    cross_references: list[dict] = field(default_factory=list)
    amendment_events: list[dict] = field(default_factory=list)


@dataclass
class LawchainHit:
    section_id: str
    source_id: str
    title: str
    heading: str
    excerpt: str
    score: float
    channels: dict[str, float] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "section_id": self.section_id,
            "source_id": self.source_id,
            "title": self.title,
            "heading": self.heading,
            "excerpt": self.excerpt,
            "score": self.score,
            "channels": self.channels,
            "rationale": self.rationale,
        }


@dataclass
class LawchainClaim:
    text: str
    section_id: str


@dataclass
class LawchainAnswer:
    question: str
    claims: list[LawchainClaim]
    hits: list[LawchainHit]

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "claims": [{"text": claim.text, "section_id": claim.section_id} for claim in self.claims],
            "hits": [hit.to_dict() for hit in self.hits],
        }
