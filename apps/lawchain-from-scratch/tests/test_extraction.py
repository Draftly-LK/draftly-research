from lawchain.extraction import build_corpus, corpus_fingerprint, select_statute_files


def test_select_statute_files_resolves_all_24() -> None:
    resolved = select_statute_files()
    assert len(resolved) == 24


def test_build_corpus_covers_all_source_ids() -> None:
    resolved = select_statute_files()
    sections = build_corpus()
    covered = {section.source_id for section in sections}
    assert covered == set(resolved)


def test_prevention_of_frauds_cross_reference_rolls_up() -> None:
    sections = build_corpus()
    by_id = {section.section_id: section for section in sections}
    assert "SRC001:s2" in by_id

    section_3 = by_id["SRC001:s3"]
    targets = {ref.get("target_section") for ref in section_3.cross_references if ref.get("kind") == "internal"}
    assert "2" in targets


def test_corpus_fingerprint_is_stable() -> None:
    assert corpus_fingerprint() == corpus_fingerprint()
