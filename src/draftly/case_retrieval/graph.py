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

Architecture toggles (all default off except DRAFTLY_CASE_CATCHWORD_EDGES,
which defaults on -- see RESULTS.md's architecture comparison for what each
measured):

  DRAFTLY_CASE_GRAPH_VERIFIED_ONLY  restricts the graph to the parts of the
      case<->case link data that are actually verified. `case_topic_links.csv`
      is 10,527 rows and every single one is `review_status="candidate"` --
      there is no verified topic link at all -- so under this toggle the
      topic bridge is dropped entirely, and the statute bridge keeps only
      `resolved_links.csv` rows with `band == "verified"` (462 of 523
      source_id-bearing rows). Measured: hurts accuracy (v2, 55% vs. the
      70% baseline) -- it trades away more useful recall than the precision
      it buys.

  DRAFTLY_CASE_GRAPH_FANOUT_WEIGHT  discounts a shared-section edge by how
      many cases cite that section: of 289 distinct (source_id,
      section_number) pairs in resolved_links.csv, 191 are cited by exactly
      one case (cannot bridge anything) and only 17 by 5+ (max 13) --
      "shares a citation to the Civil Procedure Code" is close to no
      evidence, "shares a citation nobody else does" is strong evidence.
      This targets the same problem DRAFTLY_CASE_GRAPH_VERIFIED_ONLY tried
      and failed to fix, but on the fanout axis instead of the
      verified-vs-not axis.

  DRAFTLY_CASE_CATCHWORD_EDGES  (default ON) adds a second, independent
      case<->case bridge from shared editor-assigned catchword phrases (see
      corpus.py), instead of relying solely on "cites the same statute" --
      catchwords are the editors' own classification of what a case is
      *about*, not a citation. Measured: 65% (13/20), the best-performing
      new mechanism tried, tied with DRAFTLY_CASE_CATCHWORD_STATUTE_LINKS.
      Set to 0/false/no to disable.

  DRAFTLY_CASE_CATCHWORD_STATUTE_LINKS  extracts additional, in-memory-only
      (source_id, section_number) links from catchwords that are already
      citation-shaped (e.g. "Civil Procedure Code, ss. 21, 38"), feeding the
      same by_section bridge above with more data than resolved_links.csv
      alone carries -- without touching that file or the separately
      -governed linking pipeline that produces it.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import sqlite3
from functools import lru_cache

from .index import build_index, connect
from .paths import REPO_ROOT


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes"}


def _flag_default_true(name: str) -> bool:
    """Like _flag, but on by default -- only an explicit 0/false/no opts out."""
    return os.getenv(name, "1").strip().lower() not in {"0", "false", "no"}


def _verified_only() -> bool:
    return _flag("DRAFTLY_CASE_GRAPH_VERIFIED_ONLY")


def _fanout_weight_enabled() -> bool:
    return _flag("DRAFTLY_CASE_GRAPH_FANOUT_WEIGHT")


def _catchword_edges_enabled() -> bool:
    # Default ON: measured 65% (13/20) vs. 50% for the pre-v5 baseline after
    # catchwords were added to the lexical/dense channels -- see RESULTS.md's
    # v5-v8 comparison. Set DRAFTLY_CASE_CATCHWORD_EDGES=0 to disable.
    return _flag_default_true("DRAFTLY_CASE_CATCHWORD_EDGES")


def _catchword_statute_links_enabled() -> bool:
    return _flag("DRAFTLY_CASE_CATCHWORD_STATUTE_LINKS")


STATUTE_INDEX_CSV = REPO_ROOT / "scripts" / "case-law-statute-linking" / "output" / "statute_index.csv"

BAND_WEIGHT = {"verified": 1.0, "review": 0.6, "unresolved": 0.3, "catchword": 0.5}
W_TOPIC = 0.3
W_CATCHWORD = 0.8  # a shared editor catchword phrase is a strong, independent signal

MAX_CATCHWORD_PHRASE_MEMBERS = 100  # skip near-universal phrases, same idea as topic capping
MIN_CATCHWORD_PHRASE_WORDS = 3  # "Notaries Ordinance" alone is too generic; require a fuller phrase

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


def fanout_discount(member_count: int) -> float:
    """Shrinks toward 0 as more cases cite the same (source_id, section_number).
    2 -> 0.5, 5 -> ~0.34, 13 -> ~0.26. Never used unless the fanout-weight
    toggle is on; see the module docstring for why."""
    return 1.0 / math.log2(member_count + 2)


def _catchword_phrases(catchwords: str) -> list[str]:
    """Distinctive multi-word phrases from an editor catchword field, with
    phrases that are themselves bare statute citations (e.g. "Civil
    Procedure Code, ss. 21, 38") excluded -- those duplicate the statute
    bridge rather than adding an independent signal."""
    phrases = []
    for raw in catchwords.split(";"):
        phrase = raw.strip().lower()
        if not phrase or len(phrase.split()) < MIN_CATCHWORD_PHRASE_WORDS:
            continue
        if re.search(r"\b(ordinance|act|code)\b.*\bss?\.\s*\d", phrase):
            continue
        phrases.append(phrase)
    return phrases


_SECTION_LIST_RE = re.compile(r"\bss?\.\s*([\d,\s()A-Za-z]+?)(?=;|$)")
_SECTION_NUM_RE = re.compile(r"\d+[A-Za-z]?")


def _catchword_statute_links(catchwords: str) -> list[tuple[str, str]]:
    """(source_id, section_number) pairs parsed out of citation-shaped
    catchword phrases, e.g. "Civil Procedure Code, ss. 21, 38, 46(2), 93"."""
    links: list[tuple[str, str]] = []
    for raw in catchwords.split(";"):
        phrase = raw.strip()
        if not phrase:
            continue
        source_ids = match_statutes_in_text(phrase)
        if not source_ids:
            continue
        section_match = _SECTION_LIST_RE.search(phrase.lower())
        if not section_match:
            continue
        section_numbers = _SECTION_NUM_RE.findall(section_match.group(1))
        for source_id in source_ids:
            for section_number in section_numbers:
                links.append((source_id, section_number.upper()))
    return links


def build_graph(
    conn: sqlite3.Connection,
    *,
    verified_only: bool | None = None,
    fanout_weight: bool | None = None,
    catchword_edges: bool | None = None,
    catchword_statute_links: bool | None = None,
) -> Adjacency:
    verified_only = _verified_only() if verified_only is None else verified_only
    fanout_weight = _fanout_weight_enabled() if fanout_weight is None else fanout_weight
    catchword_edges = _catchword_edges_enabled() if catchword_edges is None else catchword_edges
    catchword_statute_links = (
        _catchword_statute_links_enabled() if catchword_statute_links is None else catchword_statute_links
    )
    rows = conn.execute("SELECT case_id, statute_links_json, topic_ids_json, catchwords FROM cases").fetchall()

    by_section: dict[tuple[str, str], list[tuple[str, str]]] = {}
    by_topic: dict[str, list[str]] = {}
    by_catchword: dict[str, list[str]] = {}
    for row in rows:
        case_id = row["case_id"]
        for source_id, section_number, band in json.loads(row["statute_links_json"]):
            if not section_number:
                continue
            if verified_only and band != "verified":
                continue
            by_section.setdefault((source_id, section_number), []).append((case_id, band))
        if catchword_statute_links:
            for source_id, section_number in _catchword_statute_links(row["catchwords"]):
                by_section.setdefault((source_id, section_number), []).append((case_id, "catchword"))
        if not verified_only:  # candidate-only data; dropped entirely under verified_only
            for topic_id in json.loads(row["topic_ids_json"]):
                by_topic.setdefault(topic_id, []).append(case_id)
        if catchword_edges:
            for phrase in _catchword_phrases(row["catchwords"]):
                by_catchword.setdefault(phrase, []).append(case_id)

    adjacency: Adjacency = {}
    for members in by_section.values():
        if len(members) < 2:
            continue
        discount = fanout_discount(len(members)) if fanout_weight else 1.0
        for i, (case_a, band_a) in enumerate(members):
            for case_b, band_b in members[i + 1 :]:
                weight = min(BAND_WEIGHT.get(band_a, 0.3), BAND_WEIGHT.get(band_b, 0.3)) * discount
                _add_edge(adjacency, case_a, case_b, weight)

    for members in by_topic.values():
        if len(members) < 2 or len(members) > 200:  # skip near-universal topics
            continue
        for i, case_a in enumerate(members):
            for case_b in members[i + 1 :]:
                _add_edge(adjacency, case_a, case_b, W_TOPIC)

    for members in by_catchword.values():
        if len(members) < 2 or len(members) > MAX_CATCHWORD_PHRASE_MEMBERS:
            continue
        for i, case_a in enumerate(members):
            for case_b in members[i + 1 :]:
                _add_edge(adjacency, case_a, case_b, W_CATCHWORD)

    return adjacency


@lru_cache(maxsize=16)
def _graph_for_fingerprint(
    fingerprint: str, verified_only: bool, fanout_weight: bool, catchword_edges: bool, catchword_statute_links: bool
) -> Adjacency:
    with connect() as conn:
        return build_graph(
            conn,
            verified_only=verified_only,
            fanout_weight=fanout_weight,
            catchword_edges=catchword_edges,
            catchword_statute_links=catchword_statute_links,
        )


def get_graph() -> Adjacency:
    stats = build_index(force=False)
    return _graph_for_fingerprint(
        stats.fingerprint,
        _verified_only(),
        _fanout_weight_enabled(),
        _catchword_edges_enabled(),
        _catchword_statute_links_enabled(),
    )


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
    catchword_statute_links = _catchword_statute_links_enabled()
    seeds: dict[str, float] = {}
    for row in conn.execute("SELECT case_id, statute_links_json, catchwords FROM cases"):
        for source_id, _section_number, band in json.loads(row["statute_links_json"]):
            if source_id in source_ids:
                if verified_only and band != "verified":
                    continue
                weight = BAND_WEIGHT.get(band, 0.3)
                seeds[row["case_id"]] = max(seeds.get(row["case_id"], 0.0), weight)
        if catchword_statute_links:
            for source_id, _section_number in _catchword_statute_links(row["catchwords"]):
                if source_id in source_ids:
                    seeds[row["case_id"]] = max(seeds.get(row["case_id"], 0.0), BAND_WEIGHT["catchword"])
    return seeds


def graph_stats() -> dict[str, int]:
    adjacency = get_graph()
    return {
        "nodes_with_edges": len(adjacency),
        "edges": sum(len(neighbours) for neighbours in adjacency.values()) // 2,
    }
