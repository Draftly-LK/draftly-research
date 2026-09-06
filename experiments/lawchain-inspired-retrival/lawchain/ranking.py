"""Stage 6: reciprocal-rank fusion across BM25/dense/graph channels, then a
Gemini LLM-as-judge rerank of the fused candidate pool.

Independent RRF implementation (own RRF_K constant, not imported from
src/draftly/retrieval/search.py).
"""

from __future__ import annotations

from collections import defaultdict

from .config import LLM_JUDGE_CANDIDATE_POOL, RRF_K
from .gemini_client import call_gemini_json
from .models import LawchainHit, LawchainSection

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "ranking": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section_id": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["section_id"],
            },
        }
    },
    "required": ["ranking"],
}

JUDGE_SYSTEM_INSTRUCTION = (
    "You are ranking candidate Sri Lankan statute sections by relevance to a legal "
    "question. Use only the provided section_ids -- never invent one. Return the "
    "best matches first."
)


def fuse(
    channel_hits: list[tuple[str, list[tuple[str, float]]]],
    sections_by_id: dict[str, LawchainSection],
    *,
    k: int = RRF_K,
    limit: int = LLM_JUDGE_CANDIDATE_POOL,
) -> list[LawchainHit]:
    rrf_scores: dict[str, float] = defaultdict(float)
    channel_scores: dict[str, dict[str, float]] = defaultdict(dict)

    for channel_name, ranked in channel_hits:
        for rank, (section_id, raw_score) in enumerate(ranked, start=1):
            rrf_scores[section_id] += 1.0 / (k + rank)
            channel_scores[section_id][channel_name] = raw_score

    ranked_ids = sorted(rrf_scores, key=lambda section_id: rrf_scores[section_id], reverse=True)[:limit]

    hits = []
    for section_id in ranked_ids:
        section = sections_by_id.get(section_id)
        if section is None:
            continue
        hits.append(
            LawchainHit(
                section_id=section_id,
                source_id=section.source_id,
                title=section.title,
                heading=section.heading,
                excerpt=section.text[:400],
                score=rrf_scores[section_id],
                channels=channel_scores[section_id],
            )
        )
    return hits


def llm_judge_rerank(question: str, candidates: list[LawchainHit], *, top_k: int = 5) -> list[LawchainHit]:
    """Reranks the top candidates via Gemini; on any failure or missing key,
    falls back to the RRF-fused order untouched -- never blocks on the LLM.
    """
    if not candidates:
        return []

    listing = "\n".join(
        f"{hit.section_id} | {hit.title} | {hit.heading} | {hit.excerpt[:200]}" for hit in candidates
    )
    prompt = f"Question: {question}\n\nCandidates:\n{listing}\n\nReturn the top {top_k} section_ids, best first."
    parsed, _, error = call_gemini_json(prompt=prompt, schema=JUDGE_SCHEMA, system_instruction=JUDGE_SYSTEM_INSTRUCTION)

    if error or not isinstance(parsed.get("ranking"), list):
        return candidates[:top_k]

    by_id = {hit.section_id: hit for hit in candidates}
    reranked: list[LawchainHit] = []
    seen: set[str] = set()
    for entry in parsed["ranking"]:
        section_id = str(entry.get("section_id", "")).strip()
        hit = by_id.get(section_id)
        if hit is None or section_id in seen:
            continue
        seen.add(section_id)
        hit.rationale = str(entry.get("rationale", ""))
        reranked.append(hit)
        if len(reranked) >= top_k:
            break

    return reranked if reranked else candidates[:top_k]
