"""SQLite FTS5 BM25 index over the statute corpus.

Same technique as src/draftly/retrieval/index.py -- an fts5 virtual table with
the unicode61 tokenizer, ranked by the built-in bm25() function -- but over this
experiment's provision-level corpus and in its own database file, so it does not
touch the guarded corpus in src/draftly/retrieval/corpus.py.

search_text is the only indexed field. text is carried through untouched and is
what reaches the answering prompt as evidence.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Iterable, Sequence

# Metadata carried through retrieval alongside the BM25 score.
CARRIED_FIELDS = [
    "node_id", "citation", "act_id", "act_title", "provision_label",
    "heading", "text", "hierarchy",
]

# Closed-class English function words only. No legal vocabulary, no statute
# names, nothing numeric -- so section numbers, "notary", "registration",
# "lease", "proviso" and Act names all survive.
STOPWORDS = frozenset("""
a an and are as at be been being but by can did do does for from had has have
he her his how i if in into is it its me my nor not of on or our ours out over
she should so some such than that the their them then there these they this
those to too under until up upon was we were what when where which while who
whom why will with would you your
""".split())

TOKEN_RE = re.compile(r"[0-9a-z]+", re.I)


# --------------------------------------------------------------------------- #
# query construction
# --------------------------------------------------------------------------- #

def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", value).strip()


def question_query_text(background: str, question: str) -> str:
    """The retrieval text for a question: background and question together.

    Never the question alone -- the background carries the facts that make the
    relevant provisions findable.
    """
    return normalize_text(f"{background or ''} {question or ''}")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize_text(text).casefold())


def content_tokens(text: str) -> list[str]:
    """Tokens with function words dropped.

    A token is kept when it is not purely alphabetic (so '20c', '1998' and '21'
    survive) or when it is not a stopword. Falls back to the unfiltered tokens
    if filtering would leave nothing to match on.
    """
    tokens = tokenize(text)
    kept = [t for t in tokens if not t.isalpha() or t not in STOPWORDS]
    return kept or tokens


def match_expression(text: str) -> str:
    """An FTS5 MATCH expression: every token quoted, joined with OR.

    Quoting means punctuation in a generated query can never be parsed as FTS5
    syntax, so no query can raise.
    """
    tokens = content_tokens(text)
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in dict.fromkeys(tokens))


# --------------------------------------------------------------------------- #
# index build
# --------------------------------------------------------------------------- #

SCHEMA = """
DROP TABLE IF EXISTS nodes_fts;
DROP TABLE IF EXISTS nodes;
CREATE TABLE nodes (
    node_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL
);
CREATE VIRTUAL TABLE nodes_fts USING fts5(
    node_id UNINDEXED,
    search_text,
    tokenize = 'unicode61'
);
"""


def build_index(corpus_path: Path, db_path: Path) -> int:
    """Build the index once. Returns the number of indexed records."""
    records = []
    with corpus_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA)
        connection.executemany(
            "INSERT INTO nodes(node_id, payload) VALUES (?, ?)",
            [(r["node_id"],
              json.dumps({k: r.get(k) for k in CARRIED_FIELDS}, ensure_ascii=False))
             for r in records],
        )
        connection.executemany(
            "INSERT INTO nodes_fts(node_id, search_text) VALUES (?, ?)",
            [(r["node_id"], r.get("search_text") or "") for r in records],
        )
        connection.commit()
    finally:
        connection.close()
    return len(records)


# --------------------------------------------------------------------------- #
# search
# --------------------------------------------------------------------------- #

class Bm25Index:
    """Read-only handle on the built index, reused across all questions."""

    def __init__(self, db_path: Path):
        if not db_path.exists():
            raise FileNotFoundError(
                f"{db_path} does not exist -- run build_index.py first")
        self.db_path = db_path
        self._connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "Bm25Index":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def count(self) -> int:
        return self._connection.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    def node_ids(self) -> set[str]:
        rows = self._connection.execute("SELECT node_id FROM nodes").fetchall()
        return {row[0] for row in rows}

    def search(self, query_text: str, top_k: int) -> list[dict]:
        """Top-k by BM25. Score is negated so that higher is better."""
        expression = match_expression(query_text)
        if not expression:
            return []
        rows = self._connection.execute(
            """
            SELECT node_id, bm25(nodes_fts) AS score
            FROM nodes_fts
            WHERE nodes_fts MATCH ?
            ORDER BY score, node_id
            LIMIT ?
            """,
            (expression, top_k),
        ).fetchall()

        results = []
        for rank, (node_id, score) in enumerate(rows, start=1):
            payload = self._payload(node_id)
            payload["bm25_score"] = -float(score)
            payload["rank"] = rank
            results.append(payload)
        return results

    def _payload(self, node_id: str) -> dict:
        row = self._connection.execute(
            "SELECT payload FROM nodes WHERE node_id = ?", (node_id,)).fetchone()
        return json.loads(row[0]) if row else {"node_id": node_id}


# --------------------------------------------------------------------------- #
# merge
# --------------------------------------------------------------------------- #

def merge_candidates(
    result_sets: Sequence[tuple[str, Iterable[dict]]],
    max_candidates: int,
) -> list[dict]:
    """Merge per-query hit lists into one deduplicated ranked list.

    Ordered by the best rank a node achieved in any query, because ranks are
    comparable across queries while raw BM25 scores are not (each query has its
    own term set and length normalisation). Ties break on score then node_id, so
    the ordering is deterministic.
    """
    best: dict[str, dict] = {}
    for query_label, results in result_sets:
        for result in results:
            node_id = result["node_id"]
            existing = best.get(node_id)
            if existing is None:
                merged = dict(result)
                merged["found_by"] = [query_label]
                merged["best_rank"] = result["rank"]
                best[node_id] = merged
                continue
            existing["found_by"].append(query_label)
            existing["best_rank"] = min(existing["best_rank"], result["rank"])
            existing["bm25_score"] = max(existing["bm25_score"], result["bm25_score"])

    ordered = sorted(
        best.values(),
        key=lambda r: (r["best_rank"], -r["bm25_score"], r["node_id"]),
    )
    for position, record in enumerate(ordered, start=1):
        record["merged_rank"] = position
        record.pop("rank", None)
    return ordered[:max_candidates]
