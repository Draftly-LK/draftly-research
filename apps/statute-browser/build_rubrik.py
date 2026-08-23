"""Write `RUBRIK.md`: every statute, its amendments, and where the files are.

A register rather than a narrative. For each statute it records the citation,
the Chapter number where one can be read off the PDF, commencement, curriculum
category, section count, every local file held for it, and every amending
instrument known from either source, with the local path of that amendment or
the reason it is not held.

Amendments are known from four independent places, and the register says which:

    chain       the header block of the consolidated PDF, read by
                scripts/extract_amendment_chains.py
    marker      an inline `[section, Act of Year]` marker in the section index,
                which is where actions.csv comes from
    html        the chain in LankaLaw's HTML edition, read by
                scripts/parse_lankalaw_html.py
    curriculum  the Amendment/s column of the course statute tables

Re-running produces byte-identical output.

    uv run python apps/statute-browser/build_rubrik.py
    uv run python apps/statute-browser/build_rubrik.py --check
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

OUTPUT = APP_DIR / "RUBRIK.md"
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
SECTION_INDEX = REPO_ROOT / "data/legal-sources/manifests/statute-section-index.json"
CHAINS = REPO_ROOT / "data/processed/amendment-chains.csv"
HTML_CHAINS = REPO_ROOT / "data/processed/lankalaw-html-chains.csv"
HTML_SECTIONS = REPO_ROOT / "data/processed/lankalaw-html-sections.json"
CANONICAL_DIR = REPO_ROOT / "data/processed/canonical-statutes"
AMENDMENT_HTML = REPO_ROOT / "data/processed/lankalaw-amendment-downloads.csv"
FINALIZED_DIR = REPO_ROOT / "data/legal-sources/library/finalized"
ACTIONS = REPO_ROOT / "data/processed/actions.csv"
DOWNLOADS = REPO_ROOT / "data/processed/amendment-chain-downloads.csv"
COMMENCEMENT = REPO_ROOT / "data/processed/statute_commencement.csv"
EXTRA_TITLES = REPO_ROOT / "data/legal-sources/extra-statues-to-topics.md"
TOPICS = REPO_ROOT / "data/processed/topics.csv"

STATUTES = REPO_ROOT / "data/legal-sources/library/statutes"
AMENDMENTS = REPO_ROOT / "data/legal-sources/library/amendments"
CAP_CACHE = REPO_ROOT / "data/processed/statute-chapter-numbers.csv"

LEADING_NUMBER_YEAR = re.compile(r"^(\d{1,3})-(1[78]\d{2}|19\d{2}|20\d{2})-")
CAP = re.compile(r"\bCap(?:\.|ITER)?\s*(\d{1,3})\b", re.IGNORECASE)
# A Chapter number printed once is usually a cross-reference to another statute.
# The statute's own number repeats in the running header on every page.
CAP_MIN_OCCURRENCES = 3
EXTRA_ROW = re.compile(r"^\|\s*(SRC\d+)\s*[-—–]\s*([^|]+?)\s*\|")

# Short reasons for the register. The full outcome stays in
# data/processed/amendment-chain-downloads.csv.
CATEGORY_NAMES = {
    "1": "Category 1 (Most Important)",
    "2": "Category 2 (More Important)",
    "3": "Category 3 (Important)",
}

NOT_HELD = {
    "not-in-dataset (pre-1950, or a Law rather than an Act)": "not in the Act archive",
    "content-mismatch-title-page": "archive copy is a different Act",
    "error: ValueError": "archive row has no URL",
    "not-a-pdf": "archive returned no PDF",
    "already-held": "held under another name",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def chapter_numbers(registry: list[dict[str, str]]) -> dict[str, str]:
    """Read each statute's Chapter number off its PDF, cached to keep runs fast."""
    if CAP_CACHE.exists():
        return {r["source_id"]: r["chapter"] for r in read_csv(CAP_CACHE) if r["chapter"]}

    found = {}
    for row in registry:
        pdf = REPO_ROOT / (row.get("local_pdf_path") or "")
        if not row.get("local_pdf_path") or not pdf.exists():
            continue
        if pdf.name.startswith("legislative-enactments") or pdf.suffix.lower() != ".pdf":
            continue
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "6", "-layout", str(pdf), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        counts = collections.Counter(m.group(1) for m in CAP.finditer(result.stdout))
        if counts:
            number, hits = counts.most_common(1)[0]
            if hits >= CAP_MIN_OCCURRENCES:
                found[row["source_id"]] = number

    with CAP_CACHE.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# Chapter (Cap.) number read from the running header of each statute PDF.\n"
            f"# Only recorded where the number repeats at least {CAP_MIN_OCCURRENCES} times, so a\n"
            "# one-off cross-reference to another statute is not mistaken for this one's.\n"
            "# Generated by apps/statute-browser/build_rubrik.py. status=unverified.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=["source_id", "chapter"])
        writer.writeheader()
        for source_id in sorted(found):
            writer.writerow({"source_id": source_id, "chapter": found[source_id]})
    return found


def finalized_files() -> dict[tuple[int, int], str]:
    """Statutes signed off into `library/finalized`, keyed (number, year).

    A finalized file is a canonical tree that someone has accepted, so it is the
    one to build on. The canonical directory is regenerated output and can change
    under you; this does not.
    """
    found = {}
    if not FINALIZED_DIR.exists():
        return found
    for file in sorted(FINALIZED_DIR.rglob("*.json")):
        match = LEADING_NUMBER_YEAR.match(file.stem)
        if match:
            found[(int(match.group(1)), int(match.group(2)))] = rel(file)
    return found


def local_amendment_files() -> dict[tuple[int, int], dict[str, list[str]]]:
    """(number, year) -> {pdf: [...], html: [...]}, from the normalised names."""
    held: dict[tuple[int, int], dict[str, list[str]]] = collections.defaultdict(
        lambda: {"pdf": [], "html": []}
    )
    for directory in (AMENDMENTS, AMENDMENTS / "incoming", AMENDMENTS / "html"):
        if not directory.exists():
            continue
        for pattern in ("*.pdf", "*.html"):
            for file in sorted(directory.glob(pattern)):
                match = LEADING_NUMBER_YEAR.match(file.stem)
                if match:
                    key = (int(match.group(1)), int(match.group(2)))
                    held[key][file.suffix.lstrip(".").lower()].append(rel(file))
    return held


def statute_files(row: dict[str, str], source_id: str) -> list[tuple[str, str]]:
    """Every file on disk for this statute, labelled."""
    files = []
    for label, column in (
        ("PDF", "local_pdf_path"),
        ("Parsed JSON", "local_parsed_path"),
        ("Markdown", "local_markdown_path"),
    ):
        value = row.get(column) or ""
        if not value:
            continue
        path = REPO_ROOT / value
        files.append((label, value, path.exists()))

    number, year = row.get("act_or_ordinance_no", ""), row.get("year", "")
    if number and year.isdigit() and year != "0":
        prefix = f"{int(number)}-{year}-"
        for html in sorted((STATUTES / "HTML").glob(f"{prefix}*.html")):
            files.append(("HTML", rel(html), True))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if RUBRIK.md is stale")
    args = parser.parse_args()

    registry = {r["source_id"]: r for r in read_csv(REGISTRY)}
    index = json.loads(SECTION_INDEX.read_text(encoding="utf-8"))
    chains = read_csv(CHAINS) if CHAINS.exists() else []
    html_chains = read_csv(HTML_CHAINS) if HTML_CHAINS.exists() else []
    html_sections = (
        json.loads(HTML_SECTIONS.read_text(encoding="utf-8")) if HTML_SECTIONS.exists() else {}
    )
    actions = read_csv(ACTIONS)
    downloads = {
        (int(r["instrument_no"]), int(r["instrument_year"])): r
        for r in (read_csv(DOWNLOADS) if DOWNLOADS.exists() else [])
    }
    commencement = {r["source_id"]: r["commencement"] for r in read_csv(COMMENCEMENT)}
    topic_names = {r["topic_id"]: r["name"] for r in read_csv(TOPICS)}
    held = local_amendment_files()
    caps = chapter_numbers(list(registry.values()))
    structure = canonical_structure()
    finalized = finalized_files()
    html_outcomes = {
        (int(r["instrument_no"]), int(r["instrument_year"])): r
        for r in (read_csv(AMENDMENT_HTML) if AMENDMENT_HTML.exists() else [])
    }

    extra_titles = {}
    if EXTRA_TITLES.exists():
        for line in EXTRA_TITLES.read_text(encoding="utf-8").splitlines():
            match = EXTRA_ROW.match(line.strip())
            if match:
                extra_titles[match.group(1)] = match.group(2).strip()

    # Amendments per statute, from both sources, keyed (number, year).
    amendments: dict[str, dict[tuple[int, int], dict]] = collections.defaultdict(dict)
    for row in chains:
        if row["role"] != "amending":
            continue
        key = (int(row["instrument_no"]), int(row["instrument_year"]))
        entry = amendments[row["source_id"]].setdefault(
            key, {"type": row["instrument_type"], "sources": set()}
        )
        entry["sources"].add("chain")
    for row in html_chains:
        if row["role"] != "amending":
            continue
        key = (int(row["instrument_no"]), int(row["instrument_year"]))
        entry = amendments[row["source_id"]].setdefault(
            key, {"type": row["instrument_type"], "sources": set()}
        )
        entry["type"] = entry["type"] or row["instrument_type"]
        entry["sources"].add("html")
    for source_id, listed in curriculum_amendments().items():
        for key in listed:
            entry = amendments[source_id].setdefault(key, {"type": "", "sources": set()})
            entry["sources"].add("curriculum")
    for row in actions:
        if not row["amending_act_no"].isdigit() or not row["amending_year"].isdigit():
            continue
        key = (int(row["amending_act_no"]), int(row["amending_year"]))
        entry = amendments[row["source_id"]].setdefault(key, {"type": "", "sources": set()})
        entry["sources"].add("marker")

    curriculum = curriculum_categories()
    body = render(
        registry, index, amendments, held, downloads, commencement, topic_names,
        caps, extra_titles, curriculum, html_sections, structure, html_outcomes, finalized,
    )

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != body:
            print("RUBRIK.md is stale; re-run without --check", file=sys.stderr)
            return 1
        print("RUBRIK.md is up to date")
        return 0

    OUTPUT.write_text(body, encoding="utf-8")
    print(f"wrote {rel(OUTPUT)}")
    return 0


def canonical_structure() -> dict[str, dict]:
    """Counts per level from the canonical tree, so a flat section total does
    not hide that the Companies Act runs Part -> crossheading -> section."""
    summaries = {}
    if not CANONICAL_DIR.exists():
        return summaries
    for file in sorted(CANONICAL_DIR.glob("*.json")):
        document = json.loads(file.read_text(encoding="utf-8"))
        counts = collections.Counter()
        references = 0

        def walk(nodes):
            nonlocal references
            for node in nodes:
                counts[node["type"]] += 1
                references += len(node.get("cross_references", []))
                walk(node.get("children", []))

        walk(document["body"])
        summaries[document["source_id"]] = {
            "counts": counts,
            "cross_references": references,
            "schedules_referenced": document.get("schedules_referenced", []),
            "path": file.relative_to(REPO_ROOT).as_posix(),
        }
    return summaries


def curriculum_amendments() -> dict[str, set[tuple[int, int]]]:
    """The curriculum's own "Amendment/s" column, a source neither chain nor
    marker covers. It is how the Apartment Ownership amendments are known."""
    try:
        from build_statute_tiers import match_curriculum, read_curriculum
    except Exception:  # noqa: BLE001
        return {}
    by_serial = {e["serial"]: e["source_id"] for e in match_curriculum()[0]}
    listed: dict[str, set[tuple[int, int]]] = collections.defaultdict(set)
    for entry in read_curriculum():
        source_id = by_serial.get(entry["serial"])
        if not source_id:
            continue
        for number, year in re.findall(r"(\d{1,3})\s*of\s*(1[89]\d{2}|20\d{2})", entry["amendments"]):
            listed[source_id].add((int(number), int(year)))
    return listed


def curriculum_categories() -> dict[str, str]:
    try:
        from build_statute_tiers import match_curriculum
    except Exception:  # noqa: BLE001 - the register still works without it
        return {}
    matched, _ = match_curriculum()
    best: dict[str, str] = {}
    for entry in matched:
        current = best.get(entry["source_id"])
        best[entry["source_id"]] = min(current, entry["category"]) if current else entry["category"]
    return best


def render(
    registry, index, amendments, held, downloads, commencement, topic_names,
    caps, extra_titles, curriculum, html_sections, structure, html_outcomes, finalized,
) -> str:
    # Scope is the curriculum's own statute list, the same set as
    # PRIMARY-STATUES.md. Everything else the corpus happens to hold is out.
    ordered = sorted(
        curriculum,
        key=lambda s: (
            curriculum[s],
            (registry.get(s, {}).get("official_title") or extra_titles.get(s, s)).lower(),
        ),
    )

    total_amendments = sum(len(amendments.get(s, {})) for s in ordered)
    total_held = sum(
        1 for s in ordered for key in amendments.get(s, {}) if key in held
    )
    extracted = sum(1 for s in ordered if s in index)

    lines = [
        "# Primary statute and amendment register",
        "",
        f"The {len(ordered)} statutes named in the curriculum's Category 1 to 3 tables,",
        "the same set as `PRIMARY-STATUES.md`, with the local files held for each and",
        f"every amending instrument known for it ({total_amendments} in total, of which",
        f"{total_held} are held locally).",
        "",
        f"{extracted} of the {len(ordered)} have their sections extracted; the rest are",
        "marked below. Statutes the corpus holds but the curriculum does not name are",
        "listed in `SECONDARY-STATUES.md` and are out of scope here.",
        "",
        "Generated by `build_rubrik.py`; do not edit by hand. Paths are relative to the",
        "repository root. Every row is `status=unverified`.",
        "",
        "## How to read this",
        "",
        "An amendment is known from one or more of four independent sources, and the",
        "`Known from` column says which:",
        "",
        "- `chain` is the header block printed at the front of the consolidated statute,",
        "  which lists every instrument folded into the text.",
        "- `marker` is an inline `[section, Act of Year]` marker against a specific",
        "  section, so it also tells you which section changed.",
        "- `html` is the chain in LankaLaw's HTML edition of the statute, which covers",
        "  statutes whose PDF header block could not be read.",
        "- `curriculum` is the Amendment/s column of the course statute tables.",
        "",
        "`Own text` is the amending Act itself, which is a different document from the",
        "consolidated statute that already has it folded in. The PDF copies are image",
        "scans from the Act archive; the HTML copies are born-digital and machine",
        "readable. LankaLaw publishes standalone Acts for roughly 1960 to 2009 only,",
        "so `not published as HTML` outside that window is expected.",
        "",
        "An instrument known only from `chain` amended the statute somewhere, but the",
        "corpus does not record which section. An instrument known only from `marker`",
        "did not appear in the header block, usually because the consolidation predates",
        "it. `Local file` is the amending Act's own text, which is separate from the",
        "consolidated statute that already has it folded in.",
        "",
        "`Chapter` is read off the running header of the statute PDF and is only",
        "recorded where it repeats, so a single cross-reference to another statute is",
        "not mistaken for this one's. Absence means unresolved, not absent in law.",
        "",
        "A local file is matched to an instrument on Act number and year alone, and no",
        "title page has been read back. Expect the file's own title to differ from the",
        "statute it amends: an omnibus Act such as a Finance Act amends many statutes",
        "under its own name. That is normal, and it is also what a wrong match looks",
        "like, so treat any surprising pairing as unconfirmed until someone opens it.",
        "",
    ]

    lines += [
        "## Summary",
        "",
        "| Cat | Statute | Citation | Sections | Amendments known | Held | Final |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for source_id in ordered:
        row = registry.get(source_id, {})
        title = row.get("official_title") or extra_titles.get(source_id, source_id)
        known = amendments.get(source_id, {})
        sections = str(len(index[source_id])) if source_id in index else "not extracted"
        key = citation_key(row)
        lines.append(
            f"| {curriculum[source_id]} | {title} | {cite(row)} | {sections} "
            f"| {len(known)} | {sum(1 for k in known if k in held)} "
            f"| {'yes' if key and key in finalized else '-'} |"
        )
    lines.append("")

    for category in ("1", "2", "3"):
        group = [s for s in ordered if curriculum[s] == category]
        if not group:
            continue
        lines += [f"## {CATEGORY_NAMES[category]} ({len(group)})", ""]
        for source_id in group:
            lines += statute_block(
                source_id, registry.get(source_id, {}), index, amendments, held,
                downloads, commencement, topic_names, caps, curriculum, extra_titles,
                html_sections, structure, html_outcomes, finalized,
            )

    return "\n".join(lines).rstrip() + "\n"


def citation_key(row: dict[str, str]) -> tuple[int, int] | None:
    number, year = row.get("act_or_ordinance_no", ""), row.get("year", "")
    if number.isdigit() and year.isdigit() and year != "0":
        return int(number), int(year)
    return None


def cite(row: dict[str, str]) -> str:
    number, year = row.get("act_or_ordinance_no", ""), row.get("year", "")
    if number and year.isdigit() and year != "0":
        return f"No. {number} of {year}"
    return "not recorded"


def statute_block(
    source_id, row, index, amendments, held, downloads, commencement, topic_names,
    caps, curriculum, extra_titles, html_sections, structure, html_outcomes, finalized,
) -> list[str]:
    title = row.get("official_title") or extra_titles.get(source_id, source_id)
    entries = index.get(source_id, [])
    heading_sources = collections.Counter(e.get("heading_source", "none") for e in entries)

    facts = [f"**{cite(row)}**"]
    if source_id in caps:
        facts.append(f"Cap. {caps[source_id]}")
    if commencement.get(source_id):
        facts.append(f"commenced {commencement[source_id]}")
    if source_id in curriculum:
        facts.append(f"curriculum category {curriculum[source_id]}")
    facts.append(source_id)
    key = citation_key(row)
    if key and key in finalized:
        facts.append("**finalized**")
    if source_id not in index:
        facts.append("**sections not extracted**")

    lines = [f"### {title}", "", " · ".join(facts), ""]

    topics = [t for t in (row.get("topics") or "").split(";") if t]
    if topics:
        lines += [f"Topics: {', '.join(topic_names.get(t, t) for t in topics)}", ""]

    parsed = html_sections.get(source_id, [])
    if entries:
        detail = f"(headings from {', '.join(f'{k} {v}' for k, v in heading_sources.most_common())})"
        lines += [f"Sections: {len(entries)} in the index {detail}", ""]
    else:
        lines += [
            "Sections: none in the index. Nothing from this statute can be retrieved or",
            "cited until they are extracted.",
            "",
        ]
    if parsed:
        marked = sum(1 for section in parsed if section["amendment_markers"])
        merged = sum(1 for e in entries if "lankalaw-html" in e.get("present_in", []))
        if merged >= len(parsed):
            state = "Merged into the index by `scripts/merge_html_sections_into_index.py`."
        elif merged:
            state = f"{merged} of them merged into the index; the rest are not."
        else:
            state = "Not yet merged into the index."
        lines += [
            f"Parsed from the HTML edition: {len(parsed)} sections, {marked} carrying an "
            f"amendment marker. {state}",
            "",
        ]
    shape = structure.get(source_id)
    if shape:
        counts = shape["counts"]
        order = ("part", "chapter", "crossheading", "subheading", "section",
                 "subsection", "definition", "paragraph", "subparagraph")
        parts = [f"{counts[k]} {k}{'s' if counts[k] != 1 else ''}" for k in order if counts[k]]
        lines += [f"Canonical structure: {', '.join(parts)}."]
        extra = []
        if shape["cross_references"]:
            extra.append(f"{shape['cross_references']} cross-references")
        if shape["schedules_referenced"]:
            extra.append(f"{len(shape['schedules_referenced'])} schedules referenced (bodies not published)")
        if extra:
            lines.append(f"{'; '.join(extra).capitalize()}.")
        lines += [f"Tree: `{shape['path']}`", ""]
    if key and key in finalized:
        lines += [
            f"Finalized: `{finalized[key]}`",
            "",
            "This tree has been accepted. Build on it rather than on the canonical",
            "directory, which is regenerated output.",
            "",
        ]

    files = statute_files(row, source_id)
    if files:
        lines.append("Files:")
        lines.append("")
        for label, path, exists in files:
            suffix = "" if exists else "  (recorded in the registry but not on disk)"
            lines.append(f"- {label}: `{path}`{suffix}")
        lines.append("")
    else:
        lines += ["Files: none held.", ""]

    known = amendments.get(source_id, {})
    if not known:
        lines += [
            "Amendments: none recorded. This means no amendment history was found, "
            "which is not the same as unchanged.",
            "",
        ]
        return lines

    lines += [
        f"Amendments ({len(known)} known, {sum(1 for k in known if k in held)} held):",
        "",
        "| Instrument | Type | Known from | Own text (PDF) | Own text (HTML) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key in sorted(known, key=lambda k: (k[1], k[0])):
        number, year = key
        entry = known[key]
        kind = entry["type"] or "-"
        sources = "+".join(sorted(entry["sources"]))
        files = held.get(key, {"pdf": [], "html": []})
        if files["pdf"]:
            pdf = " ".join(f"`{path}`" for path in files["pdf"])
        else:
            pdf = f"not held: {NOT_HELD.get(downloads.get(key, {}).get('outcome', ''), 'no source located')}"
        if files["html"]:
            html_cell = " ".join(f"`{path}`" for path in files["html"])
            if html_outcomes.get(key, {}).get("title_matches_target", "").startswith("no"):
                html_cell += " (title does not match this statute; check it)"
        else:
            outcome = html_outcomes.get(key, {}).get("outcome", "")
            html_cell = "not published as HTML" if outcome else "not looked up"
        lines.append(f"| No. {number} of {year} | {kind} | {sources} | {pdf} | {html_cell} |")
    lines.append("")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
