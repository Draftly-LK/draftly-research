from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any

from dotenv import load_dotenv

from .index import build_index
from .models import AnswerClaim, StatuteAnswer, StatuteHit, StatuteQuery
from .question_analysis import analyze_question, is_supported_domain_question, known_corpus_gaps
from .search import search

DEFAULT_MODEL = "gemini-3.5-flash"
MAX_EVIDENCE_SECTIONS = 12
MAX_EVIDENCE_CHARS = 34_000
DEFAULT_GEMINI_TIMEOUT_MS = 90_000
PER_PART_EVIDENCE_QUOTA = 2
MAX_CORRECTIVE_PARTS = 3

REWRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "rewrites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "part": {"type": "string"},
                    "queries": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["part", "queries"],
            },
        }
    },
    "required": ["rewrites"],
}

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["answered", "partial", "abstained"]},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "part": {"type": "string"},
                    "text": {"type": "string"},
                    "citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["part", "text", "citations"],
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["outcome", "claims", "limitations", "missing_information"],
}

VERIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_index": {"type": "integer"},
                    "supported": {"type": "boolean"},
                    "answers_part": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["claim_index", "supported", "answers_part", "reason"],
            },
        }
    },
    "required": ["verdicts"],
}


def answer(query: StatuteQuery | str) -> StatuteAnswer:
    if isinstance(query, str):
        query = StatuteQuery(text=query)

    trace_id = uuid.uuid4().hex[:16]
    stats = build_index(force=False)
    analysis = analyze_question(query.text)
    known_gaps = known_corpus_gaps(query.text)
    hits = tuple(search(query))
    retrieval_queries = tuple(
        dict.fromkeys(item for hit in hits for item in hit.matched_queries)
    ) or (query.text.strip(),)

    blocked_by_gap = bool(known_gaps and not analysis.source_hints)
    if not hits or not is_supported_domain_question(query.text) or blocked_by_gap:
        return StatuteAnswer(
            question=query.text,
            hits=() if blocked_by_gap else hits,
            abstained=True,
            fallback_reason="known_corpus_gap" if blocked_by_gap else "no_evidence",
            outcome="insufficient_authority",
            missing_information=known_gaps
            or ("No relevant provision was found in the statutes-and-amendments corpus.",),
            retrieval_queries=retrieval_queries,
            corpus_fingerprint=stats.fingerprint,
            trace_id=trace_id,
        )

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("DRAFTLY_GEMINI_MODEL", DEFAULT_MODEL)
    if not api_key:
        return evidence_only_answer(
            query=query,
            hits=hits,
            model=model,
            reason="missing_gemini_api_key",
            trace_id=trace_id,
            fingerprint=stats.fingerprint,
            retrieval_queries=retrieval_queries,
        )

    allocated_hits = allocate_evidence(hits, analysis)
    prompt, prompt_citations = build_prompt(query.text, allocated_hits, retrieval_queries, known_gaps)
    parsed, raw, api_error = generate_json(
        api_key=api_key,
        model=model,
        prompt=prompt,
        schema=ANSWER_SCHEMA,
        system_instruction=(
            "You are a bounded Sri Lankan statutes-only research assistant. "
            "Use only supplied evidence and facts stated in the question."
        ),
    )
    if api_error:
        return evidence_only_answer(
            query=query,
            hits=hits,
            model=model,
            reason="gemini_api_error",
            invalid_reason=api_error,
            raw_response=raw,
            trace_id=trace_id,
            fingerprint=stats.fingerprint,
            retrieval_queries=retrieval_queries,
        )

    parsed, dropped_claims = sanitize_answer_payload(parsed, prompt_citations)
    validation_error = validate_answer_payload(parsed, prompt_citations)
    if validation_error:
        return evidence_only_answer(
            query=query,
            hits=hits,
            model=model,
            reason="invalid_generated_answer",
            invalid_reason=validation_error,
            raw_response=raw,
            trace_id=trace_id,
            fingerprint=stats.fingerprint,
            retrieval_queries=retrieval_queries,
        )

    canonical_citations = {hit.section_id.upper(): hit.section_id for hit in hits}
    valid_parts = {str(item.number) for item in analysis.subquestions}
    claims = [
        AnswerClaim(
            part=(
                str(claim.get("part", "")).strip()
                if analysis.subquestions
                else "1"
            ),
            text=claim["text"].strip(),
            citations=tuple(canonical_citations[str(citation).upper()] for citation in claim["citations"]),
        )
        for claim in parsed.get("claims", [])
        if not valid_parts or str(claim.get("part", "")).strip() in valid_parts
    ]
    limitations = [str(item).strip() for item in parsed.get("limitations", []) if str(item).strip()]
    limitations.extend(dropped_claims)
    missing = [str(item).strip() for item in parsed.get("missing_information", []) if str(item).strip()]
    missing.extend(known_gaps)
    verifier_error = None
    if claims and os.getenv("DRAFTLY_SKIP_ANSWER_VERIFIER", "0") != "1":
        claims, rejected, verifier_error = verify_claims(api_key, model, query.text, claims, hits)
        limitations.extend(rejected)
    else:
        claims = [
            AnswerClaim(text=claim.text, citations=claim.citations, part=claim.part, verified=False)
            for claim in claims
        ]

    if verifier_error:
        return evidence_only_answer(
            query=query,
            hits=hits,
            model=model,
            reason="claim_verifier_error",
            invalid_reason=verifier_error,
            raw_response=raw,
            trace_id=trace_id,
            fingerprint=stats.fingerprint,
            retrieval_queries=retrieval_queries,
        )

    # Corrective retrieval (CRAG-style): a part that ended up with no verified
    # claim gets ONE targeted retry — the model restates the part in statutory
    # vocabulary, retrieval reruns on the restatements, and generation +
    # verification rerun for the missing parts only. Bounded and gated by the
    # same citation/verification pipeline as the first pass.
    if (
        valid_parts
        and os.getenv("DRAFTLY_SKIP_CORRECTIVE", "0") != "1"
        and (missing_part_numbers := sorted(valid_parts - {claim.part for claim in claims}, key=int))
    ):
        extra_claims, extra_hits, extra_queries, retry_notes = corrective_retry(
            api_key=api_key,
            model=model,
            question=query.text,
            analysis=analysis,
            missing_parts=missing_part_numbers[:MAX_CORRECTIVE_PARTS],
            known_hits=hits,
        )
        claims.extend(extra_claims)
        limitations.extend(retry_notes)
        if extra_hits:
            seen_ids = {hit.section_id for hit in hits}
            hits = hits + tuple(hit for hit in extra_hits if hit.section_id not in seen_ids)
        if extra_queries:
            retrieval_queries = tuple(dict.fromkeys(retrieval_queries + extra_queries))

    if valid_parts:
        covered_parts = {claim.part for claim in claims}
        for part in sorted(valid_parts - covered_parts, key=int):
            missing.append(f"No machine-verified claim was produced for part {part}.")

    requested_outcome = str(parsed.get("outcome", "abstained"))
    if not claims:
        outcome = "insufficient_authority"
        abstained = True
    elif requested_outcome == "partial" or missing or limitations:
        outcome = "partial"
        abstained = False
    else:
        outcome = "answered"
        abstained = False

    return StatuteAnswer(
        question=query.text,
        hits=hits,
        claims=tuple(claims),
        limitations=tuple(dict.fromkeys(limitations)),
        missing_information=tuple(dict.fromkeys(missing)),
        abstained=abstained,
        outcome=outcome,
        model=model,
        verifier_model=model if claims else None,
        raw_response=raw,
        retrieval_queries=retrieval_queries,
        corpus_fingerprint=stats.fingerprint,
        trace_id=trace_id,
    )


def evidence_only_answer(
    *,
    query: StatuteQuery,
    hits: tuple[StatuteHit, ...],
    model: str,
    reason: str,
    trace_id: str,
    fingerprint: str,
    retrieval_queries: tuple[str, ...],
    invalid_reason: str | None = None,
    raw_response: str | None = None,
) -> StatuteAnswer:
    return StatuteAnswer(
        question=query.text,
        hits=hits,
        fallback_reason=reason,
        invalid_reason=invalid_reason,
        model=model,
        raw_response=raw_response,
        outcome="evidence_only",
        abstained=True,
        limitations=("No generated legal conclusion is shown; review the retrieved provisions directly.",),
        retrieval_queries=retrieval_queries,
        corpus_fingerprint=fingerprint,
        trace_id=trace_id,
    )


def generate_json(
    *,
    api_key: str,
    model: str,
    prompt: str,
    schema: dict[str, Any],
    system_instruction: str,
) -> tuple[dict[str, Any], str, str | None]:
    try:
        from google import genai
        from google.genai import types

        timeout_ms = int(os.getenv("DRAFTLY_GEMINI_TIMEOUT_MS", str(DEFAULT_GEMINI_TIMEOUT_MS)))
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_json_schema=schema,
            ),
        )
        raw = getattr(response, "text", "") or ""
    except Exception as exc:  # pragma: no cover - network/API defensive path
        return {}, "", str(exc)

    parsed, parse_error = parse_model_json(raw)
    return parsed, raw, parse_error


def verify_claims(
    api_key: str,
    model: str,
    question: str,
    claims: list[AnswerClaim],
    hits: tuple[StatuteHit, ...],
) -> tuple[list[AnswerClaim], list[str], str | None]:
    evidence_by_id = {hit.section_id.upper(): hit for hit in hits}
    claim_rows = []
    evidence_ids: set[str] = set()
    for index, claim in enumerate(claims):
        claim_rows.append(
            {"claim_index": index, "text": claim.text, "citations": list(claim.citations)}
        )
        evidence_ids.update(citation.upper() for citation in claim.citations)

    evidence = [
        {
            "id": evidence_by_id[section_id].section_id,
            "title": evidence_by_id[section_id].title,
            "text": evidence_by_id[section_id].text,
        }
        for section_id in sorted(evidence_ids)
        if section_id in evidence_by_id
    ]
    verifier_prompt = (
        "Check two things for every claim: (1) whether it is directly supported by its cited statutory text "
        "together with facts explicitly stated in the question, and (2) whether it actually answers the "
        "identified question part without overgeneralizing a narrow provision. Arithmetic and direct "
        "application are allowed only when all premises and governing rates or succession rules are present. "
        "Mark unsupported if the text merely mentions the topic, belongs to another speaker/source, "
        "requires an unstated exception, or does not support the full claim. Return one verdict per claim.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CLAIMS:\n{json.dumps(claim_rows, ensure_ascii=False)}\n\n"
        f"CITED EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False)}"
    )
    parsed, _, error = generate_json(
        api_key=api_key,
        model=model,
        prompt=verifier_prompt,
        schema=VERIFIER_SCHEMA,
        system_instruction="You are a strict claim-to-citation entailment checker.",
    )
    if error:
        return [], [], error

    verdicts = parsed.get("verdicts")
    if not isinstance(verdicts, list):
        return [], [], "verifier_verdicts_not_list"
    by_index: dict[int, dict[str, Any]] = {}
    for verdict in verdicts:
        if not isinstance(verdict, dict) or not isinstance(verdict.get("claim_index"), int):
            return [], [], "invalid_verifier_verdict"
        by_index[verdict["claim_index"]] = verdict
    if set(by_index) != set(range(len(claims))):
        return [], [], "verifier_claim_coverage_mismatch"

    accepted: list[AnswerClaim] = []
    rejected: list[str] = []
    for index, claim in enumerate(claims):
        verdict = by_index[index]
        if verdict.get("supported") is True and verdict.get("answers_part") is True:
            accepted.append(
                AnswerClaim(text=claim.text, citations=claim.citations, part=claim.part, verified=True)
            )
        else:
            reason = str(verdict.get("reason", "citation did not support the claim")).strip()
            rejected.append(f"Part {claim.part or index + 1}: omitted an unsupported draft claim ({reason}).")
    return accepted, rejected, None


def build_prompt(
    question: str,
    hits: tuple[StatuteHit, ...],
    retrieval_queries: tuple[str, ...],
    known_gaps: tuple[str, ...] = (),
) -> tuple[str, set[str]]:
    chunks: list[str] = []
    included: set[str] = set()
    budget = MAX_EVIDENCE_CHARS
    for hit in hits[:MAX_EVIDENCE_SECTIONS]:
        if hit.extraction_confidence == "interleaved_columns":
            continue
        text = hit.text.strip()
        if not text or budget <= 0:
            break
        candidate = text if len(text) <= 4_500 else hit.excerpt
        excerpt = candidate[: min(len(candidate), budget, 4_500)]
        budget -= len(excerpt)
        included.add(hit.section_id)
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
    query_plan = "\n".join(f"- {item}" for item in retrieval_queries)
    gaps = "\n".join(f"- {item}" for item in known_gaps) or "- None detected from the corpus inventory."
    return f"""Answer the question from the supplied Sri Lankan statute and amendment sections only.

Rules:
- Treat each numbered subquestion as a separate part and identify it in the `part` field.
- Every legal or procedural claim must cite at least one supplied section ID.
- Facts stated in the question may be used for reasoning, but do not invent missing facts.
- Do not use case law, textbooks, drafting customs, external knowledge, or historical-validity assumptions.
- Do not claim that a provision is currently in force.
- Keep base-statute and amendment effects distinguishable.
- If a calculation rate, schedule, provincial rule, drafting model, or authority is missing, name it in `missing_information`.
- Never calculate inheritance shares or state a final pedigree unless the cited evidence contains every governing succession rule used in the calculation.
- Use `partial` when some parts are supportable and `abstained` when no reliable answer is supportable.
- Prefer concise exam-style claims; do not add generic legal disclaimers as answer content.

Retrieval plan:
{query_plan}

Known corpus limitations:
{gaps}

Question:
{question}

Retrieved evidence:
{evidence}
""", included


def allocate_evidence(hits: tuple[StatuteHit, ...], analysis) -> tuple[StatuteHit, ...]:
    """Reorder hits so every question part gets evidence representation.

    With a single global top-k, a 5-part question loses its later parts' evidence
    to the dominant topic. Guarantee each part's best PER_PART_EVIDENCE_QUOTA
    hits a slot (matched via the part's subquery), then fill remaining slots in
    fused order.
    """
    if not analysis.subquestions or len(analysis.subquestions) < 2:
        return hits
    pairs = list(zip(analysis.subquestions, analysis.subqueries))
    selected: list[StatuteHit] = []
    chosen: set[str] = set()
    for _, subquery in pairs:
        quota = PER_PART_EVIDENCE_QUOTA
        for hit in hits:
            if quota <= 0:
                break
            if hit.section_id in chosen or subquery not in hit.matched_queries:
                continue
            selected.append(hit)
            chosen.add(hit.section_id)
            quota -= 1
    for hit in hits:
        if hit.section_id not in chosen:
            selected.append(hit)
            chosen.add(hit.section_id)
    return tuple(selected)


def corrective_retry(
    *,
    api_key: str,
    model: str,
    question: str,
    analysis,
    missing_parts: list[str],
    known_hits: tuple[StatuteHit, ...],
) -> tuple[list[AnswerClaim], list[StatuteHit], tuple[str, ...], list[str]]:
    """One bounded retry for parts that produced no verified claim.

    Mechanism (see papers/qa-agent/notes-*.md): restate the failed part in
    statutory vocabulary (query rewriting bridges the fact-pattern-to-statute
    gap), re-retrieve on the restatements, regenerate for the missing parts
    only, then run the SAME citation gate + entailment verifier. Failure is
    still an honest miss — never a relaxation of grounding.
    """
    parts_by_number = {str(part.number): part for part in analysis.subquestions}
    targets = [(number, parts_by_number[number]) for number in missing_parts if number in parts_by_number]
    if not targets:
        return [], [], (), []

    rewrite_prompt = (
        "Restate each exam-question part as 2 short search queries over Sri Lankan "
        "conveyancing statutes. Use statutory vocabulary (the words an Act would use: "
        "'instrument', 'attestation', 'proviso', 'prescribed period') rather than the "
        "narrative facts. Do not answer the question.\n\n"
        + "\n\n".join(f"PART {number}:\n{part.text[:700]}" for number, part in targets)
    )
    parsed, _, error = generate_json(
        api_key=api_key,
        model=model,
        prompt=rewrite_prompt,
        schema=REWRITE_SCHEMA,
        system_instruction="You rewrite legal exam questions into statute-search queries.",
    )
    if error or not isinstance(parsed.get("rewrites"), list):
        return [], [], (), [f"Part {number}: corrective query rewrite failed." for number, _ in targets]

    rewrites: dict[str, list[str]] = {}
    for row in parsed["rewrites"]:
        if isinstance(row, dict) and isinstance(row.get("queries"), list):
            number = str(row.get("part", "")).strip()
            rewrites[number] = [str(item).strip() for item in row["queries"] if str(item).strip()][:2]

    new_hits: list[StatuteHit] = []
    used_queries: list[str] = []
    evidence_by_part: dict[str, list[StatuteHit]] = {}
    known_ids = {hit.section_id for hit in known_hits}
    for number, part in targets:
        part_hits: list[StatuteHit] = []
        for rewritten in rewrites.get(number, []):
            used_queries.append(rewritten)
            try:
                found = search(StatuteQuery(text=rewritten, limit=6))
            except Exception:
                continue
            for hit in found:
                if hit.section_id not in {item.section_id for item in part_hits}:
                    part_hits.append(hit)
        evidence_by_part[number] = part_hits[:5]
        for hit in part_hits[:5]:
            if hit.section_id not in known_ids:
                new_hits.append(hit)
                known_ids.add(hit.section_id)

    combined: dict[str, StatuteHit] = {hit.section_id: hit for hit in known_hits}
    for hit in new_hits:
        combined[hit.section_id] = hit
    retry_evidence = tuple(
        dict.fromkeys(
            [hit for hits_ in evidence_by_part.values() for hit in hits_]
            + list(known_hits)[:4]
        )
    )
    if not retry_evidence:
        return [], [], tuple(used_queries), [
            f"Part {number}: corrective retrieval found no additional authority." for number, _ in targets
        ]

    parts_block = "\n\n".join(f"{number}. {part.text}" for number, part in targets)
    focused_question = (
        f"{question.split(chr(10), 1)[0][:600]}\n\n"
        f"Answer ONLY these previously unanswered parts:\n{parts_block}"
    )
    prompt, prompt_citations = build_prompt(focused_question, retry_evidence, tuple(used_queries))
    parsed, _, error = generate_json(
        api_key=api_key,
        model=model,
        prompt=prompt,
        schema=ANSWER_SCHEMA,
        system_instruction=(
            "You are a bounded Sri Lankan statutes-only research assistant. "
            "Use only supplied evidence and facts stated in the question."
        ),
    )
    if error:
        return [], new_hits, tuple(used_queries), [
            f"Part {number}: corrective generation failed." for number, _ in targets
        ]
    parsed, _ = sanitize_answer_payload(parsed, prompt_citations)
    canonical = {hit.section_id.upper(): hit.section_id for hit in retry_evidence}
    wanted = {number for number, _ in targets}
    candidate_claims = [
        AnswerClaim(
            part=str(claim.get("part", "")).strip(),
            text=str(claim["text"]).strip(),
            citations=tuple(canonical[str(cite).upper()] for cite in claim["citations"]),
        )
        for claim in parsed.get("claims", [])
        if str(claim.get("part", "")).strip() in wanted and claim.get("citations")
    ]
    if not candidate_claims:
        return [], new_hits, tuple(used_queries), []
    accepted, _, verifier_error = verify_claims(
        api_key, model, question, candidate_claims, retry_evidence
    )
    if verifier_error:
        return [], new_hits, tuple(used_queries), []
    notes = [
        f"Part {number}: answered on a corrective retrieval pass."
        for number in sorted({claim.part for claim in accepted}, key=int)
    ]
    return accepted, new_hits, tuple(used_queries), notes


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


def sanitize_answer_payload(
    payload: dict[str, Any],
    allowed_citations: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Canonicalize citations and omit only claims that cannot be grounded."""

    if not isinstance(payload.get("claims"), list):
        return payload, []
    allowed_upper = {citation.upper() for citation in allowed_citations}
    cleaned_claims: list[dict[str, Any]] = []
    dropped: list[str] = []
    for index, claim in enumerate(payload["claims"]):
        part = str(claim.get("part", index + 1)).strip() if isinstance(claim, dict) else str(index + 1)
        if not isinstance(claim, dict) or not str(claim.get("text", "")).strip():
            dropped.append(f"Part {part}: omitted a malformed draft claim.")
            continue
        citations = claim.get("citations", [])
        if not isinstance(citations, list):
            citations = []
        normalized: list[str] = []
        unknown: list[str] = []
        for citation in citations:
            value = str(citation).strip().upper()
            parent = re.sub(
                r"^(SRC\d{3}:S\d{1,4}[A-Z]?)(?:\([^)]*\))+$",
                r"\1",
                value,
            )
            if parent in allowed_upper:
                normalized.append(parent)
            elif value in allowed_upper:
                normalized.append(value)
            else:
                unknown.append(str(citation))
        normalized = list(dict.fromkeys(normalized))
        if not normalized:
            reason = "no citation" if not citations else f"citation not in supplied evidence ({', '.join(unknown)})"
            dropped.append(f"Part {part}: omitted an ungrounded draft claim ({reason}).")
            continue
        cleaned_claims.append({**claim, "part": part, "citations": normalized})
        if unknown:
            dropped.append(
                f"Part {part}: ignored citation identifiers that were not in supplied evidence ({', '.join(unknown)})."
            )

    cleaned = {**payload, "claims": cleaned_claims}
    if payload["claims"] and not cleaned_claims:
        cleaned["outcome"] = "abstained"
    elif cleaned_claims and cleaned.get("outcome") == "abstained":
        cleaned["outcome"] = "partial"
    elif dropped and cleaned.get("outcome") == "answered":
        cleaned["outcome"] = "partial"
    return cleaned, dropped


def validate_answer_payload(payload: dict[str, Any], allowed_citations: set[str]) -> str | None:
    outcome = payload.get("outcome")
    legacy_abstained = payload.get("abstained")
    if outcome is None and isinstance(legacy_abstained, bool):
        outcome = "abstained" if legacy_abstained else "answered"
    if outcome not in {"answered", "partial", "abstained"}:
        return "missing_or_invalid_outcome"

    claims = payload.get("claims", [])
    limitations = payload.get("limitations", [])
    missing = payload.get("missing_information", [])
    if not isinstance(claims, list):
        return "claims_not_list"
    if not isinstance(limitations, list):
        return "limitations_not_list"
    if missing is not None and not isinstance(missing, list):
        return "missing_information_not_list"
    if outcome == "abstained":
        return None if not claims else "abstained_with_claims"
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
