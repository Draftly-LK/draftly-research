"""NetworkX knowledge graph built from the finalized JSONs' already-structured
cross_references / amendment_events fields.

Deliberate scope decision (see plan): this uses NetworkX, not Neo4j, per the
repo's existing preference for file-based structures at this scale
(proj-docs/project Management/retrieval-engine-methodology.md), and per the
user's explicit choice when presented with that tradeoff.
"""

from __future__ import annotations

import pickle
import re

import networkx as nx

from .config import GRAPH_TOP_N, PAGERANK_ALPHA
from .models import LawchainSection
from .paths import graph_cache_path

_LEADING_THE_RE = re.compile(r"^\s*the\s+", re.IGNORECASE)
_TRAILING_KIND_RE = re.compile(r"\s+(ordinance|act|law)\.?\s*$", re.IGNORECASE)


def normalize_title(title: str) -> str:
    title = _LEADING_THE_RE.sub("", title or "")
    title = _TRAILING_KIND_RE.sub("", title)
    return title.strip().casefold()


def build_graph(sections: list[LawchainSection]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    section_ids = {section.section_id for section in sections}

    titles_by_source: dict[str, str] = {}
    for section in sections:
        titles_by_source.setdefault(section.source_id, section.title)
    title_to_source = {normalize_title(title): source_id for source_id, title in titles_by_source.items()}

    for section in sections:
        graph.add_node(
            section.section_id,
            source_id=section.source_id,
            heading=section.heading,
            external_amendments=list(section.amendment_events),
        )

    seen_edges: set[tuple[str, str, str]] = set()
    unresolved_enactment_refs = 0

    for section in sections:
        for ref in section.cross_references:
            kind = ref.get("kind")
            if kind == "internal":
                target_section = ref.get("target_section")
                if not target_section:
                    continue
                target_id = f"{section.source_id}:s{target_section}"
                if target_id not in section_ids or target_id == section.section_id:
                    continue
                edge_key = (section.section_id, target_id, "internal")
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                graph.add_edge(section.section_id, target_id, kind="internal")
            elif kind == "enactment":
                target_source_id = title_to_source.get(normalize_title(ref.get("target_document", "")))
                if target_source_id is None or target_source_id == section.source_id:
                    unresolved_enactment_refs += 1
                    continue
                doc_node = f"DOC:{target_source_id}"
                if doc_node not in graph:
                    graph.add_node(doc_node, source_id=target_source_id, is_document_node=True)
                edge_key = (section.section_id, doc_node, "enactment")
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                graph.add_edge(section.section_id, doc_node, kind="enactment")

    graph.graph["unresolved_enactment_refs"] = unresolved_enactment_refs
    return graph


def graph_lookup(
    graph: nx.MultiDiGraph,
    seeds: dict[str, float],
    *,
    top_n: int = GRAPH_TOP_N,
    alpha: float = PAGERANK_ALPHA,
) -> list[tuple[str, float]]:
    if graph.number_of_nodes() == 0:
        return []
    valid_seeds = {node: weight for node, weight in seeds.items() if node in graph and weight > 0}
    if not valid_seeds:
        return []

    try:
        scores = nx.pagerank(graph, alpha=alpha, personalization=valid_seeds)
    except nx.PowerIterationFailedConvergence:
        return []

    ranked = sorted(
        (
            (node, score)
            for node, score in scores.items()
            if node not in valid_seeds and not str(node).startswith("DOC:")
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return ranked[:top_n]


def build_graph_cached(sections: list[LawchainSection], *, fingerprint: str, force: bool = False) -> nx.MultiDiGraph:
    cache_path = graph_cache_path(fingerprint)
    if not force and cache_path.exists():
        try:
            with cache_path.open("rb") as file:
                return pickle.load(file)
        except (pickle.PickleError, EOFError, OSError):
            pass

    graph = build_graph(sections)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("wb") as file:
        pickle.dump(graph, file)
    return graph
