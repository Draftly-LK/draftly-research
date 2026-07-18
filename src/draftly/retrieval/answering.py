from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

from .models import AnswerClaim, StatuteAnswer, StatuteHit, StatuteQuery
from .search import search

DEFAULT_MODEL = "gemini-3.5-flash"
MAX_EVIDENCE_SECTIONS = 6
MAX_EVIDENCE_CHARS = 16_000


def answer(query: StatuteQuery | str) -> StatuteAnswer:
    if isinstance(query, str):
        query = StatuteQuery(text=query)
    hits = tuple(search(query))
    if not hits:
        return StatuteAnswer(question=query.text, hits=hits, fallback_reason="no_evidence")

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("DRAFTLY_GEMINI_MODEL", DEFAULT_MODEL)
    if not api_key:
        return StatuteAnswer(question=query.text, hits=hits, fallback_reason="missing_gemini_api_key", model=model)

    prompt = build_prompt(query.text, hits)
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
        raw = getattr(response, "text", "") or ""
    except Exception as exc:  # pragma: no cover - network/API defensive path
        return StatuteAnswer(
            question=query.text,
            hits=hits,
            fallback_reason="gemini_api_error",
            model=model,
            invalid_reason=str(exc),
        )

    parsed, invalid_reason = parse_model_json(raw)
    if invalid_reason:
        return StatuteAnswer(
            question=query.text,
            hits=hits,
            fallback_reason="invalid_generated_answer",
            model=model,
            raw_response=raw,
            invalid_reason=invalid_reason,
        )

    validation_error = validate_answer_payload(parsed, {hit.section_id for hit in hits})
    if validation_error:
        return StatuteAnswer(
            question=query.text,
            hits=hits,
            fallback_reason="invalid_generated_answer",
            model=model,
            raw_response=raw,
            invalid_reason=validation_error,
        )

    claims = tuple(
        AnswerClaim(text=claim["text"].strip(), citations=tuple(citation.upper() for citation in claim["citations"]))
        for claim in parsed.get("claims", [])
    )
    limitations = tuple(str(item).strip() for item in parsed.get("limitations", []) if str(item).strip())
    return StatuteAnswer(
        question=query.text,
        hits=hits,
        claims=claims,
        limitations=limitations,
        abstained=bool(parsed.get("abstained", False)),
        model=model,
        raw_response=raw,
    )


def build_prompt(question: str, hits: tuple[StatuteHit, ...]) -> str:
    chunks: list[str] = []
    budget = MAX_EVIDENCE_CHARS
    for hit in hits[:MAX_EVIDENCE_SECTIONS]:
        text = hit.text.strip()
        if not text or budget <= 0:
            break
        excerpt = text[: min(len(text), budget)]
        budget -= len(excerpt)
        chunks.append(
            "\n".join(
                [
                    f"ID: {hit.section_id}",
                    f"TYPE: {hit.document_type}",
                    f"TITLE: {hit.title}",
                    f"YEAR: {hit.year}",
                    f"HEADING: {hit.heading}",
                    "TEXT:",
                    excerpt,
                ]
            )
        )

    evidence = "\n\n---\n\n".join(chunks)
    return f"""You are Draftly's statutes-only retrieval assistant.

Answer using only the retrieved Sri Lankan statute and amendment sections below.
Do not use case law, external legal knowledge, historical validity reasoning, or uncited assertions.
Do not say that a law is currently in force. The corpus is a working retrieval copy only.
Display amendments separately from base statutes when relevant.
If the retrieved evidence is insufficient, set "abstained": true and explain the limitation.

Return only valid JSON in exactly this shape:
{{
  "abstained": false,
  "claims": [
    {{"text": "One answer claim.", "citations": ["SRC001:s2"]}}
  ],
  "limitations": []
}}

Question:
{question}

Retrieved evidence:
{evidence}
"""


def parse_model_json(raw: str) -> tuple[dict[str, Any], str | None]:
    cleaned = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return {}, f"malformed_json: {exc}"
    if not isinstance(parsed, dict):
        return {}, "json_root_not_object"
    return parsed, None


def validate_answer_payload(payload: dict[str, Any], allowed_citations: set[str]) -> str | None:
    if "abstained" not in payload or not isinstance(payload["abstained"], bool):
        return "missing_or_invalid_abstained"
    claims = payload.get("claims", [])
    limitations = payload.get("limitations", [])
    if not isinstance(claims, list):
        return "claims_not_list"
    if not isinstance(limitations, list):
        return "limitations_not_list"
    if payload["abstained"] and not claims:
        return None
    if not claims:
        return "no_claims"

    allowed_upper = {citation.upper() for citation in allowed_citations}
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            return f"claim_{index}_not_object"
        if not str(claim.get("text", "")).strip():
            return f"claim_{index}_missing_text"
        citations = claim.get("citations", [])
        if not isinstance(citations, list) or not citations:
            return f"claim_{index}_missing_citations"
        for citation in citations:
            normalized = str(citation).upper()
            if normalized not in allowed_upper:
                return f"claim_{index}_unknown_citation:{citation}"
            if ":S" not in normalized:
                return f"claim_{index}_non_section_citation:{citation}"
    return None

