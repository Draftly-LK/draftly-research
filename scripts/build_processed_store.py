"""Build the complete file-based retrieval store under data/processed.

Original PDFs and harvested text remain authoritative under data/legal-sources.
This script creates normalized Markdown, provenance, case records, and local
copies of the rule tables. It makes no network or cloud calls.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGAL = ROOT / "data/legal-sources"
MANIFESTS = LEGAL / "manifests"
PROCESSED = ROOT / "data/processed"
DOCS = PROCESSED / "docs"
LEGAL_KINDS = {"statute", "amendment", "gazette", "institution-guide"}
RULE_TABLES = [
    "source-registry.csv", "topics.csv", "topic-sources.csv", "topics.json",
    "slr-modern-index.csv", "slr-modern-cases.csv",
]
DOCUMENT_FIELDS = [
    "doc_id", "source_id", "source_record_id", "kind", "source", "title",
    "court", "year", "citation", "origin_url", "local_pdf",
    "raw_text_path", "text_path", "converter", "converter_version", "status",
    "retrieved_date", "retrieved_date_source", "chars", "sha256", "quality_flags",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def relative(path: Path | str) -> str:
    path = Path(path)
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def slug(value: str, fallback: str = "document") -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or fallback


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace("\f", "\n\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = "\n".join(line.rstrip() for line in value.splitlines())
    return re.sub(r"\n{4,}", "\n\n\n", value).strip()


def quality_flags(text: str) -> list[str]:
    flags = []
    if len(re.sub(r"\s+", "", text)) < 200:
        flags.append("low_text")
    if "\ufffd" in text:
        flags.append("replacement_character")
    if any(marker in text for marker in ("â€", "â€™", "Ã", "Â")):
        flags.append("possible_mojibake")
    return flags


def write_document(path: Path, title: str, body: str) -> tuple[int, str, list[str]]:
    body = normalize_text(body)
    title = re.sub(r"\s+", " ", title or "Untitled document").strip()
    content = body + "\n" if body.startswith("# ") else f"# {title}\n\n{body}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = content.encode("utf-8")
    path.write_bytes(encoded)
    return (
        len(content),
        hashlib.sha256(encoded).hexdigest(),
        quality_flags(content),
    )


def local_date(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()


def conversion_by_source() -> dict[str, dict[str, str]]:
    output = {}
    for row in read_csv(MANIFESTS / "conversion-registry.csv"):
        for source_id in re.split(r"[;\s]+", row["source_id"].strip()):
            if source_id:
                output[source_id] = row
    return output


def legal_documents() -> list[dict[str, str]]:
    conversions = conversion_by_source()
    output = []
    for source in read_csv(MANIFESTS / "source-registry.csv"):
        if source["source_type"] not in LEGAL_KINDS:
            continue
        source_id = source["source_id"]
        conversion = conversions.get(source_id, {})
        markdown_path = (
            source.get("local_markdown_path", "").strip()
            or conversion.get("markdown_path", "").strip()
        )
        candidate = ROOT / markdown_path if markdown_path else None
        destination = DOCS / f"{source['source_type']}s" / (
            f"{source_id.casefold()}-{slug(source['official_title'])}.md"
        )
        status = conversion.get("status", "") or source.get("status", "")
        chars = 0
        digest = ""
        flags: list[str] = []
        if candidate and candidate.is_file() and candidate.stat().st_size:
            body = candidate.read_text(encoding="utf-8", errors="replace")
            chars, digest, flags = write_document(destination, source["official_title"], body)
            status = "converted"
        else:
            status = "needs-ocr" if status == "needs-ocr" else "missing-text"
        retrieved = source.get("download_date", "").strip()
        output.append({
            "doc_id": source_id.casefold(), "source_id": source_id,
            "source_record_id": source_id, "kind": source["source_type"],
            "source": "source-registry", "title": source["official_title"],
            "court": "", "year": source.get("year", ""), "citation": "",
            "origin_url": source.get("preferred_source_url", ""),
            "local_pdf": source.get("local_pdf_path", "").strip(),
            "raw_text_path": markdown_path, "text_path": relative(destination),
            "converter": conversion.get("converter", "manifest-copy"),
            "converter_version": conversion.get("converter_version", ""),
            "status": status, "retrieved_date": retrieved,
            "retrieved_date_source": "registry" if retrieved else "unknown",
            "chars": str(chars), "sha256": digest,
            "quality_flags": ";".join(flags),
        })
    return output


def commonlii_documents() -> tuple[list[dict[str, str]], list[dict]]:
    documents, cases = [], []
    for case in read_csv(MANIFESTS / "case-law-commonlii-conveyancing.csv"):
        case_id = f"commonlii-{case['db']}-{case['year']}-{case['case_no']}"
        source_path = ROOT / case["text_file"]
        destination = DOCS / "case-law/commonlii" / case["db"] / case["year"] / f"{case['case_no']}.md"
        chars, digest, flags = write_document(
            destination,
            case["title"],
            source_path.read_text(encoding="utf-8", errors="replace"),
        )
        source_id = "SRC067" if "sri lr" in case["citation"].casefold() else "SRC066"
        document = {
            "doc_id": case_id, "source_id": source_id,
            "source_record_id": f"{case['db']}/{case['year']}/{case['case_no']}",
            "kind": "case-law", "source": "commonlii", "title": case["title"],
            "court": case["db"], "year": case["year"], "citation": case["citation"],
            "origin_url": case["url"], "local_pdf": "",
            "raw_text_path": case["text_file"], "text_path": relative(destination),
            "converter": "commonlii-html-strip", "converter_version": "",
            "status": "converted", "retrieved_date": local_date(source_path),
            "retrieved_date_source": "local-file-mtime", "chars": str(chars),
            "sha256": digest, "quality_flags": ";".join(flags),
        }
        documents.append(document)
        cases.append({
            "case_id": case_id, "doc_id": case_id, "source": "commonlii",
            "source_record_id": document["source_record_id"], "court": case["db"],
            "year": case["year"], "citation": case["citation"], "title": case["title"],
            "url": case["url"], "text_path": document["text_path"],
            "hits": int(case["hits"] or 0), "conveyancing_match": True,
            "status": "unverified",
        })
    return documents, cases


def inferred_year(value: str) -> str:
    years = re.findall(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)", value)
    return years[-1] if years else ""


def court_documents() -> tuple[list[dict[str, str]], list[dict]]:
    documents, cases = [], []
    for case in read_csv(MANIFESTS / "case-law-courts.csv"):
        stem = re.sub(r"\.pdf$", "", case["file"], flags=re.I)
        case_id = f"courts-{case['court']}-{case['file']}"
        source_path = ROOT / case["text_file"]
        filename_key = hashlib.sha256(case["file"].encode("utf-8")).hexdigest()[:10]
        destination = (
            DOCS / "case-law/courts" / case["court"]
            / f"{slug(stem)}-{filename_key}.md"
        )
        body = source_path.read_text(encoding="utf-8", errors="replace") if source_path.is_file() else ""
        title = re.sub(r"[-_.]+", " ", stem).strip()
        chars = 0
        digest = ""
        flags: list[str] = []
        status = "converted"
        if body.strip():
            chars, digest, flags = write_document(destination, title, body)
        else:
            status = "needs-ocr" if case["needs_ocr"] == "1" else "missing-text"
        pdf_path = source_path.with_suffix("")
        local_pdf = relative(pdf_path) if pdf_path.is_file() else ""
        document = {
            "doc_id": case_id, "source_id": "",
            "source_record_id": f"{case['court']}/{case['file']}",
            "kind": "case-law", "source": "official-courts", "title": title,
            "court": case["court"].upper(), "year": inferred_year(case["file"]),
            "citation": "", "origin_url": case["url"], "local_pdf": local_pdf,
            "raw_text_path": case["text_file"], "text_path": relative(destination),
            "converter": "pypdfium2", "converter_version": "", "status": status,
            "retrieved_date": local_date(source_path) if source_path.is_file() else "",
            "retrieved_date_source": "local-file-mtime" if source_path.is_file() else "unknown",
            "chars": str(chars), "sha256": digest, "quality_flags": ";".join(flags),
        }
        documents.append(document)
        cases.append({
            "case_id": case_id, "doc_id": case_id, "source": "official-courts",
            "source_record_id": document["source_record_id"], "court": document["court"],
            "year": document["year"], "citation": "", "title": title,
            "url": case["url"], "text_path": document["text_path"],
            "hits": int(case["hits"] or 0),
            "conveyancing_match": case["conveyancing"] == "1", "status": "unverified",
        })
    return documents, cases


def internet_archive_documents() -> list[dict[str, str]]:
    output = []
    for volume in read_csv(MANIFESTS / "case-law-ia-manifest.csv"):
        doc_id = f"internet-archive-{volume['identifier']}"
        source_path = ROOT / volume["text_file"]
        destination = DOCS / "case-law/internet-archive" / f"{volume['identifier']}.md"
        chars, digest, flags = write_document(
            destination, volume["title"],
            source_path.read_text(encoding="utf-8", errors="replace"),
        )
        output.append({
            "doc_id": doc_id, "source_id": "SRC066",
            "source_record_id": volume["identifier"], "kind": "case-law-volume",
            "source": "internet-archive", "title": volume["title"], "court": "",
            "year": volume["year"], "citation": "", "origin_url": volume["detail_url"],
            "local_pdf": "", "raw_text_path": volume["text_file"],
            "text_path": relative(destination), "converter": "internet-archive-ocr",
            "converter_version": "", "status": "converted",
            "retrieved_date": local_date(source_path), "retrieved_date_source": "local-file-mtime",
            "chars": str(chars), "sha256": digest, "quality_flags": ";".join(flags),
        })
    return output


def write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def copy_rule_tables() -> None:
    for filename in RULE_TABLES:
        source = MANIFESTS / filename
        if source.is_file():
            shutil.copy2(source, PROCESSED / filename)


def write_readme() -> None:
    (PROCESSED / "README.md").write_text(
        """# Draftly Processed Legal Corpus

This directory is the rebuildable, file-based input for Draftly's deterministic
retrieval engine. Original PDFs and harvested text remain under
`data/legal-sources/`; they remain authoritative.

## Contents

- `docs/` contains normalized UTF-8 Markdown for each available legal document,
  judgment, or historical report volume.
- `documents.csv` records provenance, conversion, status, checksum, and quality.
- `cases.jsonl` contains CommonLII and official-court records and points only to
  Markdown in this directory.
- `source-registry.csv`, `topics.csv`, `topic-sources.csv`, and `topics.json`
  are the deterministic routing tables.
- `slr-modern-*.csv` contains indexed-only references, not claimed full text.
- `case_statute_section_links.csv` contains deterministic, evidence-backed
  candidate edges; `unresolved_citations.csv` keeps passages the rules could not
  pair safely.
- `verification-sample.csv` is a 30-edge lawyer review sheet. Generated links
  remain unverified until a reviewer completes it.
- `documentai-usage.json` and `documentai-cache/` make the optional OCR fallback
  resumable and enforce its 2,000-page ceiling.

Generated links remain unverified until lawyer sign-off. Rebuild with
`uv run python scripts/build_processed_store.py`.
""",
        encoding="utf-8",
    )


def verify_documents(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    failures = []
    for row in rows:
        path = ROOT / row["text_path"]
        if not path.is_file():
            failures.append(row)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(re.sub(r"\s+", "", text)) < 200:
            failures.append(row)
    return failures


def build() -> tuple[list[dict[str, str]], list[dict], list[dict[str, str]]]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    legal = legal_documents()
    common_docs, common_cases = commonlii_documents()
    court_docs, court_cases = court_documents()
    ia_docs = internet_archive_documents()
    documents = legal + common_docs + court_docs + ia_docs
    cases = common_cases + court_cases
    if len({row["doc_id"] for row in documents}) != len(documents):
        raise ValueError("Duplicate document IDs")
    if len({row["case_id"] for row in cases}) != len(cases):
        raise ValueError("Duplicate case IDs")
    write_rows(PROCESSED / "documents.csv", documents, DOCUMENT_FIELDS)
    with (PROCESSED / "cases.jsonl").open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False) + "\n")
    copy_rule_tables()
    write_readme()
    failures = verify_documents(documents)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "documents": len(documents), "legal_source_documents": len(legal),
        "commonlii_judgments": len(common_docs),
        "official_court_judgments": len(court_docs),
        "internet_archive_volumes": len(ia_docs), "case_records": len(cases),
        "missing_or_low_text": len(failures),
    }
    (PROCESSED / "store-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return documents, cases, failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    documents, cases, failures = build()
    print(f"documents={len(documents)} cases={len(cases)} missing_or_low_text={len(failures)}")
    for row in failures:
        print(f"[missing] {row['doc_id']} {row['status']} {row['local_pdf']}")
    if args.require_complete and failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
