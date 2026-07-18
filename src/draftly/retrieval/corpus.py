from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .models import SectionNode
from .paths import DOCS_CSV, SOURCE_REGISTRY_CSV, TOPIC_SOURCES_CSV, TOPICS_CSV
from .section_parser import parse_sections

ALLOWED_KINDS = {"statute", "amendment"}
EXPECTED_COUNTS = {"statute": 57, "amendment": 18}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_topic_maps() -> tuple[dict[str, dict[str, str]], dict[str, tuple[str, ...]]]:
    topic_rows = read_csv(TOPICS_CSV)
    topics_by_id = {
        row["topic_id"]: {"slug": row["slug"], "name": row["name"], "keywords": row.get("keywords", "")}
        for row in topic_rows
    }
    source_topics: dict[str, list[str]] = {}
    for row in read_csv(TOPIC_SOURCES_CSV):
        topic = topics_by_id.get(row["topic_id"])
        if topic:
            source_topics.setdefault(row["source_id"], []).append(topic["slug"])
    return topics_by_id, {source_id: tuple(slugs) for source_id, slugs in source_topics.items()}


def load_registry() -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in read_csv(SOURCE_REGISTRY_CSV)}


def load_statute_documents() -> list[dict[str, Any]]:
    rows = [row for row in read_csv(DOCS_CSV) if row.get("status") == "converted"]
    selected = [row for row in rows if row.get("kind") in ALLOWED_KINDS]
    counts = {kind: sum(1 for row in selected if row["kind"] == kind) for kind in ALLOWED_KINDS}
    if counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Expected {EXPECTED_COUNTS} statute/amendment corpus, found {counts}.")
    blocked = [row for row in selected if row["kind"] not in ALLOWED_KINDS or "case" in row["kind"]]
    if blocked:
        raise RuntimeError(f"Non-statutory documents reached statute retrieval corpus: {blocked[:3]}")
    return selected


def corpus_fingerprint(documents: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(documents, key=lambda item: item["source_id"]):
        path = Path(row["text_path"])
        digest.update(row["source_id"].encode("utf-8"))
        digest.update(row["kind"].encode("utf-8"))
        digest.update(row.get("sha256", "").encode("utf-8"))
        digest.update(str(path).encode("utf-8"))
    return digest.hexdigest()


def build_section_nodes() -> tuple[list[SectionNode], dict[str, Any]]:
    documents = load_statute_documents()
    registry = load_registry()
    _, source_topics = load_topic_maps()
    nodes: list[SectionNode] = []

    for row in documents:
        source_id = row["source_id"]
        metadata = registry.get(source_id, {})
        path = Path(row["text_path"])
        text = path.read_text(encoding="utf-8", errors="replace")
        topics = source_topics.get(source_id) or tuple(
            topic.strip() for topic in metadata.get("topics", "").split(";") if topic.strip()
        )
        nodes.extend(
            parse_sections(
                source_id=source_id,
                doc_id=row["doc_id"],
                kind=row["kind"],
                title=row["title"],
                act_number=metadata.get("act_or_ordinance_no", ""),
                year=row.get("year", ""),
                topics=topics,
                public_source_url=row.get("origin_url", "") or metadata.get("preferred_source_url", ""),
                source_sha256=row.get("sha256", ""),
                text=text,
            )
        )

    if any(node.kind not in ALLOWED_KINDS or "case" in node.kind for node in nodes):
        raise RuntimeError("Case-law or unsupported document type entered statute section index.")

    summary = {
        "documents": len(documents),
        "statutes": sum(1 for row in documents if row["kind"] == "statute"),
        "amendments": sum(1 for row in documents if row["kind"] == "amendment"),
        "sections": len(nodes),
        "fallbacks": sum(1 for node in nodes if node.extraction_confidence == "document_fallback"),
        "fingerprint": corpus_fingerprint(documents),
    }
    return nodes, summary


def topics_for_ui() -> list[dict[str, str]]:
    topics_by_id, _ = load_topic_maps()
    return [topics_by_id[key] | {"topic_id": key} for key in sorted(topics_by_id)]


def sources_for_ui() -> list[dict[str, str]]:
    registry = load_registry()
    documents = load_statute_documents()
    result = []
    for row in sorted(documents, key=lambda item: (item["title"], item["source_id"])):
        metadata = registry.get(row["source_id"], {})
        result.append(
            {
                "source_id": row["source_id"],
                "title": row["title"],
                "kind": row["kind"],
                "year": row.get("year", ""),
                "act_number": metadata.get("act_or_ordinance_no", ""),
            }
        )
    return result

