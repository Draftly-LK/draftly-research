from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .corpus import build_case_documents, corpus_fingerprint, load_conveyancing_case_rows
from .models import CaseDoc, CaseIndexStats
from .paths import INDEX_DIR, INDEX_POINTER, fingerprinted_index_db


SCHEMA = """
DROP TABLE IF EXISTS metadata;
DROP TABLE IF EXISTS cases;
DROP TABLE IF EXISTS cases_fts;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE cases (
    case_id TEXT PRIMARY KEY,
    citation TEXT NOT NULL,
    title TEXT NOT NULL,
    court TEXT NOT NULL,
    year TEXT NOT NULL,
    url TEXT NOT NULL,
    body TEXT NOT NULL,
    rule_statement TEXT NOT NULL,
    text_sha256 TEXT NOT NULL,
    statute_links_json TEXT NOT NULL,
    topic_ids_json TEXT NOT NULL
);

CREATE VIRTUAL TABLE cases_fts USING fts5(
    title,
    body,
    rule_statement,
    case_id UNINDEXED,
    tokenize = 'unicode61'
);

CREATE INDEX idx_cases_court ON cases(court);
"""


def build_index(force: bool = False) -> CaseIndexStats:
    rows = load_conveyancing_case_rows()
    fingerprint = corpus_fingerprint(rows)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with index_build_lock():
        index_db = read_active_index(fingerprint)
        if index_db is not None and not force:
            existing = read_metadata("fingerprint", index_db)
            if existing == fingerprint:
                return CaseIndexStats(
                    db_path=str(index_db),
                    fingerprint=fingerprint,
                    cases=count_cases(index_db),
                    reused=True,
                )

        docs, summary = build_case_documents(rows)
        index_db = fingerprinted_index_db(fingerprint, uuid.uuid4().hex[:8])
        temporary_db = INDEX_DIR / f"cases.{os.getpid()}.{uuid.uuid4().hex}.sqlite"
        try:
            write_index_database(temporary_db, docs, summary)
            replace_index(temporary_db, index_db)
            write_active_index(fingerprint, index_db)
        finally:
            try:
                temporary_db.unlink(missing_ok=True)
            except PermissionError:
                pass

    return CaseIndexStats(
        db_path=str(index_db),
        fingerprint=fingerprint,
        cases=summary["cases"],
        reused=False,
    )


def write_index_database(path: Path, docs: list[CaseDoc], summary: dict) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        for key, value in summary.items():
            conn.execute("INSERT INTO metadata(key, value) VALUES (?, ?)", (key, json.dumps(value)))
        conn.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)", ("version", json.dumps("cases-conveyancing-bm25-v1"))
        )
        for doc in docs:
            conn.execute(
                """
                INSERT INTO cases (
                    case_id, citation, title, court, year, url, body, rule_statement,
                    text_sha256, statute_links_json, topic_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.case_id,
                    doc.citation,
                    doc.title,
                    doc.court,
                    doc.year,
                    doc.url,
                    doc.text,
                    doc.rule_statement,
                    doc.text_sha256,
                    json.dumps(list(doc.statute_links)),
                    json.dumps(list(doc.topic_ids)),
                ),
            )
            conn.execute(
                "INSERT INTO cases_fts(title, body, rule_statement, case_id) VALUES (?, ?, ?, ?)",
                (doc.title, doc.text, doc.rule_statement, doc.case_id),
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
                        raise TimeoutError("Timed out waiting for the case index build lock.")
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
    rows = load_conveyancing_case_rows()
    fingerprint = corpus_fingerprint(rows)
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


def count_cases(index_db: Path) -> int:
    with sqlite3.connect(index_db) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0])
