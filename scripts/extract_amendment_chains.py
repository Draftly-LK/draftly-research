"""Read the amendment chain printed at the head of each consolidated statute.

Every statute in the Legislative Enactments opens with a block naming the
principal instrument and every instrument that has been folded into the text:

    Ordinance Nos,
     23 of 1927
     19 of 1928
     ...
    Act Nos,
     6 of 1949
     ...

That block is the statute's own record of what amended it, and it is a
deterministic parse -- no LLM. The corpus currently derives amendment history
from LawLanka markers only, which covers 26 of 66 statutes; the Notaries
Ordinance shows zero amendments while its own page 1 lists fourteen.

Writes `data/processed/amendment-chains.csv`, one row per instrument.
Nothing here is verified: the block is OCR-free text from a republisher's PDF,
and a chain says an instrument touched the statute, not which section.

    uv run python scripts/extract_amendment_chains.py
    uv run python scripts/extract_amendment_chains.py --source-id SRC014 --show
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
OUTPUT = REPO_ROOT / "data/processed/amendment-chains.csv"

COLUMN_GAP = re.compile(r"\s{3,}")
TYPE_HEADING = re.compile(r"^(Ordinance|Act|Law)s?\b", re.IGNORECASE)
NUMBER_YEAR = re.compile(r"(\d{1,3})\s*of\s*(1[78]\d{2}|19\d{2}|20\d{2})")
# How many consecutive chain-free lines end the block. The list is printed as an
# unbroken run, so a short gap means the body has started.
QUIET_LINES = 4


def page_text(pdf: Path, page: int = 1, through_page: int = 1) -> str:
    result = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(through_page), "-layout", str(pdf), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout if result.returncode == 0 else ""


def header_column(text: str) -> str:
    """The left column of the header block, where the chain is printed.

    These pages are two-column: the chain runs down a narrow left column while
    the long title and enacting text sit to its right, often on the same line.
    Splitting each line on a run of three or more spaces isolates the column, so
    body text cannot contribute stray number-year pairs. An entry wrapped across
    two lines ("Law Nos, 4" / "of 1974") survives, because the column is rejoined
    before the numbers are read.
    """
    kept, quiet, started = [], 0, False
    for line in text.splitlines():
        if not line.strip():
            continue
        left = COLUMN_GAP.split(line.strip())[0].strip()
        is_chain = bool(NUMBER_YEAR.search(left)) or bool(TYPE_HEADING.match(left))
        if is_chain:
            started, quiet = True, 0
        elif started:
            quiet += 1
            if quiet >= QUIET_LINES:
                break
        kept.append(left)
    return "\n".join(kept)


def parse_chain(text: str) -> list[tuple[str, int, int]]:
    """Return [(instrument_type, number, year)] in the order printed."""
    header = header_column(text)
    if not any(TYPE_HEADING.match(line) for line in header.splitlines()):
        return []

    # Walk the whole column, letting each "Ordinance Nos," heading set the type
    # that the number-year pairs after it belong to. Scanning the joined string
    # rather than each line is what catches an entry split as "Law Nos, 4" /
    # "of 1974". A heading sorts before a pair at the same offset so that
    # "Act Nos, 6 of 1949" files 6 of 1949 under Act, not the previous type.
    events: list[tuple[int, int, str, object]] = []
    for match in re.finditer(r"^(Ordinance|Act|Law)s?\b", header, re.MULTILINE | re.IGNORECASE):
        events.append((match.start(), 0, "type", match.group(1).title()))
    for match in NUMBER_YEAR.finditer(header):
        events.append((match.start(), 1, "pair", (int(match.group(1)), int(match.group(2)))))
    events.sort()

    chain, current = [], None
    for _, _, kind, value in events:
        if kind == "type":
            current = value
        elif current:
            number, year = value
            chain.append((current, number, year))
    # The same instrument can be printed twice across a wrapped column.
    return list(dict.fromkeys(chain))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", help="only this statute")
    parser.add_argument("--show", action="store_true", help="print the header text too")
    args = parser.parse_args()

    with REGISTRY.open(encoding="utf-8-sig") as handle:
        rows = [r for r in csv.DictReader(handle) if r["source_type"] == "statute"]

    seen_pdfs: set[str] = set()
    out_rows, no_chain = [], []
    for row in rows:
        if args.source_id and row["source_id"] != args.source_id:
            continue
        pdf = REPO_ROOT / (row["local_pdf_path"] or "")
        if not row["local_pdf_path"] or not pdf.exists():
            continue
        # A compendium volume is shared by several rows; its page 1 is a cover.
        if pdf.name.startswith("legislative-enactments"):
            continue
        if pdf.name in seen_pdfs:
            continue
        seen_pdfs.add(pdf.name)

        # A heavily-amended statute's chain header can run past page 1 --
        # the Urban Councils Ordinance's 48-instrument chain wraps onto page
        # 2. header_column() already stops itself once real body text
        # starts (the QUIET_LINES break), so reading a few extra pages is
        # safe: it cannot pull in unrelated content, only give the header
        # more room when it genuinely needs it.
        text = page_text(pdf, through_page=3)
        if args.show:
            print(f"===== {row['source_id']} {row['official_title']} =====")
            print(text[:1200])
        chain = parse_chain(text)
        if not chain:
            no_chain.append(f"{row['source_id']} {row['official_title']}")
            continue

        principal = (
            row["act_or_ordinance_no"].isdigit()
            and row["year"].isdigit()
            and (int(row["act_or_ordinance_no"]), int(row["year"]))
        )
        for order, (kind, number, year) in enumerate(chain):
            out_rows.append(
                {
                    "source_id": row["source_id"],
                    "statute": row["official_title"],
                    "instrument_type": kind,
                    "instrument_no": number,
                    "instrument_year": year,
                    "role": "principal" if principal == (number, year) else "amending",
                    "chain_order": order,
                    "status": "unverified",
                }
            )

    if args.source_id:
        for r in out_rows:
            print(f"  {r['role']:9} {r['instrument_type']:9} No. {r['instrument_no']} of {r['instrument_year']}")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# Amendment chains read from the header block of each consolidated statute PDF.\n"
            "# A row means the instrument was folded into the consolidated text, not which\n"
            "# section it changed. Generated by scripts/extract_amendment_chains.py.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    statutes = len({r["source_id"] for r in out_rows})
    amending = [r for r in out_rows if r["role"] == "amending"]
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    print(f"  {len(out_rows)} instruments across {statutes} statutes")
    print(f"  {len(amending)} amending, {len(out_rows) - len(amending)} principal")
    print(f"  {len(no_chain)} statutes with no readable chain:")
    for name in no_chain:
        print(f"    {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
