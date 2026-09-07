"""Validate a matter's canonical ledger (matter-ledger.json).

The ledger is the only place a generated document may take a value from, so
it has to be traceable and clean before anything is rendered from it:

  * fact ids are unique and every entity, instrument, event, relationship and
    conflict resolves to a fact that exists;
  * every past-paper fact quotes wording that really is in source.json (the
    copy of the selected-matters record), whitespace-normalised;
  * events ordered by `sequence` do not go backwards in `date_iso`, comparing
    at the coarser granularity of each pair ('1990' vs '1990-06-12' is fine);
  * parties are fictional exam characters, never real people;
  * no string anywhere in the ledger looks like a Sri Lankan NIC or a phone
    number;
  * every predicate id the ledger lists exists in predicates.json;
  * every synthetic fact is declared in synthetic_additions, neutral ones
    cannot claim to affect anything, decisive ones demand legal review.

Passing means the ledger is consistent with its sources. Nothing here judges
whether a fact matters legally.

    python scripts/legal-qa-pipeline/validate_matter_ledgers.py --matter-dir <dir> [--report out.json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lqa_common as C  # noqa: E402

SCRIPT_NAME = "validate_matter_ledgers.py"
ENTITY_COLLECTIONS = (
    "parties", "properties", "instruments", "events", "relationships",
    "financial_values", "registrations", "notices", "court_events",
)
SYNTHETIC_ORIGINS = {"synthetic_neutral", "synthetic_decisive"}


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


def check_fact_ids(ledger: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    for f in ledger.get("source_facts") or []:
        fid = f.get("fact_id")
        if fid in facts:
            errors.append(f"duplicate fact_id {fid}")
        facts[fid] = f
    return facts


def check_references(ledger: dict[str, Any], facts: dict[str, Any], errors: list[str]) -> None:
    for coll in ENTITY_COLLECTIONS:
        seen_ids: set[str] = set()
        for item in ledger.get(coll) or []:
            label = item.get("id") or f"{item.get('from_party')}->{item.get('to_party')}"
            if item.get("id") is not None:
                if item["id"] in seen_ids:
                    errors.append(f"{coll}: duplicate id {item['id']}")
                seen_ids.add(item["id"])
            for fid in item.get("fact_ids") or []:
                if fid not in facts:
                    errors.append(f"{coll}.{label}: fact_id {fid} does not resolve")
    party_ids = {p.get("id") for p in ledger.get("parties") or []}
    for coll in ("instruments", "events"):
        for item in ledger.get(coll) or []:
            for pid in item.get("parties") or []:
                if pid not in party_ids:
                    errors.append(f"{coll}.{item.get('id')}: party {pid} is not in ledger.parties")
    instrument_ids = {i.get("id") for i in ledger.get("instruments") or []}
    for ev in ledger.get("events") or []:
        if ev.get("instrument_id") and ev["instrument_id"] not in instrument_ids:
            errors.append(f"events.{ev.get('id')}: instrument_id {ev['instrument_id']} is not in ledger.instruments")
    for rel in ledger.get("relationships") or []:
        for key in ("from_party", "to_party"):
            if rel.get(key) not in party_ids:
                errors.append(f"relationships: {key} {rel.get(key)} is not in ledger.parties")
    for conflict in ledger.get("fact_conflicts") or []:
        for fid in conflict.get("fact_ids") or []:
            if fid not in facts:
                errors.append(f"fact_conflicts: fact_id {fid} does not resolve")


def check_source_quotes(ledger: dict[str, Any], source: dict[str, Any], errors: list[str]) -> None:
    haystack = "\n".join(C.source_texts(source))
    for f in ledger.get("source_facts") or []:
        if f.get("origin") != "past_paper":
            continue
        if not C.is_ws_substring(f.get("source_quote"), haystack):
            errors.append(f"{f.get('fact_id')}: past_paper source_quote is not found in source.json text")


def check_chronology(ledger: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    events = sorted(ledger.get("events") or [], key=lambda e: (int(e.get("sequence") or 0), str(e.get("id"))))
    seqs = [e.get("sequence") for e in events]
    if len(seqs) != len(set(seqs)):
        warnings.append("events: duplicate sequence numbers")
    last_dated: dict[str, Any] | None = None
    for ev in events:
        if not ev.get("date_iso"):
            continue
        if last_dated is not None and not C.dates_non_decreasing(last_dated["date_iso"], ev["date_iso"]):
            errors.append(
                f"events: {ev.get('id')} (seq {ev.get('sequence')}, {ev['date_iso']}) is dated before "
                f"{last_dated.get('id')} (seq {last_dated.get('sequence')}, {last_dated['date_iso']})"
            )
        last_dated = ev


def check_parties(ledger: dict[str, Any], errors: list[str]) -> None:
    for p in ledger.get("parties") or []:
        if p.get("is_real_person") is not False:
            errors.append(f"parties.{p.get('id')}: is_real_person must be false")


def check_pii(ledger: dict[str, Any], errors: list[str]) -> None:
    for path, text in C.iter_strings(ledger):
        for hit in C.find_pii(text):
            errors.append(f"possible real identifier at {path}: {hit}")


def check_predicates(
    ledger: dict[str, Any], predicates: dict[str, Any] | None, errors: list[str], warnings: list[str]
) -> None:
    if predicates is None:
        errors.append("predicates.json: missing; cannot resolve ledger.predicates")
        return
    known = {p.get("predicate_id") for p in predicates.get("predicates") or []}
    for pid in ledger.get("predicates") or []:
        if pid not in known:
            errors.append(f"ledger.predicates: {pid} is not in predicates.json")
    for f in ledger.get("source_facts") or []:
        for pid in f.get("supports_predicate_ids") or []:
            if pid not in known:
                errors.append(f"{f.get('fact_id')}: supports_predicate_ids {pid} is not in predicates.json")
    listed = set(ledger.get("predicates") or [])
    for pid in sorted(known - listed):
        warnings.append(f"predicates.json {pid} is not listed in ledger.predicates")


def check_synthetic(ledger: dict[str, Any], facts: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    additions = {a.get("fact_id"): a for a in ledger.get("synthetic_additions") or []}
    for fid, f in facts.items():
        origin = f.get("origin")
        if origin not in SYNTHETIC_ORIGINS:
            if fid in additions:
                warnings.append(f"synthetic_additions lists {fid}, whose origin is {origin}")
            continue
        add = additions.get(fid)
        if add is None:
            errors.append(f"{fid}: origin {origin} but not listed in synthetic_additions")
            continue
        if origin == "synthetic_neutral" and add.get("could_affect"):
            errors.append(f"{fid}: synthetic_neutral fact claims could_affect {add['could_affect']}")
        if origin == "synthetic_decisive":
            if add.get("legal_review_required") is not True:
                errors.append(f"{fid}: synthetic_decisive fact requires legal_review_required: true")
            if not add.get("could_affect"):
                warnings.append(f"{fid}: synthetic_decisive fact lists nothing in could_affect")
    for fid in additions:
        if fid not in facts:
            errors.append(f"synthetic_additions: fact_id {fid} does not resolve")


def check_questions(ledger: dict[str, Any], source: dict[str, Any], errors: list[str]) -> None:
    qids = C.source_question_ids(source)
    for q in ledger.get("questions") or []:
        if q not in qids:
            errors.append(f"ledger.questions: {q} is not in source.json")
    for q in qids:
        if q not in (ledger.get("questions") or []):
            errors.append(f"ledger.questions: question {q} from source.json is missing")


def validate_matter(matter_dir: Path, schema_dir: Path | None = None) -> dict[str, Any]:
    matter_dir = Path(matter_dir)
    errors: list[str] = []
    warnings: list[str] = []

    source = _load(matter_dir, "source.json", errors)
    matter = (source or {}).get("benchmark_matter_id") or matter_dir.name
    ledger = _load(matter_dir, "matter-ledger.json", errors)
    predicates = _load(matter_dir, "predicates.json", errors, required=False)

    if ledger is not None:
        errors += C.validate_against_schema(ledger, "matter-ledger", schema_dir)
        if ledger.get("benchmark_matter_id") != matter:
            errors.append(f"matter-ledger.json: benchmark_matter_id {ledger.get('benchmark_matter_id')!r} != {matter!r}")
        facts = check_fact_ids(ledger, errors)
        check_references(ledger, facts, errors)
        if source is not None:
            check_source_quotes(ledger, source, errors)
            check_questions(ledger, source, errors)
        check_chronology(ledger, errors, warnings)
        check_parties(ledger, errors)
        check_pii(ledger, errors)
        check_predicates(ledger, predicates, errors, warnings)
        check_synthetic(ledger, facts, errors, warnings)
        for conflict in ledger.get("fact_conflicts") or []:
            warnings.append(f"fact conflict {conflict.get('fact_ids')}: {conflict.get('description')} ({conflict.get('resolution')})")
    if predicates is not None:
        errors += C.validate_against_schema(predicates, "predicate", schema_dir)

    return C.report(matter, errors, warnings, validator=SCRIPT_NAME, stage="ledger_built")


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
