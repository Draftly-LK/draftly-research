"""Shared Gemini structured-output helper for Stages 4, 6, and 7.

Independent reimplementation of the call shape used by
src/draftly/retrieval/answering.py::generate_json (not imported, per the
module's independence boundary) -- same genai.Client -> generate_content
call with a JSON response schema, and the same rate-limit-aware backoff.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from .config import GEMINI_API_KEY, GEMINI_MODEL

DEFAULT_TIMEOUT_MS = 90_000

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def _parse_json(raw: str) -> tuple[dict[str, Any], str | None]:
    cleaned = raw.strip()
    fenced = _FENCED_JSON_RE.search(cleaned)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as exc:
        return {}, f"malformed_json: {exc}"


def call_gemini_json(
    *,
    prompt: str,
    schema: dict[str, Any],
    system_instruction: str,
    model: str = GEMINI_MODEL,
    tries: int = 3,
) -> tuple[dict[str, Any], str, str | None]:
    """One structured-output Gemini call with retry.

    Returns (parsed, raw_text, error). Missing GEMINI_API_KEY short-circuits
    to an empty result with error="missing_api_key" so every caller can
    degrade gracefully without a network call.
    """
    if not GEMINI_API_KEY:
        return {}, "", "missing_api_key"

    last_error = ""
    for attempt in range(tries):
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=DEFAULT_TIMEOUT_MS))
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
            parsed, parse_error = _parse_json(raw)
            return parsed, raw, parse_error
        except Exception as exc:  # noqa: BLE001 - defensive network/API boundary
            last_error = str(exc)
            if attempt == tries - 1:
                break
            quota_hit = "429" in last_error or "RESOURCE_EXHAUSTED" in last_error.upper()
            time.sleep((30 * (attempt + 1)) if quota_hit else (5 * (attempt + 1)))
    return {}, "", last_error
