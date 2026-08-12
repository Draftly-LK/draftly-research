"""Phase 1 outputs and cross-checks.

Reads the parsed `consShortTitleView` records and emits the contract from
`statue-plans.md`:

    sections.jsonl   source_id, section, heading, heading_source, text_source,
                     present_in[]  (+ source_url, fetched_at, sha256,
                     retrieved_from on every record)
    actions.csv      target_section, amending_act, amending_section, operation,
                     source_url

Field discipline is enforced here, not left to the caller: LawLanka may populate
`section_present` and `heading`; only the official PDF may populate `text`. A
section LawLanka lists that our own extraction missed is recorded as
`heading_source: lawlanka, text_source: none` -- a known hole, never a silent
fill.

The cross-check reports the number the whole sub-project is for: how many of the
810 pinpoint case-to-section links that currently fail for want of an index entry
now resolve. It runs with zero fetched statutes too, in which case it reports the
baseline only.

    python scripts/lawlanka-section-index/build_outputs.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as C
from relevance_gate import load_registry

STATUTES_DIR = C.OUT / "statutes"

# The plan's closed set. A marker names the amending Act and section but not what
# it did, so `unknown` is the honest default; the others are only used when the
# page says so in words.
OPERATIONS = ("inserted", "amended", "replaced", "repealed", "unknown")
OP_WORDS = ((r"\brepeal", "repealed"), (r"\binsert|\badded\b", "inserted"),
            (r"\breplac|\bsubstitut", "replaced"), (r"\bamend", "amended"))


def sec_key(section: str) -> str:
    """Normalise a section label for comparison ('12 A' -> '12a')."""
    return re.sub(r"[^0-9a-z]", "", section.lower())


def load_fetched() -> tuple[list[dict], list[dict]]:
    """Parsed statute records, one per enactment.

    Two cited names can resolve to the same LawLanka act code ("rent restriction
    act" / "rent restriction ordinance"). Keeping both would store the same
    sections twice, so the record carrying a `source_id` wins and the other is
    returned separately as an alias.
    """
    if not STATUTES_DIR.exists():
        return [], []
    by_code: dict[str, dict] = {}
    dupes: list[dict] = []
    for p in sorted(STATUTES_DIR.glob("*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        code = rec.get("act_code", "") or f"nocode:{p.stem}"
        prev = by_code.get(code)
        if prev is None:
            by_code[code] = rec
            continue
        # prefer the one tied to a registry source_id, else the longer name
        keep, drop = ((rec, prev) if (rec.get("source_id") and not prev.get("source_id"))
                      else (prev, rec))
        by_code[code] = keep
        dupes.append({"act_code": code, "kept": keep["statute_name"],
                      "alias": drop["statute_name"]})
    return list(by_code.values()), dupes


def load_derived_index() -> dict[str, dict[str, str]]:
    """Our existing section index: source_id -> {normalised section: heading}."""
    if not C.SECTION_INDEX.exists():
        return {}
    raw = json.loads(C.SECTION_INDEX.read_text(encoding="utf-8"))
    return {sid: {sec_key(e["section"]): e.get("heading", "")
                  for e in entries if e.get("section")}
            for sid, entries in raw.items()}


def infer_operation(text: str) -> str:
    for pat, op in OP_WORDS:
        if re.search(pat, text, re.I):
            return op
    return "unknown"


def build_sections(records: list[dict], derived: dict, registry: dict) -> list[dict]:
    rows = []
    for rec in records:
        sid = rec.get("source_id", "")
        ours = derived.get(sid, {})
        # Only an official PDF may supply text. We hold text when the registry
        # records a local markdown conversion of the official source.
        holds_text = bool(registry.get(sid, {}).get("local_markdown_path"))
        for s in rec["sections"]:
            k = sec_key(s["section"])
            in_ours = k in ours
            present_in = ["lawlanka"]
            if in_ours:
                present_in.append("statute-section-index")
            rows.append({
                "source_id": sid,
                "statute_name": rec["statute_name"],
                "act_code": rec.get("act_code", ""),
                "section": s["section"],
                "heading": s["heading"],
                # LawLanka headings are complete where ours are truncated
                # fragments, so they win on heading -- and only on heading.
                "heading_source": "lawlanka" if s["heading"] else (
                    "statute-section-index" if ours.get(k) else "none"),
                "text_source": "official-pdf" if (holds_text and in_ours) else "none",
                "present_in": present_in,
                "amendment_markers": s["markers"],
                "source_url": rec["source_url"],
                "fetched_at": rec["fetched_at"],
                "sha256": rec["sha256"],
                "retrieved_from": rec["retrieved_from"],
                "status": "unverified",
            })
    return rows


def build_actions(records: list[dict]) -> list[dict]:
    rows = []
    for rec in records:
        for s in rec["sections"]:
            for m in s["markers"]:
                rows.append({
                    "source_id": rec.get("source_id", ""),
                    "statute_name": rec["statute_name"],
                    "target_section": s["section"],
                    "amending_act": m["amending_act"],
                    "amending_section": m["amending_section"],
                    "operation": infer_operation(s.get("raw", "")),
                    "verbatim": m["verbatim"],
                    "source_url": rec["source_url"],
                    "status": "unverified",
                })
    return rows


def crosscheck(records: list[dict], derived: dict) -> str:
    """Per-statute agreement, and the resolve rate on the failing links."""
    links = pd.read_csv(C.STATUTE_LINKS, dtype=str).fillna("")
    pin = links[links["section"].str.strip() != ""]
    failing = pin[pin["grade"].isin(["gap-in-index", "statute-not-indexed"])]
    out_of_range = pin[pin["grade"] == "out-of-range"]

    new_idx: dict[str, set[str]] = {}
    for rec in records:
        sid = rec.get("source_id", "")
        if sid:
            new_idx.setdefault(sid, set()).update(
                sec_key(s["section"]) for s in rec["sections"])

    resolved = 0
    per_statute: dict[str, list[int]] = {}
    for _, r in failing.iterrows():
        sid, k = r["source_id"], sec_key(r["section"])
        hit = bool(sid and k and k in new_idx.get(sid, set()))
        resolved += hit
        p = per_statute.setdefault(sid, [0, 0])
        p[0] += 1
        p[1] += hit

    lines = [
        "# LawLanka structural sweep -- cross-check",
        "",
        f"Statutes indexed from LawLanka: **{len(records)}**",
        "",
        "## Pinpoint case-to-section links",
        "",
        f"- Links with a pinpoint section: **{len(pin)}**",
        f"- Failing for want of an index entry: **{len(failing)}** "
        f"({len(pin[pin['grade'] == 'gap-in-index'])} where the statute is "
        f"indexed but the section is missing, "
        f"{len(pin[pin['grade'] == 'statute-not-indexed'])} where the statute has "
        f"no index at all)",
        f"- Genuinely out of range, not an index problem: **{len(out_of_range)}**",
        f"- Now resolved by the LawLanka section list: **{resolved}** "
        f"({resolved / len(failing) * 100:.1f}% of the failing set)"
        if len(failing) else "- No failing links to resolve",
        "",
    ]
    if per_statute:
        lines += ["| source_id | failing links | now resolved |", "| --- | --- | --- |"]
        for sid, (tot, got) in sorted(per_statute.items(),
                                      key=lambda kv: -kv[1][0]):
            lines.append(f"| {sid or '(none)'} | {tot} | {got} |")
        lines.append("")

    lines += ["## Section-count agreement per statute", "",
              "`ours` is `derived/statute-section-index.json`. Where the two "
              "disagree on whether a section exists the official PDF wins; the "
              "PDF coordinate-block extractor that would settle that is Phase 2, "
              "so no such adjudication is claimed here.", "",
              "| statute | source_id | lawlanka | ours | only in lawlanka | "
              "only in ours |", "| --- | --- | --- | --- | --- | --- |"]
    for rec in sorted(records, key=lambda r: -len(r["sections"])):
        sid = rec.get("source_id", "")
        theirs = {sec_key(s["section"]) for s in rec["sections"]}
        ours = set(derived.get(sid, {}))
        lines.append(f"| {rec['statute_name'][:44]} | {sid or '(new)'} | "
                     f"{len(theirs)} | {len(ours)} | {len(theirs - ours)} | "
                     f"{len(ours - theirs)} |")
    lines.append("")
    lines += ["## Acceptance gate", "",
              "The corpus must stay reproducible from official sources alone. "
              "LawLanka improves heading coverage and supplies the amendment "
              "markers; it never supplies statute text, and every record here is "
              "`status: unverified` until a lawyer reviews it.", ""]
    return "\n".join(lines)


def main() -> int:
    records, dupes = load_fetched()
    derived = load_derived_index()
    registry = {r["source_id"]: r for r in load_registry()}
    reg_raw = pd.read_csv(C.REGISTRY, dtype=str, encoding="utf-8-sig").fillna("")
    reg_raw.columns = [c.strip().strip('"') for c in reg_raw.columns]
    for _, r in reg_raw.iterrows():
        sid = r["source_id"].strip()
        if sid in registry:
            registry[sid]["local_markdown_path"] = r.get("local_markdown_path", "").strip()

    print(f"Phase 1 outputs")
    print(f"  statute records (one per enactment): {len(records)}")
    for d in dupes:
        print(f"    alias collapsed: {d['alias']!r} -> {d['kept']!r} "
              f"({d['act_code']})")
    print(f"  existing section index : {len(derived)} source_ids")

    sections = build_sections(records, derived, registry)
    actions = build_actions(records)

    with C.SECTIONS_JSONL.open("w", encoding="utf-8") as f:
        for row in sections:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    cols = ["source_id", "statute_name", "target_section", "amending_act",
            "amending_section", "operation", "verbatim", "source_url", "status"]
    with C.ACTIONS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(actions)

    report = crosscheck(records, derived)
    C.CROSSCHECK.write_text(report, encoding="utf-8")

    print(f"  wrote {C.SECTIONS_JSONL.relative_to(C.ROOT)} ({len(sections)} sections)")
    print(f"  wrote {C.ACTIONS_CSV.relative_to(C.ROOT)} ({len(actions)} actions)")
    print(f"  wrote {C.CROSSCHECK.relative_to(C.ROOT)}")
    if not records:
        print("\n  No statute records yet -- the cross-check reports the baseline "
              "only. Run run_sweep.py once the permission gate is cleared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
