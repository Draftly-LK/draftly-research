"""OCR a scanned Act into a text sidecar, offline and free.

Some Government Printer PDFs are 1-bit scans with no text layer. The Land
(Restrictions on Alienation) (Amendment) Act, No. 21 of 2018 is one, and its
LawLanka HTML stops at section 2 behind a subscription wall, so sections 3 and 4
exist in no machine-readable copy we hold. This reads them off the scan.

doctr runs locally on CPU, so this costs nothing and sends nothing anywhere --
which matters, because the same command must stay usable on the private files in
`data/raw/`. It is not the paid OCR benchmark in `ocr-benchmark/`; that one
compares engines and spends money, this one just recovers text.

OCR output is a reading of an image, not a text layer. It is written to a
sidecar rather than into the corpus so that the guess is never mistaken for the
source, and anything parsed from it has to say so.

    uv run python scripts/ocr_scanned_act.py --pdf <path> --out <path.txt>
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def layout_lines(result, columns: int) -> list[str]:
    """Rebuild the page's columns from where the words actually sit.

    Reading order alone loses the layout: a Government Printer page runs the
    provision down one column and the marginal note down another, and a flat
    transcript interleaves them ("...come into operation on April 1, 2018." then
    "operation." on its own line). Downstream cannot tell note from provision.

    doctr gives every word a relative box, so the page can be laid back out on a
    fixed-width grid, the same shape `pdftotext -layout` produces for a PDF that
    has a text layer. One parser then reads both.
    """
    out: list[str] = []
    for index, page in enumerate(result.pages, start=1):
        out.append(f"===== PAGE {index} =====")
        words = [
            (word.geometry[0][1], word.geometry[0][0], word.value)
            for block in page.blocks
            for line in block.lines
            for word in line.words
        ]
        if not words:
            continue
        # Group into rows by vertical position, then place each word by its
        # horizontal one. The tolerance is a fraction of page height, so it
        # scales with whatever the render size was.
        words.sort()
        rows: list[list[tuple[float, str]]] = []
        row_top = None
        for top, left, value in words:
            if row_top is None or top - row_top > 0.010:
                rows.append([])
                row_top = top
            rows[-1].append((left, value))
        for row in rows:
            line = [" "] * columns
            cursor = 0
            for left, value in sorted(row):
                # Place the word where it sits, but never on top of the previous
                # one: without the gap every word in a line runs together and the
                # transcript reads "Section5Aoftheprincipalenactment".
                start = max(min(int(left * columns), columns - 1), cursor)
                for offset, character in enumerate(value):
                    if start + offset < columns:
                        line[start + offset] = character
                cursor = min(start + len(value) + 1, columns)
            out.append("".join(line).rstrip())
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--scale",
        type=float,
        default=3.0,
        help="render multiplier. These scans are 200 dpi, which is under what "
             "the detector wants, so they are rendered up before reading.",
    )
    parser.add_argument(
        "--columns", type=int, default=125,
        help="grid width the page is laid back out on, in characters.",
    )
    args = parser.parse_args()
    args.pdf = args.pdf.resolve()
    args.out = args.out.resolve()

    if not args.pdf.exists():
        print(f"{args.pdf} is missing", file=sys.stderr)
        return 1

    warnings.filterwarnings("ignore")
    from doctr.io import DocumentFile
    from doctr.models import ocr_predictor

    pages = DocumentFile.from_pdf(str(args.pdf), scale=args.scale)
    model = ocr_predictor(pretrained=True, assume_straight_pages=True)
    result = model(pages)

    lines = layout_lines(result, args.columns)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# OCR of {args.pdf.relative_to(REPO_ROOT).as_posix()}\n"
        f"# doctr, offline, rendered at {args.scale}x. This is a reading of an "
        f"image and carries OCR errors; it is not the source text.\n"
    )
    args.out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out.relative_to(REPO_ROOT)} ({len(pages)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
