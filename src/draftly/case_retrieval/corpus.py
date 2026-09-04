"""Conveyancing-scoped case corpus loader.

Population is fixed by an existing, already-computed gate: `conveyancing_match`
in `data/processed/cases.jsonl` (5,121 of 9,177 cases, produced by
`scripts/classify_commonlii_convayancing_improved.py` and predecessors). This
module does not re-derive or widen that population — it only reads the flag.

Case-to-case bridges are built from two existing, already-graded link tables:
`resolved_links.csv` (case -> statute/section, with a quality `band`) and
`case_topic_links.csv` (case -> curriculum topic). Rule statements from
`rules_high_confidence.csv` are an optional text enrichment, not a
requirement — a case with no extracted rule still indexes on its raw text.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .models import CaseDoc
from .paths import CASE_TOPIC_LINKS_CSV, CASES_JSONL, REPO_ROOT, RESOLVED_LINKS_CSV, RULES_CSV

INDEX_INPUT_VERSION = "cases-conveyancing-v1"


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_conveyancing_case_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with CASES_JSONL.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("conveyancing_match") is True:
                rows.append(row)
    if not rows:
        raise RuntimeError(f"No conveyancing_match=true rows found in {CASES_JSONL}.")
    blocked = [row for row in rows if row.get("conveyancing_match") is not True]
    if blocked:
        raise RuntimeError(f"Non-conveyancing case reached the conveyancing case corpus: {blocked[:3]}")
    return rows


def load_statute_bridge() -> dict[str, list[tuple[str, str, str]]]:
    """case_id -> [(source_id, section_number, band), ...] from resolved_links.csv."""
    bridge: dict[str, list[tuple[str, str, str]]] = {}
    for row in read_csv(RESOLVED_LINKS_CSV):
        source_id = (row.get("source_id") or "").strip()
        if not source_id:
            continue
        case_id = row["case_id"]
        entry = (source_id, (row.get("section_number") or "").strip(), row.get("band") or "unresolved")
        bridge.setdefault(case_id, []).append(entry)
    return bridge


def load_topic_bridge() -> dict[str, list[str]]:
    bridge: dict[str, list[str]] = {}
    for row in read_csv(CASE_TOPIC_LINKS_CSV):
        bridge.setdefault(row["case_id"], []).append(row["topic_id"])
    return bridge


def load_rule_statements() -> dict[str, str]:
    statements: dict[str, str] = {}
    for row in read_csv(RULES_CSV):
        case_id = row.get("case_id")
        statement = (row.get("statement") or "").strip()
        if case_id and statement and case_id not in statements:
            statements[case_id] = statement
    return statements


def corpus_fingerprint(rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(INDEX_INPUT_VERSION.encode("utf-8"))
    for metadata_path in (RESOLVED_LINKS_CSV, CASE_TOPIC_LINKS_CSV, RULES_CSV):
        if metadata_path.exists():
            digest.update(metadata_path.read_bytes())
    for row in sorted(rows, key=lambda item: item["case_id"]):
        path = resolve_repo_path(row["text_path"])
        digest.update(row["case_id"].encode("utf-8"))
        digest.update(str(path).encode("utf-8"))
        stat = path.stat()
        digest.update(f"{stat.st_size}:{stat.st_mtime_ns}".encode("ascii"))
    return digest.hexdigest()


def build_case_documents(rows: list[dict[str, Any]] | None = None) -> tuple[list[CaseDoc], dict[str, Any]]:
    rows = rows or load_conveyancing_case_rows()
    statute_bridge = load_statute_bridge()
    topic_bridge = load_topic_bridge()
    rule_statements = load_rule_statements()

    docs: list[CaseDoc] = []
    missing_text = 0
    for row in rows:
        case_id = row["case_id"]
        path = resolve_repo_path(row["text_path"])
        if not path.exists():
            missing_text += 1
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        docs.append(
            CaseDoc(
                case_id=case_id,
                citation=row.get("citation") or "",
                title=row.get("title") or "",
                court=row.get("court") or "",
                year=str(row.get("year") or ""),
                url=row.get("url") or "",
                text=text,
                text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                rule_statement=rule_statements.get(case_id, ""),
                statute_links=tuple(statute_bridge.get(case_id, [])),
                topic_ids=tuple(topic_bridge.get(case_id, [])),
            )
        )

    summary = {
        "cases": len(docs),
        "cases_missing_text": missing_text,
        "fingerprint": corpus_fingerprint(rows),
    }
    return docs, summary
