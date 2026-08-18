"""LLM-based statute section-boundary extraction via NVIDIA NIM.

Used for statutes the coordinate-based extractors in
`data/legal-sources/library/statutes/sandbox/` can't handle without more
bespoke layout work (genuine two-physical-column pages, a mirrored
margin-on-the-right layout, or a document too large to keep debugging by
hand). See `scripts/statute-section-llm-extraction/` in CLAUDE.md-adjacent
docs / the session's plan for the full design rationale.

Design: the LLM is only ever asked to find section *boundaries*, not to
reproduce section text. For each section it returns `{number, heading,
anchor}`, where `anchor` is a short verbatim quote of where that section
begins. This script then:

1. Validates every anchor is a real substring of the statute's own source
   text (scripts/case-law-information-extraction/validate.py's
   whitespace-collapsed, lowercased substring check, extended in
   `anchors.py` to also recover the exact original-text character offset).
2. Mechanically *slices* the real source text between consecutive validated
   anchors -- a section's `raw_text` is never LLM-generated, only
   LLM-located, so hallucinated body text is structurally impossible.
3. Runs the resulting section list through `extractor.py`'s
   `validate_sections()` (duplicate/missing/ascending-order/empty checks)
   before accepting it.

Usage:
    uv run python extract_statute_sections.py \\
        --pdf ../../data/legal-sources/library/statutes/companies-act-7-2007.pdf \\
        --source-id SRC031 --official-title "Companies Act" --act-number 7 --year 2007 \\
        -o ../../data/legal-sources/library/statutes/parsed/companies-act-7-2007.json

    # Two-column source (Matrimonial Rights Ordinances):
    uv run python extract_statute_sections.py --two-column ...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import config
import llm_client
from anchors import anchor_word_count, build_collapsed, find_anchor, fuzzy_find_anchor
from text_extract import extract_text_with_ocr_fallback

sys.path.insert(0, str(config.SANDBOX))
from extractor import (  # noqa: E402
    FORM_CAPTION_RE,
    SCHEDULE_BOUNDARY_RE,
    clean_text,
    validate_sections,
)

SYSTEM_PROMPT = """You are a meticulous legal-document indexer. You are given a chunk of the running text of a Sri Lankan statute (an Act or Ordinance). Your only job is to find where each numbered SECTION begins -- not subsections, not cross-references, not Schedule/Form field numbers.

A section marker is a plain number followed by a period at the start of a new provision (e.g. "12." or "12.(1)"), never:
- part of a cross-reference inside a sentence ("under section 12", "sections 12 and 15")
- a subsection number in parentheses on its own ("(1)", "(2)")
- a lettered/numbered field in an appended Form or Schedule (these come after the last real section and should be ignored entirely)

For each section you find, in order, return an exact VERBATIM quote of 6-15 consecutive words starting exactly where that section's number begins in the text -- copy it character-for-character from the text given, never paraphrase, summarize, or fix apparent typos. If a section's own marginal heading is visible nearby, include it; otherwise use null for heading.

Respond with a JSON object only, no commentary: {"sections": [{"number": "...", "heading": "..." or null, "anchor": "..."}]}"""


def build_user_prompt(chunk: str, last_number: str | None) -> str:
    if last_number:
        continuation = (
            f'This is a continuation of the same statute. The last section found '
            f'so far was "{last_number}". Only report sections that come strictly '
            f"after it; ignore any text still discussing section {last_number} or "
            f"earlier, and ignore any Schedule/Form content."
        )
    else:
        continuation = (
            "This is the start of the document. Report sections starting from "
            "section 1 (skip any long title, preamble, or table of contents)."
        )
    return f"{continuation}\n\nTEXT:\n{chunk}"


def chunk_text(text: str, size: int, overlap: int) -> list[tuple[int, str]]:
    """Return (start_offset, chunk_text) windows covering the whole text."""
    windows: list[tuple[int, str]] = []
    pos = 0
    n = len(text)
    while pos < n:
        end = min(pos + size, n)
        windows.append((pos, text[pos:end]))
        if end >= n:
            break
        pos = end - overlap
    return windows


def extract_sections_llm(
    source_text: str, *, model: str, max_llm_calls: int | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (accepted [{number, heading, offset}], warnings)."""
    collapsed = build_collapsed(source_text)
    windows = chunk_text(source_text, config.CHUNK_CHARS, config.CHUNK_OVERLAP_CHARS)

    accepted: list[dict[str, Any]] = []
    warnings: list[str] = []
    last_number: str | None = None
    last_offset = 0
    calls = 0

    for start, chunk in windows:
        if max_llm_calls is not None and calls >= max_llm_calls:
            warnings.append(
                f"stopped at --max-llm-calls={max_llm_calls}; text from char "
                f"{start} onward not processed"
            )
            break
        result = llm_client.chat_json(
            SYSTEM_PROMPT, build_user_prompt(chunk, last_number), model
        )
        calls += 1
        if not result or not isinstance(result.get("sections"), list):
            warnings.append(f"window at char {start}: no usable response")
            continue
        for entry in result["sections"]:
            if not isinstance(entry, dict):
                continue
            number = str(entry.get("number") or "").strip()
            anchor = str(entry.get("anchor") or "")
            heading = entry.get("heading")
            if not number or not anchor:
                continue
            if anchor_word_count(anchor) < 3:
                warnings.append(f"section {number}: anchor too short, rejected")
                continue
            if accepted and number == accepted[-1]["number"]:
                continue  # duplicate re-reported from the overlap window
            offset = find_anchor(collapsed, anchor, search_from=last_offset)
            match_kind = "verbatim"
            if offset is None:
                offset = fuzzy_find_anchor(collapsed, anchor, search_from=last_offset)
                match_kind = "fuzzy"
            if offset is None:
                warnings.append(
                    f"section {number}: anchor not found verbatim or fuzzy in "
                    "source, rejected"
                )
                continue
            if match_kind == "fuzzy":
                warnings.append(f"section {number}: anchor matched fuzzily")
            accepted.append({"number": number, "heading": heading, "offset": offset})
            last_number, last_offset = number, offset

    return accepted, warnings


def _trim_trailing_schedule(text: str) -> str:
    """Drop an appended Form/Schedule that spilled into the last section."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        probe = clean_text(line)
        if SCHEDULE_BOUNDARY_RE.search(probe) or FORM_CAPTION_RE.match(probe):
            return "\n".join(lines[:i]).strip()
    return text


def slice_sections(
    source_text: str, anchors: list[dict[str, Any]], *, page_count: int
) -> list[dict[str, Any]]:
    """Turn accepted (number, heading, offset) anchors into section dicts with
    verbatim text sliced straight from source_text -- never LLM-generated."""
    total_chars = max(len(source_text), 1)
    sections: list[dict[str, Any]] = []
    for i, anchor in enumerate(anchors):
        start = anchor["offset"]
        end = anchors[i + 1]["offset"] if i + 1 < len(anchors) else len(source_text)
        raw = source_text[start:end].strip()
        if i == len(anchors) - 1:
            raw = _trim_trailing_schedule(raw)
        normalized = clean_text(raw)
        heading = anchor.get("heading")
        page = 1 + int((start / total_chars) * page_count)
        sections.append({
            "section_number": anchor["number"],
            "heading": clean_text(heading) if heading else None,
            "raw_text": raw,
            "normalized_text": normalized,
            "text": normalized,
            "subsections": [],
            "paragraphs": [],
            "page_start": min(page, page_count),
            "page_end": min(page, page_count),
        })
    return sections


def build_document(args: argparse.Namespace, source_text: str,
                    sections: list[dict[str, Any]], *,
                    used_ocr: bool = False,
                    low_confidence_pages: list[int] | None = None) -> dict[str, Any]:
    raw_text = "\n\n".join(s["raw_text"] for s in sections)
    normalized_text = "\n\n".join(s["normalized_text"] for s in sections)
    low_confidence_pages = low_confidence_pages or []
    source_errors = []
    if low_confidence_pages:
        source_errors.append(
            f"Document AI OCR confidence below threshold on page(s): "
            f"{', '.join(str(p) for p in low_confidence_pages)} -- needs review."
        )
    return {
        "source_id": args.source_id,
        "official_title": args.official_title,
        "act_number": args.act_number,
        "year": args.year,
        "source_url": args.source_url,
        "retrieved_at": args.retrieved_at,
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "verification_status": "unverified",
        "source_errors": source_errors,
        "content_hash": hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
        "extraction_method": "llm-anchor",
        "extraction_model": args.model,
        "extraction_used_ocr": used_ocr,
        "sections": sections,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--two-column", action="store_true",
                    help="source PDF has genuine two-physical-column pages")
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--official-title", required=True)
    p.add_argument("--act-number", default=None)
    p.add_argument("--year", type=int, default=None)
    p.add_argument("--source-url", default=None)
    p.add_argument("--retrieved-at", default=None)
    p.add_argument("--model", default=config.DEFAULT_MODEL)
    p.add_argument("--max-llm-calls", type=int, default=0,
                    help="0 = unlimited")
    p.add_argument("--force", action="store_true",
                    help="ignore cache, re-run the LLM")
    p.add_argument("--strict", action="store_true",
                    help="exit 2 if validate_sections() reports any warning")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)

    cache_file = config.CACHE / f"{args.source_id}.json"
    if cache_file.exists() and not args.force:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        anchors, warnings, page_count, source_text = (
            cached["anchors"], cached["warnings"], cached["page_count"],
            cached["source_text"],
        )
        used_ocr = cached.get("used_ocr", False)
        low_confidence_pages = cached.get("low_confidence_pages", [])
        print(f"[cache] reusing {cache_file}")
    else:
        import pdfplumber
        with pdfplumber.open(args.pdf) as pdf:
            page_count = len(pdf.pages)
        source_text, used_ocr, low_confidence_pages = extract_text_with_ocr_fallback(
            args.pdf, two_column=args.two_column, source_id=args.source_id,
        )
        if used_ocr:
            print(f"[ocr] {args.pdf.name}: no usable text layer, used Document AI "
                  f"({len(low_confidence_pages)} low-confidence page(s))")
        max_calls = args.max_llm_calls or None
        anchors, warnings = extract_sections_llm(
            source_text, model=args.model, max_llm_calls=max_calls
        )
        cache_file.write_text(
            json.dumps({
                "anchors": anchors, "warnings": warnings,
                "page_count": page_count, "source_text": source_text,
                "used_ocr": used_ocr, "low_confidence_pages": low_confidence_pages,
            }, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )

    for w in warnings:
        print(f"[warn] {w}")

    # Always write a JSON output, even when section-boundary detection came
    # back empty or partial: the OCR/text-extraction work that got us here
    # (often the expensive part -- Document AI calls for a scanned PDF) is
    # real and worth keeping on disk rather than discarding on an LLM
    # hiccup. An empty/partial `sections` list plus a clear source_errors
    # note is a legitimate, honestly-labeled result -- not a silently
    # missing file that looks like the document was never attempted.
    if not anchors:
        print("[error] no sections found")
        document = build_document(
            args, source_text, [],
            used_ocr=used_ocr, low_confidence_pages=low_confidence_pages,
        )
        document["source_errors"].append(
            "No section boundaries found -- every LLM extraction window "
            "failed or returned nothing usable. source_text/raw OCR text is "
            "preserved for a retry; sections is empty."
        )
        document["raw_text"] = source_text
        document["normalized_text"] = ""
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"[usage] {json.dumps(llm_client.usage_summary())}")
        return 1

    sections = slice_sections(source_text, anchors, page_count=page_count)
    validation_warnings = validate_sections(sections)

    document = build_document(
        args, source_text, sections,
        used_ocr=used_ocr, low_confidence_pages=low_confidence_pages,
    )
    window_failures = [w for w in warnings if "no usable response" in w]
    if window_failures:
        document["source_errors"].append(
            f"{len(window_failures)} of {len(chunk_text(source_text, config.CHUNK_CHARS, config.CHUNK_OVERLAP_CHARS))} "
            "extraction window(s) failed outright (LLM gave no usable "
            "response) -- sections list is likely missing entries from "
            "those windows. See warnings for the affected char offsets."
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Extracted {len(sections)} sections to {args.output}")
    for w in validation_warnings:
        print(f"Warning: {w}")
    print(f"[usage] {json.dumps(llm_client.usage_summary())}")

    return 2 if (validation_warnings and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
