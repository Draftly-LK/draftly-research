"""Build the final conveyancing keep/drop corpus from v2 labels + the resolved
review band (resolve_review_llm.py's output). Read-only over both inputs;
writes only into evaluation/runs/conveyancing-final/.

Decision rule, v2 alone plus the review resolution:
  verdict == required     -> keep   (source: required-v2)
  verdict == not-required -> drop   (source: not-required-v2)
  verdict == review       -> look up case_id in review-resolved.csv
                              llm_verdict keep/drop -> keep/drop (source: rule/nvidia/ollama)
                              llm_verdict review (unresolved) -> excluded from both
                              files, counted separately -- an unresolved case is
                              not a confident "not conveyancing" call and must not
                              be silently folded into "drop".

Usage:
    uv run python scripts/build_final_conveyancing_corpus.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V2_LABELS = ROOT / "evaluation" / "runs" / "conveyancing-gate-v2" / "conveyancing_labels.csv"
RESOLVED_CSV = ROOT / "evaluation" / "runs" / "conveyancing-final" / "review-resolved.csv"
SOURCES = [
    ROOT / "data" / "commonlii" / "parsed" / "LKCA" / "judgments.csv",
    ROOT / "data" / "commonlii" / "parsed" / "LKSC" / "judgments.csv",
]
OUT_DIR = ROOT / "evaluation" / "runs" / "conveyancing-final"
KEEP_CSV = OUT_DIR / "corpus-keep.csv"
DROP_CSV = OUT_DIR / "corpus-drop.csv"
SUMMARY_TXT = OUT_DIR / "final-summary.txt"

SLIM_FIELDS = ["case_id", "case_name", "neutral_citation", "catchwords", "text",
               "final_verdict", "source", "status"]

# review-resolved.csv's own "source" vocabulary is rule/llm/ollama/unresolved
# (llm always means "NVIDIA answered" in that script); the corpus files use the
# more explicit nvidia/rule/ollama vocabulary requested for this deliverable.
SOURCE_LABELS = {"llm": "nvidia", "rule": "rule", "ollama": "ollama", "unresolved": "unresolved"}


def load_texts(case_ids: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for src in SOURCES:
        df = pd.read_csv(src, dtype=str, usecols=["case_id", "catchwords", "text"]).fillna("")
        df = df[df["case_id"].isin(case_ids)]
        for r in df.itertuples(index=False):
            out[r.case_id] = {"catchwords": r.catchwords, "text": r.text}
    return out


def main() -> int:
    if not RESOLVED_CSV.exists():
        print(f"missing {RESOLVED_CSV} -- run resolve_review_llm.py to completion first", file=sys.stderr)
        return 1

    labels = pd.read_csv(V2_LABELS, dtype=str).fillna("")
    resolved = {row["case_id"]: row for row in
                csv.DictReader(RESOLVED_CSV.open(encoding="utf-8", newline=""))}

    all_ids = set(labels["case_id"])
    texts = load_texts(all_ids)

    keep_rows, drop_rows, unresolved_rows = [], [], []
    missing_resolution = 0
    for row in labels.to_dict("records"):
        cid = row["case_id"]
        payload = texts.get(cid, {"catchwords": "", "text": ""})
        base = {
            "case_id": cid, "case_name": row["case_name"],
            "neutral_citation": row["neutral_citation"],
            "catchwords": payload["catchwords"], "text": payload["text"],
            "status": "unverified",
        }

        if row["verdict"] == "required":
            keep_rows.append({**base, "final_verdict": "keep", "source": "required-v2"})
        elif row["verdict"] == "not-required":
            drop_rows.append({**base, "final_verdict": "drop", "source": "not-required-v2"})
        else:  # review
            rr = resolved.get(cid)
            if rr is None:
                missing_resolution += 1
                unresolved_rows.append({**base, "final_verdict": "unresolved", "source": "missing-resolution"})
                continue
            src = SOURCE_LABELS.get(rr["source"], rr["source"])
            if rr["llm_verdict"] == "keep":
                keep_rows.append({**base, "final_verdict": "keep", "source": src})
            elif rr["llm_verdict"] == "drop":
                drop_rows.append({**base, "final_verdict": "drop", "source": src})
            else:
                unresolved_rows.append({**base, "final_verdict": "unresolved", "source": src})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with KEEP_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SLIM_FIELDS)
        w.writeheader()
        w.writerows(keep_rows)
    with DROP_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SLIM_FIELDS)
        w.writeheader()
        w.writerows(drop_rows + unresolved_rows)

    # ---- stats ----
    total_v2 = len(labels)
    required_count = int((labels["verdict"] == "required").sum())
    review_rows = labels[labels["verdict"] == "review"]
    total_review = len(review_rows)

    by_source = {"rule": 0, "llm": 0, "ollama": 0, "unresolved": 0}
    review_keep = review_drop = review_unresolved = 0
    for cid in review_rows["case_id"]:
        rr = resolved.get(cid)
        if rr is None:
            review_unresolved += 1
            continue
        by_source[rr["source"]] = by_source.get(rr["source"], 0) + 1
        if rr["llm_verdict"] == "keep":
            review_keep += 1
        elif rr["llm_verdict"] == "drop":
            review_drop += 1
        else:
            review_unresolved += 1

    final_corpus_size = required_count + review_keep
    cut_pct = (total_v2 - final_corpus_size) / total_v2 * 100

    kept_damaged = sum(
        1 for row in labels.to_dict("records")
        if row["case_id"] in {r["case_id"] for r in keep_rows} and row["text_damaged"] == "True"
    )

    lines = [
        f"total review cases: {total_review}",
        f"  cleared by rule:   {by_source['rule']}",
        f"  cleared by NVIDIA: {by_source['llm']}",
        f"  cleared by Ollama: {by_source['ollama']}",
        f"  unresolved:        {by_source['unresolved'] + missing_resolution}",
        "",
        f"review keep vs drop: keep={review_keep}  drop={review_drop}  unresolved={review_unresolved}",
        "",
        f"v2 required (untouched): {required_count}",
        f"final corpus size = required ({required_count}) + review->keep ({review_keep}) "
        f"= {final_corpus_size}",
        f"cut from 9,601: {total_v2 - final_corpus_size} cases removed ({cut_pct:.1f}%)",
        "",
        f"kept cases with text_damaged==True: {kept_damaged} "
        f"({kept_damaged / final_corpus_size:.1%} of the final corpus)",
        "",
        f"corpus-keep.csv: {len(keep_rows)} rows -> {KEEP_CSV}",
        f"corpus-drop.csv: {len(drop_rows) + len(unresolved_rows)} rows "
        f"({len(drop_rows)} drop + {len(unresolved_rows)} unresolved) -> {DROP_CSV}",
    ]
    report = "\n".join(lines)
    print(report)
    SUMMARY_TXT.write_text(report + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
