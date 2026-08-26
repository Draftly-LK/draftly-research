"""Build statute.jsonl -- a leaf/provision-level retrieval corpus over the
finalized structured statute JSON, preserving the statutory hierarchy.

Rules applied, in order:

  1. Edition selection. Each finalized directory may hold several editions plus
     the amending Acts that were folded into them. Files carrying a source_id
     are base statutes; one is kept per directory, preferring
     consolidated-2024 > consolidated > original_or_unconfirmed_consolidation
     > original. Files without a source_id are amending Acts and are skipped --
     their changes already appear in the consolidation.
  2. Flattening. Recursion follows the "children" key only; cross_references and
     amendment_events are metadata, not structure. Heading-only containers
     (part / crossheading / subheading) emit no record but contribute to the
     hierarchy, search_text and parent chain of their descendants. A node emits
     a record when it has its own non-empty text, so a section with both a
     chapeau and children yields the chapeau plus each child, and descendant
     text is never copied upward.
  3. Repealed stubs. A node whose own text is nothing but a repeal/omission
     marker, and which has no substantive descendant, is excluded. Operative
     repealing provisions are kept -- they are live rules.
  4. text is the exact source text field, through the repo's existing
     normalize_text (whitespace only). Never raw_text, never rewritten.

No temporal/version handling: effective_from and effective_to are always null.
No LLM, no network. Deterministic -- byte-identical output for unchanged inputs.

Usage:
    uv run python experiments/koblex-inspired-retrieval/build_statute_corpus.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_processed_store import normalize_text, slug  # noqa: E402

FINALIZED = ROOT / "data" / "legal-sources" / "library" / "finalized"
OUT_DIR = Path(__file__).resolve().parent / "data"
STATUTE_JSONL = OUT_DIR / "statute.jsonl"
REPORT_MD = OUT_DIR / "generation-report.md"

REGEN_COMMANDS = [
    "uv run python experiments/koblex-inspired-retrieval/build_statute_corpus.py",
    "uv run pytest tests/test_koblex_statute_corpus.py -q",
]

# Exact output contract. Anything not listed cannot reach statute.jsonl.
FIELDS = [
    "node_id", "act_id", "act_title", "act_number", "act_year", "node_type",
    "citation", "provision_label", "heading", "text", "parent_id", "hierarchy",
    "search_text", "source_file", "source_url", "effective_from", "effective_to",
    "section_id", "verification_status", "edition_kind",
]

CONTAINER_TYPES = {"part", "crossheading", "subheading"}
TEXT_TYPES = {
    "section", "subsection", "paragraph", "subparagraph", "proviso",
    "definition", "item", "closing_text", "text",
}
WRAPPER_TYPES = {"inserted_provision", "substituted_provision"}
SYNTHETIC_TYPES = {"schedule", "schedule_item"}
KNOWN_TYPES = CONTAINER_TYPES | TEXT_TYPES | WRAPPER_TYPES | SYNTHETIC_TYPES

EDITION_PREFERENCE = [
    "consolidated-2024",
    "consolidated",
    "original_or_unconfirmed_consolidation",
    "original",
]
CONSOLIDATED_KINDS = {"consolidated-2024", "consolidated"}

REPEAL_STUB_RE = re.compile(r"^(?:repealed|omitted|deleted)\b", re.I)
REPEAL_STUB_MAX_CHARS = 120


# --------------------------------------------------------------------------- #
# edition selection
# --------------------------------------------------------------------------- #

def edition_kind(doc: dict) -> str:
    """edition.kind as published. One source value is free text with spaces."""
    return ((doc.get("edition") or {}).get("kind") or "").strip()


def edition_rank(kind: str) -> int:
    try:
        return EDITION_PREFERENCE.index(kind)
    except ValueError:
        return len(EDITION_PREFERENCE)


def select_editions(finalized: Path):
    """One base statute per directory. Returns (kept, skipped, problems)."""
    kept: list[tuple[Path, dict]] = []
    skipped: list[dict] = []
    problems: list[dict] = []
    by_dir: dict[str, list[tuple[Path, dict]]] = defaultdict(list)

    for path in sorted(finalized.glob("*/*.json"), key=lambda p: p.as_posix()):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append({"file": path.name, "detail": f"parse failure: {exc}"})
            continue
        by_dir[path.parent.name].append((path, doc))

    for dirname in sorted(by_dir):
        entries = by_dir[dirname]
        bases = [(p, d) for p, d in entries if d.get("source_id")]
        amenders = [(p, d) for p, d in entries if not d.get("source_id")]

        for path, doc in amenders:
            skipped.append({
                "file": path.name,
                "edition_kind": edition_kind(doc),
                "reason": "amending Act (no source_id); already folded into the consolidation",
            })

        if not bases:
            problems.append({"file": dirname, "detail": "directory has no base statute"})
            continue

        bases.sort(key=lambda item: (edition_rank(edition_kind(item[1])), item[0].name))
        winner_path, winner_doc = bases[0]
        kept.append((winner_path, winner_doc))
        for path, doc in bases[1:]:
            skipped.append({
                "file": path.name,
                "edition_kind": edition_kind(doc),
                "reason": f"superseded edition (kept {edition_kind(winner_doc)!r})",
            })

    return kept, skipped, problems


# --------------------------------------------------------------------------- #
# labels
# --------------------------------------------------------------------------- #

def act_identity(doc: dict) -> tuple[str, object, object]:
    citation = doc.get("citation") or {}
    number, year = citation.get("number"), citation.get("year")
    if number is None or year is None:
        return "", None, None
    return f"{number}-{year}", number, year


def act_label(doc: dict) -> str:
    citation = doc.get("citation") or {}
    title = (doc.get("title") or "").strip()
    number, year = citation.get("number"), citation.get("year")
    if number is None or year is None:
        return title
    return f"{title} No. {number} of {year}"


def container_label(node: dict) -> str:
    number = (node.get("number") or "").strip()
    heading = (node.get("heading") or "").strip()
    if node.get("type") == "part":
        if number and heading:
            return f"Part {number} — {heading}"
        return f"Part {number}" if number else heading
    return heading


_PRETTY = {
    "subsection": "Subsection",
    "paragraph": "Paragraph",
    "subparagraph": "Subparagraph",
}


def node_labels(node: dict, ordinal: int) -> tuple[str, str, str]:
    """(hierarchy_label, provision_suffix, id_segment) for a text-bearing node."""
    ntype = node.get("type") or "node"
    number = (node.get("number") or "").strip()
    term = (node.get("term") or "").strip()

    if ntype == "section":
        return f"Section {number}", number, f"section-{slug(number, str(ordinal))}"
    if ntype in _PRETTY:
        return (f"{_PRETTY[ntype]} ({number})", f"({number})",
                f"{ntype}-{slug(number, str(ordinal))}")
    if ntype == "item":
        return f"Item {number}", f", item {number}", f"item-{slug(number, str(ordinal))}"
    if ntype == "proviso":
        label = f"Proviso {number}".strip()
        suffix = f", proviso {number}" if number else ", proviso"
        return label, suffix, f"proviso-{slug(number, str(ordinal))}"
    if ntype == "definition":
        return (f'Definition of "{term}"', f', definition of "{term}"',
                f"definition-{slug(term, str(ordinal))}")
    if ntype == "closing_text":
        return "Closing text", "", f"closing_text-{ordinal}"
    if ntype == "text":
        return "Text", "", f"text-{ordinal}"
    return ntype, "", f"{ntype}-{ordinal}"


# --------------------------------------------------------------------------- #
# tree helpers
# --------------------------------------------------------------------------- #

def children_of(node: dict) -> list[dict]:
    kids = node.get("children")
    return [k for k in kids if isinstance(k, dict)] if isinstance(kids, list) else []


def own_text(node: dict) -> str:
    return normalize_text(node.get("text") or "")


def has_substantive_descendant(node: dict) -> bool:
    for child in children_of(node):
        if own_text(child) or has_substantive_descendant(child):
            return True
    return False


def is_repealed_stub(text: str, node: dict) -> bool:
    if has_substantive_descendant(node):
        return False
    stripped = text.strip().strip("()[]*—- ").strip()
    if not stripped or len(stripped) > REPEAL_STUB_MAX_CHARS:
        return False
    return bool(REPEAL_STUB_RE.match(stripped))


# --------------------------------------------------------------------------- #
# record construction
# --------------------------------------------------------------------------- #

class ActBuilder:
    """Emits records for one statute, tracking ids and per-act counters."""

    def __init__(self, path: Path, doc: dict, stats: "Stats"):
        self.path = path
        self.doc = doc
        self.stats = stats
        self.act_id, self.act_number, self.act_year = act_identity(doc)
        self.act_title = (doc.get("title") or "").strip()
        self.act_label = act_label(doc)
        self.long_title = (doc.get("long_title") or "").strip()
        self.edition_kind = edition_kind(doc)
        self.source_url = (doc.get("edition") or {}).get("source_url") or None
        self.verification_status = doc.get("verification_status") or None
        self.records: list[dict] = []
        self.seen_ids: set[str] = set()

    # -- ids ---------------------------------------------------------------- #

    def unique_id(self, candidate: str) -> str:
        if candidate not in self.seen_ids:
            self.seen_ids.add(candidate)
            return candidate
        self.stats.node_id_collisions.append(candidate)
        suffix = 2
        while f"{candidate}-{suffix}" in self.seen_ids:
            suffix += 1
        resolved = f"{candidate}-{suffix}"
        self.seen_ids.add(resolved)
        return resolved

    # -- body --------------------------------------------------------------- #

    def build(self) -> list[dict]:
        self.walk(
            self.doc.get("body") or [],
            containers=[],
            id_parts=[],
            hierarchy=[{"type": "act", "label": self.act_label}],
            search_parts=[p for p in (self.act_label, self.long_title) if p],
            provision_label="",
            section_id=None,
            section_heading=None,
            parent_id=self.act_id,
        )
        self.build_schedules()
        return self.records

    def walk(self, nodes, containers, id_parts, hierarchy, search_parts,
             provision_label, section_id, section_heading, parent_id):
        type_ordinals: Counter = Counter()

        for node in nodes:
            ntype = node.get("type")
            type_ordinals[ntype] += 1
            ordinal = type_ordinals[ntype]

            if ntype in WRAPPER_TYPES:
                inner = node.get("provision")
                self.stats.wrappers_seen += 1
                if isinstance(inner, dict) and (own_text(inner) or children_of(inner)):
                    self.stats.wrappers_unwrapped += 1
                    self.walk([inner], containers, id_parts, hierarchy, search_parts,
                              provision_label, section_id, section_heading, parent_id)
                else:
                    self.stats.wrappers_skipped += 1
                continue

            if ntype in CONTAINER_TYPES:
                label = container_label(node)
                self.walk(
                    children_of(node),
                    containers=containers + [(ntype, label)],
                    id_parts=id_parts,
                    hierarchy=hierarchy + [{"type": ntype, "label": label}],
                    search_parts=search_parts + ([label] if label else []),
                    provision_label=provision_label,
                    section_id=section_id,
                    section_heading=section_heading,
                    parent_id=parent_id,
                )
                continue

            if ntype not in TEXT_TYPES:
                self.stats.unknown_types[str(ntype)] += 1
                continue

            hier_label, suffix, id_segment = node_labels(node, ordinal)
            node_provision = (
                suffix if ntype == "section" else f"{provision_label}{suffix}"
            )
            heading = (node.get("heading") or "").strip()
            if ntype == "section":
                node_section_heading = heading or None
            else:
                node_section_heading = section_heading

            node_id_candidate = "/".join([self.act_id] + id_parts + [id_segment])
            text = own_text(node)
            emitted_id = None

            if text and is_repealed_stub(text, node):
                self.stats.repealed_stubs.append({
                    "act": self.act_title,
                    "node": node_id_candidate,
                    "text": text,
                })
            elif text:
                node_id = self.unique_id(node_id_candidate)
                emitted_id = node_id
                search_label = (
                    f"{hier_label} — {heading}" if (ntype == "section" and heading)
                    else hier_label
                )
                record_section_id = node_id if ntype == "section" else section_id
                self.records.append(self.make_record(
                    node_id=node_id,
                    node_type=ntype,
                    provision_label=node_provision,
                    heading=heading or node_section_heading,
                    text=text,
                    parent_id=parent_id,
                    hierarchy=hierarchy + [{"type": ntype, "label": hier_label}],
                    search_parts=search_parts + [search_label, text],
                    section_id=record_section_id,
                ))
            else:
                self.stats.empty_text[str(ntype)] += 1

            child_section_id = section_id
            if ntype == "section":
                child_section_id = emitted_id or node_id_candidate

            self.walk(
                children_of(node),
                containers=containers,
                id_parts=id_parts + [id_segment],
                hierarchy=hierarchy + [{"type": ntype, "label": hier_label}],
                search_parts=search_parts + [
                    f"{hier_label} — {heading}"
                    if (ntype == "section" and heading) else hier_label
                ],
                provision_label=node_provision,
                section_id=child_section_id,
                section_heading=node_section_heading,
                parent_id=emitted_id or parent_id,
            )

    # -- schedules ---------------------------------------------------------- #

    def build_schedules(self) -> None:
        schedules = self.doc.get("schedules")
        if not isinstance(schedules, list):
            return
        for index, schedule in enumerate(schedules, start=1):
            if not isinstance(schedule, dict):
                continue
            citation = (schedule.get("citation") or f"Schedule {index}").strip()
            heading = (schedule.get("heading") or "").strip()
            base_id = self.unique_id(f"{self.act_id}/schedule-{index}")
            hierarchy = [{"type": "act", "label": self.act_label},
                         {"type": "schedule", "label": citation}]
            search_head = [p for p in (self.act_label, self.long_title) if p]
            search_head.append(f"{citation} — {heading}" if heading else citation)

            text = normalize_text(schedule.get("text") or "")
            if text:
                self.records.append(self.make_record(
                    node_id=base_id,
                    node_type="schedule",
                    provision_label=citation,
                    heading=heading or None,
                    text=text,
                    parent_id=self.act_id,
                    hierarchy=hierarchy,
                    search_parts=search_head + [text],
                    section_id=None,
                ))
            else:
                self.stats.empty_text["schedule"] += 1

            items = schedule.get("items")
            if not isinstance(items, list):
                continue
            for item_index, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                item_text = normalize_text(item.get("text") or "")
                if not item_text:
                    self.stats.empty_text["schedule_item"] += 1
                    continue
                number = str(item.get("number") or item_index).strip()
                item_id = self.unique_id(
                    f"{base_id}/item-{slug(number, str(item_index))}")
                label = f"Item {number}"
                self.records.append(self.make_record(
                    node_id=item_id,
                    node_type="schedule_item",
                    provision_label=f"{citation}, item {number}",
                    heading=heading or None,
                    text=item_text,
                    parent_id=base_id if text else self.act_id,
                    hierarchy=hierarchy + [{"type": "schedule_item", "label": label}],
                    search_parts=search_head + [label, item_text],
                    section_id=None,
                ))
                if item.get("rates"):
                    self.stats.schedule_rate_tables += 1

    # -- assembly ----------------------------------------------------------- #

    def make_record(self, *, node_id, node_type, provision_label, heading, text,
                    parent_id, hierarchy, search_parts, section_id) -> dict:
        citation = (
            f"{self.act_title}, {provision_label}"
            if node_type in SYNTHETIC_TYPES
            else f"{self.act_title}, s {provision_label}"
        )
        record = {
            "node_id": node_id,
            "act_id": self.act_id,
            "act_title": self.act_title,
            "act_number": self.act_number,
            "act_year": self.act_year,
            "node_type": node_type,
            "citation": citation,
            "provision_label": provision_label,
            "heading": heading or None,
            "text": text,
            "parent_id": parent_id,
            "hierarchy": hierarchy,
            "search_text": " | ".join(p for p in search_parts if p),
            "source_file": self.path.name,
            "source_url": self.source_url,
            "effective_from": None,
            "effective_to": None,
            "section_id": section_id,
            "verification_status": self.verification_status,
            "edition_kind": self.edition_kind,
        }
        # Allowlist enforcement at the point of construction.
        return {key: record[key] for key in FIELDS}


# --------------------------------------------------------------------------- #
# stats
# --------------------------------------------------------------------------- #

class Stats:
    def __init__(self) -> None:
        self.empty_text: Counter = Counter()
        self.unknown_types: Counter = Counter()
        self.repealed_stubs: list[dict] = []
        self.node_id_collisions: list[str] = []
        self.wrappers_seen = 0
        self.wrappers_unwrapped = 0
        self.wrappers_skipped = 0
        self.schedule_rate_tables = 0


def consolidation_gaps(kept: list[tuple[Path, dict]]) -> list[dict]:
    """Edition-currency concerns worth reporting. Reported, never resolved."""
    gaps: list[dict] = []
    for path, doc in kept:
        title = (doc.get("title") or "").strip()
        kind = edition_kind(doc)
        siblings = sorted(
            p.name for p in path.parent.glob("*.json") if p.name != path.name
        )
        amenders = [
            name for name in siblings
            if not (json.loads((path.parent / name).read_text(encoding="utf-8"))
                    .get("source_id"))
        ]
        if kind not in CONSOLIDATED_KINDS:
            detail = f"edition kind is {kind!r}, not a confirmed consolidation"
            if amenders:
                detail += (f"; {len(amenders)} amending Act(s) present "
                           f"({', '.join(amenders)}) so their changes may be absent")
            gaps.append({"act": title, "detail": detail})
        status = doc.get("verification_status")
        if status and status != "structurally_verified":
            gaps.append({"act": title, "detail": f"verification_status is {status!r}"})
        act_id, _, _ = act_identity(doc)
        prefix = path.parent.name.split("-")[0] + "-" + path.parent.name.split("-")[1]
        if act_id and act_id != prefix:
            gaps.append({
                "act": title,
                "detail": f"act_id {act_id!r} from citation differs from "
                          f"directory prefix {prefix!r}",
            })
    return gaps


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #

def build(finalized: Path = FINALIZED):
    kept, skipped, problems = select_editions(finalized)
    stats = Stats()
    records: list[dict] = []
    for path, doc in kept:
        act_id, _, _ = act_identity(doc)
        if not act_id:
            problems.append({"file": path.name,
                             "detail": "citation has no number/year; cannot form act_id"})
            continue
        records.extend(ActBuilder(path, doc, stats).build())
    gaps = consolidation_gaps(kept)
    return records, {
        "kept": kept,
        "skipped": skipped,
        "problems": problems,
        "stats": stats,
        "gaps": gaps,
    }


def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=False) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_report(records: list[dict], meta: dict, path: Path) -> None:
    stats: Stats = meta["stats"]
    kept = meta["kept"]
    by_type = Counter(r["node_type"] for r in records)
    by_act = Counter(r["act_title"] for r in records)
    text_keys = Counter(re.sub(r"\s+", " ", r["text"]).casefold() for r in records)
    dup_texts = {k: v for k, v in text_keys.items() if v > 1}
    missing_heading = sum(1 for r in records if not r["heading"])

    out: list[str] = []
    add = out.append
    add("# statute.jsonl generation report\n")
    add("Corpus for the KoBLEX-inspired retrieval experiment. Provision-level "
        "records built from the finalized structured statute JSON. Statutory "
        "evidence only -- no generated, parametric or synthetic provisions.\n")

    add("## Counts\n")
    add(f"- Source files inspected: {len(kept) + len(meta['skipped'])}")
    add(f"- Statutes indexed: {len(kept)}")
    add(f"- Records: {len(records)}")
    add(f"- Distinct sections referenced: "
        f"{len({r['section_id'] for r in records if r['section_id']})}")
    add(f"- Records without a heading: {missing_heading}")
    add("- `section_id` is a rollup key, not a foreign key: it names the section "
        "a record belongs to even where that section has no record of its own "
        "(a section whose text lives entirely in its children emits nothing). "
        "Group by it to score at section level.")
    add("- Temporal metadata: none. `effective_from` / `effective_to` are null "
        "on every record; act-level `commencement` is deliberately not "
        "propagated to provisions.\n")

    add("### By node type\n")
    for ntype, count in sorted(by_type.items(), key=lambda kv: (-kv[1], kv[0])):
        add(f"- `{ntype}`: {count}")
    add("")

    add("### By Act\n")
    for title, count in sorted(by_act.items(), key=lambda kv: (-kv[1], kv[0])):
        add(f"- {title}: {count}")
    add("")

    add("## Skipped\n")
    add("### Files\n")
    for entry in meta["skipped"]:
        add(f"- `{entry['file']}` -- {entry['reason']}")
    add("")
    add("### Nodes\n")
    add(f"- Empty own-text (content lives in children): "
        f"{sum(stats.empty_text.values())} "
        f"({', '.join(f'{k} {v}' for k, v in sorted(stats.empty_text.items()))})")
    add(f"- Repealed stubs excluded: {len(stats.repealed_stubs)}")
    for stub in stats.repealed_stubs:
        add(f"  - `{stub['node']}` -- {stub['text']!r}")
    add(f"- `inserted_provision` / `substituted_provision` encountered: "
        f"{stats.wrappers_seen} (unwrapped {stats.wrappers_unwrapped}, "
        f"skipped as empty {stats.wrappers_skipped})")
    if stats.unknown_types:
        add(f"- Unrecognised node types: {dict(stats.unknown_types)}")
    add("")

    add("## Consolidation gaps\n")
    if meta["gaps"]:
        add("Reported, not resolved -- this build does no historical version "
            "reconstruction.\n")
        for gap in meta["gaps"]:
            add(f"- **{gap['act']}** -- {gap['detail']}")
    else:
        add("None detected.")
    add("")

    add("## Problems\n")
    if meta["problems"]:
        for problem in meta["problems"]:
            add(f"- `{problem['file']}` -- {problem['detail']}")
    else:
        add("- No parsing failures.")
    if stats.node_id_collisions:
        add(f"- Duplicate node paths disambiguated: "
            f"{len(stats.node_id_collisions)}. These are source-side labelling "
            "defects, not build artefacts -- sibling provisions carrying the "
            "same label. Both records are kept, the later one suffixed `-2`, so "
            "no provision is silently dropped. Spot-checked examples: "
            "Apartment Ownership s.20C(2) genuinely has two `paragraph (bb)` "
            "siblings with different text; Companies Act s.529(1) has several "
            "definitions collapsed under one `definition:distribution` node, so "
            "its `(a)`/`(b)` paragraphs repeat. Affected paths:")
        for collision in sorted(set(stats.node_id_collisions)):
            add(f"  - `{collision}`")
    else:
        add("- Duplicate node paths: 0")
    add(f"- Duplicate evidence texts: {len(dup_texts)} distinct strings appear "
        f"more than once ({sum(dup_texts.values())} records)")
    if stats.schedule_rate_tables:
        add(f"- Schedule items carrying `rates` tables: "
            f"{stats.schedule_rate_tables}. The band/rupees/cents tables are "
            "structured numeric data and are not flattened into `text`, so rate "
            "lookups will not retrieve them.")
    add("")

    add("## Regeneration\n")
    add("```powershell")
    for command in REGEN_COMMANDS:
        add(command)
    add("```")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    if not FINALIZED.is_dir():
        print(f"missing input directory {FINALIZED}", file=sys.stderr)
        return 1
    records, meta = build(FINALIZED)
    if not records:
        print("no records produced", file=sys.stderr)
        return 1
    write_jsonl(records, STATUTE_JSONL)
    write_report(records, meta, REPORT_MD)
    stats: Stats = meta["stats"]
    print(f"statutes indexed : {len(meta['kept'])}")
    print(f"records          : {len(records)}")
    print(f"files skipped    : {len(meta['skipped'])}")
    print(f"repealed stubs   : {len(stats.repealed_stubs)}")
    print(f"consolidation gaps: {len(meta['gaps'])}")
    print(f"wrote {STATUTE_JSONL.relative_to(ROOT).as_posix()}")
    print(f"wrote {REPORT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
