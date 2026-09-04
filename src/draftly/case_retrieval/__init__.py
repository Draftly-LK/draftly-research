"""Similar-case retrieval over the conveyancing-scoped case corpus."""

from .index import build_index
from .models import CaseHit, CaseIndexStats, CaseQuery, SimilarCaseResult
from .search import find_similar

__all__ = [
    "CaseHit",
    "CaseIndexStats",
    "CaseQuery",
    "SimilarCaseResult",
    "build_index",
    "find_similar",
]
