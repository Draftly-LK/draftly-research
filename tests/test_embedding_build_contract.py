"""The deployment's dense-index build must reject incomplete caches."""

import sqlite3
import sys
from types import SimpleNamespace

import pytest

from draftly.case_retrieval import embeddings as case_embeddings
from draftly.retrieval import __main__ as statute_cli
from draftly.retrieval import embeddings as statute_embeddings


def test_statute_cli_accepts_deployment_embedding_flag(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["draftly.retrieval", "build", "--with-embeddings"])
    monkeypatch.setattr(statute_cli, "build_index", lambda force: SimpleNamespace(to_dict=lambda: {}))
    monkeypatch.setattr(statute_cli, "build_embeddings", lambda force: 3)
    statute_cli.main()
    assert '"sections_embedded": 3' in capsys.readouterr().out


@pytest.mark.parametrize("module", [statute_embeddings, case_embeddings])
def test_unavailable_embedding_client_fails_build(monkeypatch, module):
    monkeypatch.setattr(module, "build_index", lambda force: SimpleNamespace(fingerprint="test"))
    monkeypatch.setattr(module, "_client", lambda: None)
    with pytest.raises(RuntimeError, match="embedding client is unavailable"):
        module.build_embeddings()


@pytest.mark.parametrize(
    ("module", "table", "columns", "row"),
    [
        (statute_embeddings, "sections", "section_id TEXT, title TEXT, heading TEXT, body TEXT", ("s1", "Act", "S", "Body")),
        (case_embeddings, "cases", "case_id TEXT, title TEXT, rule_statement TEXT, catchwords TEXT, body TEXT", ("c1", "Case", "Rule", "words", "Body")),
    ],
)
def test_failed_dense_batch_fails_build(monkeypatch, tmp_path, module, table, columns, row):
    index_db = tmp_path / "index.sqlite"
    with sqlite3.connect(index_db) as conn:
        conn.execute(f"CREATE TABLE {table} ({columns})")
        placeholders = ", ".join("?" for _ in row)
        conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
    monkeypatch.setattr(module, "build_index", lambda force: SimpleNamespace(fingerprint="test"))
    def connect_index():
        conn = sqlite3.connect(index_db)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(module, "connect", connect_index)
    monkeypatch.setattr(module, "EMBED_DB", tmp_path / "embed.sqlite")
    monkeypatch.setattr(module, "_client", lambda: object())
    monkeypatch.setattr(module, "_embed_batch", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="embedding batch failed"):
        module.build_embeddings()
