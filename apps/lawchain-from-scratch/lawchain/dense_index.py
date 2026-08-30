"""E5-base dense embeddings, local inference via sentence-transformers.

Genuinely different embedding source from the existing engine's
src/draftly/retrieval/embeddings.py (Gemini API, remote, 768-dim) -- this is
a local model, no API key, different vector space. Not comparable/fused
across spaces, so this module never imports the Gemini embeddings path.
"""

from __future__ import annotations

import json
from functools import lru_cache

import numpy as np

from .config import DENSE_EMBEDDING_MODEL, DISABLE_DENSE
from .models import LawchainSection
from .paths import dense_cache_dir

MAX_PASSAGE_CHARS = 2000


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(DENSE_EMBEDDING_MODEL)


def _passage_text(section: LawchainSection) -> str:
    heading = f" - {section.heading}" if section.heading else ""
    return f"passage: {section.title}{heading}\n{section.text[:MAX_PASSAGE_CHARS]}"


def _query_text(query: str) -> str:
    return f"query: {query}"


class DenseIndex:
    def __init__(self, section_ids: list[str], vectors: np.ndarray):
        self._section_ids = section_ids
        self._vectors = vectors

    def search(self, query: str, limit: int = 20) -> list[tuple[str, float]]:
        if DISABLE_DENSE or not self._section_ids:
            return []
        query_vector = _model().encode([_query_text(query)], normalize_embeddings=True)[0]
        scores = self._vectors @ query_vector
        ranked_indices = np.argsort(-scores)[:limit]
        return [(self._section_ids[i], float(scores[i])) for i in ranked_indices]


def build_dense_index(sections: list[LawchainSection], *, fingerprint: str, force: bool = False) -> DenseIndex:
    if DISABLE_DENSE:
        return DenseIndex([], np.zeros((0, 0), dtype="float32"))

    cache_dir = dense_cache_dir(fingerprint)
    vectors_path = cache_dir / "vectors.npy"
    ids_path = cache_dir / "ids.json"

    if not force and vectors_path.exists() and ids_path.exists():
        try:
            vectors = np.load(vectors_path)
            section_ids = json.loads(ids_path.read_text(encoding="utf-8"))
            return DenseIndex(section_ids, vectors)
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    section_ids = [section.section_id for section in sections]
    passages = [_passage_text(section) for section in sections]
    vectors = np.asarray(
        _model().encode(passages, normalize_embeddings=True, show_progress_bar=False),
        dtype="float32",
    )

    cache_dir.mkdir(parents=True, exist_ok=True)
    np.save(vectors_path, vectors)
    ids_path.write_text(json.dumps(section_ids), encoding="utf-8")
    return DenseIndex(section_ids, vectors)
