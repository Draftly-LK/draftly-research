from lawchain.extraction import build_corpus, corpus_fingerprint
from lawchain.lexical_index import build_lexical_index


def test_bm25_surfaces_relevant_section() -> None:
    sections = build_corpus()
    index = build_lexical_index(sections, fingerprint=corpus_fingerprint(), force=True)
    results = index.search("notary witnesses deed execution", limit=5)
    assert any(section_id == "SRC001:s2" for section_id, _ in results)
