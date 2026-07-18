from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .corpus import build_section_nodes, corpus_fingerprint, load_statute_documents
from .models import IndexStats
from .paths import INDEX_DIR, INDEX_POINTER, fingerprinted_index_db


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
    source_sha256 TEXT NOT NULL,
    metadata_json TEXT NOT NULL
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
    documents = load_statute_documents()
    fingerprint = corpus_fingerprint(documents)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with index_build_lock():
        index_db = read_active_index(fingerprint)
        if index_db is not None and not force:
            existing = read_metadata("fingerprint", index_db)
            if existing == fingerprint:
                return IndexStats(
                    db_path=str(index_db),
                    fingerprint=fingerprint,
                    documents=len(documents),
                    statutes=sum(1 for row in documents if row["kind"] == "statute"),
                    amendments=sum(1 for row in documents if row["kind"] == "amendment"),
                    sections=count_sections(index_db),
                    fallbacks=count_fallbacks(index_db),
                    reused=True,
                )

        nodes, summary = build_section_nodes(documents)
        index_db = fingerprinted_index_db(fingerprint, uuid.uuid4().hex[:8])
        temporary_db = INDEX_DIR / f"statutes.{os.getpid()}.{uuid.uuid4().hex}.sqlite"
        try:
            write_index_database(temporary_db, nodes, summary)
            replace_index(temporary_db, index_db)
            write_active_index(fingerprint, index_db)
        finally:
            try:
                temporary_db.unlink(missing_ok=True)
            except PermissionError:
                # Windows can retain a short-lived SQLite handle after a failed swap.
                pass

    return IndexStats(
        db_path=str(index_db),
        fingerprint=fingerprint,
        documents=summary["documents"],
        statutes=summary["statutes"],
        amendments=summary["amendments"],
        sections=summary["sections"],
        fallbacks=summary["fallbacks"],
        reused=False,
    )


def write_index_database(path: Path, nodes, summary: dict) -> None:
    conn = sqlite3.connect(path)
    try:
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
                    extraction_confidence, source_sha256, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(node.metadata, ensure_ascii=False),
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
    finally:
        conn.close()


def replace_index(temporary_db: Path, index_db: Path) -> None:
    deadline = time.monotonic() + 15
    while True:
        try:
            os.replace(temporary_db, index_db)
            return
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.1)


@contextmanager
def index_build_lock():
    lock_path = INDEX_DIR / "build.lock"
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"0")
            lock_file.flush()
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt

            deadline = time.monotonic() + 30
            while True:
                lock_file.seek(0)
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Timed out waiting for the statute index build lock.")
                    time.sleep(0.1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:  # pragma: no cover - Windows is the primary local target.
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def connect() -> sqlite3.Connection:
    documents = load_statute_documents()
    fingerprint = corpus_fingerprint(documents)
    index_db = read_active_index(fingerprint)
    if index_db is None:
        stats = build_index(force=False)
        index_db = Path(stats.db_path)
    conn = sqlite3.connect(index_db)
    conn.row_factory = sqlite3.Row
    return conn


def read_active_index(fingerprint: str) -> Path | None:
    if not INDEX_POINTER.exists():
        return None
    try:
        payload = json.loads(INDEX_POINTER.read_text(encoding="utf-8"))
        candidate = INDEX_DIR / Path(str(payload["filename"])).name
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if payload.get("fingerprint") != fingerprint or not candidate.exists():
        return None
    return candidate


def write_active_index(fingerprint: str, index_db: Path) -> None:
    temporary_pointer = INDEX_DIR / f"active.{os.getpid()}.{uuid.uuid4().hex}.json"
    temporary_pointer.write_text(
        json.dumps({"fingerprint": fingerprint, "filename": index_db.name}, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_pointer, INDEX_POINTER)


def read_metadata(key: str, index_db: Path) -> str | None:
    if not index_db.exists():
        return None
    try:
        with sqlite3.connect(index_db) as conn:
            row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    except sqlite3.OperationalError:
        return None
    return json.loads(row[0]) if row else None


def count_sections(index_db: Path) -> int:
    with sqlite3.connect(index_db) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0])


def count_fallbacks(index_db: Path) -> int:
    with sqlite3.connect(index_db) as conn:
        return int(
            conn.execute("SELECT COUNT(*) FROM sections WHERE extraction_confidence = 'document_fallback'").fetchone()[0]
        )
