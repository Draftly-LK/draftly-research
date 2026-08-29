"""Full-page Google Vision OCR across the whole benchmark corpus.

    uv run python ocr-benchmark/vision_corpus_run.py --dry-run
    uv run python ocr-benchmark/vision_corpus_run.py
    uv run python ocr-benchmark/vision_corpus_run.py --report-only

One Vision call per page. No docTR, no cropping, no per-region calls.

Resumable: raw responses are cached under the gitignored
renders/vision-cache/fullpage/, keyed by (document, page, dpi). A page already in
the cache is never called again, so an interrupted run resumes for free.

PRIVACY: recognised text stays in the gitignored cache. Everything this script
prints or writes to reports/ is counts and ratios - no field values, no
transcripts, no client content.
"""

from __future__ import annotations

import argparse
import gc
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import render

DPI = 200
VARIANT = "original"
LANGUAGE_HINTS = ["si", "ta", "en"]
USD_PER_UNIT = 0.0015          # DOCUMENT_TEXT_DETECTION, after 1000 free units/month
CACHE = config.RENDERS / "vision-cache" / "fullpage"
REPORT = config.REPORTS / "vision-corpus-metrics.json"

# A page below either of these is worth a human look rather than trusting.
MIN_CHARS = 40
MIN_CONFIDENCE = 0.70

_client = None


def client():
    global _client
    if _client is None:
        from dotenv import load_dotenv

        load_dotenv(config.ROOT / ".env")
        from google.cloud import vision

        _client = vision.ImageAnnotatorClient()
    return _client


def cache_path(doc_id: str, page_no: int) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in doc_id)
    return CACHE / safe / f"p{page_no:04d}@{DPI}-{VARIANT}.json"


def script_mix(text: str) -> dict[str, Any]:
    counts = {
        "sinhala": len(re.findall(r"[඀-෿]", text)),
        "tamil": len(re.findall(r"[஀-௿]", text)),
        "latin": len(re.findall(r"[A-Za-z]", text)),
        "digits": len(re.findall(r"[0-9]", text)),
    }
    total = sum(counts.values())
    ratios = {k: (v / total if total else 0.0) for k, v in counts.items()}
    return {"counts": counts, "ratios": ratios}


def call_vision(image) -> dict[str, Any]:
    """One page -> text plus block confidences. Raises on API error."""
    import io

    from google.cloud import vision

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    began = time.time()
    response = client().document_text_detection(
        image=vision.Image(content=buffer.getvalue()),
        image_context=vision.ImageContext(language_hints=LANGUAGE_HINTS),
    )
    elapsed = time.time() - began
    if response.error.message:
        raise RuntimeError(response.error.message[:200])

    annotation = response.full_text_annotation
    confidences = [b.confidence for p in annotation.pages for b in p.blocks]
    detected: list[str] = []
    for page in annotation.pages:
        for lang in getattr(page.property, "detected_languages", []) or []:
            detected.append(lang.language_code)
    return {
        "text": annotation.text or "",
        "seconds": round(elapsed, 2),
        "blocks": len(confidences),
        "mean_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "min_confidence": round(min(confidences), 4) if confidences else 0.0,
        "detected_languages": detected,
    }


def page_metrics(doc_id: str, page_no: int, payload: dict[str, Any], matter: str) -> dict[str, Any]:
    """Aggregates only. Never returns the recognised text itself."""
    text = payload.get("text", "")
    stripped = re.sub(r"\s+", "", text)
    mix = script_mix(text)
    return {
        "matter": matter,
        "document": doc_id.split("/")[-1],
        "page": page_no,
        "chars": len(stripped),
        "blocks": payload.get("blocks", 0),
        "mean_confidence": payload.get("mean_confidence", 0.0),
        "min_confidence": payload.get("min_confidence", 0.0),
        "seconds": payload.get("seconds", 0.0),
        "detected_languages": sorted(set(payload.get("detected_languages", []))),
        **{f"ratio_{k}": round(v, 4) for k, v in mix["ratios"].items()},
        **{f"count_{k}": v for k, v in mix["counts"].items()},
        "empty": len(stripped) < MIN_CHARS,
        "low_confidence": payload.get("mean_confidence", 0.0) < MIN_CONFIDENCE,
    }


def dominant_script(row: dict[str, Any]) -> str:
    ratios = {k: row[f"ratio_{k}"] for k in ("sinhala", "tamil", "latin")}
    if row["chars"] < MIN_CHARS:
        return "empty"
    best = max(ratios, key=lambda k: ratios[k])
    if ratios[best] < 0.15:
        return "numeric/other"
    others = sum(v for k, v in ratios.items() if k != best)
    return f"{best}+mixed" if others >= 0.25 else best


def enumerate_pages(limit_matter: str | None = None) -> list[tuple[str, Path, int]]:
    import pypdfium2 as pdfium

    out: list[tuple[str, Path, int]] = []
    for case in config.case_dirs():
        if limit_matter and limit_matter.lower() not in case.name.lower():
            continue
        for doc in config.case_documents(case):
            if doc.suffix.lower() == ".pdf":
                pdf = pdfium.PdfDocument(doc)
                try:
                    count = len(pdf)
                finally:
                    pdf.close()
            else:
                count = 1
            for page_no in range(1, count + 1):
                out.append((case.name, doc, page_no))
    return out


def summarise(group: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(group)
    chars = sum(r["chars"] for r in group)
    scripted = max(
        sum(r["count_sinhala"] + r["count_tamil"] + r["count_latin"] + r["count_digits"]
            for r in group),
        1,
    )
    return {
        "pages": n,
        "chars_total": chars,
        "chars_per_page": round(chars / n, 1),
        "mean_confidence": round(sum(r["mean_confidence"] for r in group) / n, 4),
        "empty_pages": sum(r["empty"] for r in group),
        "low_confidence_pages": sum(r["low_confidence"] for r in group),
        "seconds_per_page": round(sum(r["seconds"] for r in group) / n, 2),
        "script_char_share": {
            k: round(sum(r[f"count_{k}"] for r in group) / scripted, 4)
            for k in ("sinhala", "tamil", "latin", "digits")
        },
        "dominant_script_pages": dict(Counter(r["dominant_script"] for r in group)),
    }


def difficulty(row: dict[str, Any]) -> float:
    """Blend of low confidence and sparse output. Higher = more worth inspecting."""
    conf_gap = max(0.0, MIN_CONFIDENCE - row["mean_confidence"]) / MIN_CONFIDENCE
    sparsity = 1.0 - min(row["chars"], 400) / 400
    return round(0.6 * conf_gap + 0.4 * sparsity, 4)


def write_report(rows, failures, calls, wall, total_pages) -> None:
    if not rows:
        print("no pages processed")
        return

    for row in rows:
        row["dominant_script"] = dominant_script(row)
        row["difficulty"] = difficulty(row)

    by_matter: dict[str, list] = defaultdict(list)
    by_document: dict[str, list] = defaultdict(list)
    for row in rows:
        by_matter[row["matter"]].append(row)
        by_document[f"{row['matter']}/{row['document']}"].append(row)

    hardest = sorted(rows, key=lambda r: -r["difficulty"])[:10]

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "vision full-page DOCUMENT_TEXT_DETECTION",
        "languageHints": LANGUAGE_HINTS,
        "dpi": DPI,
        "renderVariant": VARIANT,
        "thresholds": {"min_chars": MIN_CHARS, "min_confidence": MIN_CONFIDENCE},
        "coverage": {
            "pages_in_corpus": total_pages,
            "pages_with_results": len(rows),
            "pages_failed": len(failures),
        },
        "cost": {
            "api_calls_this_run": calls,
            "usd_per_unit": USD_PER_UNIT,
            "estimated_usd_this_run": round(calls * USD_PER_UNIT, 4),
            "estimated_usd_full_corpus": round(total_pages * USD_PER_UNIT, 2),
            "note": "first 1000 units per month are free",
        },
        "runtime": {
            "wall_seconds": round(wall, 1),
            "mean_seconds_per_page": round(sum(r["seconds"] for r in rows) / len(rows), 2),
            "max_seconds_per_page": round(max(r["seconds"] for r in rows), 2),
        },
        "overall": summarise(rows),
        "by_matter": {m: summarise(g) for m, g in sorted(by_matter.items())},
        "by_document_script": {
            doc: {
                "pages": len(g),
                "dominant_script_pages": dict(Counter(r["dominant_script"] for r in g)),
                "mean_confidence": round(sum(r["mean_confidence"] for r in g) / len(g), 4),
            }
            for doc, g in sorted(by_document.items())
        },
        "failures": failures,
        "difficult_pages_for_manual_inspection": [
            {
                "matter": r["matter"],
                "document": r["document"],
                "page": r["page"],
                "chars": r["chars"],
                "mean_confidence": r["mean_confidence"],
                "dominant_script": r["dominant_script"],
                "difficulty": r["difficulty"],
            }
            for r in hardest
        ],
        "note": (
            "Counts and ratios only. No recognised text, field values or client content "
            "appear in this file. These are OCR COVERAGE statistics, NOT accuracy: the "
            "corpus is unlabelled apart from 37 fields in platform-case-001, so OCR "
            "output on unlabelled pages cannot be scored for correctness."
        ),
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {REPORT}")

    overall = report["overall"]
    print(
        f"\npages {overall['pages']} | empty {overall['empty_pages']} | "
        f"low-confidence {overall['low_confidence_pages']} | failed {len(failures)}"
    )
    print(
        f"mean confidence {overall['mean_confidence']:.3f} | "
        f"{overall['chars_per_page']:.0f} chars/page | {overall['seconds_per_page']:.2f} s/page"
    )
    print("script share:", {k: f"{v:.1%}" for k, v in overall["script_char_share"].items()})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="plan and cost, no calls")
    parser.add_argument("--report-only", action="store_true", help="rebuild report from cache")
    parser.add_argument("--matter", help="restrict to matters matching this string")
    parser.add_argument("--limit", type=int, help="first N pages only")
    parser.add_argument("--max-calls", type=int, default=400, help="hard spend stop")
    args = parser.parse_args(argv)

    config.assert_inputs_private()
    pages = enumerate_pages(args.matter)
    if args.limit:
        pages = pages[: args.limit]

    cached = sum(1 for m, d, p in pages if cache_path(f"{m}/{d.name}", p).is_file())
    todo = len(pages) - cached
    print(f"{len(pages)} pages | {cached} already cached | {todo} to call")
    print(
        f"estimated new spend: {todo} units ~ ${todo * USD_PER_UNIT:.2f} "
        f"(first 1000 units/month are free)"
    )
    if args.dry_run:
        return 0

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    calls = 0
    began_all = time.time()

    for index, (matter, doc, page_no) in enumerate(pages, 1):
        doc_id = f"{matter}/{doc.name}"
        dest = cache_path(doc_id, page_no)

        if dest.is_file():
            payload = json.loads(dest.read_text(encoding="utf-8"))
        elif args.report_only:
            continue
        else:
            if calls >= args.max_calls:
                print(f"\ncall cap {args.max_calls} reached; re-run to continue (progress cached)")
                break
            try:
                page = render.render_doc(doc, dpi=DPI, variant=VARIANT, page_limit=page_no)[
                    page_no - 1
                ]
            except Exception as exc:  # noqa: BLE001 - render failures are heterogeneous
                failures.append(
                    {"document": doc.name, "page": page_no, "stage": "render",
                     "error": type(exc).__name__}
                )
                continue
            payload = None
            try:
                payload = call_vision(page.image)
                calls += 1
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001 - provider errors are heterogeneous
                failures.append(
                    {"document": doc.name, "page": page_no, "stage": "vision",
                     "error": type(exc).__name__}
                )
            finally:
                page.image.close()
                gc.collect()
            if payload is None:
                continue

        rows.append(page_metrics(doc_id, page_no, payload, matter))
        if index % 20 == 0 or index == len(pages):
            print(f"  [{index:3d}/{len(pages)}] calls={calls} elapsed={time.time() - began_all:.0f}s")

    write_report(rows, failures, calls, time.time() - began_all, len(pages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
