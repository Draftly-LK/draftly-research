"""Validate a matter's document bundle: specs, predicates, ledger, rendered docs.

The bundle is what an evaluated system will see, so this gate is about two
things: every value on every page traces back to the canonical ledger, and
nothing on those pages gives the answer away.

  * every particular's `value_source` resolves to a ledger fact or a
    `ledger.<collection>.<id>.<attr>` path that exists;
  * every indispensable predicate (not `unresolved`) has at least one evidence
    document that is actually specified, and every indispensable document
    supports at least one indispensable predicate;
  * every synthetic document field maps to a ledger fact and carries that
    fact's value (string compare; `value_iso` is accepted as an alternative);
  * rendered text carries the synthetic marker verbatim and `document_hash`
    is the sha256 of the text;
  * public filenames leak no role words and are unique;
  * no gold-answer conclusion sentence, and no AUTH-/PR-/CL- id, appears in
    any rendered text or in the source background;
  * a fact rendered in two documents shows the same value in both.

A pass means the bundle is consistent and leak-free by these checks, not that
the documents are legally sufficient.

    python scripts/legal-qa-pipeline/validate_document_bundles.py --matter-dir <dir> [--report out.json]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lqa_common as C  # noqa: E402

SCRIPT_NAME = "validate_document_bundles.py"
LEDGER_PATH_RE = re.compile(r"^ledger\.([a-z_]+)\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_]+)$")
FACT_ID_RE = re.compile(r"^FACT-M[0-9]{3}-[0-9]{3}$")
MIN_CONCLUSION_SENTENCE = 25


def _load(matter_dir: Path, name: str, errors: list[str], required: bool = True) -> Any | None:
    path = matter_dir / name
    if not path.exists():
        if required:
            errors.append(f"{name}: file missing")
        return None
    try:
        return C.read_json(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{name}: not valid JSON ({exc})")
        return None


def load_synthetic_documents(matter_dir: Path, errors: list[str]) -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    sdir = matter_dir / "synthetic-documents"
    if not sdir.is_dir():
        return docs
    for path in sorted(sdir.glob("*.json")):
        try:
            doc = C.read_json(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"synthetic-documents/{path.name}: not valid JSON ({exc})")
            continue
        did = doc.get("document_id")
        if did != path.stem:
            errors.append(f"synthetic-documents/{path.name}: document_id {did!r} does not match filename")
        docs[path.stem] = doc
    return docs


def resolve_value_source(value_source: str, ledger: dict[str, Any], facts: dict[str, Any]) -> tuple[bool, str]:
    if FACT_ID_RE.match(value_source or ""):
        return (value_source in facts, f"fact {value_source} not in ledger")
    m = LEDGER_PATH_RE.match(value_source or "")
    if not m:
        return (False, f"value_source {value_source!r} is neither a FACT id nor a ledger.<collection>.<id>.<attr> path")
    coll, item_id, attr = m.groups()
    items = ledger.get(coll)
    if not isinstance(items, list):
        return (False, f"ledger collection {coll!r} does not exist")
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            if attr in item:
                return (True, "")
            return (False, f"ledger.{coll}.{item_id} has no attribute {attr!r}")
    return (False, f"ledger.{coll} has no item {item_id!r}")


def check_specs(
    specs: dict[str, Any], predicates: dict[str, Any], ledger: dict[str, Any], facts: dict[str, Any],
    errors: list[str], warnings: list[str],
) -> None:
    preds = {p.get("predicate_id"): p for p in predicates.get("predicates") or []}
    docs = {d.get("document_id"): d for d in specs.get("documents") or []}
    if len(docs) != len(specs.get("documents") or []):
        errors.append("document-specs.json: duplicate document_id")

    indispensable_preds = {
        pid for pid, p in preds.items()
        if p.get("necessity") == "indispensable" and p.get("status") != "unresolved"
    }

    seen_fields: set[str] = set()
    filenames: dict[str, str] = {}
    for did, d in docs.items():
        fname = d.get("public_filename") or ""
        if C.LABEL_LEAK_RE.search(fname):
            errors.append(f"{did}: public_filename {fname!r} leaks a label word")
        if fname in filenames:
            errors.append(f"{did}: public_filename {fname!r} is also used by {filenames[fname]}")
        filenames[fname] = did
        for pid in d.get("supports_predicate_ids") or []:
            if pid not in preds:
                errors.append(f"{did}: supports_predicate_ids {pid} is not in predicates.json")
        if d.get("necessity") == "indispensable":
            if not any(pid in indispensable_preds for pid in d.get("supports_predicate_ids") or []):
                errors.append(f"{did}: indispensable document supports no indispensable predicate")
        if d.get("document_date_fact_id") and d["document_date_fact_id"] not in facts:
            errors.append(f"{did}: document_date_fact_id {d['document_date_fact_id']} not in ledger")
        for fld in d.get("particulars") or []:
            fid = fld.get("field_id")
            if fid in seen_fields:
                errors.append(f"{did}: duplicate field_id {fid}")
            seen_fields.add(fid)
            ok, why = resolve_value_source(fld.get("value_source"), ledger, facts)
            if not ok:
                errors.append(f"{did} {fid}: {why}")
            for pid in fld.get("supports_predicate_ids") or []:
                if pid not in preds:
                    errors.append(f"{did} {fid}: supports_predicate_ids {pid} is not in predicates.json")
            if fld.get("source_origin") == "synthetic_decisive":
                warnings.append(f"{did} {fid}: synthetic_decisive particular; lawyer must confirm the generation justification")

    for pid in sorted(indispensable_preds):
        p = preds[pid]
        evidence = [d for d in p.get("evidence_document_ids") or [] if d in docs]
        if not evidence:
            errors.append(f"{pid}: indispensable predicate has no evidence document present in document-specs.json")
    for pid, p in preds.items():
        for did in p.get("evidence_document_ids") or []:
            if did not in docs:
                errors.append(f"{pid}: evidence_document_ids {did} is not in document-specs.json")


def check_synthetic_documents(
    specs: dict[str, Any], sdocs: dict[str, dict[str, Any]], facts: dict[str, Any],
    errors: list[str], warnings: list[str], schema_dir: Path | None,
) -> dict[str, dict[str, str]]:
    """Returns fact_id -> {document_id: rendered value} for cross-document checks."""
    spec_by_id = {d.get("document_id"): d for d in specs.get("documents") or []}
    spec_fields = {
        (d.get("document_id"), f.get("field_id")): f
        for d in specs.get("documents") or [] for f in d.get("particulars") or []
    }
    values_by_fact: dict[str, dict[str, str]] = {}
    filenames: dict[str, str] = {}

    for did, spec in spec_by_id.items():
        if did not in sdocs:
            if spec.get("generation_status") == "blocked":
                warnings.append(f"{did}: specified document is blocked; no synthetic document")
            else:
                errors.append(f"{did}: specified document has no synthetic-documents/{did}.json")

    for did, doc in sdocs.items():
        errors.extend(C.validate_against_schema(doc, "synthetic-document", schema_dir))
        spec = spec_by_id.get(did)
        if spec is None:
            errors.append(f"{did}: synthetic document has no entry in document-specs.json")
        else:
            if doc.get("public_filename") != spec.get("public_filename"):
                errors.append(f"{did}: public_filename differs between spec and synthetic document")
            if doc.get("benchmark_matter_id") != spec.get("benchmark_matter_id"):
                errors.append(f"{did}: benchmark_matter_id differs between spec and synthetic document")
        fname = doc.get("public_filename") or ""
        if C.LABEL_LEAK_RE.search(fname):
            errors.append(f"{did}: public_filename {fname!r} leaks a label word")
        if fname in filenames:
            errors.append(f"{did}: public_filename {fname!r} is also used by {filenames[fname]}")
        filenames[fname] = did

        text = doc.get("rendered_text") or ""
        if C.SYNTHETIC_MARKER not in text:
            errors.append(f"{did}: rendered_text does not contain the synthetic marker verbatim")
        expected_hash = C.prefixed_sha256(C.sha256_text(text))
        if doc.get("document_hash") != expected_hash:
            errors.append(f"{did}: document_hash {doc.get('document_hash')} != {expected_hash}")
        for m in C.REF_ID_RE.finditer(text):
            errors.append(f"{did}: rendered_text leaks private id {m.group(0)}")
        for m in C.LEDGER_ID_RE.finditer(text):
            warnings.append(f"{did}: rendered_text mentions ledger id {m.group(0)}")
        for hit in C.find_pii(text):
            errors.append(f"{did}: rendered_text contains a real-looking identifier {hit}")

        for fld in doc.get("fields") or []:
            fid = fld.get("fact_id")
            fact = facts.get(fid)
            label = f"{did} {fld.get('field_id')}"
            if fact is None:
                errors.append(f"{label}: fact_id {fid} is not in the ledger")
                continue
            rendered = str(fld.get("value"))
            candidates = {str(fact.get("value"))}
            if fact.get("value_iso") is not None:
                candidates.add(str(fact["value_iso"]))
            if rendered not in candidates:
                errors.append(f"{label}: value {rendered!r} != ledger {fid} value {fact.get('value')!r}")
            if spec is not None and (did, fld.get("field_id")) not in spec_fields:
                errors.append(f"{label}: field_id is not a particular of {did} in document-specs.json")
            values_by_fact.setdefault(fid, {})[did] = rendered
    return values_by_fact


def check_cross_document_consistency(values_by_fact: dict[str, dict[str, str]], errors: list[str]) -> None:
    for fid in sorted(values_by_fact):
        per_doc = values_by_fact[fid]
        if len(per_doc) < 2:
            continue
        distinct = sorted(set(per_doc.values()))
        if len(distinct) > 1:
            errors.append(f"{fid}: rendered with different values across documents: " + ", ".join(f"{d}={v!r}" for d, v in sorted(per_doc.items())))


def conclusion_sentences(legal_map: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for q in legal_map.get("questions") or []:
        conclusion = ((q.get("gold_answer_draft") or {}).get("conclusion")) or ""
        for sentence in conclusion.split("."):
            s = C.normalize_ws(sentence)
            if len(s) > MIN_CONCLUSION_SENTENCE:
                out.append((q.get("benchmark_question_id"), s))
    return out


def check_leakage(
    legal_map: dict[str, Any] | None, source: dict[str, Any] | None, sdocs: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if legal_map is None:
        return
    background = C.normalize_ws("\n".join(C.source_texts(source))) if source else ""
    rendered = {did: C.normalize_ws(d.get("rendered_text") or "") for did, d in sdocs.items()}
    for qid, sentence in conclusion_sentences(legal_map):
        if background and sentence in background:
            errors.append(f"{qid}: gold conclusion sentence appears verbatim in the source background: {sentence[:60]!r}...")
        for did, text in rendered.items():
            if sentence in text:
                errors.append(f"{qid}: gold conclusion sentence appears verbatim in {did}: {sentence[:60]!r}...")


def validate_matter(matter_dir: Path, schema_dir: Path | None = None) -> dict[str, Any]:
    matter_dir = Path(matter_dir)
    errors: list[str] = []
    warnings: list[str] = []

    source = _load(matter_dir, "source.json", errors, required=False)
    matter = (source or {}).get("benchmark_matter_id") or matter_dir.name
    specs = _load(matter_dir, "document-specs.json", errors)
    predicates = _load(matter_dir, "predicates.json", errors)
    ledger = _load(matter_dir, "matter-ledger.json", errors)
    legal_map = _load(matter_dir, "legal-map.json", errors, required=False)
    sdocs = load_synthetic_documents(matter_dir, errors)

    for obj, schema in ((specs, "document-spec"), (predicates, "predicate"), (ledger, "matter-ledger")):
        if obj is not None:
            errors += C.validate_against_schema(obj, schema, schema_dir)
            if obj.get("benchmark_matter_id") != matter:
                errors.append(f"{schema}: benchmark_matter_id {obj.get('benchmark_matter_id')!r} != {matter!r}")

    facts = {f.get("fact_id"): f for f in (ledger or {}).get("source_facts") or []}
    if specs is not None and predicates is not None and ledger is not None:
        check_specs(specs, predicates, ledger, facts, errors, warnings)
        values_by_fact = check_synthetic_documents(specs, sdocs, facts, errors, warnings, schema_dir)
        check_cross_document_consistency(values_by_fact, errors)
    if not sdocs:
        errors.append("synthetic-documents/: no documents found")
    check_leakage(legal_map, source, sdocs, errors)
    if legal_map is None:
        warnings.append("legal-map.json missing; gold-answer leakage not checked")

    return C.report(matter, errors, warnings, validator=SCRIPT_NAME, stage="synthetic_bundle_generated")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matter-dir", required=True, type=Path)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--schema-dir", type=Path, default=None)
    args = ap.parse_args(argv)
    rep = validate_matter(args.matter_dir, args.schema_dir)
    if args.report:
        C.write_json(args.report, rep)
    print(C.dumps_json(rep), end="")
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
