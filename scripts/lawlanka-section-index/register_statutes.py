"""Phase 2 -- give the swept-but-unregistered statutes a `source_id`.

The sweep indexes enactments the corpus cites but the registry has never held.
Their sections exist in `sections.jsonl` with an empty `source_id`, so nothing
can link to them: the linker keys on `source_id`, and a section list with no id
is unreachable.

This appends a registry row per enactment and writes the new id back into the
sweep outputs. It is idempotent -- an enactment already registered (by act code
or by title) is skipped, so re-running after a wider sweep only picks up what is
genuinely new.

Registry rows land with `status: index-only`:

  * `local_pdf_path` / `local_markdown_path` stay empty. We hold the section
    numbering and headings, not the text.
  * They are deliberately NOT added to `data/processed/documents.csv`.
    `src/draftly/retrieval/corpus.py` asserts
    `EXPECTED_COUNTS = {"statute": 57, "amendment": 18}` against that file and
    raises if it disagrees, and a statute with no text has nothing to
    contribute to a text index anyway.

Editing the registry does change `corpus_fingerprint()` -- it hashes
`source-registry.csv` bytes -- so the BM25 index rebuilds once on next use.
That is expected, not a failure.

Usage:
    python scripts/lawlanka-section-index/register_statutes.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as C

STATUS = "index-only"
NOTE = ("Section numbering and marginal-note headings only, from the structural "
        "sweep. No official PDF held; absent from documents.csv, so it is not in "
        "the retrieval text corpus.")

# Registry titles read "Matrimonial Rights and Inheritance Ordinance", not
# "Matrimonial Rights And Inheritance Ordinance".
LOWER = {"of", "and", "on", "for", "the", "to", "in", "a", "an", "or", "by",
         "with", "under", "upon"}


def title_case(name: str) -> str:
    words = re.split(r"(\s+)", name.strip())
    out = []
    for i, w in enumerate(words):
        if not w.strip():
            out.append(w)
            continue
        low = w.lower()
        out.append(low if (i > 0 and low in LOWER) else low[:1].upper() + low[1:])
    return "".join(out)


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()


def load_registry_rows() -> tuple[list[str], list[dict]]:
    with C.REGISTRY.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def next_free_id(rows: list[dict]) -> int:
    nums = [int(r["source_id"][3:]) for r in rows
            if re.fullmatch(r"SRC\d+", r.get("source_id", "") or "")]
    return (max(nums) + 1) if nums else 1


def unregistered(records: list[dict]) -> dict[str, dict]:
    """act_code -> {name, sections, url} for rows carrying no source_id."""
    out: dict[str, dict] = {}
    for r in records:
        if str(r.get("source_id", "")).startswith("SRC"):
            continue
        code = r.get("act_code", "")
        if not code:
            continue
        e = out.setdefault(code, {"name": r.get("statute_name", ""),
                                  "sections": 0,
                                  "url": r.get("source_url", "")})
        e["sections"] += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the rows that would be appended, write nothing")
    args = ap.parse_args()

    if not C.SECTIONS_JSONL.exists():
        raise SystemExit(f"no {C.SECTIONS_JSONL.name}: run build_outputs.py first")
    records = [json.loads(l) for l in
               C.SECTIONS_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]

    fieldnames, rows = load_registry_rows()
    by_title = {norm_title(r["official_title"]): r["source_id"] for r in rows}
    # An act code already written into a registry row's notes means we did this
    # before; the title check catches the rest.
    known_codes = {c for r in rows for c in re.findall(r"\b\d{4}Y\d+V\d+C\w*\b",
                                                       r.get("notes", "") or "")}

    todo = unregistered(records)
    new_rows, skipped = [], []
    code_to_id: dict[str, str] = {}
    nxt = next_free_id(rows)
    for code, info in sorted(todo.items(), key=lambda kv: -kv[1]["sections"]):
        title = title_case(info["name"])
        if code in known_codes or norm_title(title) in by_title:
            skipped.append((title, by_title.get(norm_title(title), code)))
            continue
        sid = f"SRC{nxt:03d}"
        nxt += 1
        by_title[norm_title(title)] = sid
        code_to_id[code] = sid
        row = {c: "" for c in fieldnames}
        row.update({
            "source_id": sid,
            "official_title": title,
            "source_type": "statute",
            "status": STATUS,
            "notes": f"{NOTE} Act code {code}; {info['sections']} sections.",
        })
        new_rows.append(row)

    print(f"unregistered enactments in {C.SECTIONS_JSONL.name}: {len(todo)}")
    print(f"  already registered : {len(skipped)}")
    print(f"  to append          : {len(new_rows)}")
    for r in new_rows:
        print(f"    {r['source_id']}  {r['official_title']}")
    if skipped:
        print("  skipped (already present):")
        for t, sid in skipped:
            print(f"    {sid}  {t}")

    if args.dry_run or not new_rows:
        return 0

    # Append rather than rewrite, so existing rows keep their exact quoting.
    text = C.REGISTRY.read_text(encoding="utf-8-sig")
    with C.REGISTRY.open("a", encoding="utf-8", newline="") as f:
        if not text.endswith("\n"):
            f.write("\n")
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writerows(new_rows)
    print(f"\n  appended {len(new_rows)} rows to {C.REGISTRY.relative_to(C.ROOT)}")

    # Write the ids back so sections.jsonl and the url map are self-describing.
    patched = 0
    for r in records:
        if not str(r.get("source_id", "")).startswith("SRC"):
            sid = code_to_id.get(r.get("act_code", ""))
            if sid:
                r["source_id"] = sid
                patched += 1
    C.SECTIONS_JSONL.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8")
    print(f"  wrote source_id into {patched} rows of {C.SECTIONS_JSONL.name}")

    if C.STATUTE_MAP.exists():
        with C.STATUTE_MAP.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cols, maprows = list(reader.fieldnames or []), list(reader)
        n = 0
        for r in maprows:
            if not r.get("source_id") and code_to_id.get(r.get("act_code", "")):
                r["source_id"] = code_to_id[r["act_code"]]
                n += 1
        with C.STATUTE_MAP.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(maprows)
        print(f"  wrote source_id into {n} rows of {C.STATUTE_MAP.name}")

    print("\n  note: the BM25 index rebuilds once on next use "
          "(corpus_fingerprint hashes source-registry.csv).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
