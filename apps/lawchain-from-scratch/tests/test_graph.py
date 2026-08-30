from lawchain.extraction import build_corpus
from lawchain.graph import build_graph, graph_lookup


def test_internal_cross_reference_edge_exists() -> None:
    sections = build_corpus()
    graph = build_graph(sections)
    assert graph.has_edge("SRC001:s3", "SRC001:s2")


def test_graph_lookup_surfaces_related_section() -> None:
    sections = build_corpus()
    graph = build_graph(sections)
    results = graph_lookup(graph, {"SRC001:s3": 1.0}, top_n=5)
    assert any(section_id == "SRC001:s2" for section_id, _ in results)
