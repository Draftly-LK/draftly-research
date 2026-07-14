"""Collect a pilot conveyancing case-law digest for Draftly.

This script intentionally records what it can verify and marks case citations as
unverified until the underlying law-report text is checked.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import ssl
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup
except ImportError as exc:  # pragma: no cover - dependency is available via repo env.
    raise SystemExit(
        "BeautifulSoup is required in this repo environment. Run `uv sync` first."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = ROOT / "data" / "legal-sources" / "library" / "case-law"
MARKDOWN_ROOT = ROOT / "data" / "legal-sources" / "library-markdown" / "case-law"
MANIFESTS_ROOT = ROOT / "data" / "legal-sources" / "manifests"
CONVERSION_REGISTRY = MANIFESTS_ROOT / "conversion-registry.csv"
CITATIONS_CSV = MANIFESTS_ROOT / "case-law-citations.csv"

LAWNET_URLS = [
    "https://lawnet.gov.lk/wp-content/uploads/",
    "https://www.lawnet.gov.lk/wp-content/uploads/",
]
LAWNET_SSL_NOTE = (
    "LawNet HTTPS failed certificate verification during this pilot; "
    "the uploads directory also returned 404 when retried without verification."
)
LAWNET_FALLBACK_DIGEST_URL = (
    "https://www.lawlanka.com/lal_v2/relatedCases?"
    "chapterId=2001Y5V117C&subjectName=registration+of+documents"
)
SUBJECT = "registration of documents"
SOURCE_ID = "SRC089-ROD-DIGEST"
TOPIC_ID = "19"
STATUTE_ID = "SRC005"

SAMPLE_CASE_TITLES = {
    "DE SILVA v. WEERAPPA CHETTIAR",
    "REV.MAUSSAGOLLE DHARMARAKKITHA THERO AND ANOTHER v. REGISTRAR OF LANDS AND OTHERS",
    "REGISTRAR GENERAL v. SANGARAPILLAI",
}


@dataclass(frozen=True)
class DigestEntry:
    row_id: str
    section: str
    case_name: str
    report_series: str
    report_year: str
    report_volume: str
    page: str
    citation: str
    source_url: str
    match_reason: str
    verification_status: str
    notes: str


def fetch_text(url: str, *, verify_tls: bool = True) -> str:
    request = Request(url, headers={"User-Agent": "Draftly case-law pilot/0.1"})
    context = ssl.create_default_context() if verify_tls else ssl._create_unverified_context()
    with urlopen(request, timeout=30, context=context) as response:
        data = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return data.decode(charset, errors="replace")


def check_lawnet() -> list[str]:
    notes: list[str] = []
    for url in LAWNET_URLS:
        try:
            fetch_text(url, verify_tls=True)
            notes.append(f"<{url}> reachable with TLS verification.")
        except Exception as exc:
            notes.append(f"<{url}> TLS fetch failed: {type(exc).__name__}: {exc}")
        try:
            fetch_text(url, verify_tls=False)
            notes.append(f"<{url}> reachable only with TLS verification disabled.")
        except HTTPError as exc:
            notes.append(f"<{url}> insecure retry failed: HTTP {exc.code}")
        except URLError as exc:
            notes.append(f"<{url}> insecure retry failed: {exc.reason}")
        except Exception as exc:
            notes.append(f"<{url}> insecure retry failed: {type(exc).__name__}: {exc}")
    return notes


def parse_digest(html: str) -> list[DigestEntry]:
    soup = BeautifulSoup(html, "html.parser")
    entries: list[DigestEntry] = []
    current_section = "subject"

    for tr in soup.find_all("tr"):
        cells = [
            cell.get_text(" ", strip=True)
            for cell in tr.find_all(["td", "th"], recursive=False)
        ]
        if len(cells) == 1 and cells[0].startswith("Section No"):
            match = re.search(r"Section No\s*:\s*(\d+)", cells[0])
            current_section = match.group(1) if match else cells[0]
            continue
        if len(cells) != 3 or cells[1] not in {"NLR", "SLR"}:
            continue

        case_name, series, report = cells
        year, volume, page = parse_report(series, report)
        citation = build_citation(series, year, volume, page)
        row_id = f"ROD-{len(entries) + 1:03d}"
        entries.append(
            DigestEntry(
                row_id=row_id,
                section=current_section,
                case_name=normalize_case_name(case_name),
                report_series=series,
                report_year=year,
                report_volume=volume,
                page=page,
                citation=citation,
                source_url=LAWNET_FALLBACK_DIGEST_URL,
                match_reason="LawLanka Registration of Documents related-case digest",
                verification_status="unverified",
                notes=(
                    "Citation extracted from digest page; full LawNet/Law Report "
                    "PDF text not verified in this pilot."
                ),
            )
        )

    return entries


def parse_report(series: str, report: str) -> tuple[str, str, str]:
    if series == "SLR":
        match = re.search(r"(?P<year>\d{4}),\s*Vol\s*:\s*(?P<vol>\d+),\s*Page\s*:\s*(?P<page>\d+)", report)
        if match:
            return match.group("year"), match.group("vol"), match.group("page")
    match = re.search(r"Vol\s*:\s*(?P<vol>\d+),\s*Page\s*:\s*(?P<page>\d+)", report)
    if match:
        return "", match.group("vol"), match.group("page")
    return "", "", ""


def build_citation(series: str, year: str, volume: str, page: str) -> str:
    if series == "SLR" and year:
        return f"{year} {volume} SLR {page}"
    if series == "NLR":
        return f"{volume} NLR {page}"
    return f"{series} Vol {volume} Page {page}".strip()


def normalize_case_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace(" VS ", " v. ")).strip()


def slugify(value: str) -> str:
    value = value.lower().replace("'", "")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "case"


def write_csv(entries: list[DigestEntry]) -> None:
    MANIFESTS_ROOT.mkdir(parents=True, exist_ok=True)
    with CITATIONS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(DigestEntry.__dataclass_fields__))
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.__dict__)


def write_raw_digest(html: str, law_net_notes: list[str]) -> tuple[Path, Path]:
    raw_dir = LIBRARY_ROOT / "registration-of-documents-digest" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    html_path = raw_dir / "lawlanka-registration-of-documents-related-cases.html"
    notes_path = raw_dir.parent / "fetch-notes.md"
    html_path.write_text(html, encoding="utf-8")
    notes_path.write_text(build_fetch_notes(law_net_notes), encoding="utf-8")
    return html_path, notes_path


def build_fetch_notes(law_net_notes: list[str]) -> str:
    lines = [
        "# Registration of Documents Case-Law Fetch Notes",
        "",
        "## LawNet Status",
        "",
        LAWNET_SSL_NOTE,
        "",
    ]
    lines.extend(f"- {note}" for note in law_net_notes)
    lines.extend(
        [
            "",
            "## Fallback Digest Used",
            "",
            f"- Source: <{LAWNET_FALLBACK_DIGEST_URL}>",
            "- Subject: `registration of documents`",
            "- Status: digest page fetched and parsed; individual law-report PDFs were not fetched.",
            "",
        ]
    )
    return "\n".join(lines)


def write_case_nodes(entries: list[DigestEntry]) -> list[Path]:
    node_dir = MARKDOWN_ROOT / "registration-of-documents" / "nodes"
    node_dir.mkdir(parents=True, exist_ok=True)
    selected: list[DigestEntry] = []
    for entry in entries:
        normalized = normalize_case_name(entry.case_name)
        if normalized in SAMPLE_CASE_TITLES and normalized not in {e.case_name for e in selected}:
            selected.append(entry)
        if len(selected) == 3:
            break

    paths: list[Path] = []
    for entry in selected:
        path = node_dir / f"{slugify(entry.case_name)}.md"
        path.write_text(build_case_node(entry), encoding="utf-8")
        paths.append(path)
    return paths


def build_case_node(entry: DigestEntry) -> str:
    return f"""---
node_id: case-law-{entry.row_id.lower()}
type: case-node
status: unverified
citation: "{entry.citation}"
case_name: "{entry.case_name}"
report_series: "{entry.report_series}"
report_year: "{entry.report_year}"
report_volume: "{entry.report_volume}"
page: "{entry.page}"
source_digest_row_id: "{entry.row_id}"
source_url: "{entry.source_url}"
statutes_cited:
  - {STATUTE_ID}-s{entry.section}
topics:
  - "{TOPIC_ID}"
catchwords:
  - registration of documents
  - conveyancing
---

# {entry.case_name}

## Pilot Status

This is a linked sample case node from the Registration of Documents related-case
digest. The citation is extracted from the digest, but the full judgment text has
not been verified from LawNet or the law-report PDF, so the node remains
`unverified`.

## Citation

{entry.citation}

## Links

- Digest row: `{entry.row_id}`
- Statute link candidate: `{STATUTE_ID}-s{entry.section}`
- Topic: `{TOPIC_ID}` case law on conveyancing
- Source digest: <{entry.source_url}>

## Headnote

Not extracted in this pilot. Add only after verifying the underlying law-report
text or an authorised headnote source.
"""


def write_readme(entries: list[DigestEntry], law_net_notes: list[str], node_paths: list[Path]) -> Path:
    path = MARKDOWN_ROOT / "case-law-pilot-README.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    unique = {(e.case_name, e.report_series, e.citation) for e in entries}
    sections = sorted({e.section for e in entries})
    garbled = [
        "LawNet HTTPS certificate verification failed for `lawnet.gov.lk` and `www.lawnet.gov.lk`.",
        "LawNet `/wp-content/uploads/` returned 404 when retried without TLS verification.",
        "The digest page says `Showing 1-25 of 25`, but the parsed table contains more row-level references because cases are repeated under multiple Registration of Documents sections.",
        "Some party-name casing/punctuation is inconsistent in the digest, for example `VS` versus `v.` and names ending in `et al.,`; those are preserved or lightly normalized, not silently corrected.",
    ]
    text = [
        "# Case-Law Pilot README",
        "",
        "## Source",
        "",
        f"- Parsed digest: <{LAWNET_FALLBACK_DIGEST_URL}>",
        "- Subject filter: `registration of documents`",
        "- Primary intended source: LawNet PDFs, but the pilot could not fetch them reliably.",
        "",
        "## Counts",
        "",
        f"- Digest row-level entries seen: {len(entries)}",
        f"- Unique case citations seen: {len(unique)}",
        f"- Entries matched by conveyancing filter: {len(entries)}",
        f"- Registration of Documents sections represented: {', '.join(sections)}",
        "",
        "## Outputs",
        "",
        f"- Citation CSV: `{CITATIONS_CSV.relative_to(ROOT).as_posix()}`",
    ]
    text.extend(
        f"- Sample node: `{node.relative_to(ROOT).as_posix()}`" for node in node_paths
    )
    text.extend(
        [
            "",
            "## LawNet Fetch Notes",
            "",
            LAWNET_SSL_NOTE,
            "",
        ]
    )
    text.extend(f"- {note}" for note in law_net_notes)
    text.extend(["", "## Garbled Or Uncertain Extraction", ""])
    text.extend(f"- {item}" for item in garbled)
    text.extend(
        [
            "",
            "## Verification Rule",
            "",
            "Every row is `unverified` until the underlying NLR/SLR report text is",
            "checked. Do not copy headnotes or legal propositions into public docs from",
            "this pilot alone.",
            "",
        ]
    )
    path.write_text("\n".join(text), encoding="utf-8")
    return path


def update_conversion_registry(paths: list[tuple[str, str, str, str]]) -> None:
    existing: list[dict[str, str]] = []
    if CONVERSION_REGISTRY.exists():
        with CONVERSION_REGISTRY.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            existing = list(reader)
    else:
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

    seen = {(row["source_id"], row["source_path"], row["markdown_path"]) for row in existing}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for source_id, source_type, source_path, markdown_path in paths:
        key = (source_id, source_path, markdown_path)
        if key in seen:
            continue
        existing.append(
            {
                "source_id": source_id,
                "source_type": source_type,
                "source_path": source_path,
                "markdown_path": markdown_path,
                "converter": "collect_case_law.py",
                "converter_version": "0.1",
                "ocr_enabled": "false",
                "language_hint": "eng",
                "status": "indexed-reference",
                "quality_notes": "Digest-derived pilot metadata; citations remain unverified until full report text is checked.",
                "converted_at": now,
            }
        )

    with CONVERSION_REGISTRY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run() -> None:
    law_net_notes = check_lawnet()
    html = fetch_text(LAWNET_FALLBACK_DIGEST_URL, verify_tls=True)
    entries = parse_digest(html)
    if not entries:
        raise SystemExit("No digest entries parsed; inspect the source page before proceeding.")

    html_path, notes_path = write_raw_digest(html, law_net_notes)
    write_csv(entries)
    node_paths = write_case_nodes(entries)
    readme_path = write_readme(entries, law_net_notes, node_paths)

    registry_paths = [
        (
            SOURCE_ID,
            "case-law-digest-html",
            html_path.relative_to(ROOT).as_posix(),
            notes_path.relative_to(ROOT).as_posix(),
        ),
        (
            SOURCE_ID,
            "case-law-citation-index",
            html_path.relative_to(ROOT).as_posix(),
            CITATIONS_CSV.relative_to(ROOT).as_posix(),
        ),
        (
            SOURCE_ID,
            "case-law-readme",
            html_path.relative_to(ROOT).as_posix(),
            readme_path.relative_to(ROOT).as_posix(),
        ),
    ]
    for node_path in node_paths:
        registry_paths.append(
            (
                SOURCE_ID,
                "case-law-node",
                CITATIONS_CSV.relative_to(ROOT).as_posix(),
                node_path.relative_to(ROOT).as_posix(),
            )
        )
    update_conversion_registry(registry_paths)

    unique_count = len({(e.case_name, e.report_series, e.citation) for e in entries})
    print(f"Digest entries seen: {len(entries)}")
    print(f"Unique case citations: {unique_count}")
    print(f"Conveyancing-filter matches: {len(entries)}")
    print(f"Citation CSV: {CITATIONS_CSV}")
    print(f"Sample nodes: {len(node_paths)}")
    print(f"Digest HTML sha256: {sha256(html_path)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
