from __future__ import annotations

import json
import sqlite3

from .corpus import build_section_nodes
from .models import IndexStats
from .paths import INDEX_DB, INDEX_DIR


SCHEMA = """
DROP TABLE IF EXISTS metadata;
DROP TABLE IF EXISTS sections;
DROP TABLE IF EXISTS sections_fts;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('statute', 'amendment')),
    title TEXT NOT NULL,
    act_number TEXT NOT NULL,
    year TEXT NOT NULL,
    topics_json TEXT NOT NULL,
    topic_slugs TEXT NOT NULL,
    heading TEXT NOT NULL,
    body TEXT NOT NULL,
    public_source_url TEXT NOT NULL,
    extraction_confidence TEXT NOT NULL,
    source_sha256 TEXT NOT NULL
);

CREATE VIRTUAL TABLE sections_fts USING fts5(
    title,
    heading,
    body,
    section_id UNINDEXED,
    source_id UNINDEXED,
    tokenize = 'unicode61'
);

CREATE INDEX idx_sections_source ON sections(source_id);
CREATE INDEX idx_sections_kind ON sections(kind);
CREATE INDEX idx_sections_topic_slugs ON sections(topic_slugs);
"""


def build_index(force: bool = False) -> IndexStats:
    nodes, summary = build_section_nodes()
    fingerprint = summary["fingerprint"]

    if INDEX_DB.exists() and not force:
        existing = read_metadata("fingerprint")
        if existing == fingerprint:
            return IndexStats(
                db_path=str(INDEX_DB),
                fingerprint=fingerprint,
                documents=summary["documents"],
                statutes=summary["statutes"],
                amendments=summary["amendments"],
                sections=count_sections(),
                fallbacks=count_fallbacks(),
                reused=True,
            )

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(INDEX_DB) as conn:
        conn.executescript(SCHEMA)
        for key, value in summary.items():
            conn.execute("INSERT INTO metadata(key, value) VALUES (?, ?)", (key, json.dumps(value)))
        conn.execute("INSERT INTO metadata(key, value) VALUES (?, ?)", ("version", json.dumps("statutes-bm25-v1")))
        for node in nodes:
            topics_json = json.dumps(list(node.topics), ensure_ascii=False)
            topic_slugs = ";" + ";".join(node.topics) + ";"
            conn.execute(
                """
                INSERT INTO sections (
                    section_id, source_id, doc_id, kind, title, act_number, year,
                    topics_json, topic_slugs, heading, body, public_source_url,
                    extraction_confidence, source_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node.section_id,
                    node.source_id,
                    node.doc_id,
                    node.kind,
                    node.title,
                    node.act_number,
                    node.year,
                    topics_json,
                    topic_slugs,
                    node.heading,
                    node.text,
                    node.public_source_url,
                    node.extraction_confidence,
                    node.source_sha256,
                ),
            )
            conn.execute(
                """
                INSERT INTO sections_fts(title, heading, body, section_id, source_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (node.title, node.heading, node.text, node.section_id, node.source_id),
            )
        conn.commit()

    return IndexStats(
        db_path=str(INDEX_DB),
        fingerprint=fingerprint,
        documents=summary["documents"],
        statutes=summary["statutes"],
        amendments=summary["amendments"],
        sections=summary["sections"],
        fallbacks=summary["fallbacks"],
        reused=False,
    )


def connect() -> sqlite3.Connection:
    if not INDEX_DB.exists():
        build_index(force=False)
    conn = sqlite3.connect(INDEX_DB)
    conn.row_factory = sqlite3.Row
    return conn


def read_metadata(key: str) -> str | None:
    if not INDEX_DB.exists():
        return None
    with sqlite3.connect(INDEX_DB) as conn:
        row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    return json.loads(row[0]) if row else None


def count_sections() -> int:
    with sqlite3.connect(INDEX_DB) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0])


def count_fallbacks() -> int:
    with sqlite3.connect(INDEX_DB) as conn:
        return int(
            conn.execute("SELECT COUNT(*) FROM sections WHERE extraction_confidence = 'document_fallback'").fetchone()[0]
        )

