"""Build the frozen structured statutory corpus for statutory-qa-v1.

Input: the finalized structured statute JSON under
data/legal-sources/library/finalized/<act-dir>/*.json. One base (consolidated)
edition is kept per directory, preferring consolidated-2024 > consolidated >
original_or_unconfirmed_consolidation > original, exactly as
experiments/koblex-inspired-retrieval/build_statute_corpus.py does. Amending
Acts in the same directories are kept as separate documents of kind
"amendment" so that `amends` edges have a source node.

Output, under data/evaluvation/statutory-qa-v1/corpus/:

  acts.jsonl        one row per document (principal enactment or amending Act)
  sections.jsonl    one row per section: the retrieval and scoring unit
  provisions.jsonl  one row per text-bearing node (section, subsection, ...)
  edges.jsonl       typed section-to-section edges:
                    defines | excepts | qualifies | amends | cross_references |
                    procedurally_requires | parent_of
  manifest.json     counts, per-file sha256 and a corpus fingerprint

Deterministic: no LLM, no network; byte-identical output for unchanged input.

    uv run python scripts/statutory-qa/build_corpus.py
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402

EDITION_PREFERENCE = ["consolidated-2024", "consolidated",
                      "original_or_unconfirmed_consolidation", "original"]
CONTAINER_TYPES = {"part", "crossheading", "subheading"}
TEXT_TYPES = {"section", "subsection", "paragraph", "subparagraph", "proviso",
              "definition", "item", "closing_text", "text"}
REPEAL_STUB_RE = re.compile(r"^(?:repealed|omitted|deleted)\b", re.I)

# Cue words that type a cross-reference by the wording around it.
CUES = [
    ("defines", re.compile(r"(within the meaning of|as defined in|has the same meaning|have the same meaning|meaning assigned|definition)", re.I)),
    ("excepts", re.compile(r"(notwithstanding|except|save as|unless otherwise|shall not apply|does not apply|other than)", re.I)),
    ("qualifies", re.compile(r"(subject to|in accordance with the provisions of|without prejudice)", re.I)),
    ("procedurally_requires", re.compile(r"(in the manner|as provided|prescribed|in accordance with|under section|under sub-?section|by virtue of|pursuant to|as required by|specified in|referred to in)", re.I)),
]


def norm_title(t: str) -> str:
    t = C.normalize_ws(t).casefold()
    t = re.sub(r"\(.*?\)", " ", t)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\b(no|of|the|and|act|ordinance|law|chapter|cap)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def edition_kind(doc: dict) -> str:
    return ((doc.get("edition") or {}).get("kind") or "").strip()


def edition_rank(kind: str) -> int:
    return EDITION_PREFERENCE.index(kind) if kind in EDITION_PREFERENCE else len(EDITION_PREFERENCE)


def children_of(n: dict) -> list[dict]:
    kids = n.get("children")
    return [k for k in kids if isinstance(k, dict)] if isinstance(kids, list) else []


def own_text(n: dict) -> str:
    return C.normalize_ws(n.get("text") or "")


def subtree_text(n: dict) -> str:
    parts = []
    t = own_text(n)
    if t:
        label = node_inline_label(n)
        parts.append(f"{label} {t}".strip() if label else t)
    for k in children_of(n):
        parts.append(subtree_text(k))
    return C.normalize_ws(" ".join(p for p in parts if p))


def node_inline_label(n: dict) -> str:
    t = n.get("type")
    num = (n.get("number") or "").strip()
    if t in ("subsection", "paragraph", "subparagraph", "item") and num:
        return f"({num})"
    if t == "proviso":
        return "Provided that" if not own_text(n).lower().startswith("provided") else ""
    return ""


def has_substantive_descendant(n: dict) -> bool:
    return any(own_text(k) or has_substantive_descendant(k) for k in children_of(n))


def is_repealed_stub(n: dict) -> bool:
    if has_substantive_descendant(n):
        return False
    s = own_text(n).strip("()[]*—- ").strip()
    return bool(s) and len(s) <= 120 and bool(REPEAL_STUB_RE.match(s))


def select_documents() -> tuple[list[tuple[Path, dict, str]], list[dict]]:
    """[(path, doc, kind)], skipped. kind is 'principal' or 'amendment'."""
    kept, skipped = [], []
    by_dir: dict[str, list[tuple[Path, dict]]] = collections.defaultdict(list)
    for path in sorted(C.FINALIZED_DIR.glob("*/*.json"), key=lambda p: p.as_posix()):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            skipped.append({"file": C.rel(path), "reason": f"parse failure: {exc}"})
            continue
        by_dir[path.parent.name].append((path, doc))
    for dirname in sorted(by_dir):
        entries = by_dir[dirname]
        bases = [(p, d) for p, d in entries if d.get("source_id")]
        amenders = [(p, d) for p, d in entries if not d.get("source_id")]
        if bases:
            bases.sort(key=lambda it: (edition_rank(edition_kind(it[1])), it[0].name))
            kept.append((bases[0][0], bases[0][1], "principal"))
            for p, d in bases[1:]:
                skipped.append({"file": C.rel(p), "reason": f"superseded edition (kept {edition_kind(bases[0][1])!r})"})
        else:
            skipped.append({"file": dirname, "reason": "directory has no base statute"})
        for p, d in sorted(amenders, key=lambda it: it[0].name):
            if d.get("body"):
                kept.append((p, d, "amendment"))
            else:
                skipped.append({"file": C.rel(p), "reason": "amending Act without body text"})
    return kept, skipped


def act_id_of(doc: dict, path: Path, kind: str) -> str:
    cit = doc.get("citation") or {}
    if cit.get("number") is not None and cit.get("year") is not None:
        return f"{cit['number']}-{cit['year']}"
    m = re.match(r"(\d+-\d{4})", path.name)
    return m.group(1) if m else path.stem


def year_of(ev: dict) -> int | None:
    for key in ("amending_year",):
        if ev.get(key):
            try:
                return int(ev[key])
            except (TypeError, ValueError):
                pass
    for key in ("instrument", "amending_act", "verbatim"):
        v = ev.get(key)
        if isinstance(v, str):
            m = re.search(r"(1[89]\d\d|20\d\d)", v)
            if m:
                return int(m.group(1))
    return None


def instrument_of(ev: dict) -> str | None:
    inst = ev.get("instrument")
    if isinstance(inst, str) and re.match(r"^\d+-\d{4}$", inst):
        return inst
    no, yr = ev.get("amending_act_no"), ev.get("amending_year")
    if no and yr:
        return f"{no}-{yr}"
    v = ev.get("amending_act") or ev.get("verbatim") or ""
    m = re.search(r"(?:No\.?\s*)?(\d+)\s+of\s+(\d{4})", str(v))
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


class Builder:
    def __init__(self) -> None:
        self.acts: list[dict] = []
        self.sections: list[dict] = []
        self.provisions: list[dict] = []
        self.edges: list[dict] = []
        self.title_index: dict[str, str] = {}
        self.section_lookup: dict[tuple[str, str], str] = {}
        self.pending_xrefs: list[dict] = []
        self.pending_amend_targets: list[dict] = []
        self.definitions: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)

    # ----------------------------------------------------------------- docs
    def add_document(self, path: Path, doc: dict, kind: str) -> None:
        act_id = act_id_of(doc, path, kind)
        cit = doc.get("citation") or {}
        title = C.normalize_ws(doc.get("title") or "")
        amends = doc.get("amends") or {}
        amends_id = None
        if kind == "amendment" and amends.get("number") and amends.get("year"):
            amends_id = f"{amends['number']}-{amends['year']}"
        act = {
            "act_id": act_id,
            "kind": kind,
            "title": title,
            "long_title": C.normalize_ws(doc.get("long_title") or ""),
            "instrument_type": cit.get("type"),
            "number": cit.get("number"),
            "year": cit.get("year"),
            "label": f"{title} No. {cit.get('number')} of {cit.get('year')}" if cit.get("number") else title,
            "source_id": doc.get("source_id"),
            "amends_act_id": amends_id,
            "amendments_folded_in": [f"{a.get('number')}-{a.get('year')}" for a in (doc.get("amendments") or []) if a.get("number") and a.get("year")],
            "edition_kind": edition_kind(doc),
            "edition_publisher": (doc.get("edition") or {}).get("publisher"),
            "source_file": C.rel(path),
            "source_sha256": C.sha256_file(path),
            "verification_status": doc.get("verification_status") or "unverified",
            "n_sections": 0,
            "n_provisions": 0,
        }
        self.acts.append(act)
        if kind == "principal":
            self.title_index[norm_title(title)] = act_id
        else:
            self.title_index.setdefault(norm_title(title), act_id)
        if kind == "amendment" and amends.get("title"):
            self.title_index.setdefault(norm_title(amends["title"]) + " amendment", act_id)

        part_heading = ""
        for node in doc.get("body") or []:
            if not isinstance(node, dict):
                continue
            self._walk_top(node, act, part_heading, doc)
        for sch in doc.get("schedules") or []:
            if isinstance(sch, dict):
                self._walk_top(sch, act, "Schedule", doc, schedule=True)

    def _walk_top(self, node: dict, act: dict, part_heading: str, doc: dict, schedule: bool = False) -> None:
        t = node.get("type")
        if t in CONTAINER_TYPES or (t is None and children_of(node) and not own_text(node)):
            heading = C.normalize_ws(node.get("heading") or "")
            number = (node.get("number") or "").strip()
            label = heading
            if t == "part":
                label = f"Part {number} {heading}".strip()
            for k in children_of(node):
                self._walk_top(k, act, label or part_heading, doc)
            return
        if t == "section" or schedule or (t is None):
            self._emit_section(node, act, part_heading, schedule=schedule)
            return
        # Stray text-bearing node at the top level: treat as its own section.
        self._emit_section(node, act, part_heading, schedule=schedule)

    def _emit_section(self, node: dict, act: dict, part_heading: str, schedule: bool) -> None:
        act_id = act["act_id"]
        number = (node.get("number") or "").strip()
        if not number:
            number = f"x{act['n_sections'] + 1}"
        base = f"{act_id}/s{re.sub(r'[^0-9A-Za-z]+', '-', number)}"
        section_id = base
        k = 2
        existing = {s["section_id"] for s in self.sections if s["act_id"] == act_id}
        while section_id in existing:
            section_id = f"{base}-{k}"
            k += 1
        if is_repealed_stub(node):
            return
        body = subtree_text(node)
        if not body:
            return
        heading = C.normalize_ws(node.get("heading") or "")
        # provisions
        provs: list[dict] = []
        self._emit_provisions(node, act, section_id, [], provs)
        # definitions in this section
        terms = [C.normalize_ws(p["term"]) for p in provs if p.get("term")]
        # cross references (own + descendants)
        xrefs = self._collect_xrefs(node)
        xref_text = " ".join(C.normalize_ws(x.get("verbatim") or "") for x in xrefs)
        # amendments
        events = self._collect_events(node)
        ev_rows = []
        inserted_year = None
        latest_change_year = None
        for ev in events:
            op = (ev.get("operation") or "unknown").lower()
            yr = year_of(ev)
            ev_rows.append({"operation": op, "instrument": instrument_of(ev), "year": yr,
                            "amending_section": ev.get("amending_section")})
            if yr:
                latest_change_year = max(latest_change_year or 0, yr)
                if op.startswith("insert") and node_level_event(ev, node):
                    inserted_year = yr if inserted_year is None else min(inserted_year, yr)
        in_force_from_year = inserted_year or act.get("year")
        citation = f"{act['title']}, s {number}" if not schedule else f"{act['title']}, {heading or number}"
        row = {
            "section_id": section_id,
            "act_id": act_id,
            "act_kind": act["kind"],
            "act_title": act["title"],
            "act_label": act["label"],
            "act_year": act.get("year"),
            "part_heading": part_heading,
            "section_number": number,
            "heading": heading,
            "citation": citation,
            "body": body,
            "n_chars": len(body),
            "provision_ids": [p["node_id"] for p in provs],
            "n_provisions": len(provs),
            "defined_terms": terms,
            "xref_text": C.normalize_ws(xref_text),
            "n_xrefs": len(xrefs),
            "amendment_events": ev_rows,
            "in_force_from_year": in_force_from_year,
            "latest_change_year": latest_change_year,
            "is_schedule": schedule,
            "source_file": act["source_file"],
            "verification_status": "unverified",
        }
        self.sections.append(row)
        self.provisions.extend(provs)
        act["n_sections"] += 1
        act["n_provisions"] += len(provs)
        self.section_lookup[(act_id, number)] = section_id
        for x in xrefs:
            self.pending_xrefs.append({"src": section_id, "act_id": act_id, "xref": x, "context": body})
        for term in terms:
            if len(term) >= 4:
                self.definitions[act_id].append((term, section_id))
        if act["kind"] == "amendment":
            for ev in []:
                pass
        # amendment targets for amending Acts: from doc-level instructions handled later
        self.pending_amend_targets.append({"section_id": section_id, "act": act, "node": node})

    def _emit_provisions(self, node: dict, act: dict, section_id: str, path: list[str], out: list[dict]) -> None:
        t = node.get("type")
        num = (node.get("number") or "").strip()
        term = (node.get("term") or "").strip()
        seg = None
        if t == "section":
            seg = None
        elif t == "definition":
            seg = "def-" + re.sub(r"[^0-9A-Za-z]+", "-", term.lower())[:40] if term else f"def-{len(out) + 1}"
        elif t in TEXT_TYPES:
            seg = f"{t[:3]}-{re.sub(r'[^0-9A-Za-z]+', '-', num) or len(out) + 1}"
        new_path = path + ([seg] if seg else [])
        text = own_text(node)
        if text and not is_repealed_stub(node):
            node_id = section_id + ("/" + "/".join(new_path) if new_path else "")
            base, k = node_id, 2
            existing = {p["node_id"] for p in out}
            while node_id in existing:
                node_id = f"{base}-{k}"
                k += 1
            out.append({
                "node_id": node_id,
                "section_id": section_id,
                "act_id": act["act_id"],
                "node_type": t or "text",
                "number": num,
                "term": term or None,
                "path_label": " ".join(new_path),
                "text": text,
            })
        for k in children_of(node):
            self._emit_provisions(k, act, section_id, new_path, out)

    def _collect_xrefs(self, node: dict) -> list[dict]:
        out = [x for x in (node.get("cross_references") or []) if isinstance(x, dict)]
        for k in children_of(node):
            out.extend(self._collect_xrefs(k))
        return out

    def _collect_events(self, node: dict) -> list[dict]:
        out = [e for e in (node.get("amendment_events") or []) if isinstance(e, dict)]
        for k in children_of(node):
            out.extend(self._collect_events(k))
        return out

    # ----------------------------------------------------------------- edges
    def resolve_edges(self) -> dict[str, int]:
        stats: collections.Counter[str] = collections.Counter()
        seen: set[tuple[str, str, str]] = set()

        def add(src: str, dst: str, rel: str, evidence: str) -> None:
            if src == dst:
                return
            key = (src, dst, rel)
            if key in seen:
                return
            seen.add(key)
            self.edges.append({"src": src, "dst": dst, "relation": rel, "evidence": evidence[:200]})
            stats[rel] += 1

        # cross-references
        for item in self.pending_xrefs:
            x = item["xref"]
            target_doc = C.normalize_ws(x.get("target_document") or "")
            kind = (x.get("kind") or "").lower()
            if kind == "internal" or not target_doc or norm_title(target_doc) == norm_title(self._act_title(item["act_id"])):
                target_act = item["act_id"]
            else:
                target_act = self.title_index.get(norm_title(target_doc))
                if target_act is None:
                    stats["unresolved_external_document"] += 1
                    continue
            tsec = str(x.get("target_section") or "").strip()
            if not tsec:
                # whole-document reference: link to the first section of that Act
                first = next((s["section_id"] for s in self.sections if s["act_id"] == target_act), None)
                if first and target_act != item["act_id"]:
                    add(item["src"], first, "cross_references", x.get("verbatim") or "")
                else:
                    stats["unresolved_no_section"] += 1
                continue
            dst = self.section_lookup.get((target_act, tsec))
            if dst is None:
                m = re.match(r"(\d+[A-Z]*)", tsec)
                dst = self.section_lookup.get((target_act, m.group(1))) if m else None
            if dst is None:
                stats["unresolved_section"] += 1
                continue
            rel = self._type_xref(x.get("verbatim") or "", item["context"])
            add(item["src"], dst, rel, x.get("verbatim") or "")

        # definitions: a section that uses a defined term links to the defining section
        sec_by_act: dict[str, list[dict]] = collections.defaultdict(list)
        for s in self.sections:
            sec_by_act[s["act_id"]].append(s)
        for act_id, defs in self.definitions.items():
            for term, def_sec in defs:
                pat = re.compile(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", re.I)
                for s in sec_by_act[act_id]:
                    if s["section_id"] != def_sec and pat.search(s["body"]):
                        add(s["section_id"], def_sec, "defines", f'term "{term}"')

        # amendments: amending-Act section -> principal section it amends
        for act in self.acts:
            if act["kind"] != "amendment" or not act["amends_act_id"]:
                continue
            for s in self.sections:
                if s["act_id"] != act["act_id"]:
                    continue
                for m in re.finditer(r"[Ss]ection\s+(\d+[A-Z]*)\s+of\s+the\s+principal\s+enactment", s["body"]):
                    dst = self.section_lookup.get((act["amends_act_id"], m.group(1)))
                    if dst:
                        add(s["section_id"], dst, "amends", m.group(0))
                for m in re.finditer(r"amended\s+in\s+section\s+(\d+[A-Z]*)", s["body"]):
                    dst = self.section_lookup.get((act["amends_act_id"], m.group(1)))
                    if dst:
                        add(s["section_id"], dst, "amends", m.group(0))
        # principal section -> amending instrument section (reverse of amends), from amendment_events
        amend_secs: dict[str, list[dict]] = collections.defaultdict(list)
        for s in self.sections:
            if s["act_kind"] == "amendment":
                amend_secs[s["act_id"]].append(s)
        for s in self.sections:
            for ev in s["amendment_events"]:
                inst = ev.get("instrument")
                if inst and inst in amend_secs:
                    asec = ev.get("amending_section")
                    dst = self.section_lookup.get((inst, str(asec))) if asec else None
                    if dst:
                        add(dst, s["section_id"], "amends", f"{inst} s.{asec} {ev['operation']}")
        return dict(stats)

    def _act_title(self, act_id: str) -> str:
        for a in self.acts:
            if a["act_id"] == act_id:
                return a["title"]
        return ""

    @staticmethod
    def _type_xref(verbatim: str, context: str) -> str:
        v = C.normalize_ws(verbatim)
        idx = context.find(v) if v else -1
        window = context[max(0, idx - 90): idx + len(v) + 40] if idx >= 0 else v
        for rel, pat in CUES:
            if pat.search(window):
                return rel
        return "cross_references"


def node_level_event(ev: dict, node: dict) -> bool:
    """True when an insert event belongs to the section node itself rather than
    to a descendant (a new subsection inserted into an old section does not
    make the section new)."""
    return ev in (node.get("amendment_events") or [])


def main() -> int:
    kept, skipped = select_documents()
    b = Builder()
    for path, doc, kind in kept:
        b.add_document(path, doc, kind)
    edge_stats = b.resolve_edges()

    # parent_of edges are implicit (section -> provisions); record counts only.
    C.CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    C.write_jsonl(C.CORPUS_DIR / "acts.jsonl", b.acts)
    C.write_jsonl(C.CORPUS_DIR / "sections.jsonl", b.sections)
    C.write_jsonl(C.CORPUS_DIR / "provisions.jsonl", b.provisions)
    C.write_jsonl(C.CORPUS_DIR / "edges.jsonl", sorted(b.edges, key=lambda e: (e["src"], e["relation"], e["dst"])))

    fp_src = "\n".join(f"{a['source_file']} {a['source_sha256']}" for a in b.acts)
    fingerprint = C.sha256_text(fp_src)
    manifest = {
        "status": "unverified",
        "generated": C.utc_now(),
        "corpus_fingerprint": fingerprint,
        "documents": {
            "principal_enactments": sum(a["kind"] == "principal" for a in b.acts),
            "amending_acts": sum(a["kind"] == "amendment" for a in b.acts),
            "total": len(b.acts),
        },
        "sections": len(b.sections),
        "sections_in_principal_enactments": sum(s["act_kind"] == "principal" for s in b.sections),
        "provisions": len(b.provisions),
        "edges": collections.Counter(e["relation"] for e in b.edges),
        "edge_resolution": edge_stats,
        "definitions": sum(len(v) for v in b.definitions.values()),
        "sections_with_amendment_events": sum(bool(s["amendment_events"]) for s in b.sections),
        "sections_inserted_after_enactment": sum(1 for s in b.sections if s["in_force_from_year"] and s["act_year"] and s["in_force_from_year"] > s["act_year"]),
        "edition_kinds": collections.Counter(a["edition_kind"] for a in b.acts),
        "skipped": skipped,
        "files": {C.rel(C.CORPUS_DIR / n): C.sha256_file(C.CORPUS_DIR / n) for n in ("acts.jsonl", "sections.jsonl", "provisions.jsonl", "edges.jsonl")},
    }
    C.write_json(C.CORPUS_DIR / "manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("skipped", "files")}, indent=1, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
