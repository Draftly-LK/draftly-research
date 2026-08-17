"""LLM tie-breaker for the conveyancing "review" band only.

Input: evaluation/runs/conveyancing-gate-v2/conveyancing_labels.csv (the
output of classify_commonlii_convayancing_improved.py). Every row whose
verdict is "required" or "not-required" is already decided and is not
touched here -- only verdict == "review" rows are processed.

Each review case is resolved one of three ways, cheapest first:

  1. Rule: text_damaged AND no statute hit AND no topic hit -- there is no
     conveyancing signal at all, damaged or not, so this never needs a
     model call. Auto-dropped.
  2. LLM: NVIDIA NIM (MODEL, below), a yes/no "is this conveyancing"
     question over a minimal payload (catchwords + first 2500 chars of
     the judgment body -- not the whole text).
  3. Ollama (qwen2.5:7b), local fallback if NVIDIA is unreachable after
     retries. If neither answers, the case is left "review" (unresolved)
     rather than guessed at.

Resumable: writes evaluation/runs/conveyancing-final/review-resolved.csv
one row at a time as each case resolves. On restart, already-resolved
case_ids are skipped, so a interrupted run (or a rerun to pick up the
unresolved leftovers) never re-spends API calls.

Usage:
    uv run python scripts/resolve_review_llm.py
    uv run python scripts/resolve_review_llm.py --limit 20   # smoke test
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

LABELS_CSV = ROOT / "evaluation" / "runs" / "conveyancing-gate-v2" / "conveyancing_labels.csv"
SOURCES = [
    ROOT / "data" / "commonlii" / "parsed" / "LKCA" / "judgments.csv",
    ROOT / "data" / "commonlii" / "parsed" / "LKSC" / "judgments.csv",
]
OUT_DIR = ROOT / "evaluation" / "runs" / "conveyancing-final"
OUT_CSV = OUT_DIR / "review-resolved.csv"
OUT_FIELDS = ["case_id", "llm_verdict", "llm_reason", "source", "status"]

# Single constant so the model is a one-line change.
MODEL = "meta/llama-3.1-8b-instruct"
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

TEXT_EXCERPT_CHARS = 2500
MAX_CONCURRENCY = 2
SUBMIT_DELAY_S = 0.3  # pace new requests onto the pool, not just cap concurrency
NVIDIA_TRIES = 3
OLLAMA_TRIES = 2
PARSE_RETRIES = 1

SYS_PROMPT = """You are classifying Sri Lankan case law for a conveyancing-law corpus. \
Conveyancing covers: deeds, land and property matters, partition, prescription and title, \
mortgages, servitudes, succession and wills, gifts, leases, state land, and notarial practice. \
Criminal, tax, labour, constitutional/fundamental-rights, and election matters are NOT \
conveyancing. Output strict JSON only, no prose, no markdown fences: \
{"conveyancing": true or false, "reason": "<short reason, max 15 words>"}"""

USER_TEMPLATE = """CATCHWORDS: {catchwords}

JUDGMENT EXCERPT:
\"\"\"{text}\"\"\"

Is this case conveyancing? Return the JSON object only."""


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def load_labels():
    import pandas as pd

    return pd.read_csv(LABELS_CSV, dtype=str).fillna("")


def load_case_texts(case_ids: set[str]) -> dict[str, dict]:
    """catchwords + text for exactly the case_ids we still need to call the LLM for."""
    import pandas as pd

    out: dict[str, dict] = {}
    for src in SOURCES:
        if not src.exists() or not case_ids:
            continue
        df = pd.read_csv(src, dtype=str, usecols=["case_id", "catchwords", "text"]).fillna("")
        df = df[df["case_id"].isin(case_ids)]
        for r in df.itertuples(index=False):
            out[r.case_id] = {"catchwords": r.catchwords, "text": r.text}
    return out


def load_resolved() -> dict[str, dict]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open(encoding="utf-8", newline="") as fh:
        return {row["case_id"]: row for row in csv.DictReader(fh)}


# --------------------------------------------------------------------------
# LLM calls
# --------------------------------------------------------------------------

def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.I | re.M).strip()
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
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


def _is_transient(exc: Exception) -> bool:
    from openai import APIConnectionError, APIStatusError, APITimeoutError, NotFoundError, RateLimitError

    if isinstance(exc, (RateLimitError, APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    # NVIDIA's hosted MODEL 404s ("model '...' not found") intermittently for
    # models that ARE in the account's catalogue and DO work seconds later --
    # confirmed by replaying the identical request and watching it flip
    # between success and 404. Treat as a flaky backend, not a missing model.
    return isinstance(exc, NotFoundError)


def chat_json(client, model: str, system: str, user: str, *, tries: int) -> tuple[dict | None, str]:
    """Returns (parsed_json_or_None, status). status is 'ok', 'transient_exhausted', or 'parse_failed'."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    last_status = "transient_exhausted"
    for attempt in range(tries):
        try:
            r = client.chat.completions.create(
                model=model, messages=msgs, temperature=0.0, max_tokens=120,
            )
        except Exception as e:  # noqa: BLE001
            if not _is_transient(e) or attempt == tries - 1:
                return None, "transient_exhausted"
            time.sleep(min(2 ** attempt, 20))
            continue

        content = r.choices[0].message.content or ""
        parsed = _extract_json(content)
        if parsed is not None and "conveyancing" in parsed:
            return parsed, "ok"
        # parse failure: one extra retry, separate from the transient budget above.
        for _ in range(PARSE_RETRIES):
            try:
                r2 = client.chat.completions.create(
                    model=model, messages=msgs, temperature=0.0, max_tokens=120,
                )
                parsed2 = _extract_json(r2.choices[0].message.content or "")
                if parsed2 is not None and "conveyancing" in parsed2:
                    return parsed2, "ok"
            except Exception:
                pass
        last_status = "parse_failed"
        return None, last_status
    return None, last_status


def resolve_one(row: dict, nvidia_client, ollama_client, texts: dict[str, dict]) -> dict:
    case_id = row["case_id"]
    payload = texts.get(case_id, {"catchwords": "", "text": ""})
    user = USER_TEMPLATE.format(
        catchwords=payload["catchwords"], text=payload["text"][:TEXT_EXCERPT_CHARS],
    )

    parsed, status = chat_json(nvidia_client, MODEL, SYS_PROMPT, user, tries=NVIDIA_TRIES)
    if parsed is not None:
        verdict = "keep" if parsed.get("conveyancing") else "drop"
        return {"case_id": case_id, "llm_verdict": verdict,
                "llm_reason": str(parsed.get("reason", ""))[:200], "source": "llm",
                "status": "unverified"}

    if status == "parse_failed":
        return {"case_id": case_id, "llm_verdict": "review", "llm_reason": "unparseable LLM reply",
                "source": "unresolved", "status": "unverified"}

    if ollama_client is not None:
        parsed2, status2 = chat_json(ollama_client, OLLAMA_MODEL, SYS_PROMPT, user, tries=OLLAMA_TRIES)
        if parsed2 is not None:
            verdict = "keep" if parsed2.get("conveyancing") else "drop"
            return {"case_id": case_id, "llm_verdict": verdict,
                    "llm_reason": str(parsed2.get("reason", ""))[:200], "source": "ollama",
                    "status": "unverified"}

    return {"case_id": case_id, "llm_verdict": "review", "llm_reason": "NVIDIA and Ollama unavailable",
            "source": "unresolved", "status": "unverified"}


def make_ollama_client():
    from openai import OpenAI

    try:
        import urllib.request

        urllib.request.urlopen(OLLAMA_BASE_URL.rsplit("/v1", 1)[0] + "/api/tags", timeout=2)
    except Exception:
        return None
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0, help="process at most N unresolved cases")
    args = ap.parse_args()

    api_key = os.environ.get("NVIDIA_API_KEY_1")
    if not api_key:
        print("NVIDIA_API_KEY_1 is not set (checked process env and .env). "
              "Set it before running -- refusing to guess or fall back silently.",
              file=sys.stderr)
        return 1

    from openai import OpenAI

    nvidia_client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    labels = load_labels()
    required_count = int((labels["verdict"] == "required").sum())
    review_rows = labels[labels["verdict"] == "review"].to_dict("records")
    total_review = len(review_rows)
    resolved = load_resolved()
    log(f"[start] review cases: {total_review}  already resolved: {len(resolved)}")

    pending = [r for r in review_rows if r["case_id"] not in resolved]

    # ---- rule pre-filter: damaged parse + zero signal, no LLM call needed.
    rule_cleared: list[dict] = []
    needs_llm: list[dict] = []
    for r in pending:
        damaged = r.get("text_damaged") == "True"
        no_signal = not r.get("statutes") and not r.get("topics")
        if damaged and no_signal:
            rule_cleared.append({
                "case_id": r["case_id"], "llm_verdict": "drop",
                "llm_reason": "rule: damaged, no signal", "source": "rule",
                "status": "unverified",
            })
        else:
            needs_llm.append(r)

    if args.limit:
        needs_llm = needs_llm[: args.limit]

    log(f"[rule] cleared without a call: {len(rule_cleared)}  remaining for LLM: {len(needs_llm)}")

    write_lock = threading.Lock()
    file_is_new = not OUT_CSV.exists()

    def append_rows(rows: list[dict]) -> None:
        with write_lock, OUT_CSV.open("a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
            nonlocal file_is_new
            if file_is_new:
                w.writeheader()
                file_is_new = False
            for row in rows:
                w.writerow(row)
            fh.flush()

    if rule_cleared:
        append_rows(rule_cleared)

    llm_resolved_count = 0
    ollama_resolved_count = 0
    unresolved_count = 0

    if needs_llm:
        texts = load_case_texts({r["case_id"] for r in needs_llm})
        ollama_client = make_ollama_client()
        log(f"[llm] ollama fallback available: {ollama_client is not None}")

        done = 0
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
            pending_iter = iter(needs_llm)
            in_flight: dict = {}

            def submit_next() -> bool:
                r = next(pending_iter, None)
                if r is None:
                    return False
                in_flight[pool.submit(resolve_one, r, nvidia_client, ollama_client, texts)] = r["case_id"]
                return True

            # Prime the window, then replace each task as it finishes rather than
            # queuing everything up front -- keeps writes flowing continuously
            # instead of buffering behind a long submission phase.
            for _ in range(MAX_CONCURRENCY):
                if not submit_next():
                    break

            while in_flight:
                fut = next(as_completed(in_flight))
                result = fut.result()
                del in_flight[fut]
                append_rows([result])
                if result["source"] == "llm":
                    llm_resolved_count += 1
                elif result["source"] == "ollama":
                    ollama_resolved_count += 1
                else:
                    unresolved_count += 1
                done += 1
                if done % 25 == 0 or done == len(needs_llm):
                    log(f"  {done}/{len(needs_llm)} resolved "
                        f"(llm={llm_resolved_count} ollama={ollama_resolved_count} "
                        f"unresolved={unresolved_count})")
                time.sleep(SUBMIT_DELAY_S)
                submit_next()

    # ---- final tally from the full resolved set (this run + prior runs).
    all_resolved = load_resolved()
    by_source = {"rule": 0, "llm": 0, "ollama": 0, "unresolved": 0}
    keep = drop = 0
    for row in all_resolved.values():
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1
        if row["llm_verdict"] == "keep":
            keep += 1
        elif row["llm_verdict"] == "drop":
            drop += 1

    print(f"\nreview cases total: {total_review}")
    print(f"  cleared by rule:   {by_source['rule']}")
    print(f"  cleared by LLM:    {by_source['llm'] + by_source['ollama']} "
          f"(nvidia={by_source['llm']}, ollama={by_source['ollama']})")
    print(f"  unresolved:        {by_source['unresolved']}")
    print(f"\nfinal split (rule + LLM only, excludes unresolved): keep={keep}  drop={drop}")
    print(f"\nrequired (already decided, untouched): {required_count}")
    print(f"final corpus size = required ({required_count}) + review->keep ({keep}) "
          f"= {required_count + keep}")
    print(f"\noutput: {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
