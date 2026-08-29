"""Layout-aware extraction of the 24 finalized statute JSONs.

The finalized JSONs under ``data/legal-sources/library/finalized/`` store a
recursive ``body`` tree (part -> crossheading -> section -> subsection ->
paragraph -> proviso/definition, not always all levels present). Section
nodes are not always top-level ``body`` entries -- e.g. the Companies Act
nests every section under part/crossheading containers -- so finding them
requires a recursive walk, not a flat scan of ``body``.

Amendment-Act JSONs living inside a principal statute's folder (e.g.
``27-2002-apartment-ownership-amendment.json``) have ``source_id: null`` in
this dataset, which is what actually separates them from the 24 principal
consolidated statutes -- filtering on a present ``source_id`` is simpler and
more robust than matching on filename substrings, so both are used
defensively.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from .config import EXPECTED_STATUTE_COUNT, STATUTE_FILE_OVERRIDES
from .models import LawchainSection
from .paths import FINALIZED_DIR, SOURCE_REGISTRY_CSV

# Preference order when a folder holds more than one principal-statute JSON.
# Verified against the two folders that actually collide in this dataset
# (11-1973-apartment-ownership-law: consolidated vs. original;
# 21-1844-wills-ordinance: consolidated-2024 vs. consolidated) -- in both
# cases the most-current consolidated edition is the right pick.
_EDITION_KIND_PRIORITY = ("consolidated-2024", "consolidated", "original")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_registry() -> dict[str, dict[str, str]]:
    with SOURCE_REGISTRY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        return {row["source_id"]: row for row in csv.DictReader(file)}


def _pick_by_edition_kind(candidates: list[tuple[Path, dict[str, Any]]]) -> Path | None:
    for kind in _EDITION_KIND_PRIORITY:
        matches = [path for path, doc in candidates if (doc.get("edition") or {}).get("kind") == kind]
        if len(matches) == 1:
            return matches[0]
    return None


def _pick_by_registry_basename(candidates: list[tuple[Path, dict[str, Any]]], registry_row: dict[str, str] | None) -> Path | None:
    if not registry_row:
        return None
    registry_basename = Path(registry_row.get("local_pdf_path", "")).name
    if not registry_basename:
        return None
    matches = [
        path
        for path, doc in candidates
        if Path((doc.get("edition") or {}).get("local_path", "")).name == registry_basename
    ]
    return matches[0] if len(matches) == 1 else None


def select_statute_files() -> dict[str, Path]:
    """Resolve exactly one principal-statute JSON per source_id.

    Raises RuntimeError if a folder's candidates can't be disambiguated and
    isn't covered by config.STATUTE_FILE_OVERRIDES, or if the final count
    doesn't match config.EXPECTED_STATUTE_COUNT.
    """
    registry = _load_registry()
    resolved: dict[str, Path] = {}

    for folder in sorted(p for p in FINALIZED_DIR.iterdir() if p.is_dir()):
        candidates: list[tuple[Path, dict[str, Any]]] = []
        for json_path in sorted(folder.glob("*.json")):
            document = _load_json(json_path)
            if document.get("source_id"):
                candidates.append((json_path, document))

        if not candidates:
            continue

        by_source_id: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
        for path, document in candidates:
            by_source_id.setdefault(document["source_id"], []).append((path, document))

        for source_id, group in by_source_id.items():
            if len(group) == 1:
                resolved[source_id] = group[0][0]
                continue

            chosen = _pick_by_edition_kind(group)
            if chosen is None:
                chosen = _pick_by_registry_basename(group, registry.get(source_id))
            if chosen is None and source_id in STATUTE_FILE_OVERRIDES:
                override_name = STATUTE_FILE_OVERRIDES[source_id]
                override_matches = [path for path, _ in group if path.name == override_name]
                chosen = override_matches[0] if override_matches else None
            if chosen is None:
                candidate_names = ", ".join(path.name for path, _ in group)
                raise RuntimeError(
                    f"Cannot disambiguate finalized JSON for {source_id} in {folder}: {candidate_names}"
                )
            resolved[source_id] = chosen

    if len(resolved) != EXPECTED_STATUTE_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_STATUTE_COUNT} finalized statutes, resolved {len(resolved)}: "
            f"{sorted(resolved)}"
        )
    return resolved


def _iter_section_nodes(node: dict[str, Any]) -> Iterator[dict[str, Any]]:
    if node.get("type") == "section":
        yield node
        return
    for child in node.get("children") or []:
        yield from _iter_section_nodes(child)


def _collect_text_and_refs(node: dict[str, Any]) -> tuple[str, list[dict], list[dict]]:
    texts: list[str] = []
    own_text = node.get("text") or node.get("raw_text") or ""
    if own_text:
        texts.append(own_text)
    cross_references = list(node.get("cross_references") or [])
    amendment_events = list(node.get("amendment_events") or [])

    for child in node.get("children") or []:
        child_text, child_refs, child_events = _collect_text_and_refs(child)
        if child_text:
            texts.append(child_text)
        cross_references.extend(child_refs)
        amendment_events.extend(child_events)

    return "\n".join(texts), cross_references, amendment_events


def flatten_sections(document: dict[str, Any], source_id: str) -> list[LawchainSection]:
    title = document.get("title") or document.get("long_title") or ""
    sections: list[LawchainSection] = []
    for top_node in document.get("body") or []:
        for section_node in _iter_section_nodes(top_node):
            number = str(section_node.get("number", "")).strip()
            if not number:
                continue
            text, cross_references, amendment_events = _collect_text_and_refs(section_node)
            sections.append(
                LawchainSection(
                    section_id=f"{source_id}:s{number}",
                    source_id=source_id,
                    title=title,
                    number=number,
                    heading=section_node.get("heading") or "",
                    text=text,
                    cross_references=cross_references,
                    amendment_events=amendment_events,
                )
            )
    return sections


def build_corpus() -> list[LawchainSection]:
    sections: list[LawchainSection] = []
    for source_id, path in sorted(select_statute_files().items()):
        document = _load_json(path)
        sections.extend(flatten_sections(document, source_id))
    return sections


def corpus_fingerprint() -> str:
    """Content hash of the resolved statute files, gating cache invalidation.

    Hashes file bytes directly rather than mtime/size, since mtimes aren't
    stable across a fresh checkout.
    """
    hasher = hashlib.sha256()
    for source_id, path in sorted(select_statute_files().items()):
        hasher.update(source_id.encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()
