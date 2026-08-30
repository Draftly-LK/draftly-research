"""Stage 4: bounded agentic query expansion.

Mirrors the *philosophy* of src/draftly/retrieval/answering.py's one bounded
corrective retry -- a cheap sufficiency check gates whether a second,
LLM-guided round of rewriting even happens -- without importing that module.
"""

from __future__ import annotations

from typing import Callable

from .config import MAX_EXPANSION_ROUNDS, SUFFICIENCY_MIN_HITS, SUFFICIENCY_SCORE_THRESHOLD
from .gemini_client import call_gemini_json
from .models import LawchainHit

REWRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "rewrites": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 4,
        }
    },
    "required": ["rewrites"],
}

SYSTEM_INSTRUCTION = (
    "You rewrite a lay legal question into 2-4 search queries using Sri Lankan "
    "statutory vocabulary (formal terms, section-style phrasing) likely to match "
    "text in consolidated Acts and Ordinances. Return only the requested JSON."
)


def _sufficiency_gate(hits: list[LawchainHit]) -> bool:
    return len(hits) >= SUFFICIENCY_MIN_HITS and bool(hits) and hits[0].score >= SUFFICIENCY_SCORE_THRESHOLD


def _propose_rewrites(question: str, *, weak_headings: list[str]) -> list[str]:
    context = f"\n\nEarlier weak results (headings): {'; '.join(weak_headings)}" if weak_headings else ""
    parsed, _, error = call_gemini_json(
        prompt=f"Lay question: {question}{context}",
        schema=REWRITE_SCHEMA,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    if error or not isinstance(parsed.get("rewrites"), list):
        return []
    return [str(item).strip() for item in parsed["rewrites"] if str(item).strip()]


def expand_query(question: str, *, retrieve_and_fuse: Callable[[list[str]], list[LawchainHit]]) -> list[LawchainHit]:
    """Runs a baseline retrieval, then up to MAX_EXPANSION_ROUNDS LLM-guided
    rewrite-and-retry rounds if the baseline (or a prior round) is weak.

    retrieve_and_fuse takes the current list of query strings (the original
    question plus any rewrites) and returns fused hits across BM25/dense/
    graph -- this function owns *when* to expand, not the fusion itself.
    """
    queries = [question]
    hits = retrieve_and_fuse(queries)

    for _ in range(MAX_EXPANSION_ROUNDS):
        if _sufficiency_gate(hits):
            break
        weak_headings = [hit.heading for hit in hits[:5] if hit.heading]
        rewrites = _propose_rewrites(question, weak_headings=weak_headings)
        if not rewrites:
            break
        queries = [question, *rewrites]
        hits = retrieve_and_fuse(queries)

    return hits
