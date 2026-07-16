"""Normalize legal PDFs/HTML with local-first extraction.

PDF routing is Docling without OCR, then memory-bounded RapidOCR at 150 DPI.
Google Document AI is an opt-in last resort for pages local OCR cannot read and
is protected by a persistent, repository-wide 2,000-page ceiling.
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pypdfium2 as pdfium
from dotenv import load_dotenv
from markdownify import markdownify

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "data/legal-sources/manifests"
CONVERSION_REGISTRY = MANIFESTS / "conversion-registry.csv"
DOCUMENT_AI_LEDGER = ROOT / "data/processed/documentai-usage.json"
DOCUMENT_AI_CACHE = ROOT / "data/processed/documentai-cache"
MIN_DOCUMENT_CHARS = 200
MIN_PAGE_CHARS = 35
MIN_PAGE_CONFIDENCE = 0.62
MAX_DOCUMENT_AI_PAGES = 2_000


@dataclass
class ConversionResult:
    markdown: str
    converter: str
    pages: int
    local_ocr_pages: int = 0
    document_ai_pages: int = 0
    mean_confidence: float | None = None
    notes: str = ""


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def non_ws_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def normalize_markdown(text: str) -> str:
    text = (text or "").replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{4,}", "\n\n\n", text).strip()


def strip_docling_placeholders(text: str) -> str:
    return re.sub(r"<!--\s*(?:image|page)\s*-->", "", text, flags=re.I).strip()


def build_docling_converter() -> Any:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions()
    options.do_ocr = False
    options.generate_page_images = False
    options.generate_picture_images = False
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def docling_extract(converter: Any, source: Path) -> str:
    result = converter.convert(source)
    return strip_docling_placeholders(result.document.export_to_markdown())


def build_rapidocr() -> Any:
    from rapidocr import RapidOCR
    from rapidocr.utils.typings import EngineType, LangDet, LangRec, ModelType, OCRVersion

    params = {
        "Det.engine_type": EngineType.ONNXRUNTIME,
        "Cls.engine_type": EngineType.ONNXRUNTIME,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Det.lang_type": LangDet.EN,
        "Det.model_type": ModelType.MOBILE,
        "Rec.lang_type": LangRec.EN,
        "Rec.model_type": ModelType.MOBILE,
        "Det.ocr_version": OCRVersion.PPOCRV4,
        "Rec.ocr_version": OCRVersion.PPOCRV4,
        "Global.log_level": "warning",
    }
    return RapidOCR(params=params)


def image_has_content(image: Any) -> bool:
    gray = np.asarray(image.convert("L"))
    if not gray.size:
        return False
    ink_ratio = float(np.mean(gray < 235))
    return ink_ratio >= 0.004 and float(np.std(gray)) >= 8.0


def local_ocr_page(engine: Any, image: Any) -> tuple[str, float]:
    result = engine(image)
    lines = [str(value).strip() for value in (result.txts or []) if str(value).strip()]
    scores = [float(value) for value in (result.scores or [])]
    return "\n".join(lines), (sum(scores) / len(scores) if scores else 0.0)


def load_document_ai_ledger() -> dict[str, Any]:
    if DOCUMENT_AI_LEDGER.is_file():
        return json.loads(DOCUMENT_AI_LEDGER.read_text(encoding="utf-8"))
    return {"page_limit": MAX_DOCUMENT_AI_PAGES, "pages_used": 0, "events": []}


def save_document_ai_ledger(ledger: dict[str, Any]) -> None:
    DOCUMENT_AI_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENT_AI_LEDGER.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def document_ai_cache_path(source_id: str, page_number: int) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", source_id).strip("-")
    return DOCUMENT_AI_CACHE / safe_id / f"page-{page_number:04d}.txt"


def seed_document_ai_cache(source_id: str, markdown_path: Path) -> int:
    if not markdown_path.is_file():
        return 0
    markdown = markdown_path.read_text(encoding="utf-8", errors="replace")
    matches = list(re.finditer(r"(?m)^## Page (\d+)\s*$", markdown))
    seeded = 0
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        text = normalize_markdown(markdown[match.end():end])
        if non_ws_chars(text) < MIN_PAGE_CHARS:
            continue
        cache = document_ai_cache_path(source_id, int(match.group(1)))
        if not cache.is_file():
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(text + "\n", encoding="utf-8")
            seeded += 1
    return seeded


def document_ai_ocr_page(image: Any, source_id: str, page_number: int) -> str:
    from google.api_core.client_options import ClientOptions
    from google.cloud import documentai

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.environ.get("GOOGLE_DOCUMENTAI_LOCATION", "").strip()
    processor_id = os.environ.get("GOOGLE_DOCUMENTAI_OCR_PROCESSOR_ID", "").strip()
    if not all((project, location, processor_id)):
        raise RuntimeError(
            "Document AI fallback requires GOOGLE_CLOUD_PROJECT, "
            "GOOGLE_DOCUMENTAI_LOCATION, and GOOGLE_DOCUMENTAI_OCR_PROCESSOR_ID"
        )

    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    )
    name = client.processor_path(project, location, processor_id)
    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(content=buffer.getvalue(), mime_type="image/png"),
    )
    print(f"[{source_id}] sending page {page_number} to Document AI", flush=True)
    response = client.process_document(request=request, timeout=90)
    text = normalize_markdown(response.document.text)
    if not text:
        raise RuntimeError(f"Document AI returned no text for {source_id} page {page_number}")
    return text


def maybe_document_ai(
    image: Any,
    source_id: str,
    page_number: int,
    local_text: str,
    local_score: float,
    allow_document_ai: bool,
    page_limit: int,
    force_document_ai: bool = False,
) -> tuple[str, bool, str]:
    if not allow_document_ai:
        return local_text, False, ""
    if not force_document_ai and not image_has_content(image):
        return local_text, False, ""
    local_is_hard = force_document_ai or non_ws_chars(local_text) < MIN_PAGE_CHARS or (
        local_text and local_score < MIN_PAGE_CONFIDENCE
    )
    if not local_is_hard:
        return local_text, False, ""

    cache = document_ai_cache_path(source_id, page_number)
    if force_document_ai and cache.is_file():
        cached_text = normalize_markdown(cache.read_text(encoding="utf-8", errors="replace"))
        if cached_text:
            return cached_text, True, ""

    ledger = load_document_ai_ledger()
    used = int(ledger.get("pages_used", 0))
    effective_limit = min(page_limit, MAX_DOCUMENT_AI_PAGES)
    if used >= effective_limit:
        return local_text, False, "document-ai-page-budget-exhausted"
    try:
        cloud_text = document_ai_ocr_page(image, source_id, page_number)
    except Exception as exc:  # Preserve local output and make the failure auditable.
        detail = re.sub(r"\s+", " ", str(exc)).strip()[:300]
        return local_text, False, f"document-ai-failed:{type(exc).__name__}:{detail}"

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(cloud_text + "\n", encoding="utf-8")
    ledger["page_limit"] = MAX_DOCUMENT_AI_PAGES
    ledger["pages_used"] = used + 1
    ledger.setdefault("events", []).append({
        "source_id": source_id,
        "page": page_number,
        "used_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    save_document_ai_ledger(ledger)
    return cloud_text, True, ""


def ocr_pdf(
    source: Path,
    source_id: str,
    dpi: int,
    allow_document_ai: bool,
    page_limit: int,
    engine: Any | None,
    prefer_document_ai: bool = False,
) -> ConversionResult:
    pdf = pdfium.PdfDocument(source)
    pages: list[str] = []
    scores: list[float] = []
    cloud_pages = 0
    warnings: list[str] = []
    try:
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            bitmap = page.render(scale=dpi / 72.0)
            image = bitmap.to_pil()
            if prefer_document_ai:
                text, score = "", 0.0
            else:
                if engine is None:
                    raise RuntimeError("Local OCR engine was not initialized")
                text, score = local_ocr_page(engine, image)
            text, used_cloud, warning = maybe_document_ai(
                image, source_id, page_index + 1, text, score,
                allow_document_ai or prefer_document_ai, page_limit,
                prefer_document_ai,
            )
            if warning:
                warnings.append(f"page-{page_index + 1}:{warning}")
            cloud_pages += int(used_cloud)
            scores.append(score)
            pages.append(f"## Page {page_index + 1}\n\n{text}".rstrip())
            del image, bitmap, page
            gc.collect()
            print(
                f"[{source_id}] page {page_index + 1}/{len(pdf)} "
                f"local_chars={non_ws_chars(text)} cloud={used_cloud}",
                flush=True,
            )
    finally:
        pdf.close()

    if prefer_document_ai:
        converter_name = "docling+documentai-ocr"
    else:
        converter_name = "docling+rapidocr-local" + (
            "+documentai-fallback" if cloud_pages else ""
        )
    return ConversionResult(
        markdown="\n\n".join(pages),
        converter=converter_name,
        pages=len(pages),
        local_ocr_pages=0 if prefer_document_ai else len(pages),
        document_ai_pages=cloud_pages,
        mean_confidence=(sum(scores) / len(scores) if scores else None),
        notes="; ".join(warnings),
    )


def convert_pdf(
    source: Path,
    source_id: str,
    docling_converter: Any | None,
    rapidocr_engine: Any,
    dpi: int,
    allow_document_ai: bool,
    page_limit: int,
    docling_already_attempted: bool = False,
    prefer_document_ai: bool = False,
) -> ConversionResult:
    text = ""
    if docling_already_attempted:
        print(f"[{source_id}] using recorded insufficient Docling result", flush=True)
    else:
        if docling_converter is None:
            raise RuntimeError("Docling converter was not initialized")
        try:
            text = docling_extract(docling_converter, source)
        except Exception as exc:
            print(f"[{source_id}] Docling failed: {type(exc).__name__}: {exc}", flush=True)
    if non_ws_chars(text) >= MIN_DOCUMENT_CHARS:
        pdf = pdfium.PdfDocument(source)
        try:
            page_count = len(pdf)
        finally:
            pdf.close()
        return ConversionResult(text, "docling", pages=page_count)
    fallback_name = "Document AI" if prefer_document_ai else "local OCR"
    print(f"[{source_id}] Docling text insufficient; starting {fallback_name}", flush=True)
    return ocr_pdf(
        source, source_id, dpi, allow_document_ai, page_limit, rapidocr_engine,
        prefer_document_ai,
    )


def convert_html(source: Path) -> ConversionResult:
    html = source.read_text(encoding="utf-8", errors="replace")
    return ConversionResult(normalize_markdown(markdownify(html)), "markdownify", pages=1)


def update_conversion_row(row: dict[str, str], result: ConversionResult) -> None:
    confidence = (
        f"{result.mean_confidence:.3f}" if result.mean_confidence is not None else "n/a"
    )
    notes = (
        f"pages={result.pages}; non_ws_chars={non_ws_chars(result.markdown)}; "
        f"local_ocr_pages={result.local_ocr_pages}; "
        f"document_ai_pages={result.document_ai_pages}; mean_local_confidence={confidence}"
    )
    if result.notes:
        notes += f"; {result.notes}"
    has_page_failure = "document-ai-" in result.notes
    row.update({
        "converter": result.converter,
        "ocr_enabled": str(bool(result.local_ocr_pages or result.document_ai_pages)).lower(),
        "status": (
            "converted"
            if non_ws_chars(result.markdown) >= MIN_DOCUMENT_CHARS and not has_page_failure
            else "ocr-review-required"
        ),
        "quality_notes": notes,
        "converted_at": datetime.now(timezone.utc).isoformat(),
    })


def convert_registry(
    source_ids: set[str],
    force: bool,
    dry_run: bool,
    dpi: int,
    allow_document_ai: bool,
    page_limit: int,
    prefer_document_ai: bool,
) -> int:
    rows, fields = read_csv(CONVERSION_REGISTRY)
    selected = [
        row for row in rows
        if (not source_ids or row["source_id"] in source_ids)
        and (force or row["status"] in {"needs-ocr", "failed", "ocr-review-required"})
    ]
    if not selected:
        print("No conversion-registry rows selected.")
        return 0
    if dry_run:
        for row in selected:
            print(f"[dry-run] {row['source_id']} {row['source_path']} -> {row['markdown_path']}")
        return 0

    docling_converter = None
    rapidocr_engine = None if prefer_document_ai else build_rapidocr()
    failures = 0
    for row in selected:
        source = ROOT / row["source_path"]
        output = ROOT / row["markdown_path"]
        try:
            if prefer_document_ai and "documentai" in row.get("converter", "").casefold():
                seeded = seed_document_ai_cache(row["source_id"], output)
                if seeded:
                    print(f"[{row['source_id']}] seeded {seeded} cached pages", flush=True)
            suffix = source.suffix.casefold()
            if suffix == ".pdf":
                prior_docling_attempt = (
                    row.get("converter", "").casefold().startswith("docling+")
                    or (
                        row["status"] == "needs-ocr"
                        and row.get("converter", "").casefold().startswith("docling")
                    )
                )
                if not prior_docling_attempt and docling_converter is None:
                    docling_converter = build_docling_converter()
                result = convert_pdf(
                    source, row["source_id"], docling_converter, rapidocr_engine,
                    dpi, allow_document_ai, page_limit, prior_docling_attempt,
                    prefer_document_ai,
                )
            elif suffix in {".html", ".htm"}:
                result = convert_html(source)
            else:
                raise ValueError(f"Unsupported input format: {suffix}")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(normalize_markdown(result.markdown) + "\n", encoding="utf-8")
            update_conversion_row(row, result)
            if row["status"] != "converted":
                failures += 1
            print(
                f"[{row['source_id']}] status={row['status']} "
                f"chars={non_ws_chars(result.markdown)} converter={result.converter}",
                flush=True,
            )
        except Exception as exc:
            failures += 1
            row["status"] = "failed"
            row["quality_notes"] = f"{type(exc).__name__}: {exc}"
            row["converted_at"] = datetime.now(timezone.utc).isoformat()
            print(f"[{row['source_id']}] failed: {type(exc).__name__}: {exc}", flush=True)
        write_csv(CONVERSION_REGISTRY, rows, fields)
    return failures


def update_court_manifest(output: Path, chars: int) -> None:
    court_root = (ROOT / "data/legal-sources/library/case-law/courts").resolve()
    try:
        output.resolve().relative_to(court_root)
    except ValueError:
        return
    if not output.name.casefold().endswith(".pdf.txt"):
        return
    manifest = MANIFESTS / "case-law-courts.csv"
    rows, fields = read_csv(manifest)
    pdf_name = output.name[:-4]
    matched = False
    for row in rows:
        if row["file"].casefold() == pdf_name.casefold():
            row["chars"] = str(chars)
            row["needs_ocr"] = "0"
            matched = True
            break
    if not matched:
        raise RuntimeError(f"Court manifest has no row for {pdf_name}")
    write_csv(manifest, rows, fields)


def convert_single(
    source: Path,
    output: Path,
    label: str,
    dpi: int,
    prefer_document_ai: bool,
    page_limit: int,
) -> int:
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.casefold() == ".pdf":
        rapidocr_engine = None if prefer_document_ai else build_rapidocr()
        docling_converter = None if prefer_document_ai else build_docling_converter()
        result = convert_pdf(
            source, label, docling_converter, rapidocr_engine, dpi,
            prefer_document_ai, page_limit, prefer_document_ai,
            prefer_document_ai,
        )
    elif source.suffix.casefold() in {".html", ".htm"}:
        result = convert_html(source)
    else:
        raise ValueError(f"Unsupported input format: {source.suffix}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(normalize_markdown(result.markdown) + "\n", encoding="utf-8")
    chars = non_ws_chars(result.markdown)
    update_court_manifest(output, chars)
    print(
        f"[{label}] status={'converted' if chars >= MIN_DOCUMENT_CHARS else 'ocr-review-required'} "
        f"chars={chars} converter={result.converter}",
        flush=True,
    )
    return 0 if chars >= MIN_DOCUMENT_CHARS and not result.notes else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--label")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--allow-document-ai", action="store_true")
    parser.add_argument(
        "--prefer-document-ai",
        action="store_true",
        help="After an insufficient Docling result, send nonblank pages directly to Document AI.",
    )
    parser.add_argument("--document-ai-page-limit", type=int, default=MAX_DOCUMENT_AI_PAGES)
    args = parser.parse_args()
    if not 100 <= args.dpi <= 200:
        parser.error("--dpi must be between 100 and 200")
    if not 1 <= args.document_ai_page_limit <= MAX_DOCUMENT_AI_PAGES:
        parser.error(f"--document-ai-page-limit must be between 1 and {MAX_DOCUMENT_AI_PAGES}")
    if bool(args.input) != bool(args.output):
        parser.error("--input and --output must be supplied together")
    return args


def main() -> None:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    if args.input:
        source = args.input if args.input.is_absolute() else ROOT / args.input
        output = args.output if args.output.is_absolute() else ROOT / args.output
        label = args.label or source.stem
        raise SystemExit(convert_single(
            source, output, label, args.dpi, args.prefer_document_ai,
            args.document_ai_page_limit,
        ))
    failures = convert_registry(
        set(args.source_id), args.force, args.dry_run, args.dpi,
        args.allow_document_ai, args.document_ai_page_limit, args.prefer_document_ai,
    )
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
