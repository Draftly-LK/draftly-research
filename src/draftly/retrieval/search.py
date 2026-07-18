from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import replace

from .corpus import sources_for_ui, topics_for_ui
from .index import build_index, connect
from .models import StatuteHit, StatuteQuery
from .question_analysis import analyze_question

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
SECTION_ID_RE = re.compile(r"\b(SRC\d{3}:s\d{1,4}[A-Z]?)\b", re.IGNORECASE)
SOURCE_ID_RE = re.compile(r"\b(SRC\d{3})\b", re.IGNORECASE)
SECTION_REF_RE = re.compile(r"\b(?:section|s)\.?\s*(\d{1,4}[A-Z]?)\b", re.IGNORECASE)
SECTION_RANGE_RE = re.compile(
    r"\bsections?\s+(\d{1,4})\s*(?:to|through|-)\s*(\d{1,4})\b",
    re.IGNORECASE,
)
RRF_K = 60
MAX_DIRECT_RANGE_END = 1500

QUERY_EXPANSIONS = {
    "deed valid": ("immovable property", "executed", "notary", "witnesses"),
    "deed of transfer": ("instrument", "immovable property", "executed"),
    "stamp duty": ("chargeable", "instrument", "payable", "duty"),
    "power of attorney": ("execute", "attest", "register"),
    "last will": ("testator", "execute", "attest", "witnesses"),
    "prescriptive rights": ("adverse possession", "uninterrupted", "ten years"),
    "caveat": ("caveator", "notice", "registration"),
    "foreign": ("transfer of land", "foreigner", "alienation"),
    "condominium": ("unit", "plan", "management corporation"),
}

SOURCE_HINT_TERMS = {
    "SRC001": "deed instrument immovable property executed notary witnesses",
    "SRC002": "amendment deed instrument executed notary witnesses",
    "SRC003": "amendment transfer deed signatures thumb impressions witnesses",
    "SRC004": "intestate succession spouse children heirs shares",
    "SRC005": "instrument registration registrar caveat priority",
    "SRC011": "title registration notary cadastral owner occupier",
    "SRC012": "condominium unit plan management corporation fund",
    "SRC014": "notary deed attest title search protocol duties",
    "SRC015": "amendment notary deed attest title search protocol duties",
    "SRC016": "amendment notary duplicates deed registrar",
    "SRC017": "power of attorney execute attest register",
    "SRC019": "amendment power of attorney execute attest register",
    "SRC020": "amendment power of attorney ambassador execute",
    "SRC021": "restriction transfer land foreigner foreign company exemption",
    "SRC022": "restriction transfer land foreigner exemption condominium",
    "SRC024": "will testator execute testament revoke",
    "SRC026": "amendment will testator execute revoke",
    "SRC027": "partition land decree co-owner",
    "SRC030": "civil procedure probate executor administrator estate testament inventory",
    "SRC034": "stamp duty instrument chargeable payable value",
    "SRC035": "western province stamp duty instrument property value payment",
    "SRC050": "grant land successor mortgage cancellation",
    "SRC068": "stamp duty instrument payment",
    "SRC069": "amendment stamp duty manner payment liable",
    "SRC071": "adverse uninterrupted possession immovable property ten years",
}

SOURCE_HINT_SECTION_SEEDS = {
    "SRC001": ("2",),
    "SRC002": ("2",),
    "SRC003": ("2",),
    "SRC004": ("22", "23", "24", "25", "26"),
    "SRC005": ("7",),
    "SRC012": ("9", "10"),
    "SRC014": ("26",),
    "SRC015": ("28",),
    "SRC016": ("28",),
    "SRC017": ("2",),
    "SRC019": ("3A",),
    "SRC020": ("2",),
    "SRC021": ("2", "3"),
    "SRC022": ("2", "3"),
    "SRC024": ("2",),
    "SRC026": ("2", "4"),
    "SRC030": ("518", "524"),
    "SRC034": ("2", "24"),
    "SRC035": ("48",),
    "SRC068": ("3",),
    "SRC069": ("6", "8"),
    "SRC071": ("3",),
}


def search(query: StatuteQuery | str) -> list[StatuteHit]:
    build_index(force=False)
    if isinstance(query, str):
        query = StatuteQuery(text=query)
    if not query.text.strip() and not query.source_id:
        return []

    analysis = analyze_question(query.text)
    subqueries = analysis.subqueries or (query.text.strip(),)
    global_hints = tuple(hint.source_id for hint in analysis.source_hints)

    ranked_lists: list[tuple[str, list[StatuteHit], float]] = []
    with connect() as conn:
        for subquery in subqueries[:8]:
            scoped = replace(query, text=subquery, limit=max(query.limit, 10))
            direct_hits = direct_lookup(conn, scoped)
            lexical_hits = lexical_lookup(
                conn,
                scoped,
                exclude={hit.section_id for hit in direct_hits},
            )
            ranked_lists.append((subquery, direct_hits + lexical_hits, 1.0))

            issue_text = subquery.split(" Context:", 1)[0]
            local_analysis = analyze_question(issue_text)
            local_hints = tuple(hint.source_id for hint in local_analysis.source_hints)
            for source_id in local_hints[:6]:
                if query.source_id and query.source_id.upper() != source_id:
                    continue
                hint_terms = SOURCE_HINT_TERMS.get(source_id, "")
                hinted_query = replace(
                    scoped,
                    text=f"{issue_text} {hint_terms}".strip(),
                    source_id=source_id,
                    limit=5,
                )
                hinted = lexical_lookup(conn, hinted_query, exclude=set())
                if hinted:
                    ranked_lists.append((subquery, hinted, 1.35))

        seeded = seeded_source_hits(conn, query, global_hints)
        if seeded:
            ranked_lists.append(("Curated statutory entry points", seeded, 1.8))

    return fuse_rankings(ranked_lists, limit=query.limit, source_hints=set(global_hints))


def seeded_source_hits(
    conn: sqlite3.Connection,
    query: StatuteQuery,
    source_hints: tuple[str, ...],
) -> list[StatuteHit]:
    hits: list[StatuteHit] = []
    for source_id in source_hints:
        if query.source_id and query.source_id.upper() != source_id:
            continue
        for section in SOURCE_HINT_SECTION_SEEDS.get(source_id, ()):
            row = conn.execute(
                "SELECT * FROM sections WHERE section_id = ?",
                (f"{source_id}:s{section}",),
            ).fetchone()
            if row and row_allowed(row, query):
                hits.append(row_to_hit(row, score=-100.0, query_text=query.text))
    return hits


def fuse_rankings(
    ranked_lists: list[tuple[str, list[StatuteHit], float]],
    *,
    limit: int,
    source_hints: set[str],
) -> list[StatuteHit]:
    scores: dict[str, float] = {}
    hits_by_id: dict[str, StatuteHit] = {}
    matched: dict[str, list[str]] = {}
    for subquery, hits, weight in ranked_lists:
        for rank, hit in enumerate(hits, start=1):
            score = weight / (RRF_K + rank)
            if hit.score <= -100:
                score += 0.05
            if hit.source_id in source_hints:
                score += 0.006
            scores[hit.section_id] = scores.get(hit.section_id, 0.0) + score
            hits_by_id.setdefault(hit.section_id, hit)
            matched.setdefault(hit.section_id, []).append(subquery)

    ordered = sorted(scores, key=lambda section_id: (-scores[section_id], section_id))
    result: list[StatuteHit] = []
    seen_passages: set[tuple[str, str]] = set()
    for section_id in ordered:
        hit = hits_by_id[section_id]
        passage_key = (hit.source_id, re.sub(r"\s+", " ", hit.text).strip().lower())
        if passage_key in seen_passages:
            continue
        seen_passages.add(passage_key)
        result.append(
            replace(
                hit,
                score=round(scores[section_id], 6),
                matched_queries=tuple(dict.fromkeys(matched[section_id])),
            )
        )
        if len(result) >= limit:
            break
    return result


def direct_lookup(conn: sqlite3.Connection, query: StatuteQuery) -> list[StatuteHit]:
    ids = {match.upper() for match in SECTION_ID_RE.findall(query.text)}
    if query.source_id:
        section_match = SECTION_REF_RE.search(query.text)
        if section_match:
            ids.add(f"{query.source_id.upper()}:s{section_match.group(1)}")
    source_match = SOURCE_ID_RE.search(query.text)
    section_match = SECTION_REF_RE.search(query.text)
    range_match = SECTION_RANGE_RE.search(query.text)
    if source_match and section_match:
        ids.add(f"{source_match.group(1).upper()}:s{section_match.group(1)}")

    for source in sources_for_ui():
        title = source["title"].lower()
        if title and title in query.text.lower() and section_match:
            ids.add(f"{source['source_id']}:s{section_match.group(1)}")
        if title and title in query.text.lower() and range_match:
            start, end = (int(range_match.group(1)), int(range_match.group(2)))
            if 0 < start <= end <= MAX_DIRECT_RANGE_END and end - start <= 20:
                ids.update(f"{source['source_id']}:s{number}" for number in range(start, end + 1))

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
    metadata = json.loads(row["metadata_json"]) if "metadata_json" in row.keys() else {}
    target_section = str(metadata.get("target_section", ""))
    citation_note = ""
    if metadata.get("alias_kind") == "principal_section_target":
        citation_note = (
            f"This node is an amendment passage targeting section {target_section} of the principal enactment; "
            "the internal ID is a retrieval alias, not the amending Act's own section number."
        )
    if metadata.get("quality_warning"):
        citation_note = str(metadata["quality_warning"])
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
        citation_note=citation_note,
        target_section=target_section,
    )


def make_fts_query(text: str) -> str:
    tokens = [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS]
    tokens = [token for token in tokens if not token.startswith("src")]
    lowered = text.lower()
    for phrase, expansions in QUERY_EXPANSIONS.items():
        if phrase in lowered:
            for expansion in expansions:
                tokens.extend(token.lower() for token in TOKEN_RE.findall(expansion))
    if not tokens:
        return ""
    unique = list(dict.fromkeys(tokens))[:24]
    return " OR ".join(f"{token}*" for token in unique)


def rerank_with_soft_topics(hits: list[StatuteHit], text: str) -> list[StatuteHit]:
    lowered = text.lower()
    topic_rows = topics_for_ui()
    detected = []
    for topic in topic_rows:
        keyword_text = f"{topic['name']} {topic.get('keywords', '')}".lower()
        if any(
            re.search(rf"\b{re.escape(token.lower())}\b", lowered)
            for token in TOKEN_RE.findall(keyword_text)
            if len(token) > 4
        ):
            detected.append(topic["slug"])
    if not detected:
        return hits
    adjusted = []
    for hit in hits:
        boost = -0.75 if any(slug in hit.topics for slug in detected) else 0.0
        adjusted.append((hit.score + boost, hit))
    adjusted.sort(key=lambda item: item[0])
    return [hit for _, hit in adjusted]


def make_excerpt(text: str, query_text: str, radius: int = 900) -> str:
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
