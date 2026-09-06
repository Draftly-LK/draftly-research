from __future__ import annotations

import pickle
import re

from rank_bm25 import BM25Okapi

from .models import LawchainSection
from .paths import lexical_cache_path

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class LexicalIndex:
    def __init__(self, sections: list[LawchainSection]):
        self._section_ids = [section.section_id for section in sections]
        corpus = [tokenize(f"{section.heading}\n{section.text}") for section in sections]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, limit: int = 20) -> list[tuple[str, float]]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self._section_ids, scores), key=lambda pair: pair[1], reverse=True)
        return [(section_id, float(score)) for section_id, score in ranked[:limit] if score > 0]


def build_lexical_index(sections: list[LawchainSection], *, fingerprint: str, force: bool = False) -> LexicalIndex:
    cache_path = lexical_cache_path(fingerprint)
    if not force and cache_path.exists():
        try:
            with cache_path.open("rb") as file:
                return pickle.load(file)
        except (pickle.PickleError, EOFError, OSError):
            pass

    index = LexicalIndex(sections)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("wb") as file:
        pickle.dump(index, file)
    return index
