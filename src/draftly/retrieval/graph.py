"""Deterministic statute graph + personalized-PageRank expansion.

Statutes are graphs: sections cross-reference each other ("subject to section
5"), amendments target sections of their principal enactment, and interpretation
sections define the terms every sibling section uses. This module builds that
graph once per index fingerprint — from the section bodies and alias metadata
already in the SQLite index, no LLM — and expands retrieval seeds along it with
a small personalized-PageRank pass (the HippoRAG mechanism, deterministic
seeds/graph; see papers/qa-agent/notes-graph-rag.md).

Edge types and weights:
  cross_ref   1.0   section body cites "section N" of the same enactment
  amendment   1.2   amendment alias node <-> targeted principal section
  definition  0.25  section -> interpretation/definition sections of its source

All edges are stored bidirectionally (retrieving the referenced section should
also surface the section that relies on it).
"""

from __future__ import annotations

import json
import re
import sqlite3
from functools import lru_cache

from .index import build_index, connect

XREF_RE = re.compile(r"\bsections?\s+(\d{1,4}[A-Z]?)\b", re.IGNORECASE)
DEFINITION_HEADING_RE = re.compile(r"\b(interpretation|definitions?)\b", re.IGNORECASE)
AMENDMENT_SUFFIX_RE = re.compile(r"\s*\((amendment|special provisions)\b.*$", re.IGNORECASE)

W_CROSS_REF = 1.0
W_AMENDMENT = 1.2
W_DEFINITION = 0.25

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


def _principal_map(rows: list[sqlite3.Row]) -> dict[str, str]:
    """Map amendment source_id -> principal statute source_id by title stem."""
    stems: dict[str, str] = {}
    for row in rows:
        if row["kind"] != "statute":
            continue
        stem = AMENDMENT_SUFFIX_RE.sub("", row["title"]).strip().lower()
        stem = re.sub(r"\s+(?:ordinance|act|law)\b.*$", "", stem).strip()
        if stem:
            stems.setdefault(stem, row["source_id"])
    mapping: dict[str, str] = {}
    for row in rows:
        if row["kind"] != "amendment":
            continue
        stem = AMENDMENT_SUFFIX_RE.sub("", row["title"]).strip().lower()
        stem = re.sub(r"\s+(?:ordinance|act|law)\b.*$", "", stem).strip()
        principal = stems.get(stem)
        if principal and principal != row["source_id"]:
            mapping[row["source_id"]] = principal
    return mapping


def build_graph(conn: sqlite3.Connection) -> Adjacency:
    rows = conn.execute(
        "SELECT section_id, source_id, kind, title, heading, body, metadata_json FROM sections"
    ).fetchall()
    known_ids = {row["section_id"] for row in rows}
    doc_rows = conn.execute(
        "SELECT DISTINCT source_id, kind, title FROM sections"
    ).fetchall()
    principal_of = _principal_map(doc_rows)

    definition_sections: dict[str, list[str]] = {}
    for row in rows:
        if DEFINITION_HEADING_RE.search(row["heading"] or ""):
            definition_sections.setdefault(row["source_id"], []).append(row["section_id"])

    adjacency: Adjacency = {}
    for row in rows:
        section_id, source_id = row["section_id"], row["source_id"]
        own_number = section_id.rsplit(":s", 1)[-1].upper()

        # (a) intra-statute cross-references
        for number in {match.upper() for match in XREF_RE.findall(row["body"] or "")}:
            if number == own_number:
                continue
            target = f"{source_id}:s{number}"
            if target in known_ids:
                _add_edge(adjacency, section_id, target, W_CROSS_REF)

        # (b) amendment alias -> targeted principal section
        metadata = json.loads(row["metadata_json"] or "{}")
        target_section = str(metadata.get("target_section", "")).strip()
        if target_section:
            principal = principal_of.get(source_id)
            if principal:
                target = f"{principal}:s{target_section.upper()}"
                if target in known_ids:
                    _add_edge(adjacency, section_id, target, W_AMENDMENT)

        # (c) weak edge to the source's interpretation/definition sections
        for definition_id in definition_sections.get(source_id, ()):
            _add_edge(adjacency, section_id, definition_id, W_DEFINITION)

    return adjacency


@lru_cache(maxsize=2)
def _graph_for_fingerprint(fingerprint: str) -> Adjacency:
    with connect() as conn:
        return build_graph(conn)


def get_graph() -> Adjacency:
    stats = build_index(force=False)
    return _graph_for_fingerprint(stats.fingerprint)


def expand_seeds(
    seeds: dict[str, float],
    *,
    adjacency: Adjacency | None = None,
    top_n: int = 8,
) -> list[tuple[str, float]]:
    """Personalized PageRank from retrieval seeds; returns NEW sections only.

    Seeds are the fused retrieval hits (weight = fused score, normalized here).
    The walk surfaces sections structurally entangled with the evidence — the
    provision a seed says it is "subject to", the amendment that rewrites it,
    the definitions its terms depend on — even when no query token matches them.
    """
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

    expansion = [
        (section_id, score)
        for section_id, score in scores.items()
        if section_id not in seeds and score > 1e-6
    ]
    expansion.sort(key=lambda item: (-item[1], item[0]))
    return expansion[:top_n]


def graph_stats() -> dict[str, int]:
    adjacency = get_graph()
    return {
        "nodes_with_edges": len(adjacency),
        "edges": sum(len(neighbours) for neighbours in adjacency.values()) // 2,
    }
