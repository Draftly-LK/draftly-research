from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = ROOT / "data" / "legal-sources" / "library"
MARKDOWN_ROOT = ROOT / "data" / "legal-sources" / "library-markdown"
SOURCE_REGISTRY = ROOT / "data" / "legal-sources" / "manifests" / "source-registry.csv"
CONVERSION_REGISTRY = ROOT / "data" / "legal-sources" / "manifests" / "conversion-registry.csv"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_source_registry() -> dict[str, dict[str, str]]:
    by_pdf: dict[str, dict[str, str]] = {}
    if not SOURCE_REGISTRY.exists():
        return by_pdf

    with SOURCE_REGISTRY.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            pdf = row.get("local_pdf_path", "").strip()
            if not pdf:
                continue
            info = by_pdf.setdefault(
                pdf,
                {
                    "source_ids": [],
                    "source_types": [],
                },
            )
            info["source_ids"].append(row.get("source_id", "").strip())
            info["source_types"].append(row.get("source_type", "").strip())
    return by_pdf


def infer_source_type(pdf: Path) -> str:
    try:
        return pdf.relative_to(LIBRARY_ROOT).parts[0]
    except ValueError:
        return "unknown"


def markdown_target(pdf: Path) -> Path:
    relative = pdf.relative_to(LIBRARY_ROOT).with_suffix(".md")
    return MARKDOWN_ROOT / relative


def normalize_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def pdf_pages(pdf: Path) -> int | None:
    try:
        proc = subprocess.run(
            ["pdfinfo", str(pdf)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return None

    match = re.search(r"(?m)^Pages:\s+(\d+)", proc.stdout + proc.stderr)
    return int(match.group(1)) if match else None


def pdftotext_fallback(pdf: Path) -> str:
    proc = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return normalize_markdown(proc.stdout) if proc.stdout.strip() else ""


def rapidocr_fallback(pdf: Path, pages: int | None, timeout: int) -> str:
    from rapidocr import RapidOCR
    from rapidocr.utils.typings import EngineType, ModelType, OCRVersion

    params = {
        "Det.engine_type": EngineType.TORCH,
        "Cls.engine_type": EngineType.TORCH,
        "Rec.engine_type": EngineType.TORCH,
        "Det.ocr_version": OCRVersion.PPOCRV4,
        "Rec.ocr_version": OCRVersion.PPOCRV4,
        "Det.model_type": ModelType.MOBILE,
        "Rec.model_type": ModelType.MOBILE,
        "Global.log_level": "warning",
    }
    engine = RapidOCR(params=params)
    rendered_pages: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="draftly-rapidocr-pages-") as tmp:
        prefix = Path(tmp) / "page"
        cmd = [
            "pdftoppm",
            "-r",
            "90",
            "-png",
            str(pdf),
            str(prefix),
        ]
        subprocess.run(cmd, check=True, timeout=timeout)
        rendered_pages = sorted(Path(tmp).glob("*.png"))

        chunks = [f"# {pdf.stem}", "", "<!-- OCR fallback generated with RapidOCR from rendered PDF pages. -->"]
        for page_number, image_path in enumerate(rendered_pages, start=1):
            result = engine(str(image_path))
            lines = [text.strip() for text in getattr(result, "txts", ()) if text and text.strip()]
            chunks.extend(["", f"## Page {page_number}", ""])
            chunks.extend(lines or ["[No OCR text detected on this page.]"])

        detected = len(rendered_pages)
        if pages and detected != pages:
            chunks.extend(
                [
                    "",
                    "## OCR Warning",
                    "",
                    f"Rendered {detected} pages, but pdfinfo reported {pages} pages.",
                ]
            )
        return normalize_markdown("\n".join(chunks))


def docling_executable() -> Path:
    scripts = Path(sys.executable).resolve().parent
    candidate = scripts / ("docling.exe" if os.name == "nt" else "docling")
    if candidate.exists():
        return candidate
    found = shutil.which("docling")
    if found:
        return Path(found)
    raise FileNotFoundError("docling executable was not found in the active environment")


def convert_one(
    pdf: Path,
    source_info: dict[str, dict[str, str]],
    force: bool,
    timeout: int,
    docling_path: Path,
    recovery_only: bool,
) -> dict[str, str]:
    source_path = rel(pdf)
    target = markdown_target(pdf)
    target.parent.mkdir(parents=True, exist_ok=True)

    registry_info = source_info.get(source_path, {})
    source_ids = ";".join(registry_info.get("source_ids", [])) or "UNREGISTERED"
    source_types = [value for value in registry_info.get("source_types", []) if value]
    source_type = ";".join(sorted(set(source_types))) if source_types else infer_source_type(pdf)

    pages = pdf_pages(pdf)
    converted_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    if target.exists() and not force:
        text = target.read_text(encoding="utf-8", errors="replace")
        chars = len(re.sub(r"\s+", "", text))
        ocr_text = ""
        try:
            ocr_text = rapidocr_fallback(pdf, pages, timeout)
        except Exception as exc:
            ocr_text = ""
            ocr_error = str(exc)
        else:
            ocr_error = ""

        if ocr_text and len(re.sub(r"\s+", "", ocr_text)) > 0:
            target.write_text(ocr_text, encoding="utf-8")
            chars = len(re.sub(r"\s+", "", ocr_text))
            per_page = round(chars / pages, 1) if pages else "unknown"
            return {
                "source_id": source_ids,
                "source_type": source_type,
                "source_path": source_path,
                "markdown_path": rel(target),
                "converter": "rapidocr",
                "converter_version": "",
                "ocr_enabled": "true",
                "language_hint": "eng,sin,tam",
                "status": "ocr-recovered",
                "quality_notes": (
                    f"Docling failed with exit={proc.returncode}; RapidOCR fallback used; "
                    f"pages={pages}; non_ws_chars={chars}; chars_per_page={per_page}."
                ),
                "converted_at": converted_at,
            }

        return {
            "source_id": source_ids,
            "source_type": source_type,
            "source_path": source_path,
            "markdown_path": rel(target),
            "converter": "existing",
            "converter_version": "",
            "ocr_enabled": "unknown",
            "language_hint": "eng,sin,tam",
            "status": "skipped-existing",
            "quality_notes": f"Existing markdown kept; pages={pages}; non_ws_chars={chars}.",
            "converted_at": converted_at,
        }

    if recovery_only:
        ocr_text = rapidocr_fallback(pdf, pages, timeout)
        target.write_text(ocr_text, encoding="utf-8")
        chars = len(re.sub(r"\s+", "", ocr_text))
        per_page = round(chars / pages, 1) if pages else "unknown"
        return {
            "source_id": source_ids,
            "source_type": source_type,
            "source_path": source_path,
            "markdown_path": rel(target),
            "converter": "rapidocr",
            "converter_version": "PP-OCRv4-mobile",
            "ocr_enabled": "true",
            "language_hint": "eng,sin,tam",
            "status": "ocr-recovered" if chars else "failed",
            "quality_notes": f"Recovery-only RapidOCR pass; pages={pages}; non_ws_chars={chars}; chars_per_page={per_page}.",
            "converted_at": converted_at,
        }

    with tempfile.TemporaryDirectory(prefix="draftly-docling-") as tmp:
        tmp_path = Path(tmp)
        cmd = [
            str(docling_path),
            "convert",
            "--to",
            "md",
            "--image-export-mode",
            "placeholder",
            "--ocr",
            "--tables",
            "--num-threads",
            "2",
            "--page-batch-size",
            "2",
            "--document-timeout",
            str(timeout),
            "--output",
            str(tmp_path),
            str(pdf),
        ]
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + 60,
        )

        md_files = list(tmp_path.glob("*.md"))
        if proc.returncode == 0 and md_files:
            text = normalize_markdown(md_files[0].read_text(encoding="utf-8", errors="replace"))
            target.write_text(text, encoding="utf-8")
            chars = len(re.sub(r"\s+", "", text))
            per_page = round(chars / pages, 1) if pages else "unknown"
            status = "converted-low-text" if pages and chars / pages < 100 else "converted"
            notes = f"Docling conversion; pages={pages}; non_ws_chars={chars}; chars_per_page={per_page}."
            return {
                "source_id": source_ids,
                "source_type": source_type,
                "source_path": source_path,
                "markdown_path": rel(target),
                "converter": "docling",
                "converter_version": "2.112.0",
                "ocr_enabled": "true",
                "language_hint": "eng,sin,tam",
                "status": status,
                "quality_notes": notes,
                "converted_at": converted_at,
            }

        fallback = pdftotext_fallback(pdf)
        if fallback:
            target.write_text(fallback, encoding="utf-8")
            chars = len(re.sub(r"\s+", "", fallback))
            return {
                "source_id": source_ids,
                "source_type": source_type,
                "source_path": source_path,
                "markdown_path": rel(target),
                "converter": "pdftotext",
                "converter_version": "",
                "ocr_enabled": "false",
                "language_hint": "eng,sin,tam",
                "status": "fallback-pdftotext",
                "quality_notes": (
                    f"Docling failed with exit={proc.returncode}; fallback text used; "
                    f"pages={pages}; non_ws_chars={chars}."
                ),
                "converted_at": converted_at,
            }

        return {
            "source_id": source_ids,
            "source_type": source_type,
            "source_path": source_path,
            "markdown_path": rel(target),
            "converter": "docling",
            "converter_version": "2.112.0",
            "ocr_enabled": "true",
            "language_hint": "eng,sin,tam",
            "status": "failed",
            "quality_notes": (
                f"Docling failed with exit={proc.returncode}; no pdftotext fallback text. "
                f"RapidOCR error={ocr_error}; stderr={proc.stderr[-500:].replace(chr(10), ' ')}"
            ),
            "converted_at": converted_at,
        }


def read_conversion_registry() -> dict[str, dict[str, str]]:
    if not CONVERSION_REGISTRY.exists():
        return {}
    with CONVERSION_REGISTRY.open("r", encoding="utf-8-sig", newline="") as f:
        return {row["source_path"]: row for row in csv.DictReader(f)}


def write_conversion_registry(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "source_id",
        "source_type",
        "source_path",
        "markdown_path",
        "converter",
        "converter_version",
        "ocr_enabled",
        "language_hint",
        "status",
        "quality_notes",
        "converted_at",
    ]
    CONVERSION_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with CONVERSION_REGISTRY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Draftly legal-source PDFs to Markdown.")
    parser.add_argument("--workers", type=int, default=2, help="Number of parallel file conversions.")
    parser.add_argument("--timeout", type=int, default=3600, help="Docling timeout per PDF in seconds.")
    parser.add_argument("--force", action="store_true", help="Reconvert even when Markdown exists.")
    parser.add_argument("--limit", type=int, default=0, help="Convert only the first N PDFs for testing.")
    parser.add_argument(
        "--only-status",
        default="",
        help="Only process PDFs whose current conversion-registry status matches this value.",
    )
    parser.add_argument(
        "--recovery-only",
        action="store_true",
        help="Skip Docling and run the OCR fallback directly.",
    )
    parser.add_argument("--match", default="", help="Only process PDFs whose relative path contains this text.")
    args = parser.parse_args()

    pdfs = sorted(LIBRARY_ROOT.rglob("*.pdf"))
    if args.match:
        pdfs = [pdf for pdf in pdfs if args.match.lower() in rel(pdf).lower()]
    existing_rows = read_conversion_registry()
    if args.only_status:
        pdfs = [
            pdf
            for pdf in pdfs
            if existing_rows.get(rel(pdf), {}).get("status") == args.only_status
        ]
    if args.limit:
        pdfs = pdfs[: args.limit]

    source_info = read_source_registry()
    docling_path = docling_executable()
    rows_by_source = dict(existing_rows)

    print(f"PDFs queued: {len(pdfs)}")
    print(f"Docling executable: {docling_path}")
    print(f"Markdown root: {MARKDOWN_ROOT}")

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {
            pool.submit(
                convert_one,
                pdf,
                source_info,
                args.force,
                args.timeout,
                docling_path,
                args.recovery_only,
            ): pdf
            for pdf in pdfs
        }
        for idx, future in enumerate(as_completed(futures), start=1):
            pdf = futures[future]
            try:
                row = future.result()
            except Exception as exc:  # Keep the batch moving and record the failure.
                row = {
                    "source_id": "UNKNOWN",
                    "source_type": infer_source_type(pdf),
                    "source_path": rel(pdf),
                    "markdown_path": rel(markdown_target(pdf)),
                    "converter": "docling",
                    "converter_version": "2.112.0",
                    "ocr_enabled": "true",
                    "language_hint": "eng,sin,tam",
                    "status": "failed",
                    "quality_notes": f"Unhandled conversion error: {exc}",
                    "converted_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                }
            rows_by_source[row["source_path"]] = row
            print(f"[{idx}/{len(pdfs)}] {row['status']}: {row['source_path']}")

    rows = sorted(rows_by_source.values(), key=lambda row: row["source_path"])
    write_conversion_registry(rows)
    failed = sum(1 for row in rows if row["status"] == "failed")
    print(f"Conversion registry written: {CONVERSION_REGISTRY}")
    print(f"Failed conversions: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
