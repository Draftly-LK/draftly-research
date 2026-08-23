"""Parse a text-layer consolidated statute PDF into the canonical node model.

Most statutes reach the canonical layer through `build_canonical_statutes.py`,
which reads LankaLaw's HTML and its semantic classes. A few have no HTML edition
at all. The Land (Restrictions on Alienation) Act is one: LankaLaw does not
publish it, and the registry's own PDF is a scan with no text layer, so nothing
could read it until a consolidated PDF with real text appeared.

These PDFs are two-column. The marginal note runs down a narrow left column and
the operative text down a wide right one, and `pdftotext -layout` puts both on
the same line separated by a run of spaces:

    Short title and date 1.(1) This Act may be cited as the Land (Restrictions
    of operation.          No. 38 of 2014.

Reading the whole line would splice the note into the middle of the provision,
which is exactly the damage seen in the older LLM extractions. So each line is
split at the column gap, the two columns are rebuilt separately, and the note is
attached as the section heading rather than mixed into its text.

Output matches `build_canonical_statutes.py`, so both sources land in the same
shape and the same directory. A PDF gives less than the HTML does: there are no
inline amendment markers to read, so nodes carry no amendment events.

    uv run python scripts/parse_consolidated_pdf.py --source-id SRC021
    uv run python scripts/parse_consolidated_pdf.py --source-id SRC021 --show
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_canonical_statutes import (  # noqa: E402
    DEFINITION,
    DEFINITION_VERB,
    PROVISO,
    SCHEDULE_REF,
    classify,
    cross_references,
    nest,
    quality_flags,
)

REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
COMMENCEMENT = REPO_ROOT / "data/processed/statute_commencement.csv"
CHAINS = REPO_ROOT / "data/processed/amendment-chains.csv"
OUT_DIR = REPO_ROOT / "data/processed/canonical-statutes"

COLUMN_GAP = re.compile(r"\s{3,}")
# The gap between the two columns is not reliably wide. `Short title and date
# 1.(1) This Act may be cited...` separates them with a single space, so a
# whitespace rule alone leaves the note glued to the front of the line and hides
# the section number behind it. Where a line carries a marginal note followed by
# something that looks like the start of a section, split on that instead.
NOTE_THEN_SECTION = re.compile(
    r"^(?P<note>[A-Za-z][A-Za-z ,'()-]{0,45}?)\s+(?P<body>\d{1,3}[A-Z]{0,2}\.\s*[({A-Z].*)$"
)
# A section opens with its number at the start of the body column, as "1." or
# "1.(1)" or "12A.". The trailing dot is what separates it from a stray figure.
SECTION_START = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.\s*(.*)$", re.DOTALL)
ENUM_START = re.compile(r"^\(\s*\w{1,4}\s*\)")
CHAIN_LINE = re.compile(r"^(?:(Ordinance|Act|Law)s?\s*Nos?[.,]?|\s*\d{1,3}\s+of\s+\d{4}\s*,?)$", re.I)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def page_text(pdf: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def split_columns(text: str) -> list[tuple[str, str]]:
    """(marginal note, body) per line, using the column gap as the boundary."""
    rows = []
    for line in text.splitlines():
        if not line.strip():
            rows.append(("", ""))
            continue
        indent = len(line) - len(line.lstrip())
        carried = NOTE_THEN_SECTION.match(line.strip())
        if carried and indent < 24:
            rows.append((carried.group("note").strip(), carried.group("body").strip()))
            continue
        fields = COLUMN_GAP.split(line.strip())
        if len(fields) >= 2 and indent < 24:
            # Note on the left, provision on the right.
            rows.append((fields[0].strip(), " ".join(f.strip() for f in fields[1:])))
        else:
            rows.append(("", line.strip()))
    return rows


def blocks_from(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Group the body column into (pending note, block) runs."""
    blocks, note_parts, body_parts = [], [], []

    def flush():
        body = re.sub(r"\s+", " ", " ".join(body_parts)).strip()
        note = re.sub(r"\s+", " ", " ".join(note_parts)).strip(" .")
        if body:
            blocks.append((note, body))
        note_parts.clear()
        body_parts.clear()

    for note, body in rows:
        starts_block = bool(SECTION_START.match(body) or ENUM_START.match(body))
        if starts_block and body_parts:
            flush()
        if note and not CHAIN_LINE.match(note):
            note_parts.append(note)
        if body:
            body_parts.append(body)
    flush()
    return blocks


def parse(pdf: Path, title: str) -> list[dict]:
    text = page_text(pdf)
    stream: list[dict] = []
    current_note = ""

    for note, body in blocks_from(split_columns(text)):
        if note:
            current_note = note
        section = SECTION_START.match(body)
        # A bare "7." with nothing after it is a page artefact, not a section:
        # the real section 7 follows with its own text. Opening one here would
        # swallow the following provisions under an empty duplicate.
        if section and not section.group(2).strip():
            continue
        if section and not body[:1].isalpha():
            number, remainder = section.group(1), section.group(2).strip()
            stream.append(
                {
                    "type": "section",
                    "number": number,
                    "heading": current_note,
                    "raw_text": body,
                    "text": "" if ENUM_START.match(remainder) else remainder,
                    "amendment_events": [],
                    "cross_references": cross_references(remainder, title),
                }
            )
            current_note = ""
            if ENUM_START.match(remainder):
                body = remainder
            else:
                continue

        if not stream:
            continue
        defined = DEFINITION.match(body)
        if defined and DEFINITION_VERB.match(defined.group(2).strip()):
            stream.append(
                {
                    "type": "definition",
                    "term": re.sub(r"\s+", " ", defined.group(1)).strip(),
                    "raw_text": body,
                    "text": defined.group(2).strip(),
                    "amendment_events": [],
                    "cross_references": cross_references(defined.group(2), title),
                }
            )
            continue
        kind, label, remainder = classify(body)
        if kind == "text" and stream and stream[-1]["type"] != "section":
            stream[-1]["text"] = (stream[-1]["text"] + " " + remainder).strip()
            continue
        node = {
            "type": kind,
            "number": label,
            "raw_text": body,
            "text": remainder,
            "amendment_events": [],
            "cross_references": cross_references(remainder, title),
        }
        if PROVISO.search(remainder):
            node["is_proviso"] = True
        stream.append(node)

    return nest(stream)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    registry = {r["source_id"]: r for r in read_csv(REGISTRY)}
    row = registry[args.source_id]
    pdf = REPO_ROOT / row["local_pdf_path"]
    if not pdf.exists():
        print(f"{pdf} is missing", file=sys.stderr)
        return 1

    body = parse(pdf, row["official_title"])
    if not body:
        print("no sections found; this PDF probably has no text layer", file=sys.stderr)
        return 1

    chain = [
        r
        for r in (read_csv(CHAINS) if CHAINS.exists() else [])
        if r["source_id"] == args.source_id and r["role"] == "amending"
    ]
    commencement = {r["source_id"]: r["commencement"] for r in read_csv(COMMENCEMENT)}
    full_text = page_text(pdf)

    document = {
        "source_id": args.source_id,
        "title": row["official_title"],
        "long_title": "",
        "citation": {
            "type": chain[0]["instrument_type"] if chain else "",
            "number": int(row["act_or_ordinance_no"]),
            "year": int(row["year"]),
        },
        "commencement": commencement.get(args.source_id, ""),
        "language": "en",
        "edition": {
            "publisher": "lankalaw",
            "kind": "consolidated",
            "local_path": pdf.relative_to(REPO_ROOT).as_posix(),
            "caveat": "parsed from a two-column PDF; no inline amendment markers exist to read",
        },
        "amendments": [
            {
                "type": r["instrument_type"],
                "number": int(r["instrument_no"]),
                "year": int(r["instrument_year"]),
            }
            for r in chain
        ],
        "verification_status": "unverified",
        "quality_flags": quality_flags(full_text),
        "schedules_referenced": sorted({m.group(1) for m in SCHEDULE_REF.finditer(full_text)}),
        "schedules": [],
        "body": body,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / f"{args.source_id}-{document['citation']['number']}-{document['citation']['year']}.json"
    target.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    sections = [n for n in body if n["type"] == "section"]
    print(f"wrote {target.relative_to(REPO_ROOT)}")
    print(f"  {len(sections)} sections, {len(document['amendments'])} amendments in the chain")
    if args.show:
        def show(nodes, indent=0):
            for node in nodes:
                label = node.get("term") or node.get("number") or ""
                print("  " * indent + f"{node['type']:12} {label:16} {node.get('text', '')[:46]}")
                show(node.get("children", []), indent + 1)
        show(body[:6])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
