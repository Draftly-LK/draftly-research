"""Split the corpus into PRIMARY-STATUES.md and SECONDARY-STATUES.md.

Primary is what the proposed curriculum names in its Category 1-3 statute
tables. Secondary is everything the corpus holds that the curriculum does not
name. Re-running produces byte-identical output; nothing calls the network.

    uv run python apps/statute-browser/build_statute_tiers.py
    uv run python apps/statute-browser/build_statute_tiers.py --check

Matching a curriculum row to a registry row is done on the Act number and year
first, then on the title. Both are unreliable on their own, so `OVERRIDES`
below pins the rows where they disagree, and `--audit` prints every match with
the method used so the mapping can be checked by hand.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import re
import sys
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from loader import REPO_ROOT, SOURCE_REGISTRY_CSV, load_statutes  # noqa: E402

CURRICULUM = REPO_ROOT / "proj-docs/project Management/Proposed Curriculum Conveyancing Course.md"
PRIMARY_OUT = APP_DIR / "PRIMARY-STATUES.md"
SECONDARY_OUT = APP_DIR / "SECONDARY-STATUES.md"

CATEGORY_NAMES = {
    "1": "Category 1 (Most Important)",
    "2": "Category 2 (More Important)",
    "3": "Category 3 (Important)",
}

# Curriculum serial -> source_id, for rows where number-and-year matching lands
# on the wrong statute. Each one is a discrepancy in the curriculum document.
OVERRIDES = {
    # Cites "No.21 of 1844", which is the Wills Ordinance. The registry has the
    # Powers of Attorney Ordinance as No. 4 of 1902.
    "017": "SRC017",
    # "Crown Lands Ordinance" is the pre-1972 name of the State Lands Ordinance,
    # already listed at serials 037 and 047.
    "057": "SRC056",
}

STOPWORDS = {"ordinance", "act", "law", "code", "the", "of", "and", "no", "statute", "on", "ground"}
NUMBER_YEAR = re.compile(r"\bN[o°]?\.?\s*(\d+)\s+of\s+(\d{4})", re.IGNORECASE)


def _stem(title: str) -> str:
    title = NUMBER_YEAR.sub("", title)
    words = re.sub(r"[^a-zA-Z ]", " ", title).lower().split()
    return " ".join(sorted(re.sub(r"s\b", "", w) for w in words if w and w not in STOPWORDS))


def _number_year(title: str) -> tuple[str, str] | None:
    match = NUMBER_YEAR.search(title)
    return (str(int(match.group(1))), match.group(2)) if match else None


def read_registry() -> list[dict[str, str]]:
    with SOURCE_REGISTRY_CSV.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def read_curriculum() -> list[dict[str, str]]:
    """Serial, category and raw title from the Category 1-3 statute tables."""
    body = CURRICULUM.read_text(encoding="utf-8")
    body = body.split("## 3. Statutory Law")[1].split("## 4. Case Law")[0]
    entries, category = [], None
    for line in body.splitlines():
        heading = re.match(r"### Category (\d)", line)
        if heading:
            category = heading.group(1)
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"\d{3}", cells[0] or ""):
            entries.append(
                {
                    "serial": cells[0],
                    "category": category,
                    "title": cells[2],
                    "amendments": cells[3] if len(cells) > 3 else "",
                }
            )
    return entries


def match_curriculum() -> tuple[list[dict], list[dict]]:
    """Resolve each curriculum row to a source_id. Returns (matched, unmatched)."""
    registry = read_registry()
    by_number = {}
    stems = {}
    for row in registry:
        if row["act_or_ordinance_no"] and row["year"].isdigit():
            by_number[(str(int(row["act_or_ordinance_no"])), row["year"])] = row["source_id"]
        stems[row["source_id"]] = _stem(row["official_title"])

    matched, unmatched = [], []
    for entry in read_curriculum():
        source_id, method = None, ""
        if entry["serial"] in OVERRIDES:
            source_id, method = OVERRIDES[entry["serial"]], "override"
        if not source_id:
            key = _number_year(entry["title"])
            if key and key in by_number:
                source_id, method = by_number[key], "number+year"
        if not source_id:
            close = difflib.get_close_matches(_stem(entry["title"]), list(stems.values()), n=1, cutoff=0.80)
            if close:
                source_id = next(k for k, v in stems.items() if v == close[0])
                method = "title"
        if source_id:
            matched.append({**entry, "source_id": source_id, "method": method})
        else:
            unmatched.append(entry)
    return matched, unmatched


def _statute_rows() -> dict[str, dict]:
    return {row["source_id"]: row for row in load_statutes().to_dict("records")}


def _registry_titles() -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in read_registry()}


def _cite(registry_row: dict[str, str]) -> str:
    number, year = registry_row.get("act_or_ordinance_no"), registry_row.get("year")
    if number and year and year.isdigit() and year != "0":
        return f"No. {number} of {year}"
    return "not recorded"


def _changes(row: dict | None) -> str:
    if not row or pd.isna(row["first_change"]):
        return "none recorded"
    if row["first_change"] == row["last_change"]:
        return str(row["first_change"])
    return f"{row['first_change']}-{row['last_change']}"


def render_primary(matched: list[dict], unmatched: list[dict]) -> str:
    statutes = _statute_rows()
    registry = _registry_titles()

    # One row per statute. Where the curriculum lists a statute twice, keep the
    # strongest category and record every serial that points at it.
    merged: dict[str, dict] = {}
    for entry in matched:
        current = merged.setdefault(
            entry["source_id"], {"category": entry["category"], "serials": []}
        )
        current["serials"].append(entry["serial"])
        current["category"] = min(current["category"], entry["category"])

    extracted = [s for s in merged if s in statutes]
    missing = [s for s in merged if s not in statutes]

    lines = [
        "# Primary statutes",
        "",
        f"The {len(merged)} statutes named in the statute tables of",
        "`proj-docs/project Management/Proposed Curriculum Conveyancing Course.md`,",
        "grouped by the category the curriculum assigns.",
        "Generated by `build_statute_tiers.py`; do not edit by hand.",
        "",
        f"The curriculum lists {len(matched) + len(unmatched)} rows, which resolve to "
        f"{len(merged)} distinct statutes; the rest are repeats.",
        f"{len(extracted)} have their sections extracted and appear in the browser.",
        f"**{len(missing)} do not** and are listed separately at the end.",
        "",
        "`Changed` is the span of years in which some section was amended.",
        "`none recorded` means no amendment history was harvested, which is not the",
        "same as unchanged. Every row is `status=unverified`.",
        "",
    ]

    for category in ("1", "2", "3"):
        group = sorted(
            (s for s in extracted if merged[s]["category"] == category),
            key=lambda s: min(merged[s]["serials"]),
        )
        if not group:
            continue
        lines += [f"## {CATEGORY_NAMES[category]}", "", _primary_table(group, merged, statutes, registry)]

    if missing:
        lines += [
            "## Named in the curriculum but not extracted",
            "",
            "These are downloaded and sit in `data/legal-sources/library/`, but the",
            "section index holds no sections for them, so they do not appear in the",
            "browser and nothing can be retrieved from them.",
            "",
            "| Serial | Cat | Statute | Citation | Registry status |",
            "| --- | --- | --- | --- | --- |",
        ]
        for source_id in sorted(missing, key=lambda s: min(merged[s]["serials"])):
            row = registry[source_id]
            lines.append(
                f"| {', '.join(sorted(merged[source_id]['serials']))} "
                f"| {merged[source_id]['category']} | {row['official_title']} "
                f"| {_cite(row)} | {row['status']} |"
            )
        lines.append("")

    if unmatched:
        lines += [
            "## Not found in the registry",
            "",
            "| Serial | Cat | As written in the curriculum |",
            "| --- | --- | --- |",
        ]
        for entry in unmatched:
            lines.append(f"| {entry['serial']} | {entry['category']} | {entry['title']} |")
        lines.append("")

    lines += _discrepancies(matched, registry)
    return "\n".join(lines).rstrip() + "\n"


OVERRIDE_NOTES = {
    "017": "No. 21 of 1844 is the Wills Ordinance, listed separately at serial 018.",
    "057": "Pre-1972 name of the State Lands Ordinance, already listed at serials 037 and 047.",
}


def _discrepancies(matched: list[dict], registry: dict[str, dict[str, str]]) -> list[str]:
    """Rows where the curriculum's citation does not match the registry's."""
    rows = []
    for entry in matched:
        cited = _number_year(entry["title"])
        row = registry[entry["source_id"]]
        held = (
            (str(int(row["act_or_ordinance_no"])), row["year"])
            if row["act_or_ordinance_no"] and row["year"].isdigit()
            else None
        )
        if not cited or not held or cited == held:
            continue
        note = OVERRIDE_NOTES.get(entry["serial"], "-")
        rows.append(
            f"| {entry['serial']} | {entry['title']} | {row['official_title']}, "
            f"No. {held[0]} of {held[1]} | {note} |"
        )
    if not rows:
        return []
    return [
        "## Citation discrepancies",
        "",
        f"{len(rows)} curriculum rows cite an Act number or year the registry does not",
        "hold. The statute was still matched, by title or by a pinned entry in",
        "`OVERRIDES`. Which citation is correct is a question for the curriculum",
        "author, not something this script can settle.",
        "",
        "| Serial | As written in the curriculum | Registry holds | Note |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
    ]


def _primary_table(group, merged, statutes, registry) -> str:
    rows = [
        "| Serial | Statute | Citation | Sections | Amended | Changed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for source_id in group:
        row = statutes[source_id]
        rows.append(
            f"| {', '.join(sorted(merged[source_id]['serials']))} | {row['statute']} "
            f"| {_cite(registry.get(source_id, {}))} | {row['sections']} "
            f"| {row['amended_sections']} | {_changes(row)} |"
        )
    rows.append("")
    return "\n".join(rows)


def render_secondary(matched: list[dict]) -> str:
    statutes = _statute_rows()
    named = {entry["source_id"] for entry in matched}
    rest = [row for source_id, row in statutes.items() if source_id not in named]
    in_registry = sorted((r for r in rest if r["in_registry"]), key=lambda r: -r["sections"])
    index_only = sorted((r for r in rest if not r["in_registry"]), key=lambda r: -r["sections"])

    lines = [
        "# Secondary statutes",
        "",
        f"The {len(rest)} statutes the corpus holds structure for that the proposed",
        "curriculum does not name in its statute tables.",
        "Generated by `build_statute_tiers.py`; do not edit by hand.",
        "",
        "Absence from the curriculum's tables is not a decision to drop a statute.",
        "Several of these are used in conveyancing practice regardless. Treat this",
        "as the list to review, not the list to delete. Every row is",
        "`status=unverified`.",
        "",
        f"## In the registry ({len(in_registry)})",
        "",
        "Curated sources with a registry row and a downloaded PDF.",
        "",
        _secondary_table(in_registry),
        f"## Index-only ({len(index_only)})",
        "",
        "Section numbers and headings only. These were dropped from",
        "`source-registry.csv` because the corpus never held their verified text, so",
        "nothing can be cited from them. Their titles come from",
        "`data/legal-sources/extra-statues-to-topics.md`, a proposed mapping.",
        "",
        _secondary_table(index_only),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _secondary_table(rows) -> str:
    out = [
        "| Statute | Dated | Sections | Amended | Changed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        dated = row["dated_year"] if pd.notna(row["dated_year"]) else "?"
        out.append(
            f"| {row['statute']} | {dated} | {row['sections']} "
            f"| {row['amended_sections']} | {_changes(row)} |"
        )
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if either file is stale")
    parser.add_argument("--audit", action="store_true", help="print every match and its method")
    args = parser.parse_args()

    matched, unmatched = match_curriculum()

    if args.audit:
        registry = _registry_titles()
        statutes = _statute_rows()
        for entry in matched:
            title = registry[entry["source_id"]]["official_title"]
            similarity = difflib.SequenceMatcher(
                None, _stem(entry["title"]), _stem(title)
            ).ratio()
            flag = "  <-- CHECK" if similarity < 0.6 else ""
            extracted = "" if entry["source_id"] in statutes else "  [not extracted]"
            print(
                f"{entry['serial']} cat{entry['category']} via {entry['method']:11} "
                f"{entry['source_id']}  {title}{extracted}{flag}"
            )
        for entry in unmatched:
            print(f"{entry['serial']} cat{entry['category']} UNMATCHED   {entry['title']}")
        return 0

    outputs = {PRIMARY_OUT: render_primary(matched, unmatched), SECONDARY_OUT: render_secondary(matched)}
    if args.check:
        stale = [
            path.name
            for path, text in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
        if stale:
            print(f"stale: {', '.join(stale)}; re-run without --check", file=sys.stderr)
            return 1
        print("PRIMARY-STATUES.md and SECONDARY-STATUES.md are up to date")
        return 0

    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
