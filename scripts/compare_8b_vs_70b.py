"""One-off: re-run the cases resolve_review_llm.py already answered via NVIDIA
8B (source == "llm" in review-resolved.csv) through the 70B model instead, to
see whether the stronger model actually changes verdicts before committing to
a ~40x-slower full batch. Writes only to review-70b-compare.csv; never touches
review-resolved.csv.

Usage:
    uv run python scripts/compare_8b_vs_70b.py
"""

from __future__ import annotations

import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import resolve_review_llm as rr  # noqa: E402
from openai import OpenAI  # noqa: E402

COMPARE_MODEL = "meta/llama-3.3-70b-instruct"
CONCURRENCY = 2
OUT_CSV = ROOT / "evaluation" / "runs" / "conveyancing-final" / "review-70b-compare.csv"
FIELDS = ["case_id", "verdict_8b", "reason_8b", "verdict_70b", "reason_70b",
          "agree", "seconds", "status_70b"]


def main() -> int:
    resolved = {row["case_id"]: row for row in
                csv.DictReader((ROOT / "evaluation" / "runs" / "conveyancing-final" /
                                "review-resolved.csv").open(encoding="utf-8", newline=""))}
    eightb_rows = [r for r in resolved.values() if r["source"] == "llm"]
    print(f"[start] 8B-resolved cases available for comparison: {len(eightb_rows)}", file=sys.stderr)

    api_key = os.environ["NVIDIA_API_KEY_1"]
    client = OpenAI(base_url=rr.NVIDIA_BASE_URL, api_key=api_key)
    assert rr.NVIDIA_BASE_URL == "https://integrate.api.nvidia.com/v1"

    texts = rr.load_case_texts({r["case_id"] for r in eightb_rows})

    def run_one(row: dict) -> dict:
        cid = row["case_id"]
        payload = texts.get(cid, {"catchwords": "", "text": ""})
        user = rr.USER_TEMPLATE.format(
            catchwords=payload["catchwords"], text=payload["text"][: rr.TEXT_EXCERPT_CHARS],
        )
        t0 = time.monotonic()
        parsed, status = rr.chat_json(client, COMPARE_MODEL, rr.SYS_PROMPT, user, tries=rr.NVIDIA_TRIES)
        elapsed = time.monotonic() - t0

        if parsed is not None:
            v70 = "keep" if parsed.get("conveyancing") else "drop"
            r70 = str(parsed.get("reason", ""))[:200]
        else:
            v70, r70 = "unresolved", f"70B call failed: {status}"

        return {
            "case_id": cid, "verdict_8b": row["llm_verdict"], "reason_8b": row["llm_reason"],
            "verdict_70b": v70, "reason_70b": r70,
            "agree": "yes" if v70 == row["llm_verdict"] else "no",
            "seconds": f"{elapsed:.1f}", "status_70b": status,
        }

    results = []
    done = 0
    t_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(run_one, r): r["case_id"] for r in eightb_rows}
        with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for fut in as_completed(futures):
                result = fut.result()
                results.append(result)
                w.writerow(result)
                fh.flush()
                done += 1
                if done % 10 == 0 or done == len(eightb_rows):
                    elapsed_total = time.monotonic() - t_start
                    print(f"  {done}/{len(eightb_rows)}  "
                          f"avg {elapsed_total / done:.1f}s/case  "
                          f"elapsed {elapsed_total:.0f}s", file=sys.stderr, flush=True)

    total_elapsed = time.monotonic() - t_start
    agree = sum(1 for r in results if r["agree"] == "yes")
    disagree = [r for r in results if r["agree"] == "no"]

    print(f"\ncases compared: {len(results)}")
    print(f"agree: {agree} ({agree / len(results):.1%})")
    print(f"disagree: {len(disagree)} ({len(disagree) / len(results):.1%})")
    print(f"\ntotal time: {total_elapsed:.0f}s  avg: {total_elapsed / len(results):.1f}s/case "
          f"(concurrency={CONCURRENCY})")
    print(f"\nfull 1,372-case batch at this rate, concurrency={CONCURRENCY}: "
          f"~{1372 * total_elapsed / len(results) / 60:.0f} minutes")
    print(f"\noutput: {OUT_CSV}")

    print("\n--- disagreement examples ---")
    for r in disagree[:5]:
        print(f"  {r['case_id']}")
        print(f"    8B  -> {r['verdict_8b']:<5} : {r['reason_8b']}")
        print(f"    70B -> {r['verdict_70b']:<5} : {r['reason_70b']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
