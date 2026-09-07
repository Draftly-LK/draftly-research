"""Validate a matter's issue map, authority files and legal map.

Checks four artifacts in one matter directory against the frozen schemas and
then cross-checks them against each other and against the source files the
verifier says it read:

  * every authority the legal map cites exists in verified-authorities.json;
  * every indispensable authority is `verified` (anything else blocks the
    matter);
  * every claim that leans on authority quotes an excerpt that matches the
    verifier's exact excerpt (either direction, whitespace-normalised);
  * every local source path exists, its hash matches when one is recorded, and
    the exact excerpt really is in the file when the file is text;
  * every question in source.json is mapped in both maps;
  * hop counts are at least 1 wherever indispensable authorities exist;
  * superseded or history-unknown provisions on indispensable authorities are
    surfaced as temporal warnings.

A pass here means "internally consistent and traceable to the cited files". It
says nothing about whether the law is right; only a lawyer can say that.

    python scripts/legal-qa-pipeline/validate_legal_maps.py --matter-dir <dir> [--report out.json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lqa_common as C  # noqa: E402

SCRIPT_NAME = "validate_legal_maps.py"
AUTHORITY_SUPPORT_STRENGTHS = {"direct", "combined", "inferential"}
TEMPORAL_FLAGS = {"current_text_superseded_since_event", "history_unknown"}
PASSING_MAP_STATUS = "authorities_verified"


def _load(matter_dir: Path, name: str, errors: list[str]) -> Any | None:
    path = matter_dir / name
    if not path.exists():
        errors.append(f"{name}: file missing")
        return None
    try:
        return C.read_json(path)
    except Exception as exc:  # noqa: BLE001 - report, do not crash
        errors.append(f"{name}: not valid JSON ({exc})")
        return None


def _matter_of(matter_dir: Path, source: dict[str, Any] | None) -> str:
    if source and source.get("benchmark_matter_id"):
        return source["benchmark_matter_id"]
    return matter_dir.name


def _check_header(obj: dict[str, Any], name: str, matter: str, errors: list[str]) -> None:
    if obj.get("benchmark_matter_id") != matter:
        errors.append(f"{name}: benchmark_matter_id {obj.get('benchmark_matter_id')!r} != {matter!r}")


def validate_issue_map(matter_dir: Path, schema_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    source = _load(matter_dir, "source.json", errors)
    matter = _matter_of(matter_dir, source)
    issue_map = _load(matter_dir, "issue-map.json", errors)
    if issue_map is not None:
        errors += C.validate_against_schema(issue_map, "issue-map", schema_dir)
        _check_header(issue_map, "issue-map.json", matter, errors)
        if source is not None:
            _check_question_coverage(C.source_question_ids(source), issue_map, "issue-map.json", errors)
    return C.report(matter, errors, warnings, validator=SCRIPT_NAME, stage="issue_mapped")


def validate_candidate_authorities(matter_dir: Path, schema_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    source = _load(matter_dir, "source.json", errors)
    matter = _matter_of(matter_dir, source)
    cands = _load(matter_dir, "candidate-authorities.json", errors)
    if cands is not None:
        errors += C.validate_against_schema(cands, "authority", schema_dir)
        _check_header(cands, "candidate-authorities.json", matter, errors)
        if cands.get("stage") != "authorities_candidate":
            errors.append(f"candidate-authorities.json: stage is {cands.get('stage')!r}, expected 'authorities_candidate'")
        _check_unique_authority_ids(cands, "candidate-authorities.json", errors)
        if source is not None:
            qids = set(C.source_question_ids(source))
            for a in cands.get("authorities") or []:
                for q in a.get("benchmark_question_ids") or []:
                    if q not in qids:
                        errors.append(f"candidate-authorities.json: {a.get('authority_id')} cites unknown question {q}")
        if not cands.get("authorities"):
            warnings.append("candidate-authorities.json: no candidate authorities listed")
    return C.report(matter, errors, warnings, validator=SCRIPT_NAME, stage="authorities_candidate")


def _check_unique_authority_ids(auth_file: dict[str, Any], name: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for a in auth_file.get("authorities") or []:
        aid = a.get("authority_id")
        if aid in seen:
            errors.append(f"{name}: duplicate authority_id {aid}")
        seen.add(aid)


def _check_question_coverage(source_qids: list[str], mapping: dict[str, Any], name: str, errors: list[str]) -> None:
    mapped = [q.get("benchmark_question_id") for q in mapping.get("questions") or []]
    for q in source_qids:
        if q not in mapped:
            errors.append(f"{name}: question {q} from source.json is not mapped")
    for q in mapped:
        if q not in source_qids:
            errors.append(f"{name}: question {q} is not in source.json")
    if len(mapped) != len(set(mapped)):
        errors.append(f"{name}: duplicate question entries")


def _indispensable_ids(legal_map: dict[str, Any], verified: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for q in legal_map.get("questions") or []:
        ids.update(q.get("indispensable_authority_ids") or [])
    for a in verified.get("authorities") or []:
        v = a.get("verification") or {}
        if v.get("necessity_assessed") == "indispensable":
            ids.add(a["authority_id"])
    return ids


def _referenced_authority_ids(question: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for aid in question.get("indispensable_authority_ids") or []:
        refs.append(("indispensable_authority_ids", aid))
    for aid in question.get("supporting_authority_ids") or []:
        refs.append(("supporting_authority_ids", aid))
    for step in question.get("reasoning_chain") or []:
        for aid in step.get("authority_ids") or []:
            refs.append((f"reasoning_chain[{step.get('step')}]", aid))
    for claim in question.get("answer_claims") or []:
        cid = claim.get("claim_id")
        for aid in claim.get("supporting_authority_ids") or []:
            refs.append((f"claim {cid}", aid))
        for ex in claim.get("supporting_excerpts") or []:
            refs.append((f"claim {cid} excerpt", ex.get("authority_id")))
    return refs


def check_authority_sources(
    verified: dict[str, Any], root: Path, errors: list[str], warnings: list[str]
) -> None:
    """Local source path exists, hash matches, excerpt is in the text."""
    for a in verified.get("authorities") or []:
        aid = a.get("authority_id")
        v = a.get("verification")
        if not isinstance(v, dict):
            continue
        sp = v.get("source_path")
        if not sp:
            continue
        if C.is_url(sp):
            if v.get("source_hash"):
                warnings.append(f"{aid}: source_hash given for a URL source; cannot check")
            continue
        path = C.local_source_path(sp, root)
        if not path.is_file():
            errors.append(f"{aid}: source_path {sp!r} does not exist relative to {root}")
            continue
        if v.get("source_hash"):
            actual = C.sha256_file(path)
            if C.strip_sha256_prefix(v["source_hash"]).lower() != actual:
                errors.append(f"{aid}: source_hash mismatch for {sp} (recorded {v['source_hash']}, file sha256:{actual})")
        else:
            warnings.append(f"{aid}: local source {sp} has no source_hash recorded")
        text = C.source_text_for_excerpt_check(path)
        if text is None:
            warnings.append(f"{aid}: {sp} is not a text file; excerpt not checked against file")
            continue
        if not C.is_ws_substring(v.get("exact_excerpt"), text):
            errors.append(f"{aid}: exact_excerpt is not a whitespace-normalised substring of {sp}")


def check_legal_map_against_authorities(
    legal_map: dict[str, Any],
    verified: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    temporal_warnings: list[str],
) -> None:
    by_id = {a["authority_id"]: a for a in verified.get("authorities") or [] if a.get("authority_id")}
    indispensable = _indispensable_ids(legal_map, verified)

    for aid in sorted(indispensable):
        a = by_id.get(aid)
        if a is None:
            errors.append(f"matter cannot advance: indispensable authority {aid} is not in verified-authorities.json")
            continue
        status = a.get("verification_status")
        if status != "verified":
            errors.append(f"matter cannot advance: indispensable authority {aid} has verification_status {status!r}")
        v = a.get("verification") or {}
        if v.get("applicable_version_for_matter_date") in TEMPORAL_FLAGS:
            temporal_warnings.append(
                f"{aid}: applicable_version_for_matter_date={v['applicable_version_for_matter_date']} on an indispensable authority; needs legal review"
            )
        if v.get("supports_claimed_proposition") in ("no", "cannot_determine"):
            errors.append(f"matter cannot advance: indispensable authority {aid} supports_claimed_proposition={v.get('supports_claimed_proposition')}")
        elif v.get("supports_claimed_proposition") == "partially":
            warnings.append(f"{aid}: verifier says the authority only partially supports the claimed proposition")

    for a in by_id.values():
        aid = a["authority_id"]
        if aid in indispensable:
            continue
        if a.get("verification_status") in ("unresolved", "original_judgment_required", "partially_verified"):
            warnings.append(f"{aid}: supporting authority has verification_status {a['verification_status']}")
        v = a.get("verification") or {}
        if v.get("omitted_authority_needed"):
            warnings.append(f"{aid}: verifier notes a missing authority: {v['omitted_authority_needed']}")

    for conflict in verified.get("source_conflicts") or []:
        warnings.append(f"source conflict recorded for {conflict.get('authority_id')}: {conflict.get('description')}")
        if conflict.get("authority_id") in indispensable:
            errors.append(f"matter cannot advance: indispensable authority {conflict.get('authority_id')} has an unresolved source conflict")

    if legal_map.get("status") != PASSING_MAP_STATUS:
        errors.append(f"legal-map.json: status is {legal_map.get('status')!r}; matter cannot advance")

    for q in legal_map.get("questions") or []:
        qid = q.get("benchmark_question_id")
        if q.get("status") != PASSING_MAP_STATUS:
            errors.append(f"legal-map.json {qid}: status is {q.get('status')!r}; matter cannot advance")
        for where, aid in _referenced_authority_ids(q):
            if aid not in by_id:
                errors.append(f"legal-map.json {qid}: {where} references {aid}, which is not in verified-authorities.json")
        q_indisp = q.get("indispensable_authority_ids") or []
        if q_indisp and int(q.get("legal_hop_count") or 0) < 1:
            errors.append(f"legal-map.json {qid}: legal_hop_count must be >= 1 when indispensable authorities exist")
        if not q_indisp:
            warnings.append(f"legal-map.json {qid}: no indispensable authorities listed")
        for claim in q.get("answer_claims") or []:
            _check_claim_support(claim, qid, by_id, errors, warnings)


def _check_claim_support(
    claim: dict[str, Any], qid: str, by_id: dict[str, Any], errors: list[str], warnings: list[str]
) -> None:
    cid = claim.get("claim_id")
    if claim.get("support_strength") not in AUTHORITY_SUPPORT_STRENGTHS:
        return
    matched = False
    for ex in claim.get("supporting_excerpts") or []:
        a = by_id.get(ex.get("authority_id"))
        if a is None:
            continue
        v = a.get("verification") or {}
        exact = v.get("exact_excerpt") or ""
        text = ex.get("excerpt") or ""
        if C.is_ws_substring(text, exact) or C.is_ws_substring(exact, text):
            matched = True
            break
    if not matched:
        errors.append(
            f"legal-map.json {qid} claim {cid}: no supporting excerpt matches a verified authority's exact_excerpt"
        )
    if claim.get("verification_status") in ("unverified", "rejected"):
        errors.append(f"legal-map.json {qid} claim {cid}: verification_status {claim['verification_status']}; matter cannot advance")
    elif claim.get("verification_status") == "partially_verified":
        warnings.append(f"legal-map.json {qid} claim {cid}: only partially verified")


def validate_matter(matter_dir: Path, root: Path | None = None, schema_dir: Path | None = None) -> dict[str, Any]:
    """Full check for the `authorities_verified` gate."""
    root = Path(root) if root else C.ROOT
    matter_dir = Path(matter_dir)
    errors: list[str] = []
    warnings: list[str] = []
    temporal_warnings: list[str] = []

    source = _load(matter_dir, "source.json", errors)
    matter = _matter_of(matter_dir, source)
    issue_map = _load(matter_dir, "issue-map.json", errors)
    cands = _load(matter_dir, "candidate-authorities.json", errors)
    verified = _load(matter_dir, "verified-authorities.json", errors)
    legal_map = _load(matter_dir, "legal-map.json", errors)

    for obj, name, schema in (
        (issue_map, "issue-map.json", "issue-map"),
        (cands, "candidate-authorities.json", "authority"),
        (verified, "verified-authorities.json", "authority"),
        (legal_map, "legal-map.json", "legal-map"),
    ):
        if obj is not None:
            errors += C.validate_against_schema(obj, schema, schema_dir)
            _check_header(obj, name, matter, errors)

    if verified is not None:
        if verified.get("stage") != "authorities_verified":
            errors.append(f"verified-authorities.json: stage is {verified.get('stage')!r}, expected 'authorities_verified'")
        _check_unique_authority_ids(verified, "verified-authorities.json", errors)
        for a in verified.get("authorities") or []:
            if a.get("verification_status") == "candidate":
                warnings.append(f"{a.get('authority_id')}: still a candidate in verified-authorities.json")
        if cands is not None:
            cand_ids = {a.get("authority_id") for a in cands.get("authorities") or []}
            for a in verified.get("authorities") or []:
                if a.get("authority_id") not in cand_ids:
                    warnings.append(f"{a.get('authority_id')}: appears in verified-authorities.json but not in candidate-authorities.json")
        check_authority_sources(verified, root, errors, warnings)

    if source is not None:
        qids = C.source_question_ids(source)
        if issue_map is not None:
            _check_question_coverage(qids, issue_map, "issue-map.json", errors)
        if legal_map is not None:
            _check_question_coverage(qids, legal_map, "legal-map.json", errors)

    if legal_map is not None and verified is not None:
        check_legal_map_against_authorities(legal_map, verified, errors, warnings, temporal_warnings)

    all_warnings = warnings + temporal_warnings
    return C.report(
        matter, errors, all_warnings,
        temporal_warnings=temporal_warnings, validator=SCRIPT_NAME, stage="authorities_verified",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matter-dir", required=True, type=Path)
    ap.add_argument("--report", type=Path, default=None, help="Write the JSON report here as well as printing it.")
    ap.add_argument("--root", type=Path, default=None, help="Repo root for relative source paths (default: this repo).")
    ap.add_argument("--schema-dir", type=Path, default=None)
    ap.add_argument(
        "--check", choices=["issue-map", "candidate-authorities", "all"], default="all",
        help="Which gate to check (default all = authorities_verified).",
    )
    args = ap.parse_args(argv)

    if args.check == "issue-map":
        rep = validate_issue_map(args.matter_dir, args.schema_dir)
    elif args.check == "candidate-authorities":
        rep = validate_candidate_authorities(args.matter_dir, args.schema_dir)
    else:
        rep = validate_matter(args.matter_dir, args.root, args.schema_dir)

    if args.report:
        C.write_json(args.report, rep)
    print(C.dumps_json(rep), end="")
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
