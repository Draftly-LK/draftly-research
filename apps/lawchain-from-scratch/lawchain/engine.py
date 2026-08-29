from __future__ import annotations

from dataclasses import dataclass

from .dense_index import DenseIndex, build_dense_index
from .extraction import build_corpus, corpus_fingerprint
from .generation import summarize
from .graph import build_graph_cached, graph_lookup
from .lexical_index import LexicalIndex, build_lexical_index
from .models import LawchainAnswer, LawchainHit, LawchainSection
from .query_expansion import expand_query
from .ranking import fuse, llm_judge_rerank


@dataclass
class LawchainBuildStats:
    fingerprint: str
    sections: int
    source_ids: int
    graph_nodes: int
    graph_edges: int


_state: dict = {}


def build(*, force: bool = False) -> LawchainBuildStats:
    sections = build_corpus()
    fingerprint = corpus_fingerprint()

    lexical = build_lexical_index(sections, fingerprint=fingerprint, force=force)
    dense = build_dense_index(sections, fingerprint=fingerprint, force=force)
    graph = build_graph_cached(sections, fingerprint=fingerprint, force=force)

    sections_by_id = {section.section_id: section for section in sections}
    source_ids = {section.source_id for section in sections}

    _state.clear()
    _state.update(
        fingerprint=fingerprint,
        sections=sections,
        sections_by_id=sections_by_id,
        lexical=lexical,
        dense=dense,
        graph=graph,
    )

    return LawchainBuildStats(
        fingerprint=fingerprint,
        sections=len(sections),
        source_ids=len(source_ids),
        graph_nodes=graph.number_of_nodes(),
        graph_edges=graph.number_of_edges(),
    )


def _ensure_built() -> None:
    if not _state:
        build()


def _retrieve_and_fuse(queries: list[str]) -> list[LawchainHit]:
    lexical: LexicalIndex = _state["lexical"]
    dense: DenseIndex = _state["dense"]
    graph = _state["graph"]
    sections_by_id: dict[str, LawchainSection] = _state["sections_by_id"]

    lexical_hits: dict[str, float] = {}
    dense_hits: dict[str, float] = {}
    for query in queries:
        for section_id, score in lexical.search(query, limit=20):
            lexical_hits[section_id] = max(lexical_hits.get(section_id, 0.0), score)
        for section_id, score in dense.search(query, limit=20):
            dense_hits[section_id] = max(dense_hits.get(section_id, 0.0), score)

    seed_pool = sorted(lexical_hits.items(), key=lambda pair: pair[1], reverse=True)[:5]
    seed_pool += sorted(dense_hits.items(), key=lambda pair: pair[1], reverse=True)[:5]
    seeds = {section_id: score for section_id, score in seed_pool if score > 0}
    graph_hits = graph_lookup(graph, seeds) if seeds else []

    channel_hits = [
        ("lexical", sorted(lexical_hits.items(), key=lambda pair: pair[1], reverse=True)),
        ("dense", sorted(dense_hits.items(), key=lambda pair: pair[1], reverse=True)),
        ("graph", graph_hits),
    ]
    return fuse(channel_hits, sections_by_id)


def retrieve(question: str, *, limit: int = 5) -> list[LawchainHit]:
    _ensure_built()
    fused = expand_query(question, retrieve_and_fuse=_retrieve_and_fuse)
    return llm_judge_rerank(question, fused, top_k=limit)


def answer(question: str, *, limit: int = 5) -> LawchainAnswer:
    hits = retrieve(question, limit=limit)
    return summarize(question, hits)
