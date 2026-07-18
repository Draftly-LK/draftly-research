from __future__ import annotations

import json
import math
import re
import sqlite3

from .corpus import sources_for_ui, topics_for_ui
from .index import build_index, connect
from .models import StatuteHit, StatuteQuery

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "by",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "which",
    "who",
}
TOKEN_RE = re.compile(r"[A-Za-z0-9]{2,}")
SECTION_ID_RE = re.compile(r"\b(SRC\d{3}:s\d{1,3}[A-Z]?)\b", re.IGNORECASE)
SOURCE_ID_RE = re.compile(r"\b(SRC\d{3})\b", re.IGNORECASE)
SECTION_REF_RE = re.compile(r"\b(?:section|s)\.?\s*(\d{1,3}[A-Z]?)\b", re.IGNORECASE)


def search(query: StatuteQuery | str) -> list[StatuteHit]:
    build_index(force=False)
    if isinstance(query, str):
        query = StatuteQuery(text=query)
    if not query.text.strip() and not query.source_id:
        return []

    with connect() as conn:
        direct_hits = direct_lookup(conn, query)
        lexical_hits = lexical_lookup(conn, query, exclude={hit.section_id for hit in direct_hits})
    hits = direct_hits + lexical_hits
    return hits[: query.limit]


def direct_lookup(conn: sqlite3.Connection, query: StatuteQuery) -> list[StatuteHit]:
    ids = {match.upper() for match in SECTION_ID_RE.findall(query.text)}
    if query.source_id:
        section_match = SECTION_REF_RE.search(query.text)
        if section_match:
            ids.add(f"{query.source_id.upper()}:s{section_match.group(1)}")
    source_match = SOURCE_ID_RE.search(query.text)
    section_match = SECTION_REF_RE.search(query.text)
    if source_match and section_match:
        ids.add(f"{source_match.group(1).upper()}:s{section_match.group(1)}")

    for source in sources_for_ui():
        title = source["title"].lower()
        if title and title in query.text.lower() and section_match:
            ids.add(f"{source['source_id']}:s{section_match.group(1)}")

    if not ids:
        return []

    rows = []
    for section_id in sorted(ids):
        row = conn.execute("SELECT * FROM sections WHERE section_id = ?", (section_id,)).fetchone()
        if row and row_allowed(row, query):
            rows.append(row_to_hit(row, score=-100.0, query_text=query.text))
    return rows


def lexical_lookup(conn: sqlite3.Connection, query: StatuteQuery, exclude: set[str]) -> list[StatuteHit]:
    fts_query = make_fts_query(query.text)
    if not fts_query:
        return []

    where = ["s.kind IN ('statute', 'amendment')"]
    params: list[str | float] = [fts_query]
    if query.source_id:
        where.append("s.source_id = ?")
        params.append(query.source_id.upper())
    if query.kinds:
        placeholders = ",".join("?" for _ in query.kinds)
        where.append(f"s.kind IN ({placeholders})")
        params.extend(query.kinds)
    if query.topic_slug:
        where.append("s.topic_slugs LIKE ?")
        params.append(f"%;{query.topic_slug};%")
    if exclude:
        placeholders = ",".join("?" for _ in exclude)
        where.append(f"s.section_id NOT IN ({placeholders})")
        params.extend(sorted(exclude))

    sql = f"""
        SELECT s.*, bm25(sections_fts, 4.0, 3.0, 1.0) AS bm25_score
        FROM sections_fts
        JOIN sections s ON s.section_id = sections_fts.section_id
        WHERE sections_fts MATCH ? AND {" AND ".join(where)}
        ORDER BY bm25_score ASC
        LIMIT ?
    """
    params.append(max(query.limit * 3, 20))
    rows = conn.execute(sql, params).fetchall()
    hits = [row_to_hit(row, score=float(row["bm25_score"]), query_text=query.text) for row in rows]
    return rerank_with_soft_topics(hits, query.text)


def row_allowed(row: sqlite3.Row, query: StatuteQuery) -> bool:
    if row["kind"] not in {"statute", "amendment"}:
        return False
    if query.kinds and row["kind"] not in query.kinds:
        return False
    if query.source_id and row["source_id"] != query.source_id.upper():
        return False
    if query.topic_slug and f";{query.topic_slug};" not in row["topic_slugs"]:
        return False
    return True


def row_to_hit(row: sqlite3.Row, *, score: float, query_text: str) -> StatuteHit:
    topics = tuple(json.loads(row["topics_json"]))
    body = row["body"]
    return StatuteHit(
        source_id=row["source_id"],
        section_id=row["section_id"],
        title=row["title"],
        act_number=row["act_number"],
        year=row["year"],
        document_type=row["kind"],
        topics=topics,
        heading=row["heading"],
        excerpt=make_excerpt(body, query_text),
        score=round(score, 6),
        public_source_url=row["public_source_url"],
        extraction_confidence=row["extraction_confidence"],
        text=body,
    )


def make_fts_query(text: str) -> str:
    tokens = [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS]
    tokens = [token for token in tokens if not token.startswith("src")]
    if not tokens:
        return ""
    unique = list(dict.fromkeys(tokens[:12]))
    return " OR ".join(f"{token}*" for token in unique)


def rerank_with_soft_topics(hits: list[StatuteHit], text: str) -> list[StatuteHit]:
    lowered = text.lower()
    topic_rows = topics_for_ui()
    detected = []
    for topic in topic_rows:
        keyword_text = f"{topic['name']} {topic.get('keywords', '')}".lower()
        if any(token in lowered for token in TOKEN_RE.findall(keyword_text) if len(token) > 4):
            detected.append(topic["slug"])
    if not detected:
        return hits
    adjusted = []
    for hit in hits:
        boost = -0.75 if any(slug in hit.topics for slug in detected) else 0.0
        adjusted.append((hit.score + boost, hit))
    adjusted.sort(key=lambda item: item[0])
    return [hit for _, hit in adjusted]


def make_excerpt(text: str, query_text: str, radius: int = 360) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= radius * 2:
        return normalized
    tokens = [token.lower() for token in TOKEN_RE.findall(query_text) if token.lower() not in STOPWORDS]
    lowered = normalized.lower()
    positions = [lowered.find(token) for token in tokens if lowered.find(token) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - radius)
    end = min(len(normalized), center + radius)
    prefix = "..." if start else ""
    suffix = "..." if end < len(normalized) else ""
    return f"{prefix}{normalized[start:end].strip()}{suffix}"


def score_to_similarity(score: float) -> float:
    if score < 0:
        return 1.0
    return 1.0 / (1.0 + math.exp(min(score, 50.0)))

