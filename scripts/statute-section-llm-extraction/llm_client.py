"""Thin OpenAI-compatible client for NVIDIA NIM, with JSON parsing, retry/backoff,
and cumulative token-usage tracking.

Adapted from scripts/case-law-information-extraction/llm_client.py -- same
shape, pointed at this pipeline's config.
"""

from __future__ import annotations

import json
import re
import sys
import time

import config

if str(config.ROOT) not in sys.path:
    sys.path.insert(0, str(config.ROOT))

from LLMs.nvidia import NvidiaManager  # noqa: E402

# Originally set to 30s (shorter than NvidiaManager's 60s default) because a
# different model (meta/llama-3.3-70b-instruct) hung the full 60s repeatedly
# on trivial requests. That reasoning doesn't hold for this pipeline's real
# workload: a full extraction chunk is ~10K prompt tokens with up to 4096
# output tokens, and under real (occasionally flaky) network conditions that
# generation genuinely can take longer than 30s even on a normally-fast
# model/endpoint -- observed as repeated APITimeoutError on large documents
# specifically, never on small health-check-sized requests. 60s gives real
# extraction calls room to finish instead of being cut off mid-generation.
_manager = NvidiaManager.from_env(env_file=config.ROOT / ".env", timeout=60.0)

USAGE: dict[str, dict[str, int]] = {}
HTTP_ATTEMPTS: dict[str, int] = {"count": 0}


def _record(model: str, usage) -> None:
    u = USAGE.setdefault(model, {"prompt": 0, "completion": 0, "calls": 0})
    u["calls"] += 1
    if usage is not None:
        u["prompt"] += getattr(usage, "prompt_tokens", 0) or 0
        u["completion"] += getattr(usage, "completion_tokens", 0) or 0


def _extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of a model reply (handles code fences / stray prose)."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.I | re.M).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except Exception:
                    return None
    return None


def chat_json(
    system: str, user: str, model: str, *, temperature: float = 0.0,
    max_tokens: int | None = None, tries: int = 2,
) -> dict | None:
    """One chat call expecting a JSON object back. Returns parsed dict or None.

    Retries with backoff on transient errors (429/5xx/network). Requests JSON
    response format; falls back to plain if the model/endpoint rejects it.

    tries=2 (was 4): a genuinely large document has many chunks, so a chunk
    that's going to fail eating 4 tries * up to 60s each (~4-8 minutes) before
    giving up was the single biggest reason big documents disproportionately
    hit the driver's per-document time limit -- the whole document is already
    retried at the document level on a later pass, so failing a bad chunk
    faster (and moving on to the rest of the document) beats exhausting the
    time budget on one chunk.
    """
    max_tokens = max_tokens or config.MAX_TOKENS_OUT
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    for attempt in range(tries):
        try:
            kwargs = dict(model=model, messages=msgs, temperature=temperature,
                          max_tokens=max_tokens)
            try:
                HTTP_ATTEMPTS["count"] += 1
                r = _manager.create_chat_completion(
                    response_format={"type": "json_object"}, **kwargs)
            except Exception:
                HTTP_ATTEMPTS["count"] += 1
                r = _manager.create_chat_completion(**kwargs)
            _record(model, getattr(r, "usage", None))
            return _extract_json(r.choices[0].message.content or "")
        except Exception as e:  # noqa: BLE001
            wait = min(2**attempt, 20)
            if attempt == tries - 1:
                print(f"[llm] giving up on {model} after {tries} tries: {repr(e)[:160]}")
                return None
            time.sleep(wait)
    return None


def usage_summary() -> dict:
    total_prompt = sum(u["prompt"] for u in USAGE.values())
    total_comp = sum(u["completion"] for u in USAGE.values())
    total_calls = sum(u["calls"] for u in USAGE.values())
    return {"by_model": USAGE, "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_comp, "total_calls": total_calls,
            "http_attempts": HTTP_ATTEMPTS["count"]}
