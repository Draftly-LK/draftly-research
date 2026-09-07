"""Structural validation of the canonical trees in `library/finalized/`.

    uv run python scripts/validate_finalized_trees.py               # all trees
    uv run python scripts/validate_finalized_trees.py --slug 2-1889-civil-procedure-code
    uv run python scripts/validate_finalized_trees.py --strict      # undocumented defects fail too

There is no JSON Schema for the trees, and five parsers write them with
slightly different key sets, so this checks the contract every consumer relies
on rather than a fixed schema:

Hard errors (exit 1):
  - missing `title`, `citation.number`, `citation.year`, `edition.kind`,
    `verification_status`, `body`
  - a principal tree without `source_id`, or an amending tree without
    `instrument_id` and `amends`
  - `verification_status` outside the allowed set
  - a node without `type`, an unknown node `type`, a section without `number`
  - a section with no text, no heading and no children
  - a `provenance.hand_corrected` tree with no `provenance.what_changed`

Structural warnings (exit 0 unless `--strict`):
  - duplicate section numbers
  - gaps in section numbering
  - sections with no heading
  - a section whose text appears to contain the start of another section
  - an internal cross-reference pointing past the last section
  - a section whose text repeats its first child's text

A warning counts as *documented* when the section number appears in the tree's
`quality_flags`, `editorial_notes`, `quality_notes`, `omitted_provisions` or
`known_ocr_defects`, or in the statute's entry in
`data/processed/canonical-overrides.json` / `amendment-overrides.json`.
`--strict` fails only on undocumented warnings. Passing this says the tree is
well-formed; it says nothing about the legal text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FINALIZED = REPO_ROOT / "data/legal-sources/library/finalized"
CANONICAL_OVERRIDES = REPO_ROOT / "data/processed/canonical-overrides.json"
AMENDMENT_OVERRIDES = REPO_ROOT / "data/processed/amendment-overrides.json"

ALLOWED_STATUS = {
    "unverified",
    "structurally_verified",
    "needs_structural_review",
    "blocked_insufficient_local_source",
}
NODE_TYPES = {
    "part",
    "chapter",
    "crossheading",
    "subheading",
    "section",
    "subsection",
    "paragraph",
    "subparagraph",
    "item",
    "proviso",
    "definition",
    "text",
    "closing_text",
    "schedule",
    "form",
    "recital",
}
CONTAINER_TYPES = {"part", "chapter", "crossheading", "subheading", "schedule"}
SECTION_NUMBER = re.compile(r"^(\d+)([A-Za-z]*)$")
# "... some words. 26b. All fines imposed ..." -- a section label mid-text.
EMBEDDED_SECTION = re.compile(r"[a-z\)\]\*]\s*\*{0,2}\s*(\d{1,3}[A-Za-z]?)\.\s+[A-Z]")
INTERNAL_REF = re.compile(r"\bsections?\s+(\d{1,4})[A-Za-z]?\b(?!\s+of\s+(?:the|that|such|any))", re.I)


def load_overrides() -> dict:
    out = {}
    for path in (CANONICAL_OVERRIDES, AMENDMENT_OVERRIDES):
        if path.exists():
            out.update(json.loads(path.read_text(encoding="utf-8")))
    return out


def sections(nodes: list, out: list) -> list:
    for node in nodes or []:
        if isinstance(node, dict):
            if node.get("type") == "section":
                out.append(node)
            sections(node.get("children") or [], out)
    return out


def all_nodes(nodes: list, out: list) -> list:
    for node in nodes or []:
        if isinstance(node, dict):
            out.append(node)
            all_nodes(node.get("children") or [], out)
    return out


def note_text(tree: dict, overrides: dict) -> str:
    parts = []
    for key in ("quality_flags", "editorial_notes", "quality_notes", "omitted_provisions", "known_ocr_defects", "checked_against"):
        parts.append(json.dumps(tree.get(key, ""), ensure_ascii=False))
    key = tree.get("source_id") or tree.get("instrument_id")
    if key and key in overrides:
        parts.append(json.dumps(overrides[key], ensure_ascii=False))
    return " ".join(parts)


def documented(number: str, notes: str) -> bool:
    return re.search(rf"(?<![\dA-Za-z]){re.escape(number)}(?![\dA-Za-z])", notes) is not None


def validate_tree(path: Path, overrides: dict) -> tuple[list[str], list[tuple[str, bool]]]:
    """Return (errors, warnings); each warning is (message, documented)."""
    errors: list[str] = []
    warnings: list[tuple[str, bool]] = []
    try:
        tree = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"not valid JSON: {exc}"], []

    for key in ("title", "citation", "edition", "verification_status", "body"):
        if key not in tree:
            errors.append(f"missing top-level `{key}`")
    citation = tree.get("citation") or {}
    for key in ("number", "year"):
        if citation.get(key) in (None, ""):
            errors.append(f"missing citation.{key}")
    if not (tree.get("edition") or {}).get("kind"):
        errors.append("missing edition.kind")
    status = tree.get("verification_status")
    if status not in ALLOWED_STATUS:
        errors.append(f"verification_status {status!r} not in {sorted(ALLOWED_STATUS)}")
    is_amending = tree.get("instrument_role") == "amending" or "instrument_id" in tree
    if is_amending:
        if not tree.get("instrument_id"):
            errors.append("amending tree without instrument_id")
        if not tree.get("amends"):
            errors.append("amending tree without `amends`")
    elif not tree.get("source_id"):
        errors.append("principal tree without source_id")
    provenance = tree.get("provenance") or {}
    if provenance.get("hand_corrected") and not provenance.get("what_changed"):
        errors.append("hand_corrected tree without provenance.what_changed")
    if not isinstance(tree.get("body"), list) or not tree.get("body"):
        errors.append("body is empty or not a list")
        return errors, warnings

    nodes = all_nodes(tree["body"], [])
    for node in nodes:
        ntype = node.get("type")
        if not ntype:
            errors.append(f"node without type: {json.dumps(node)[:80]}")
        elif ntype not in NODE_TYPES:
            errors.append(f"unknown node type {ntype!r}")
        if ntype == "section":
            if node.get("number") in (None, ""):
                errors.append(f"section without number: heading={node.get('heading')!r}")
            elif not (node.get("text") or node.get("raw_text") or node.get("heading") or node.get("children")):
                errors.append(f"section {node['number']} has no text, heading or children")
        elif ntype in CONTAINER_TYPES and not (node.get("heading") or node.get("children")):
            warnings.append((f"{ntype} {node.get('number')!r} has neither heading nor children", False))

    secs = sections(tree["body"], [])
    notes = note_text(tree, overrides)
    numbers = [str(s.get("number")) for s in secs]
    seen: dict[str, int] = {}
    for n in numbers:
        seen[n] = seen.get(n, 0) + 1
    for n, count in seen.items():
        if count > 1:
            warnings.append((f"section {n} appears {count} times", documented(n, notes)))
    ints = sorted({int(m.group(1)) for n in numbers if (m := SECTION_NUMBER.match(n))})
    if ints:
        missing = [i for i in range(ints[0], ints[-1] + 1) if i not in set(ints)]
        if missing:
            undocumented = [str(i) for i in missing if not documented(str(i), notes)]
            spans = compress(missing)
            warnings.append(
                (f"{len(missing)} numbering gap(s): {spans}; {len(undocumented)} not mentioned in notes", not undocumented)
            )
    last = ints[-1] if ints else 0
    repeats: list[str] = []
    for s in secs:
        n = str(s.get("number"))
        text = s.get("text") or s.get("raw_text") or ""
        if not s.get("heading") and not is_amending:
            warnings.append((f"section {n} has no heading", documented(n, notes)))
        own = SECTION_NUMBER.match(n)
        for m in EMBEDDED_SECTION.finditer(text):
            label = m.group(1)
            if label.lower() == n.lower() or not own:
                continue
            if any(str(c.get("number", "")).lower() == label.lower() for c in s.get("children") or []):
                continue
            # Only a neighbouring section number is evidence of a swallowed
            # section; "section 5." deep inside a long section is a citation.
            if abs(int(re.match(r"\d+", label).group()) - int(own.group(1))) <= 2:
                warnings.append(
                    (
                        f"section {n} text contains what looks like the start of section {label}",
                        documented(label, notes) or documented(n, notes),
                    )
                )
        children = s.get("children") or []
        if children and text:
            first = (children[0].get("text") or children[0].get("raw_text") or "").strip()
            if first and len(first) > 40 and first[:60] in text:
                repeats.append(n)
        for ref in s.get("cross_references") or []:
            if not isinstance(ref, dict):
                continue
            if ref.get("kind") == "external" or ref.get("scope") == "external":
                continue
            if ref.get("scope") in (None, "internal") and not ref.get("target_statute") and not ref.get("statute"):
                tgt = ref.get("section") or ref.get("target_section") or ref.get("target")
                if isinstance(tgt, (str, int)) and (m := re.match(r"\d+", str(tgt))) and int(m.group()) > last:
                    warnings.append((f"section {n} references internal section {tgt} beyond last section {last}", documented(str(tgt), notes) or documented(n, notes)))
    # Some parsers keep a section's full text, children included, in `text`;
    # that is a convention, not a defect, and shows as most sections repeating.
    # A handful doing it in a tree that otherwise does not is the defect.
    if repeats:
        with_children = sum(1 for s in secs if s.get("children"))
        convention = with_children and len(repeats) / with_children > 0.5
        msg = f"{len(repeats)} section(s) repeat their first child's text: {', '.join(repeats[:8])}"
        if convention:
            msg += " (parser convention: full text kept on the section)"
        warnings.append((msg, bool(convention) or all(documented(n, notes) for n in repeats)))
    return errors, warnings


def compress(values: list[int]) -> str:
    spans = []
    start = prev = values[0]
    for v in values[1:]:
        if v == prev + 1:
            prev = v
            continue
        spans.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = v
    spans.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(spans[:12]) + (" ..." if len(spans) > 12 else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slug", action="append", default=[], help="only these finalized folders")
    parser.add_argument("--strict", action="store_true", help="undocumented warnings fail")
    parser.add_argument("--quiet", action="store_true", help="only print trees with findings")
    args = parser.parse_args()
    overrides = load_overrides()
    folders = [FINALIZED / s for s in args.slug] if args.slug else sorted(p for p in FINALIZED.iterdir() if p.is_dir())
    total_err = total_undoc = total_doc = 0
    for folder in folders:
        for tree in sorted(folder.glob("*.json")):
            errors, warnings = validate_tree(tree, overrides)
            undoc = [w for w, ok in warnings if not ok]
            doc = [w for w, ok in warnings if ok]
            total_err += len(errors)
            total_undoc += len(undoc)
            total_doc += len(doc)
            if args.quiet and not errors and not undoc:
                continue
            print(f"{folder.name}/{tree.name}: {len(errors)} errors, {len(undoc)} undocumented, {len(doc)} documented warnings")
            for e in errors:
                print(f"  ERROR {e}")
            for w in undoc:
                print(f"  WARN  {w}")
            if not args.quiet:
                for w in doc:
                    print(f"  noted {w}")
    print(f"errors={total_err} undocumented_warnings={total_undoc} documented_warnings={total_doc}")
    if total_err or (args.strict and total_undoc):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
