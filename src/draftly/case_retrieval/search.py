"""Similar-case retrieval: lexical + dense + statute/topic-graph channels,
fused with reciprocal-rank fusion (RRF), same shape as
`draftly.retrieval.search.fuse_rankings`.

Abstention ("no similar cases") is deliberately not a bare score threshold.
Dense cosine similarity alone is easy to fool with generic legal boilerplate
("the plaintiff", "the District Court held"), so a hit is only returned if it
is corroborated by at least one of the lexical or graph (statute/topic
bridge) channels — dense similarity is additive evidence, never sufficient by
itself. See `scripts/similar-case-retrieval/RESULTS.md` for the calibration
notes and the honest caveat that this is a heuristic, not a proven cutoff.

Architecture toggle: `DRAFTLY_CASE_LEXICAL_IDF=1` replaces the flat
`MIN_LEXICAL_OVERLAP` token-count gate with a rarity-weighted one. A token
that appears in more than `MAX_DOCUMENT_FREQUENCY_RATIO` of the corpus (a
generic word like "will" or "land", or an institutional phrase fragment
like "commissioner") no longer counts toward lexical corroboration --
only genuinely rare, doctrine-specific overlap does. See
`scripts/similar-case-retrieval/RESULTS.md`'s architecture comparison for
the measured effect versus the flat count.
"""

from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import replace
from functools import lru_cache

from . import embeddings, graph
from .index import build_index, connect
from .models import CaseHit, CaseQuery, SimilarCaseResult

RRF_K = 60
LEXICAL_WEIGHT = 1.0
DENSE_WEIGHT = 0.8
GRAPH_WEIGHT = 0.7
CORROBORATED_CHANNELS = {"lexical", "graph"}

STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "to", "and", "or", "is", "was", "for",
    "by", "with", "at", "as", "his", "her", "its", "their", "he", "she", "it",
    "they", "be", "been", "that", "this", "these", "those", "shall", "may",
}


def find_similar(query: CaseQuery | str) -> SimilarCaseResult:
    if isinstance(query, str):
        query = CaseQuery(text=query)
    stats = build_index(force=False)

    with connect() as conn:
        lexical_hits = lexical_lookup(conn, query.text, limit=query.limit * 3)

        dense_pairs = embeddings.dense_lookup(query.text, limit=query.limit * 3)
        dense_hits = hits_for_ids(conn, [case_id for case_id, _ in dense_pairs], query_text=query.text)

        seeds: dict[str, float] = dict(graph.seeds_from_statute_mentions(conn, query.text))
        for rank, hit in enumerate(lexical_hits[:5], start=1):
            seeds[hit.case_id] = max(seeds.get(hit.case_id, 0.0), 1.0 / rank)
        expansion = graph.expand_seeds(seeds, top_n=query.limit * 2)
        graph_hits = hits_for_ids(conn, [case_id for case_id, _ in expansion], query_text=query.text)

        fused = fuse_rankings(
            [
                ("lexical", lexical_hits, LEXICAL_WEIGHT),
                ("dense", dense_hits, DENSE_WEIGHT),
                ("graph", graph_hits, GRAPH_WEIGHT),
            ],
            limit=query.limit * 2,
        )

    corroborated = [hit for hit in fused if set(hit.matched_signals) & CORROBORATED_CHANNELS]
    if not corroborated:
        reason = (
            "No case in the conveyancing corpus shares a statute citation, topic, "
            "or meaningful text overlap with this fact pattern."
            if not fused
            else "Only weak, uncorroborated (dense-only) similarity was found; "
            "no case shares a statute citation, topic, or lexical overlap with this fact pattern."
        )
        return SimilarCaseResult(query=query.text, hits=(), outcome="no_similar_cases", reason=reason, corpus_fingerprint=stats.fingerprint)

    return SimilarCaseResult(
        query=query.text,
        hits=tuple(corroborated[: query.limit]),
        outcome="similar_cases_found",
        corpus_fingerprint=stats.fingerprint,
    )


def fuse_rankings(
    ranked_lists: list[tuple[str, list[CaseHit], float]],
    *,
    limit: int,
) -> list[CaseHit]:
    scores: dict[str, float] = {}
    hits_by_id: dict[str, CaseHit] = {}
    matched: dict[str, list[str]] = {}
    for channel, hits, weight in ranked_lists:
        for rank, hit in enumerate(hits, start=1):
            score = weight / (RRF_K + rank)
            scores[hit.case_id] = scores.get(hit.case_id, 0.0) + score
            hits_by_id.setdefault(hit.case_id, hit)
            matched.setdefault(hit.case_id, []).append(channel)

    ordered = sorted(scores, key=lambda case_id: (-scores[case_id], case_id))
    result: list[CaseHit] = []
    for case_id in ordered:
        hit = hits_by_id[case_id]
        result.append(
            replace(
                hit,
                score=round(scores[case_id], 6),
                matched_signals=tuple(dict.fromkeys(matched[case_id])),
            )
        )
        if len(result) >= limit:
            break
    return result


def hits_for_ids(conn: sqlite3.Connection, case_ids: list[str], *, query_text: str = "") -> list[CaseHit]:
    if not case_ids:
        return []
    placeholders = ",".join("?" for _ in case_ids)
    rows = {
        row["case_id"]: row
        for row in conn.execute(f"SELECT * FROM cases WHERE case_id IN ({placeholders})", case_ids)
    }
    hits = []
    for case_id in case_ids:
        row = rows.get(case_id)
        if row is not None:
            hits.append(row_to_hit(row, score=0.0, query_text=query_text))
    return hits


MIN_LEXICAL_OVERLAP = 3  # two coincidental token matches (e.g. "quantum" and
# "computing" both appearing, in unrelated senses, in a land-acquisition
# case about "computing the quantum of compensation") must not count as
# corroboration on their own — see RESULTS.md for the calibration note.

MAX_DOCUMENT_FREQUENCY_RATIO = 0.05  # DRAFTLY_CASE_LEXICAL_IDF only: a token
# appearing in more than this share of the corpus doesn't count as rare
# enough to corroborate on its own. Empirically, institutional/generic terms
# like "divisional"/"secretary"/"development" sit at 6-9% document frequency
# individually — above 0.12 they still passed and let administrative writs
# through on an LDO query; 0.05 was the value that actually excluded them in
# manual probing before the formal architecture comparison in RESULTS.md.


def _idf_enabled() -> bool:
    return os.getenv("DRAFTLY_CASE_LEXICAL_IDF", "").strip().lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def _total_case_count() -> int:
    with connect() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0])


@lru_cache(maxsize=4096)
def _document_frequency(token: str) -> int:
    with connect() as conn:
        try:
            return int(
                conn.execute("SELECT COUNT(*) FROM cases_fts WHERE cases_fts MATCH ?", (f'"{token}"',)).fetchone()[0]
            )
        except sqlite3.OperationalError:
            return 0


def _rare_tokens(tokens: list[str]) -> list[str]:
    """Tokens whose corpus document frequency is below MAX_DOCUMENT_FREQUENCY_RATIO."""
    total = _total_case_count() or 1
    return [token for token in tokens if _document_frequency(token) / total <= MAX_DOCUMENT_FREQUENCY_RATIO]


def lexical_lookup(conn: sqlite3.Connection, query_text: str, *, limit: int) -> list[CaseHit]:
    tokens = query_tokens(query_text)
    fts_query = make_fts_query(tokens)
    if not fts_query:
        return []
    try:
        rows = conn.execute(
            """
            SELECT cases.*, bm25(cases_fts) AS rank
            FROM cases_fts
            JOIN cases ON cases.case_id = cases_fts.case_id
            WHERE cases_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, limit * 3),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    corroboration_tokens = _rare_tokens(tokens) if _idf_enabled() else tokens
    min_overlap = min(MIN_LEXICAL_OVERLAP, len(corroboration_tokens)) if corroboration_tokens else MIN_LEXICAL_OVERLAP
    hits = []
    for row in rows:
        haystack = f"{row['title']} {row['body']} {row['rule_statement']}".lower()
        overlap = sum(1 for token in corroboration_tokens if token in haystack)
        if overlap >= min_overlap:
            hits.append(row_to_hit(row, score=-float(row["rank"]), query_text=query_text))
        if len(hits) >= limit:
            break
    return hits


def query_tokens(text: str) -> list[str]:
    tokens = [token for token in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower()) if token not in STOPWORDS]
    return list(dict.fromkeys(tokens))


def make_fts_query(tokens: list[str]) -> str:
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in tokens[:40])


BOILERPLATE_MARKER = "Database Search | Name Search | Recent Decisions | Noteup | LawCite | Help"


def row_to_hit(row: sqlite3.Row, *, score: float, query_text: str = "") -> CaseHit:
    return CaseHit(
        case_id=row["case_id"],
        citation=row["citation"],
        title=row["title"],
        court=row["court"],
        year=row["year"],
        url=row["url"],
        excerpt=make_excerpt(row["body"], query_text),
        score=score,
    )


def make_excerpt(text: str, query_text: str, radius: int = 450) -> str:
    """Boilerplate-skipping, query-anchored excerpt.

    Every CommonLII page repeats the same nav header before the judgment
    body starts, so a plain head-of-text slice is useless as evidence — this
    finds the real body, then centers on the best query-token match in it.
    """
    marker_index = text.find(BOILERPLATE_MARKER)
    body = text[marker_index + len(BOILERPLATE_MARKER) :].strip() if marker_index != -1 else text.strip()
    if not body:
        return ""

    tokens = query_tokens(query_text)
    best_index = -1
    lowered = body.lower()
    for token in tokens:
        found = lowered.find(token)
        if found != -1 and (best_index == -1 or found < best_index):
            best_index = found

    if best_index == -1:
        return (body[:radius] + "…") if len(body) > radius else body
    start = max(0, best_index - radius // 2)
    end = min(len(body), start + radius)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(body) else ""
    return prefix + body[start:end].strip() + suffix
