"""FastAPI service exposing the statutes-only retrieval engine over HTTP.

Wires the existing `answer`/`search`/`topics_for_ui`/`sources_for_ui`
functions and their `to_dict()` serializers to `/answer`, `/search`,
`/topics`, and `/sources`. `build_index()` runs once at startup (via the
lifespan handler) rather than per request; `search`/`answer` still call it
internally on every request, but that call is a cheap fingerprint check that
reuses the already-built index unless the corpus changed.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from .answering import answer as answer_query
from .corpus import sources_for_ui, topics_for_ui
from .index import build_index
from .models import StatuteQuery
from .search import search as search_query

logger = logging.getLogger(__name__)

ALLOWED_KINDS = {"statute", "amendment"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    stats = build_index(force=False)
    logger.info(
        "Statute index ready: %s sections, fingerprint %s (reused=%s)",
        stats.sections,
        stats.fingerprint[:12],
        stats.reused,
    )
    yield


app = FastAPI(
    title="Draftly Statute Retrieval API",
    description=(
        "Grounded, citation-gated search and answering over the Sri Lankan "
        "statutes-and-amendments corpus. Read-only; no matter data, auth, or "
        "legal-corpus governance is implemented here (see DRA-30)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def _validate_kinds(kind: list[str] | None) -> tuple[str, ...] | None:
    if not kind:
        return None
    invalid = sorted(set(kind) - ALLOWED_KINDS)
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid kind(s): {', '.join(invalid)}. Expected one of {sorted(ALLOWED_KINDS)}.",
        )
    return tuple(kind)


@app.get("/health")
def health() -> dict[str, Any]:
    try:
        stats = build_index(force=False)
    except Exception as exc:  # noqa: BLE001 - surfaced as a 503, not a 500
        raise HTTPException(status_code=503, detail=f"Index not ready: {exc}") from exc
    return {"status": "ok", "index": stats.to_dict()}


@app.get("/topics")
def topics() -> list[dict[str, str]]:
    return topics_for_ui()


@app.get("/sources")
def sources() -> list[dict[str, str]]:
    return sources_for_ui()


@app.get("/search")
def search_endpoint(
    q: str = Query(..., min_length=1, description="Search query, e.g. a question or a direct section ID like 'SRC001:s2'."),
    topic_slug: str | None = Query(None, description="Restrict results to one curriculum topic slug."),
    kind: list[str] | None = Query(None, description="Filter by document type: statute, amendment. Repeatable."),
    source_id: str | None = Query(None, description="Restrict results to one source ID, e.g. SRC001."),
    limit: int = Query(8, ge=1, le=50),
) -> list[dict[str, Any]]:
    query = StatuteQuery(
        text=q,
        topic_slug=topic_slug,
        kinds=_validate_kinds(kind),
        source_id=source_id,
        limit=limit,
    )
    hits = search_query(query)
    return [hit.to_dict(include_text=False) for hit in hits]


@app.get("/answer")
def answer_endpoint(
    q: str = Query(..., min_length=1, description="Question, including a full multi-part question if needed."),
    limit: int = Query(12, ge=1, le=50),
) -> dict[str, Any]:
    response = answer_query(StatuteQuery(text=q, limit=limit))
    return response.to_dict()
