"""Send the preprocessed past-paper PDF to Google Document AI and collect the text.

This is the third OCR arrangement over the same document, after Tesseract via
`ocrmypdf-script.py`. It reads `preprocess-pdf.pdf` (67 pages) and writes one
text file per page plus a joined transcript.

Pages are sent as single-page PDF slices, not as re-rendered images. The input
has already been through deskewing and manual rotation, and rasterising it again
would resample pixels that were corrected once already and force a DPI guess on
a file whose page box is not a reliable resolution hint. Slicing hands Document
AI the bytes that are already there.

Spending is bounded three ways, because this is the only script in this
directory that costs money per page:

  * The shared ledger at `data/processed/documentai-usage.json` caps total pages
    across every Document AI caller in the repo, not just this one. This script
    takes the same lock and writes the same events as `scripts/convert_to_text.py`.
  * `--max-pages` caps a single run.
  * Every page's text is cached under `data/processed/documentai-cache/`, so a
    re-run costs nothing for pages already fetched. Delete the cache directory,
    or pass `--refresh`, to genuinely re-fetch.

`--dry-run` reports the plan, the cache hits and the projected cost without
opening a client or spending anything.

What comes out is text and Document AI's own per-page confidence, not accuracy.
This document has no ground truth in `ocr-benchmark/labels/`, so treat every
output as status=unverified and compare it against `1-ocrmypdf-outputs/` on
yield and confidence only.

Usage:
    uv run python data/evaluvation/documentai-script.py --dry-run
    uv run python data/evaluvation/documentai-script.py --pages 1-5
    uv run python data/evaluvation/documentai-script.py
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from deskew_pages import parse_pages  # noqa: E402

DEFAULT_PDF = HERE / "preprocess-pdf.pdf"
DEFAULT_OUT = HERE / "2-documentai-outputs"

# Shared with scripts/convert_to_text.py. Same file, same lock, same event shape:
# the budget is only a budget if every caller counts against it.
LEDGER = ROOT / "data" / "processed" / "documentai-usage.json"
CACHE = ROOT / "data" / "processed" / "documentai-cache"

SOURCE_ID = "EVAL-PREPROCESS-PDF"

# Enterprise Document OCR list price at the time of writing, USD per page. Only
# used to print an estimate before spending; override if the rate has moved.
DEFAULT_PRICE_PER_PAGE = 0.0015

MANIFEST_FIELDS = [
    "page_no",
    "paper_no",
    "paper_page",
    "session",
    "chars",
    "words",
    "lines",
    "alpha_ratio",
    "confidence",
    "cached",
    "empty",
    "error",
]


# ── ledger ───────────────────────────────────────────────────────────────────
@contextmanager
def ledger_lock():
    """Cross-process lock around the ledger's check-then-increment.

    scripts/convert_to_text.py uses fcntl, which does not exist on Windows, and
    this repo is worked on from Windows. Same guarantee, both platforms: without
    it two concurrent runs can each read pages_used=N, each decide there is room,
    and one write clobbers the other.
    """
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    lock_path = LEDGER.with_suffix(".lock")
    with open(lock_path, "w") as fh:
        try:
            import fcntl

            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        except ImportError:
            import msvcrt

            fh.write(" ")
            fh.flush()
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)


def load_ledger() -> dict:
    if LEDGER.is_file():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"page_limit": 2000, "pages_used": 0, "events": []}


def save_ledger(ledger: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def ledger_remaining() -> tuple[int, int]:
    ledger = load_ledger()
    used = int(ledger.get("pages_used", 0))
    limit = int(ledger.get("page_limit", 2000))
    return used, limit


def record_page(page_no: int, confidence: float | None) -> None:
    with ledger_lock():
        ledger = load_ledger()
        ledger["pages_used"] = int(ledger.get("pages_used", 0)) + 1
        ledger.setdefault("events", []).append(
            {
                "source_id": SOURCE_ID,
                "page": page_no,
                "used_at_utc": datetime.now(timezone.utc).isoformat(),
                "confidence": confidence,
            }
        )
        save_ledger(ledger)


# ── cache ────────────────────────────────────────────────────────────────────
def cache_path(page_no: int) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", SOURCE_ID).strip("-")
    return CACHE / safe / f"page-{page_no:04d}.txt"


def cache_meta_path(page_no: int) -> Path:
    """Sidecar for what the text alone cannot carry.

    Confidence is Document AI's, not ours, and it cannot be recomputed from the
    cached text. Without this, a resumed run reports a blank confidence column
    for every page it served from cache, which reads as "not measured" rather
    than "measured earlier".
    """
    return cache_path(page_no).with_suffix(".json")


def read_cached(page_no: int) -> tuple[str, float | None]:
    text = normalize(cache_path(page_no).read_text(encoding="utf-8"))
    confidence = None
    meta_path = cache_meta_path(page_no)
    if meta_path.is_file():
        try:
            value = json.loads(meta_path.read_text(encoding="utf-8")).get("confidence")
            confidence = float(value) if value is not None else None
        except (ValueError, TypeError):
            confidence = None
    return text, confidence


def write_cached(page_no: int, text: str, confidence: float | None) -> None:
    dest = cache_path(page_no)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text + "\n", encoding="utf-8")
    cache_meta_path(page_no).write_text(
        json.dumps(
            {
                "confidence": confidence,
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


# ── Document AI ──────────────────────────────────────────────────────────────
def require_config() -> tuple[str, str, str]:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.environ.get("GOOGLE_DOCUMENTAI_LOCATION", "").strip()
    processor = os.environ.get("GOOGLE_DOCUMENTAI_OCR_PROCESSOR_ID", "").strip()
    if not all((project, location, processor)):
        raise SystemExit(
            "error: Document AI needs GOOGLE_CLOUD_PROJECT, "
            "GOOGLE_DOCUMENTAI_LOCATION and GOOGLE_DOCUMENTAI_OCR_PROCESSOR_ID in .env"
        )
    credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if credentials and not Path(credentials).is_file():
        raise SystemExit(f"error: GOOGLE_APPLICATION_CREDENTIALS points at a missing file: {credentials}")
    return project, location, processor


def build_client(location: str):
    from google.api_core.client_options import ClientOptions
    from google.cloud import documentai

    return documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    )


def page_confidence(document) -> float | None:
    """Document AI's own confidence for the single page processed.

    Falls back to averaging block layout confidences when the page-level figure
    is not populated, and to None rather than silently reporting 0.0, which
    would read as "certainly wrong" instead of "not reported".
    """
    pages = list(getattr(document, "pages", []) or [])
    if not pages:
        return None
    page = pages[0]
    value = getattr(getattr(page, "layout", None), "confidence", 0.0) or 0.0
    if value > 0.0:
        return float(value)
    blocks = [
        float(b.layout.confidence)
        for b in getattr(page, "blocks", []) or []
        if getattr(getattr(b, "layout", None), "confidence", 0.0)
    ]
    return sum(blocks) / len(blocks) if blocks else None


def slice_page(pdf, page_no: int) -> bytes:
    """Extract one page as a standalone PDF, without rasterising it."""
    import pypdfium2 as pdfium

    single = pdfium.PdfDocument.new()
    try:
        single.import_pages(pdf, [page_no - 1])
        buffer = io.BytesIO()
        single.save(buffer)
        return buffer.getvalue()
    finally:
        single.close()


def process_page(client, name: str, payload: bytes, page_no: int, timeout: int):
    from google.cloud import documentai

    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(content=payload, mime_type="application/pdf"),
    )
    response = client.process_document(request=request, timeout=timeout)
    return normalize(response.document.text), page_confidence(response.document)


# ── paper index ──────────────────────────────────────────────────────────────
def load_paper_index(path: Path) -> dict[int, tuple[str, int, str]]:
    """Map each PDF page to (paper_no, page-within-paper, session) from papers.csv.

    The bundle is 16 past papers back to back, so a PDF page number alone does
    not say which paper a page belongs to or where it sits inside it. papers.csv
    owns that mapping at one row per paper; this flattens it to one entry per
    page so the manifest can carry it without duplicating the ranges.

    Missing or unreadable papers.csv is not fatal: the columns come out blank.
    This script's job is OCR, and it should still run before the paper index
    exists or if that pipeline is mid-rebuild.
    """
    if not path.is_file():
        return {}
    index: dict[int, tuple[str, int, str]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                start, end = int(row["start_page"]), int(row["end_page"])
            except (KeyError, TypeError, ValueError):
                continue
            paper_no = (row.get("paper_no") or "").strip()
            session = (row.get("session") or "").strip()
            for offset, page in enumerate(range(start, end + 1), start=1):
                index[page] = (paper_no, offset, session)
    return index


# ── results ──────────────────────────────────────────────────────────────────
@dataclass
class PageResult:
    page_no: int
    text: str = ""
    confidence: float | None = None
    cached: bool = False
    error: str = ""
    paper_no: str = ""
    paper_page: str = ""
    session: str = ""

    def as_row(self) -> dict[str, object]:
        stripped = self.text.strip()
        letters = sum(1 for c in stripped if c.isalpha())
        return {
            "page_no": self.page_no,
            "paper_no": self.paper_no,
            "paper_page": self.paper_page,
            "session": self.session,
            "chars": len(stripped),
            "words": len(stripped.split()),
            "lines": len([ln for ln in stripped.splitlines() if ln.strip()]),
            "alpha_ratio": round(letters / len(stripped), 4) if stripped else 0.0,
            "confidence": round(self.confidence, 4) if self.confidence is not None else "",
            "cached": self.cached,
            "empty": not stripped,
            "error": self.error,
        }


def write_manifest(path: Path, results: list[PageResult]) -> None:
    rows: dict[int, dict[str, object]] = {}
    if path.is_file():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    rows[int(row["page_no"])] = {k: row.get(k, "") for k in MANIFEST_FIELDS}
                except (KeyError, TypeError, ValueError):
                    continue
    for result in results:
        rows[result.page_no] = result.as_row()

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for page_no in sorted(rows):
            writer.writerow(rows[page_no])


def validate_args(args: argparse.Namespace) -> None:
    if args.max_pages is not None and args.max_pages < 0:
        raise ValueError(f"--max-pages cannot be negative, got {args.max_pages}")
    if args.timeout <= 0:
        raise ValueError(f"--timeout must be greater than 0, got {args.timeout}")
    if args.price_per_page < 0:
        raise ValueError(f"--price-per-page cannot be negative, got {args.price_per_page}")


def run(args: argparse.Namespace) -> int:
    validate_args(args)

    pdf_path: Path = args.pdf
    if not pdf_path.is_file():
        print(f"error: no such PDF: {pdf_path}", file=sys.stderr)
        return 1

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_path)
    try:
        total = len(pdf)
        pages = parse_pages(args.pages, total)

        cached = [n for n in pages if cache_path(n).is_file() and not args.refresh]
        to_fetch = [n for n in pages if n not in set(cached)]
        if args.max_pages is not None and len(to_fetch) > args.max_pages:
            print(f"note: capping this run at {args.max_pages} of {len(to_fetch)} billable page(s)")
            to_fetch = to_fetch[: args.max_pages]

        used, limit = ledger_remaining()
        remaining = limit - used
        print(f"{pdf_path.name}: {total} pages, selected {len(pages)}")
        print(f"cache hits {len(cached)} | to fetch {len(to_fetch)}")
        print(f"ledger: {used}/{limit} used, {remaining} remaining")
        print(f"estimated cost: ${len(to_fetch) * args.price_per_page:.2f} "
              f"at ${args.price_per_page:.4f}/page")

        if len(to_fetch) > remaining:
            print(
                f"error: this run needs {len(to_fetch)} page(s) but the shared budget "
                f"has {remaining} left. Raise page_limit in {LEDGER.name} or use --pages.",
                file=sys.stderr,
            )
            return 1

        if args.dry_run:
            print("dry run: no client opened, nothing sent, nothing written")
            return 0

        results: list[PageResult] = []
        fetch_set = set(to_fetch)
        client = name = None
        if to_fetch:
            project, location, processor = require_config()
            client = build_client(location)
            name = client.processor_path(project, location, processor)

        started = time.perf_counter()
        for page_no in pages:
            dest = cache_path(page_no)
            if page_no not in fetch_set:
                if dest.is_file():
                    text, confidence = read_cached(page_no)
                    results.append(
                        PageResult(page_no, text, confidence=confidence, cached=True)
                    )
                continue

            try:
                text, confidence = process_page(
                    client, name, slice_page(pdf, page_no), page_no, args.timeout
                )
            except Exception as exc:  # noqa: BLE001 - one page must not kill the run
                detail = re.sub(r"\s+", " ", str(exc)).strip()[:200]
                print(f"  page {page_no:>3}  FAILED {type(exc).__name__}: {detail}")
                results.append(PageResult(page_no, error=f"{type(exc).__name__}:{detail}"))
                continue

            # Ledger first: a page that was billed must be counted even if writing
            # the cache then fails. Over-counting is recoverable, silent spend is not.
            record_page(page_no, confidence)
            write_cached(page_no, text, confidence)

            result = PageResult(page_no, text, confidence=confidence)
            results.append(result)
            row = result.as_row()
            print(
                f"  page {page_no:>3}  {row['chars']:>6} chars  {row['words']:>5} words"
                f"  conf={row['confidence'] or 'n/a'}"
                f"  {'EMPTY' if row['empty'] else ''}"
            )
        elapsed = time.perf_counter() - started
    finally:
        pdf.close()

    paper_index = load_paper_index(args.papers)
    if paper_index:
        unmapped = [r.page_no for r in results if r.page_no not in paper_index]
        for result in results:
            entry = paper_index.get(result.page_no)
            if entry:
                result.paper_no, offset, result.session = entry
                result.paper_page = str(offset)
        if unmapped:
            print(
                f"note: {len(unmapped)} page(s) not covered by {args.papers.name}, "
                f"paper columns left blank: {unmapped[:10]}"
            )
    else:
        print(f"note: no paper index at {args.papers}; paper columns left blank")

    out_dir: Path = args.out
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        if result.text:
            (pages_dir / f"page-{result.page_no:03d}.txt").write_text(
                result.text, encoding="utf-8"
            )

    joined = "\n\n".join(
        f"## Page {r.page_no}\n\n{r.text}" for r in results if r.text
    )
    (out_dir / "full.txt").write_text(joined + "\n", encoding="utf-8")
    write_manifest(out_dir / "manifest.csv", results)

    fetched = [r for r in results if not r.cached and not r.error]
    failed = [r for r in results if r.error]
    confidences = [r.confidence for r in results if r.confidence is not None]
    chars = sum(len(r.text.strip()) for r in results)
    used_after, limit_after = ledger_remaining()

    (out_dir / "run.json").write_text(
        json.dumps(
            {
                "source": str(pdf_path.relative_to(ROOT)) if pdf_path.is_relative_to(ROOT) else str(pdf_path),
                "processor_location": os.environ.get("GOOGLE_DOCUMENTAI_LOCATION", ""),
                "pages": [r.page_no for r in results],
                "pages_billed_this_run": len(fetched),
                "pages_from_cache": sum(1 for r in results if r.cached),
                "pages_failed": len(failed),
                "chars": chars,
                "seconds": round(elapsed, 2),
                "mean_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
                "estimated_cost_usd": round(len(fetched) * args.price_per_page, 4),
                "ledger_after": {"pages_used": used_after, "page_limit": limit_after},
                "caveat": (
                    "Character counts and confidence measure yield, not accuracy; this "
                    "document has no ground truth in ocr-benchmark/labels/. status=unverified."
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=" * 64)
    print(
        f"done: {len(results)} page(s) | {chars} chars | billed {len(fetched)}"
        f" | cached {sum(1 for r in results if r.cached)} | failed {len(failed)}"
    )
    if confidences:
        print(f"mean confidence {sum(confidences) / len(confidences):.4f}"
              f" | lowest {min(confidences):.4f}")
    print(f"ledger now {used_after}/{limit_after} | spent this run "
          f"~${len(fetched) * args.price_per_page:.2f} | {elapsed:.1f}s")
    if failed:
        print(f"failed pages: {', '.join(str(r.page_no) for r in failed)}")
    print("status=unverified: no ground truth for this document. Yield and confidence only.")
    print(f"output: {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="source PDF")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument("--pages", help='page spec, e.g. "1-10,15,40-" (default: all)')
    parser.add_argument(
        "--papers",
        type=Path,
        default=HERE / "papers.csv",
        help="paper index used to fill the paper_no/paper_page/session columns",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="cap billable pages for this run (cache hits do not count)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="ignore cached page text and re-fetch, which spends again",
    )
    parser.add_argument("--timeout", type=int, default=120, help="per-page timeout in seconds")
    parser.add_argument(
        "--price-per-page",
        type=float,
        default=DEFAULT_PRICE_PER_PAGE,
        help=f"USD per page, for the cost estimate only (default: {DEFAULT_PRICE_PER_PAGE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report the plan and projected cost without sending anything",
    )
    return parser


def main() -> int:
    try:
        return run(build_parser().parse_args())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
