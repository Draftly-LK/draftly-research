import lawchain.dense_index as dense_index_module


def test_engine_build_and_retrieve_smoke(monkeypatch) -> None:
    # Avoid the ~440MB E5 model download in automated test runs; the dense
    # channel itself is exercised manually (see plan verification step 6).
    monkeypatch.setattr(dense_index_module, "DISABLE_DENSE", True)

    from lawchain import engine

    stats = engine.build(force=True)
    assert stats.sections > 0
    assert stats.source_ids == 24
    assert stats.graph_nodes > 0

    hits = engine.retrieve("what makes a deed valid", limit=5)
    assert hits
    assert all(hit.section_id for hit in hits)
