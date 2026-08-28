"""SQLite FTS5 BM25 index over the statute corpus, with act and section lookup.

Same technique as the koblex experiment's corpus_index.py -- an fts5 virtual
table with the unicode61 tokenizer, ranked by the built-in bm25() function --
duplicated here rather than imported for the same reason that one duplicates
src/draftly/retrieval/index.py: an experiment must not be able to perturb the
thing it is measured against. The koblex index database and its committed run
artifacts are left untouched.

What is new here is the hierarchy. The corpus already carries three levels --
act_id, the section_id rollup key, and node_id -- so this schema surfaces them
as columns and adds an ordinal for document order. That is what lets a BM25 hit
be expanded to its whole section subtree, which is the analog of HiREC's
page-level context.

search_text is the only indexed field. text is carried through untouched and is
what reaches the answering prompt as evidence.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

# Metadata carried through retrieval alongside the BM25 score. The koblex list
# plus section_id, node_type and parent_id: the curation prompt needs node_type
# to say what kind of provision it is looking at, and the sibling rule needs to
# know where a provision sits.
CARRIED_FIELDS = [
    "node_id", "citation", "act_id", "act_title", "provision_label",
    "heading", "text", "hierarchy", "section_id", "node_type", "parent_id",
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

# The second " | " segment of search_text is the Act's long title, except where
# that segment is already a provision heading (an Act with no long title).
_SECTION_HEAD_RE = re.compile(r"^(Section|Part|Schedule|Chapter)\b", re.I)


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
DROP TABLE IF EXISTS acts;
CREATE TABLE nodes (
    node_id TEXT PRIMARY KEY,
    act_id TEXT NOT NULL,
    section_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX nodes_section ON nodes(section_id, ordinal);
CREATE INDEX nodes_act ON nodes(act_id);
CREATE TABLE acts (
    act_id TEXT PRIMARY KEY,
    act_title TEXT,
    act_number INTEGER,
    act_year INTEGER,
    long_title TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    section_count INTEGER NOT NULL
);
CREATE VIRTUAL TABLE nodes_fts USING fts5(
    node_id UNINDEXED,
    search_text,
    tokenize = 'unicode61'
);
"""


def long_title_of(search_text: str) -> str:
    """The Act's long title, as carried in every record's search_text.

    It is the second " | " segment. Returns "" when that segment is a provision
    heading instead, which is how an Act with no long title presents.
    """
    parts = [p.strip() for p in (search_text or "").split(" | ")]
    if len(parts) < 2 or _SECTION_HEAD_RE.match(parts[1]):
        return ""
    return parts[1]


def _act_rows(records: Sequence[dict]) -> list[tuple]:
    """One row per Act, with the modal long title across its records."""
    titles: dict[str, Counter] = {}
    meta: dict[str, dict] = {}
    counts: dict[str, int] = {}
    sections: dict[str, set] = {}

    for record in records:
        act_id = record["act_id"]
        titles.setdefault(act_id, Counter())[long_title_of(record.get("search_text"))] += 1
        meta.setdefault(act_id, record)
        counts[act_id] = counts.get(act_id, 0) + 1
        sections.setdefault(act_id, set()).add(
            record.get("section_id") or record["node_id"])

    rows = []
    missing = []
    for act_id, counter in titles.items():
        # Ignore the empty string when a non-empty long title exists anywhere.
        non_empty = Counter({k: v for k, v in counter.items() if k})
        long_title = (non_empty or counter).most_common(1)[0][0]
        if not long_title:
            missing.append(act_id)
        rows.append((
            act_id,
            meta[act_id].get("act_title"),
            meta[act_id].get("act_number"),
            meta[act_id].get("act_year"),
            long_title,
            counts[act_id],
            len(sections[act_id]),
        ))

    if missing:
        raise ValueError(
            "no long title could be recovered for act(s): "
            f"{sorted(missing)}. The act-selection prompt is worthless without "
            "them, so this is a build failure rather than an empty string.")
    # Deliberately not a fixed count. The corpus gains statutes as sources are
    # ingested -- it went 18 -> 21 acts in a single day -- so asserting a magic
    # number here fails the build every time the data legitimately grows. What
    # must hold is that the acts table covers every act present in the records:
    # that catches an act silently dropped by this function, which is the actual
    # failure mode, without breaking on growth.
    distinct = {r["act_id"] for r in records}
    if len(rows) != len(distinct):
        raise ValueError(
            f"acts table has {len(rows)} rows but the corpus holds "
            f"{len(distinct)} distinct act_id values; "
            f"missing: {sorted(distinct - {r[0] for r in rows})}")
    return sorted(rows)


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
            "INSERT INTO nodes(node_id, act_id, section_id, ordinal, payload) "
            "VALUES (?, ?, ?, ?, ?)",
            [(r["node_id"],
              r["act_id"],
              # Four schedule records carry a null section_id. Coalescing to the
              # node's own id here means no null branch downstream: such a
              # record simply expands to itself.
              r.get("section_id") or r["node_id"],
              ordinal,
              json.dumps({k: r.get(k) for k in CARRIED_FIELDS}, ensure_ascii=False))
             for ordinal, r in enumerate(records)],
        )
        connection.executemany(
            "INSERT INTO acts(act_id, act_title, act_number, act_year, "
            "long_title, record_count, section_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
            _act_rows(records),
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
                f"{db_path} does not exist -- run hirec_build_index.py first")
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

    def acts(self) -> list[dict]:
        """Every Act, for the act-selection prompt. Ordered by act_id."""
        rows = self._connection.execute(
            "SELECT act_id, act_title, act_number, act_year, long_title, "
            "record_count, section_count FROM acts ORDER BY act_id").fetchall()
        return [
            {"act_id": r[0], "act_title": r[1], "act_number": r[2],
             "act_year": r[3], "long_title": r[4], "record_count": r[5],
             "section_count": r[6]}
            for r in rows
        ]

    def search(self, query_text: str, top_k: int,
               act_ids: Sequence[str] | None = None) -> list[dict]:
        """Top-k by BM25. Score is negated so that higher is better.

        act_ids scopes the search to those Acts. None or empty means unscoped --
        an empty IN () would silently return nothing, which is not what "no act
        filter" should mean.
        """
        expression = match_expression(query_text)
        if not expression:
            return []

        if act_ids:
            placeholders = ", ".join("?" for _ in act_ids)
            sql = (
                "SELECT f.node_id, bm25(nodes_fts) AS score "
                "FROM nodes_fts f JOIN nodes n ON n.node_id = f.node_id "
                f"WHERE nodes_fts MATCH ? AND n.act_id IN ({placeholders}) "
                "ORDER BY score, f.node_id LIMIT ?"
            )
            params = (expression, *act_ids, top_k)
        else:
            sql = (
                "SELECT node_id, bm25(nodes_fts) AS score "
                "FROM nodes_fts WHERE nodes_fts MATCH ? "
                "ORDER BY score, node_id LIMIT ?"
            )
            params = (expression, top_k)

        rows = self._connection.execute(sql, params).fetchall()

        results = []
        for rank, (node_id, score) in enumerate(rows, start=1):
            payload = self._payload(node_id)
            payload["bm25_score"] = -float(score)
            payload["rank"] = rank
            results.append(payload)
        return results

    # -- hierarchy ------------------------------------------------------ #

    def section_ids_for(self, node_ids: Sequence[str]) -> list[str]:
        """The sections the given nodes belong to, deduplicated, in first-seen
        order of the input."""
        if not node_ids:
            return []
        placeholders = ", ".join("?" for _ in node_ids)
        rows = self._connection.execute(
            f"SELECT node_id, section_id FROM nodes WHERE node_id IN ({placeholders})",
            tuple(node_ids),
        ).fetchall()
        lookup = dict(rows)
        ordered = [lookup[nid] for nid in node_ids if nid in lookup]
        return list(dict.fromkeys(ordered))

    def subtrees(self, section_ids: Sequence[str]) -> list[dict]:
        """Every record of every named section, in document order.

        One IN query rather than N round trips: a K=20 seed spans roughly 15
        sections.
        """
        if not section_ids:
            return []
        placeholders = ", ".join("?" for _ in section_ids)
        rows = self._connection.execute(
            f"SELECT payload, section_id, ordinal FROM nodes "
            f"WHERE section_id IN ({placeholders}) ORDER BY ordinal",
            tuple(section_ids),
        ).fetchall()
        records = []
        for payload, section_id, ordinal in rows:
            record = json.loads(payload)
            record["section_id"] = section_id
            record["ordinal"] = ordinal
            records.append(record)
        return records

    def _payload(self, node_id: str) -> dict:
        row = self._connection.execute(
            "SELECT payload, section_id, ordinal FROM nodes WHERE node_id = ?",
            (node_id,)).fetchone()
        if not row:
            return {"node_id": node_id}
        record = json.loads(row[0])
        record["section_id"] = row[1]
        record["ordinal"] = row[2]
        return record


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
