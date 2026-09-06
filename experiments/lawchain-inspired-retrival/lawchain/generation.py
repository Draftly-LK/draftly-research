"""Stage 7: Gemini RAG summarization citing top sections.

Independent citation-discipline reimplementation -- same philosophy as
src/draftly/retrieval/answering.py (every claim must cite provided evidence),
not imported. Any claim citing a section_id outside the evidence set is
dropped, not trusted.
"""

from __future__ import annotations

from .gemini_client import call_gemini_json
from .models import LawchainAnswer, LawchainClaim, LawchainHit

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "section_id": {"type": "string"},
                },
                "required": ["text", "section_id"],
            },
        }
    },
    "required": ["claims"],
}

SYSTEM_INSTRUCTION = (
    "You answer Sri Lankan statutory-law questions using ONLY the provided evidence "
    "sections. Every claim must cite exactly one section_id drawn from the evidence. "
    "If the evidence is insufficient, return an empty claims list rather than guessing."
)


def summarize(question: str, hits: list[LawchainHit]) -> LawchainAnswer:
    if not hits:
        return LawchainAnswer(question=question, claims=[], hits=[])

    evidence = "\n\n".join(f"[{hit.section_id}] {hit.title} - {hit.heading}\n{hit.excerpt}" for hit in hits)
    parsed, _, error = call_gemini_json(
        prompt=f"Question: {question}\n\nEvidence:\n{evidence}",
        schema=ANSWER_SCHEMA,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    valid_section_ids = {hit.section_id for hit in hits}
    claims: list[LawchainClaim] = []
    if not error and isinstance(parsed.get("claims"), list):
        for entry in parsed["claims"]:
            section_id = str(entry.get("section_id", "")).strip()
            text = str(entry.get("text", "")).strip()
            if text and section_id in valid_section_ids:
                claims.append(LawchainClaim(text=text, section_id=section_id))

    return LawchainAnswer(question=question, claims=claims, hits=hits)
