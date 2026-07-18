"""Statutes-only retrieval API."""

from .answering import answer
from .index import build_index
from .models import IndexStats, StatuteAnswer, StatuteHit, StatuteQuery
from .search import search

__all__ = [
    "IndexStats",
    "StatuteAnswer",
    "StatuteHit",
    "StatuteQuery",
    "answer",
    "build_index",
    "search",
]

