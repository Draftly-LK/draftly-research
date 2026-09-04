"""Case-to-case bridge graph, built through the statute/topic links that
already exist for this corpus — the "statute -> case -> case" link the
feature is asked to consider, as distinct from raw text similarity.

Two cases become graph-adjacent when:
  statute_link   they cite the same (source_id, section_number) per
                 resolved_links.csv, weighted by the weaker of the two
                 rows' quality `band` (verified > review > unresolved).
  topic_link     they share a curriculum topic_id per case_topic_links.csv
                 (weak edge — topics are broad).

A query has no pre-existing links of its own, so `seeds_from_statute_mentions`
detects statute names/citations mentioned directly in the query text (against
the closed statute catalogue used by the linking pipeline) and seeds the graph
walk from every case already linked to that statute. This is the mechanism
that lets a fact pattern naming "the Partition Act" or "the Prescription
Ordinance" reach precedent cases even when no word in the judgment matches
the query lexically.

Architecture toggle: `DRAFTLY_CASE_GRAPH_VERIFIED_ONLY=1` restricts the
graph to the parts of the case<->case link data that are actually verified.
`case_topic_links.csv` is 10,527 rows and every single one is
`review_status="candidate"` -- there is no verified topic link at all -- so
under this toggle the topic bridge is dropped entirely, and the statute
bridge keeps only `resolved_links.csv` rows with `band == "verified"` (462
of 523 source_id-bearing rows). See RESULTS.md's architecture comparison
for the measured effect.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from functools import lru_cache

from .index import build_index, connect
from .paths import REPO_ROOT


def _verified_only() -> bool:
    return os.getenv("DRAFTLY_CASE_GRAPH_VERIFIED_ONLY", "").strip().lower() in {"1", "true", "yes"}

STATUTE_INDEX_CSV = REPO_ROOT / "scripts" / "case-law-statute-linking" / "output" / "statute_index.csv"

BAND_WEIGHT = {"verified": 1.0, "review": 0.6, "unresolved": 0.3}
W_TOPIC = 0.3

PPR_DAMPING = 0.5
PPR_ITERATIONS = 12

Adjacency = dict[str, dict[str, float]]


def _add_edge(adjacency: Adjacency, a: str, b: str, weight: float) -> None:
    if a == b:
        return
    adjacency.setdefault(a, {})
    adjacency.setdefault(b, {})
    adjacency[a][b] = max(adjacency[a].get(b, 0.0), weight)
    adjacency[b][a] = max(adjacency[b].get(a, 0.0), weight)


def build_graph(conn: sqlite3.Connection, *, verified_only: bool | None = None) -> Adjacency:
    verified_only = _verified_only() if verified_only is None else verified_only
    rows = conn.execute("SELECT case_id, statute_links_json, topic_ids_json FROM cases").fetchall()

    by_section: dict[tuple[str, str], list[tuple[str, str]]] = {}
    by_topic: dict[str, list[str]] = {}
    for row in rows:
        case_id = row["case_id"]
        for source_id, section_number, band in json.loads(row["statute_links_json"]):
            if not section_number:
                continue
            if verified_only and band != "verified":
                continue
            by_section.setdefault((source_id, section_number), []).append((case_id, band))
        if not verified_only:  # candidate-only data; dropped entirely under verified_only
            for topic_id in json.loads(row["topic_ids_json"]):
                by_topic.setdefault(topic_id, []).append(case_id)

    adjacency: Adjacency = {}
    for members in by_section.values():
        if len(members) < 2:
            continue
        for i, (case_a, band_a) in enumerate(members):
            for case_b, band_b in members[i + 1 :]:
                weight = min(BAND_WEIGHT.get(band_a, 0.3), BAND_WEIGHT.get(band_b, 0.3))
                _add_edge(adjacency, case_a, case_b, weight)

    for members in by_topic.values():
        if len(members) < 2 or len(members) > 200:  # skip near-universal topics
            continue
        for i, case_a in enumerate(members):
            for case_b in members[i + 1 :]:
                _add_edge(adjacency, case_a, case_b, W_TOPIC)

    return adjacency


@lru_cache(maxsize=4)
def _graph_for_fingerprint(fingerprint: str, verified_only: bool) -> Adjacency:
    with connect() as conn:
        return build_graph(conn, verified_only=verified_only)


def get_graph() -> Adjacency:
    stats = build_index(force=False)
    return _graph_for_fingerprint(stats.fingerprint, _verified_only())


def expand_seeds(
    seeds: dict[str, float],
    *,
    adjacency: Adjacency | None = None,
    top_n: int = 8,
) -> list[tuple[str, float]]:
    """Personalized PageRank from seed cases; returns NEW cases only."""
    if not seeds:
        return []
    adjacency = adjacency if adjacency is not None else get_graph()
    total = sum(max(value, 0.0) for value in seeds.values()) or 1.0
    personalization = {key: max(value, 0.0) / total for key, value in seeds.items()}

    scores = dict(personalization)
    for _ in range(PPR_ITERATIONS):
        next_scores = {key: (1 - PPR_DAMPING) * value for key, value in personalization.items()}
        for node, score in scores.items():
            neighbours = adjacency.get(node)
            if not neighbours or score <= 0:
                continue
            weight_total = sum(neighbours.values())
            spread = PPR_DAMPING * score
            for neighbour, weight in neighbours.items():
                next_scores[neighbour] = next_scores.get(neighbour, 0.0) + spread * weight / weight_total
        scores = next_scores

    expansion = [(case_id, score) for case_id, score in scores.items() if case_id not in seeds and score > 1e-6]
    expansion.sort(key=lambda item: (-item[1], item[0]))
    return expansion[:top_n]


@lru_cache(maxsize=1)
def _statute_catalog() -> tuple[tuple[str, str], ...]:
    """(source_id, official_title) pairs, longest title first so a longer,
    more specific name matches before a shorter substring of it does."""
    if not STATUTE_INDEX_CSV.exists():
        return ()
    import csv

    with STATUTE_INDEX_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        rows = [
            (row["source_id"], row["official_title"])
            for row in csv.DictReader(file)
            if row.get("source_id") and row.get("official_title")
        ]
    rows.sort(key=lambda pair: -len(pair[1]))
    return tuple(rows)


def match_statutes_in_text(text: str) -> set[str]:
    """Source IDs of catalogued statutes named (by official title) in `text`."""
    lowered = text.lower()
    matched: set[str] = set()
    for source_id, title in _statute_catalog():
        stem = re.sub(r"\s+(?:ordinance|act|law)\b.*$", "", title.strip().lower())
        if len(stem) >= 6 and stem in lowered:
            matched.add(source_id)
    return matched


def seeds_from_statute_mentions(conn: sqlite3.Connection, text: str) -> dict[str, float]:
    """case_id -> weight for cases linked to a statute the query text names."""
    source_ids = match_statutes_in_text(text)
    if not source_ids:
        return {}
    verified_only = _verified_only()
    seeds: dict[str, float] = {}
    for row in conn.execute("SELECT case_id, statute_links_json FROM cases"):
        for source_id, _section_number, band in json.loads(row["statute_links_json"]):
            if source_id in source_ids:
                if verified_only and band != "verified":
                    continue
                weight = BAND_WEIGHT.get(band, 0.3)
                seeds[row["case_id"]] = max(seeds.get(row["case_id"], 0.0), weight)
    return seeds


def graph_stats() -> dict[str, int]:
    adjacency = get_graph()
    return {
        "nodes_with_edges": len(adjacency),
        "edges": sum(len(neighbours) for neighbours in adjacency.values()) // 2,
    }
