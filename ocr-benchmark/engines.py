"""OCR/extraction engines behind one interface, plus capability guards and spend accounting.

Every engine reads a rendered page and returns (text, blocks, fields). Engines that
are not installed raise EngineUnavailable, which the runner catches so a run is
reported as `skipped` with a reason rather than crashing the benchmark.

The spend ledger is modelled on the Document AI page-budget ledger in
scripts/convert_to_text.py: a persistent JSON keyed by (variant, doc, page, purpose)
so re-running a partially completed benchmark never pays twice for the same page.
"""

from __future__ import annotations

import base64
import io
import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from PIL import Image

import config
import normalize
from contract import (
    Block,
    FieldValue,
    bbox_apply,
    bbox_contains,
    bbox_from_gemini,
    clamp_bbox,
)
from render import RenderedPage, crop


class EngineUnavailable(RuntimeError):
    """The engine is not installed or not configured. Not a failure of the run."""


@dataclass
class PageReading:
    text: str = ""
    blocks: list[Block] = field(default_factory=list)
    fields: list[FieldValue] = field(default_factory=list)
    confidence: float | None = None
    calls: int = 0
    http_attempts: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    errors: list[str] = field(default_factory=list)


# ── capability guards ────────────────────────────────────────────────────────
def gemini_available() -> tuple[bool, str]:
    if not config.GEMINI_API_KEY:
        return False, "GEMINI_API_KEY not set"
    try:
        import google.genai  # noqa: F401
    except ImportError:
        return False, "google-genai not installed"
    return True, ""


def surya_available() -> tuple[bool, str]:
    try:
        import surya  # noqa: F401
    except ImportError:
        return False, "surya-ocr not installed"
    return True, ""


def rapidocr_available() -> tuple[bool, str]:
    try:
        from rapidocr import RapidOCR  # noqa: F401
    except ImportError:
        return False, "rapidocr not installed"
    return True, ""


def capabilities() -> dict[str, str]:
    """Human-readable capability table, printed by the runner and the notebook.

    "configured" is not "working": these are import and env checks only. Verifying
    a key would cost a live call, so a bad credential surfaces as a failed run
    rather than here.
    """
    out = {}
    for name, probe, ready in (
        ("gemini", gemini_available, "key configured (not verified)"),
        ("surya", surya_available, "installed"),
        ("rapidocr", rapidocr_available, "installed"),
    ):
        ok, why = probe()
        out[name] = ready if ok else why
    return out


# ── spend ledger ─────────────────────────────────────────────────────────────
def _load_ledger() -> dict[str, Any]:
    if config.USAGE_JSON.is_file():
        try:
            return json.loads(config.USAGE_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"max_calls": config.MAX_CALLS, "calls": 0, "estimated_usd": 0.0, "events": []}


def _save_ledger(ledger: dict[str, Any]) -> None:
    config.USAGE_JSON.parent.mkdir(parents=True, exist_ok=True)
    config.USAGE_JSON.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def estimate_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price = config.PRICE_PER_MTOK.get(model)
    if not price:
        return 0.0
    return (
        prompt_tokens / 1_000_000 * price["input"]
        + completion_tokens / 1_000_000 * price["output"]
    )


def record_usage(model: str, reading: PageReading, label: str) -> None:
    """Append to the persistent ledger and stop hard when a cap is crossed."""
    ledger = _load_ledger()
    usd = estimate_usd(model, reading.prompt_tokens, reading.completion_tokens)
    ledger["calls"] += reading.calls
    ledger["estimated_usd"] = round(float(ledger["estimated_usd"]) + usd, 6)
    ledger["events"].append(
        {
            "label": label,
            "model": model,
            "calls": reading.calls,
            "prompt_tokens": reading.prompt_tokens,
            "completion_tokens": reading.completion_tokens,
            "estimated_usd": round(usd, 6),
        }
    )
    _save_ledger(ledger)
    if ledger["calls"] > config.MAX_CALLS:
        raise SystemExit(
            f"call cap reached: {ledger['calls']} > MAX_CALLS={config.MAX_CALLS}. "
            f"Raise DRAFTLY_OCR_MAX_CALLS or clear {config.USAGE_JSON}."
        )
    if ledger["estimated_usd"] > config.MAX_USD:
        raise SystemExit(
            f"spend cap reached: ${ledger['estimated_usd']:.2f} > MAX_USD=${config.MAX_USD:.2f}."
        )


def usage_summary() -> dict[str, Any]:
    ledger = _load_ledger()
    return {
        "calls": ledger.get("calls", 0),
        "estimated_usd": ledger.get("estimated_usd", 0.0),
    }


# ── stub engine (offline, deterministic) ─────────────────────────────────────
def stub_read_page(
    page: RenderedPage,
    truth: Sequence[dict[str, Any]] | None = None,
    noise: float = 0.0,
    seed: int = 0,
) -> PageReading:
    """Return the known text and boxes for a synthetic page.

    With noise=0 this is a perfect reader, so any deviation from 1.00 accuracy or
    0.00 CER in the harness is a measurement bug rather than a model result. With
    noise>0 it corrupts characters and jitters boxes at a known rate, which proves
    the metrics actually move in the right direction.
    """
    rng = random.Random(f"{seed}-{page.page_no}")
    rows = list(truth or [])
    blocks: list[Block] = []
    fields: list[FieldValue] = []
    lines: list[str] = []

    for index, row in enumerate(rows):
        text = str(row.get("text", ""))
        value = str(row.get("verbatimValue", ""))
        bbox = clamp_bbox(row["bbox"])
        if noise > 0:
            text = _corrupt(text, noise, rng)
            value = _corrupt(value, noise, rng)
            bbox = _jitter(bbox, noise, rng)
        lines.append(text)
        block_id = f"p{page.page_no}-b{index:03d}"
        blocks.append(
            Block(
                block_id=block_id,
                page_no=page.page_no,
                text=text,
                bbox=bbox,
                bbox_original=bbox_apply(bbox, page.transform_to_original),
                confidence=1.0 - noise,
                source="synthetic",
                script=normalize.script_of(text),
            )
        )
        fields.append(
            FieldValue(
                key=str(row["key"]),
                value=value,
                page_no=page.page_no,
                bbox=bbox,
                bbox_original=bbox_apply(bbox, page.transform_to_original),
                block_ids=[block_id],
                engine="stub",
                model_confidence=1.0 - noise,
                provenance_level="region",
            )
        )

    page_text = "\n".join(lines)
    for value_field in fields:
        value_field.verbatim_in_page_text = normalize.value_in_text(
            value_field.value or "", page_text
        )
        value_field.box_contains_value = (
            bbox_contains(value_field.bbox, value_field.bbox)
            if value_field.bbox is not None
            else None
        )
    return PageReading(text=page_text, blocks=blocks, fields=fields, confidence=1.0 - noise)


def _corrupt(text: str, rate: float, rng: random.Random) -> str:
    """Flip characters at approximately `rate`, so CER lands near `rate`."""
    if not text:
        return text
    chars = list(text)
    for i, ch in enumerate(chars):
        if ch != " " and rng.random() < rate:
            chars[i] = rng.choice("0123456789abcdefghijklmnopqrstuvwxyz")
    return "".join(chars)


def _jitter(bbox: Sequence[float], rate: float, rng: random.Random) -> tuple[float, ...]:
    shift = rate * 0.1
    return clamp_bbox(tuple(v + rng.uniform(-shift, shift) for v in bbox))


# ── Gemini ───────────────────────────────────────────────────────────────────
_PAGE_PROMPT = """You are reading a scanned Sri Lankan legal or property document page.

Return JSON with:
- "transcript": the full verbatim text of the page, preserving line breaks, in the
  original scripts (Sinhala, Tamil, English). Do not translate. Do not correct
  spelling. Do not expand abbreviations.
- "blocks": each visually distinct text block, with its "text" and "box_2d".
- "fields": the requested fields you can actually see, each with "key", "value" and
  "box_2d".

Rules:
- box_2d is [ymin, xmin, ymax, xmax], integers 0-1000, relative to this image.
- Every value is a STRING, exactly as printed. Preserve leading zeros, punctuation,
  and separators. "0021" is not 21.
- If a field is not visible on this page, omit it. Never guess a plausible value.
- If text is illegible, transcribe what is legible and stop; do not invent.

Requested field keys:
{field_keys}
"""

_PAGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript": {"type": "string"},
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "box_2d": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                },
                "required": ["text"],
            },
        },
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    # string-or-null, never number: "0021" must not decode to 21.
                    "value": {"type": ["string", "null"]},
                    "box_2d": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                },
                "required": ["key", "value"],
            },
        },
    },
    "required": ["transcript"],
}

_CROP_PROMPT = """This is a tight crop from a Sri Lankan legal document, containing the
field "{key}" ({label}).

Return JSON: {{"value": "<exactly the characters shown, as a string>"}}

Preserve leading zeros and punctuation exactly. If the crop does not legibly contain
this field, return {{"value": null}}. Never guess.
"""

_CROP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"value": {"type": ["string", "null"]}},
    "required": ["value"],
}


_CLASSIFY_PROMPT = """Classify this scanned Sri Lankan document page into exactly one kind.

Kinds:
- identity-card: National Identity Card. Photo, NIC number, name, date of birth.
- title-certificate: Registration of Title Act certificate. National emblem,
  "හිමිකම් සහතිකය" heading, cadastral map / block / parcel numbers, extent in
  hectares, a parcel diagram.
- form8-instrument: RTA Form 8, Instrument of Transfer under section 43. Numbered
  boxes, transferor and transferee particulars, consideration, notary attestation.
- survey-plan: A licensed surveyor's plan. Plan number, surveyor name and
  registration, lot numbers, extent, boundaries, a scaled diagram.
- other: anything else, including receipts, cheques, letters, and resolutions.

Return JSON: {"kind": "<one of the above>", "confidence": <0.0-1.0>}
Judge only what is visible. Use "other" when unsure rather than guessing a kind.
"""

_CLASSIFY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": [
                "identity-card",
                "title-certificate",
                "form8-instrument",
                "survey-plan",
                "other",
            ],
        },
        "confidence": {"type": "number"},
    },
    "required": ["kind", "confidence"],
}


def page_prompt(field_keys: Sequence[str]) -> str:
    return _PAGE_PROMPT.format(field_keys=", ".join(field_keys))


def gemini_classify_page(
    page: RenderedPage, model: str | None = None, temperature: float = 0.0
) -> tuple[str, float, PageReading]:
    """Classify one page into a registry kind.

    Mirrors production, which classifies a whole document from page 1 only
    (processing_service.py calls classify(pages[0])). Kept as its own call so the
    routing metric measures the same thing production does.
    """
    model = model or config.CLASSIFY_MODEL
    client = _client()
    payload, attempts, ptok, ctok, errors = _generate(
        client, model, _CLASSIFY_PROMPT, page.image, _CLASSIFY_SCHEMA, temperature
    )
    kind = str(payload.get("kind") or "other")
    try:
        confidence = float(payload.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return kind, confidence, PageReading(
        calls=1,
        http_attempts=attempts,
        prompt_tokens=ptok,
        completion_tokens=ctok,
        errors=errors,
    )


def _client() -> Any:
    ok, why = gemini_available()
    if not ok:
        raise EngineUnavailable(why)
    from google import genai

    return genai.Client(api_key=config.GEMINI_API_KEY)


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def _generate(
    client: Any,
    model: str,
    prompt: str,
    image: Image.Image,
    schema: dict[str, Any],
    temperature: float,
    retries: int = 3,
) -> tuple[dict[str, Any], int, int, int, list[str]]:
    """One schema-constrained Gemini call with backoff.

    Returns (payload, http_attempts, prompt_tokens, completion_tokens, errors).
    Follows the pattern already working in notebooks/05_courts_judgment_extraction.ipynb.
    """
    from google.genai import types

    errors: list[str] = []
    attempts = 0
    for attempt in range(retries):
        attempts += 1
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=_png_bytes(image), mime_type="image/png"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_json_schema=schema,
                ),
            )
            usage = getattr(response, "usage_metadata", None)
            prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
            completion_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
            payload = json.loads(response.text or "{}")
            return payload, attempts, prompt_tokens, completion_tokens, errors
        except Exception as exc:  # noqa: BLE001 - provider errors are heterogeneous
            errors.append(f"{type(exc).__name__}: {exc}"[:300])
            if attempt == retries - 1:
                break
            time.sleep(2**attempt + random.random())
    return {}, attempts, 0, 0, errors


def gemini_read_page(
    page: RenderedPage,
    field_keys: Sequence[str],
    model: str | None = None,
    temperature: float = 0.0,
) -> PageReading:
    """Whole-page transcript plus field values and boxes."""
    model = model or config.EXTRACT_MODEL
    client = _client()
    width, height = page.size
    payload, attempts, ptok, ctok, errors = _generate(
        client, model, page_prompt(field_keys), page.image, _PAGE_SCHEMA, temperature
    )

    blocks: list[Block] = []
    for index, raw in enumerate(payload.get("blocks") or []):
        box = raw.get("box_2d")
        if not box:
            continue
        bbox = bbox_from_gemini(box)
        blocks.append(
            Block(
                block_id=f"p{page.page_no}-b{index:03d}",
                page_no=page.page_no,
                text=str(raw.get("text", "")),
                bbox=bbox,
                bbox_original=bbox_apply(bbox, page.transform_to_original),
                source="gemini-box",
                script=normalize.script_of(str(raw.get("text", ""))),
            )
        )

    transcript = str(payload.get("transcript", ""))
    fields: list[FieldValue] = []
    for raw in payload.get("fields") or []:
        key = str(raw.get("key", "")).strip()
        if not key:
            continue
        value = normalize.null_collapse(raw.get("value"))
        box = raw.get("box_2d")
        bbox = bbox_from_gemini(box) if box else None
        fields.append(
            FieldValue(
                key=key,
                value=value,
                page_no=page.page_no,
                bbox=bbox,
                bbox_original=bbox_apply(bbox, page.transform_to_original) if bbox else None,
                engine="gemini",
                provenance_level="region" if bbox else "page",
                verbatim_in_page_text=normalize.value_in_text(value or "", transcript)
                if value
                else None,
            )
        )

    return PageReading(
        text=transcript,
        blocks=blocks,
        fields=fields,
        calls=1,
        http_attempts=attempts,
        prompt_tokens=ptok,
        completion_tokens=ctok,
        errors=errors,
    )


def gemini_read_crop(
    page: RenderedPage,
    key: str,
    label: str,
    bbox: Sequence[float],
    model: str | None = None,
    temperature: float = 0.0,
    pad: float = 0.02,
) -> tuple[str | None, PageReading]:
    """Re-read a single field from a padded crop of its box."""
    model = model or config.EXTRACT_MODEL
    client = _client()
    patch = crop(page.image, bbox, pad=pad)
    payload, attempts, ptok, ctok, errors = _generate(
        client,
        model,
        _CROP_PROMPT.format(key=key, label=label),
        patch,
        _CROP_SCHEMA,
        temperature,
    )
    value = normalize.null_collapse(payload.get("value"))
    return value, PageReading(
        calls=1,
        http_attempts=attempts,
        prompt_tokens=ptok,
        completion_tokens=ctok,
        errors=errors,
    )
