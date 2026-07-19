"""Dense retrieval channel: Gemini embeddings over section nodes, cached.

Hybrid BM25 + embedding retrieval fused with RRF is the uncontroversial modern
baseline (see papers/qa-agent/notes-*.md); the lexical channel misses paraphrase
("sign abroad" vs "outside Sri Lanka", "reserve fund" vs "sinking fund"), which
exam questions exploit constantly.

Design constraints honoured:
- Vectors are cached in a SQLite file keyed by the corpus fingerprint, so the
  corpus is embedded once (~3.5K sections) and reused until the corpus changes.
- Everything degrades gracefully: no GEMINI_API_KEY, no network, or a failed
  build -> empty results, and search() silently stays lexical-only.
- No new index formats: numpy float32 blobs in SQLite, loaded once per process.
"""

from __future__ import annotations

import os
import sqlite3
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

from .index import build_index, connect
from .paths import INDEX_DIR

EMBEDDING_MODEL = os.getenv("DRAFTLY_EMBEDDING_MODEL", "gemini-embedding-001")
EMBED_DIM = 768  # requested via output_dimensionality; keeps the cache small
BATCH_SIZE = 64
MAX_SECTION_CHARS = 1800
EMBED_DB = INDEX_DIR / "section-embeddings.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS embeddings (
    fingerprint TEXT NOT NULL,
    section_id TEXT NOT NULL,
    vector BLOB NOT NULL,
    PRIMARY KEY (fingerprint, section_id)
);
"""


def _client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai

        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _embed_batch(client, texts: list[str], *, task_type: str) -> list[np.ndarray] | None:
    from google.genai import types

    for attempt in range(4):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBED_DIM,
                ),
            )
            vectors = [np.asarray(item.values, dtype=np.float32) for item in response.embeddings]
            return [vector / (np.linalg.norm(vector) or 1.0) for vector in vectors]
        except Exception:
            if attempt == 3:
                return None
            time.sleep(2**attempt)
    return None


def _section_chunks(row: sqlite3.Row) -> list[tuple[str, str]]:
    """(vector_key, text) pairs. Oversized OCR blobs (several real sections fused
    into one node) are embedded in overlapping chunks so deep content stays
    visible to the dense channel; vector keys get a '#k' suffix that
    dense_lookup() strips back to the parent section_id."""
    header = f"{row['title']} — {row['heading']}\n"
    body = row["body"]
    if len(body) <= MAX_SECTION_CHARS:
        return [(row["section_id"], header + body)]
    chunks: list[tuple[str, str]] = []
    step = MAX_SECTION_CHARS - 300  # 300-char overlap
    for index, start in enumerate(range(0, len(body), step)):
        piece = body[start : start + MAX_SECTION_CHARS]
        if len(piece) < 200 and chunks:
            break
        chunks.append((f"{row['section_id']}#{index}", header + piece))
        if index >= 15:  # cap pathological blobs
            break
    return chunks


def build_embeddings(force: bool = False) -> int:
    """Embed every section for the active corpus fingerprint. Returns count (0 = unavailable)."""
    stats = build_index(force=False)
    client = _client()
    if client is None:
        return 0

    EMBED_DB.parent.mkdir(parents=True, exist_ok=True)
    store = sqlite3.connect(EMBED_DB)
    try:
        store.executescript(_SCHEMA)
        if force:
            store.execute("DELETE FROM embeddings WHERE fingerprint = ?", (stats.fingerprint,))
            store.commit()
        have = {
            row[0]
            for row in store.execute(
                "SELECT section_id FROM embeddings WHERE fingerprint = ?", (stats.fingerprint,)
            )
        }
        pending: list[tuple[str, str]] = []
        with connect() as conn:
            for row in conn.execute(
                "SELECT section_id, title, heading, body FROM sections ORDER BY section_id"
            ):
                for key, text in _section_chunks(row):
                    if key not in have:
                        pending.append((key, text))
        for start in range(0, len(pending), BATCH_SIZE):
            batch = pending[start : start + BATCH_SIZE]
            vectors = _embed_batch(
                client, [text for _, text in batch], task_type="RETRIEVAL_DOCUMENT"
            )
            if vectors is None:
                break
            store.executemany(
                "INSERT OR REPLACE INTO embeddings (fingerprint, section_id, vector) VALUES (?, ?, ?)",
                [
                    (stats.fingerprint, key, vector.tobytes())
                    for (key, _), vector in zip(batch, vectors)
                ],
            )
            store.commit()
        total = store.execute(
            "SELECT COUNT(*) FROM embeddings WHERE fingerprint = ?", (stats.fingerprint,)
        ).fetchone()[0]
        return int(total)
    finally:
        store.close()


@lru_cache(maxsize=1)
def _load_matrix(fingerprint: str) -> tuple[list[str], np.ndarray] | None:
    if not EMBED_DB.exists():
        return None
    store = sqlite3.connect(EMBED_DB)
    try:
        rows = store.execute(
            "SELECT section_id, vector FROM embeddings WHERE fingerprint = ? ORDER BY section_id",
            (fingerprint,),
        ).fetchall()
    finally:
        store.close()
    if not rows:
        return None
    ids = [row[0] for row in rows]
    matrix = np.vstack([np.frombuffer(row[1], dtype=np.float32) for row in rows])
    return ids, matrix


def dense_lookup(query_text: str, *, limit: int = 12) -> list[tuple[str, float]]:
    """Cosine top-k section IDs for a query. Empty when the channel is unavailable."""
    stats = build_index(force=False)
    loaded = _load_matrix(stats.fingerprint)
    if loaded is None:
        return []
    client = _client()
    if client is None:
        return []
    vectors = _embed_batch(client, [query_text[:2000]], task_type="RETRIEVAL_QUERY")
    if not vectors:
        return []
    ids, matrix = loaded
    scores = matrix @ vectors[0]
    order = np.argsort(-scores)[: limit * 3]
    best: dict[str, float] = {}
    for i in order:
        if scores[i] <= 0.05:
            break
        section_id = ids[i].split("#", 1)[0]  # chunk vectors map back to their section
        if section_id not in best:
            best[section_id] = float(scores[i])
        if len(best) >= limit:
            break
    return sorted(best.items(), key=lambda item: -item[1])


def embedding_status() -> dict[str, object]:
    stats = build_index(force=False)
    loaded = _load_matrix(stats.fingerprint)
    return {
        "model": EMBEDDING_MODEL,
        "cache": str(EMBED_DB),
        "sections_embedded": 0 if loaded is None else len(loaded[0]),
        "available": loaded is not None and _client() is not None,
    }
