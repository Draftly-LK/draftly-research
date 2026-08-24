"""Compare a canonical tree against the source it was parsed from.

This is the stopping rule for the parse-and-review loop. A tree can look right
in a spot check and still have dropped a clause: the Land (Restrictions on
Alienation) Act read cleanly while missing "Lanka within the meaning of the",
because a wrapped line had been cut at a stale column. Reading the tree cannot
find that. Counting can.

Every word of the source is counted, every word of the tree is counted, and what
is in the first and not the second is reported. Word counts, not exact strings,
because the tree drops the enumerators' brackets and normalises whitespace by
design; those differences are not losses.

What comes out is a percentage and a list. The percentage says whether to go
round again. The list says where to look.

    uv run python scripts/check_parse_coverage.py --source-id SRC021
    uv run python scripts/check_parse_coverage.py --tree <path> --pdf <path>
    uv run python scripts/check_parse_coverage.py --tree <path> --text <path>

Anything under about 0.5% unmatched is usually cover and running-header text
that does not belong in the tree. Read the list before believing that.
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

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
CANONICAL = REPO_ROOT / "data/processed/canonical-statutes"

# The enacting formula is the last thing before the sections start. What comes
# before it -- cover page, long title, amendment chain -- is held in the tree's
# own metadata fields rather than its body, so counting it as body text reports
# losses that are not losses.
BODY_STARTS = re.compile(r"as\s+follows\s*[:\-–—]", re.IGNORECASE)
# A Government Printer Act repeats its short title as a running header on every
# page and closes with the Publications Bureau imprint. Neither is a provision,
# and counting them makes a complete tree look like it lost a fifth of the Act.
FURNITURE = re.compile(
    r"^\s*[\"“]?(?:\d+\s*)?(?:"
    r"PRINTED|TO\s+BE\s+PURCHASED|Price\s*:|Postage\s*:|Annual\s+subscription|"
    r"English\s+(?:Acts|Bills)|GOVERNMENT\s+PRINTING|DEPARTMENT\s+OF|PARLIAMENT\s+OF|"
    r"December\s+each\s+year|This\s+Act\s+can\s+be|Published\s+as\s+a\s+Supplement|"
    r"\d+\s*[-–—]{1,2}\s*PL|Printed\s+on\s+the\s+Order"
    r")",
    re.IGNORECASE,
)
RUNNING_HEADER = re.compile(r"^\s*\d*\s*(?:Act,\s*No\.|\(Amendment\)\s*Act)", re.IGNORECASE)


def words(text: str) -> collections.Counter:
    return collections.Counter(re.sub(r"[^A-Za-z0-9 ]", " ", text).lower().split())


def pdf_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return result.stdout


def tree_words(document: dict) -> collections.Counter:
    """Every word the tree holds, wherever it holds it."""
    collected: list[str] = []

    def walk(nodes: list[dict]) -> None:
        for node in nodes:
            for key in ("heading", "text", "term", "qualifier", "number"):
                value = node.get(key)
                if value:
                    collected.append(str(value))
            for event in node.get("amendment_events", []):
                collected.append(event.get("verbatim", ""))
            walk(node.get("children", []))
            # An inserted or substituted provision is part of the document even
            # though it hangs off an instruction rather than the body.
            for wrapper in ("inserted_provisions", "substituted_provisions"):
                for held in node.get(wrapper, []):
                    walk([held["provision"]])

    walk(document.get("body", []))
    for recital in document.get("preamble", []):
        collected.append(recital.get("text", ""))
    return words(" ".join(collected))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", help="look the tree and its PDF up in the registry")
    parser.add_argument("--tree", type=Path)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--text", type=Path, help="a text or OCR sidecar instead of a PDF")
    parser.add_argument("--show", type=int, default=25, help="how many missing words to list")
    parser.add_argument(
        "--fail-over",
        type=float,
        default=None,
        help="exit non-zero if the unmatched share exceeds this percentage",
    )
    args = parser.parse_args()

    if args.source_id:
        with REGISTRY.open(encoding="utf-8-sig") as handle:
            registry = {r["source_id"]: r for r in csv.DictReader(handle)}
        row = registry[args.source_id]
        source = REPO_ROOT / row["local_pdf_path"]
        trees = sorted(CANONICAL.glob(f"{args.source_id}-*.json"))
        if not trees:
            print(f"no canonical tree for {args.source_id}", file=sys.stderr)
            return 1
        tree = trees[0]
        raw = pdf_text(source)
    elif args.tree and (args.pdf or args.text):
        tree, source = args.tree, (args.pdf or args.text)
        raw = pdf_text(source) if args.pdf else source.read_text(encoding="utf-8", errors="replace")
    else:
        print("give --source-id, or --tree with --pdf or --text", file=sys.stderr)
        return 1

    start = BODY_STARTS.search(raw)
    if start:
        raw = raw[start.end():]
    # Furniture wraps. The Publications Bureau address runs five lines past the
    # word that identifies it, so once a block is recognised it is dropped until
    # the next blank line rather than line by line.
    kept: list[str] = []
    dropping = False
    for line in raw.splitlines():
        if not line.strip():
            dropping = False
            continue
        if line.startswith("===== PAGE"):
            continue
        if FURNITURE.match(line):
            dropping = True
        if dropping or RUNNING_HEADER.match(line):
            continue
        kept.append(line)
    raw = "\n".join(kept)

    document = json.loads(Path(tree).read_text(encoding="utf-8"))
    in_source = words(raw)
    missing = in_source - tree_words(document)
    total = sum(in_source.values())
    share = 100 * sum(missing.values()) / total if total else 0.0

    print(f"tree   {Path(tree).name}")
    print(f"source {Path(source).name}")
    print(f"{total} words in the source, {sum(missing.values())} unmatched ({share:.2f}%)")
    if missing:
        listed = ", ".join(f"{w}x{n}" if n > 1 else w for w, n in missing.most_common(args.show))
        print(f"missing: {listed}")
    if args.fail_over is not None and share > args.fail_over:
        print(f"over the {args.fail_over}% threshold", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
