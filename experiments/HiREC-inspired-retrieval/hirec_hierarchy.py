"""Section-subtree pooling. Pure policy: no LLM, no network, no gold.

This is the domain analog of HiREC's page-level context. HiREC retrieves 1024-
character passages but can hand the generator the whole page a passage came from
(--use_full_page), because a passage torn out of a filing table loses the header
that makes it mean anything. A statutory provision has the same property and
more sharply: paragraph (b) of section 52 is unintelligible and unusable without
section 52 and its other paragraphs.

So a BM25 hit is not the unit of evidence. The unit is the section the hit lives
in, expanded to every record the corpus holds for it. Measured over the 20
smoke questions, seeding with BM25 top-20 and expanding this way puts the
complete gold evidence in the pool for 20 of 20 questions, against 0.90 for both
the flat koblex baselines.

Ordering is deterministic: sections by the best rank any of their records
achieved in the seed, then document order within a section. That makes the pool
a genuinely ranked list, so rank-aware metrics apply to it without inventing an
ordering the retriever never produced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

# Carried evidence from earlier iterations sorts ahead of newly retrieved
# sections, which is what HiREC does (`pages = relevant_pages + pages`).
CARRIED_RANK = 0

# Fields rendered into the curation and answering prompts.
_RENDER_FIELDS = ("node_id", "citation", "heading", "text")

# Explicit cross-references, as legislation actually writes them.
_REFERENCE_PATTERNS = (
    re.compile(r"\bsections?\s+(\d+[A-Za-z]?)", re.I),
    re.compile(r"\bsubsections?\s*\(\s*(\d+)\s*\)", re.I),
    re.compile(r"\bparagraphs?\s*\(\s*([a-z]{1,2})\s*\)", re.I),
)


@dataclass
class Pool:
    """A pooled candidate set, plus enough provenance to score and debug it."""

    records: list[dict]
    seed_node_ids: list[str] = field(default_factory=list)
    section_ids: list[str] = field(default_factory=list)
    section_rank: dict[str, int] = field(default_factory=dict)
    truncated: bool = False
    dropped_section_ids: list[str] = field(default_factory=list)
    char_count: int = 0

    @property
    def node_ids(self) -> list[str]:
        return [r["node_id"] for r in self.records]

    def by_id(self) -> dict[str, dict]:
        return {r["node_id"]: r for r in self.records}


# --------------------------------------------------------------------------- #
# sizing
# --------------------------------------------------------------------------- #

def record_chars(record: dict) -> int:
    """Roughly what one record costs in a prompt, counting what is rendered."""
    return sum(len(str(record.get(k) or "")) for k in _RENDER_FIELDS)


def pool_order(records: Sequence[dict], section_rank: dict[str, int]) -> list[dict]:
    """Sections by best seed rank, then document order within the section."""
    return sorted(
        records,
        key=lambda r: (section_rank.get(r.get("section_id"), 10**6),
                       r.get("ordinal", 0),
                       r["node_id"]),
    )


# --------------------------------------------------------------------------- #
# pooling
# --------------------------------------------------------------------------- #

def section_pool(index, hits: Sequence[dict], *, max_records: int,
                 max_chars: int) -> Pool:
    """Expand BM25 hits to their whole sections, ordered and size-bounded.

    Truncation drops whole sections from the tail of the ranking, never part of
    one. A half-present section would make the sibling rule in the curation
    prompt a lie -- the prompt promises that where a section appears, all of its
    provisions appear with it.
    """
    seed_node_ids = [h["node_id"] for h in hits]
    section_ids = index.section_ids_for(seed_node_ids)
    if not section_ids:
        return Pool(records=[], seed_node_ids=seed_node_ids)

    section_rank = {sid: rank for rank, sid in enumerate(section_ids, start=1)}
    records = index.subtrees(section_ids)

    grouped: dict[str, list[dict]] = {}
    for record in records:
        grouped.setdefault(record["section_id"], []).append(record)

    kept: list[dict] = []
    kept_sections: list[str] = []
    dropped: list[str] = []
    total_chars = 0
    for section_id in sorted(section_ids, key=lambda s: section_rank[s]):
        block = grouped.get(section_id, [])
        block_chars = sum(record_chars(r) for r in block)
        if kept and (len(kept) + len(block) > max_records
                     or total_chars + block_chars > max_chars):
            dropped.append(section_id)
            continue
        kept.extend(block)
        kept_sections.append(section_id)
        total_chars += block_chars

    return Pool(
        records=pool_order(kept, section_rank),
        seed_node_ids=seed_node_ids,
        section_ids=kept_sections,
        section_rank={s: section_rank[s] for s in kept_sections},
        truncated=bool(dropped),
        dropped_section_ids=dropped,
        char_count=total_chars,
    )


def carried_pool(records: Sequence[dict]) -> Pool:
    """A pool holding evidence retained from earlier iterations.

    Every section is given CARRIED_RANK so retained evidence sorts ahead of
    anything newly retrieved, matching HiREC's `relevant_pages + pages`.
    """
    section_ids = list(dict.fromkeys(r.get("section_id") for r in records))
    rank = {sid: CARRIED_RANK for sid in section_ids}
    return Pool(
        records=pool_order(records, rank),
        section_ids=[s for s in section_ids if s is not None],
        section_rank={s: CARRIED_RANK for s in section_ids if s is not None},
        char_count=sum(record_chars(r) for r in records),
    )


def merge_pools(previous: Pool, new: Pool, *, max_records: int,
                max_chars: int) -> Pool:
    """Retained evidence first, then the new pool, deduplicated by node_id.

    Retained evidence is never dropped by truncation: it has already been judged
    relevant, so evicting it to make room for a fresh candidate would lose
    ground the pipeline has already gained.
    """
    section_rank = dict(previous.section_rank)
    for section_id, rank in new.section_rank.items():
        section_rank.setdefault(section_id, rank)

    carried_ids = {r["node_id"] for r in previous.records}
    seen = set()
    kept: list[dict] = []
    total_chars = 0
    truncated = new.truncated
    dropped = list(new.dropped_section_ids)

    for record in list(previous.records) + list(new.records):
        node_id = record["node_id"]
        if node_id in seen:
            continue
        carried = node_id in carried_ids
        chars = record_chars(record)
        if not carried and kept and (len(kept) + 1 > max_records
                                    or total_chars + chars > max_chars):
            truncated = True
            section_id = record.get("section_id")
            if section_id and section_id not in dropped:
                dropped.append(section_id)
            continue
        seen.add(node_id)
        kept.append(record)
        total_chars += chars

    return Pool(
        records=pool_order(kept, section_rank),
        seed_node_ids=list(new.seed_node_ids),
        section_ids=list(dict.fromkeys(
            r.get("section_id") for r in kept if r.get("section_id"))),
        section_rank=section_rank,
        truncated=truncated,
        dropped_section_ids=dropped,
        char_count=total_chars,
    )


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #

def render_pool(pool: Pool) -> str:
    """The pool as prompt text, grouped by section.

    Grouping is what makes the sibling rule legible: the model can see that a
    section's paragraphs are all present, so declining to select one is a
    judgement rather than an oversight.
    """
    blocks: list[str] = []
    current_section = object()
    for record in pool.records:
        if record.get("section_id") != current_section:
            current_section = record.get("section_id")
            blocks.append(f"### Section group: {current_section}")
        heading = record.get("heading") or "(no heading)"
        blocks.append(
            f"node_id: {record['node_id']}\n"
            f"citation: {record.get('citation') or ''}\n"
            f"node_type: {record.get('node_type') or ''}\n"
            f"heading: {heading}\n"
            f"text: {record.get('text') or ''}"
        )
    return "\n\n".join(blocks)


def render_acts(acts: Sequence[dict]) -> str:
    """The Act list for the act-selection prompt."""
    return "\n\n".join(
        f"act_id: {a['act_id']}\n"
        f"title: {a.get('act_title') or ''}\n"
        f"long_title: {a.get('long_title') or ''}\n"
        f"provisions: {a.get('record_count')}"
        for a in acts
    )


# --------------------------------------------------------------------------- #
# deterministic cross-reference check
# --------------------------------------------------------------------------- #

def unresolved_references(selected: Sequence[dict], pool: Pool) -> list[str]:
    """Provisions the selected text points at that the pool does not contain.

    Deliberately not part of the default pipeline. It is not HiREC -- it exploits
    a fact about legislation rather than about documents, namely that statutes
    cross-reference each other explicitly and machine-readably. Kept behind a
    flag so the headline calibration finding stays a statement about the model's
    own judgement.

    Only section references are resolved. A bare "subsection (2)" or
    "paragraph (b)" is relative to the provision doing the referring, and
    resolving those correctly needs the parent chain, not a regex; they are
    reported by their text so a human can look, but never treated as absent.
    """
    present = set(pool.node_ids)
    findings: list[str] = []
    for record in selected:
        act_id = record.get("act_id")
        text = record.get("text") or ""
        for match in _REFERENCE_PATTERNS[0].finditer(text):
            number = match.group(1).lower()
            target = f"{act_id}/section-{number}"
            if target not in present:
                findings.append(
                    f"section {match.group(1)} of the same Act, referred to by "
                    f"{record['node_id']} (expected {target})")
    return list(dict.fromkeys(findings))
