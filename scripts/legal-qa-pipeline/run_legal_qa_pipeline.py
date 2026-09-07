"""Orchestrate a legal-qa-v1 benchmark run: manifest, state machine, merge.

This is bookkeeping, not research. It never calls a model, never reads the
law and never decides whether an answer is right. What it does:

    init      create runs/<run-id>/, copy the frozen schemas, hash the source
              dataset, list every matter as `selected`, and write each pilot
              matter's source.json (the exact selected-matters record plus its
              selected-questions rows).
    validate  run the validator for one target stage and, only if it passes,
              advance the matter by exactly one state. Skipping states is
              refused. `lawyer_validated` is refused unconditionally (exit 3):
              only a lawyer can set it, by hand.
    block     park a matter in a failure state with a reason.
    event     append an audit event (retry, refinement, note).
    audit     run all three validators and write consistency-audit.json.
    packet    build the lawyer review packet and blank approval.json.
    render    write synthetic-documents/<DOC>.txt from rendered_text and
              check every document_hash.
    merge     coordinator step: build private/gold/gold-questions.jsonl,
              public/input/questions.jsonl and public document copies for
              every matter at or past lawyer_review_pending, plus audit files.
              Public files are scanned for private field names before the
              command reports success.

Every timestamp can be pinned with --now so that runs are reproducible.
All output is status=unverified.

    python scripts/legal-qa-pipeline/run_legal_qa_pipeline.py init --run-id X --pilot M001,M006 --reason M001="..."
    python scripts/legal-qa-pipeline/run_legal_qa_pipeline.py validate --run-id X --matter M001 --stage issue_mapped
    python scripts/legal-qa-pipeline/run_legal_qa_pipeline.py merge --run-id X
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_review_packets as BRP  # noqa: E402
import lqa_common as C  # noqa: E402
import validate_document_bundles as VDB  # noqa: E402
import validate_legal_maps as VLM  # noqa: E402
import validate_matter_ledgers as VML  # noqa: E402

SCRIPT_NAME = "run_legal_qa_pipeline.py"
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_HUMAN_ONLY = 3

PRIVATE_FIELD_RE = re.compile(r"\b(authority_id|predicate|gold_answer|claim_id)\b")
PUBLIC_ORDERED_MIN_STATE = "lawyer_review_pending"


class PipelineError(Exception):
    def __init__(self, message: str, code: int = EXIT_FAIL) -> None:
        super().__init__(message)
        self.code = code


def now_iso(pinned: str | None) -> str:
    if pinned:
        return pinned
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Run directory access
# ---------------------------------------------------------------------------

class Run:
    def __init__(self, run_id: str, runs_dir: Path | None = None, root: Path | None = None) -> None:
        self.run_id = run_id
        self.runs_dir = Path(runs_dir) if runs_dir else C.RUNS_DIR
        self.root = Path(root) if root else C.ROOT
        self.run_dir = self.runs_dir / run_id
        self.manifest_path = self.run_dir / "manifest.json"
        self.schema_dir = self.run_dir / "schemas"

    def load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            raise PipelineError(f"no manifest at {self.manifest_path}; run init first", EXIT_USAGE)
        return C.read_json(self.manifest_path)

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        errors = C.validate_against_schema(manifest, "run-manifest", self.effective_schema_dir())
        if errors:
            raise PipelineError("refusing to write an invalid manifest: " + "; ".join(errors))
        C.write_json(self.manifest_path, manifest)

    def effective_schema_dir(self) -> Path:
        return self.schema_dir if (self.schema_dir / C.SCHEMA_FILES["run-manifest"]).exists() else C.SCHEMA_DIR

    def matter_entry(self, manifest: dict[str, Any], matter: str) -> dict[str, Any]:
        for m in manifest["matters"]:
            if m["benchmark_matter_id"] == matter:
                return m
        raise PipelineError(f"matter {matter} is not in the manifest", EXIT_USAGE)

    def matter_dir(self, entry: dict[str, Any]) -> Path:
        return self.run_dir / entry["artifact_dir"]

    def add_event(self, manifest: dict[str, Any], matter: str | None, event: str, detail: str, at: str) -> None:
        manifest["events"].append({"at": at, "matter": matter, "event": event, "detail": detail})


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def parse_reasons(items: list[str] | None) -> dict[str, str]:
    reasons: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise PipelineError(f"--reason expects Mxxx=text, got {item!r}", EXIT_USAGE)
        key, value = item.split("=", 1)
        reasons[C.check_matter_id(key.strip())] = value.strip().strip('"')
    return reasons


def build_source_record(
    record: dict[str, Any], flat: list[dict[str, Any]], matters_sha: str, questions_sha: str, run_id: str,
    matters_path: str, questions_path: str,
) -> dict[str, Any]:
    qids = [q["benchmark_question_id"] for q in record.get("questions") or []]
    flat_ids = [q["benchmark_question_id"] for q in flat]
    if sorted(qids) != sorted(flat_ids):
        raise PipelineError(
            f"{record.get('benchmark_matter_id')}: selected-matters questions {qids} != selected-questions rows {flat_ids}"
        )
    out = dict(record)
    out["run_id"] = run_id
    out["flat_questions"] = flat
    out["source_paths"] = {"selected_matters": matters_path, "selected_questions": questions_path}
    out["source_sha256"] = {
        "selected_matters_jsonl": matters_sha,
        "selected_questions_jsonl": questions_sha,
        "matter_record": C.sha256_text(C.canonical_json(record)),
        "flat_questions": C.sha256_text(C.canonical_json(flat)),
    }
    out["status"] = "unverified"
    return out


def cmd_init(args: argparse.Namespace) -> int:
    run = Run(args.run_id, args.runs_dir, args.root)
    source_dir = Path(args.source_dir) if args.source_dir else C.DEFAULT_SOURCE_DIR
    matters_path = source_dir / "selected-matters.jsonl"
    questions_path = source_dir / "selected-questions.jsonl"
    for p in (matters_path, questions_path):
        if not p.exists():
            raise PipelineError(f"source file missing: {p}", EXIT_USAGE)
    if run.manifest_path.exists() and not args.force:
        raise PipelineError(f"{run.manifest_path} already exists; use --force to re-initialise", EXIT_USAGE)

    pilots = [C.check_matter_id(m.strip()) for m in (args.pilot or "").split(",") if m.strip()]
    reasons = parse_reasons(args.reason)
    for m in reasons:
        if m not in pilots:
            raise PipelineError(f"--reason given for {m}, which is not a pilot matter", EXIT_USAGE)

    records = C.read_jsonl(matters_path)
    flat_rows = C.read_jsonl(questions_path)
    by_matter = {r["benchmark_matter_id"]: r for r in records}
    for m in pilots:
        if m not in by_matter:
            raise PipelineError(f"pilot matter {m} is not in {matters_path}", EXIT_USAGE)

    matters_sha = C.sha256_file(matters_path)
    questions_sha = C.sha256_file(questions_path)
    at = now_iso(args.now)

    run.run_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("pilot", "audits", "review-packets", "schemas", "public/input", "private/gold", "private/audit"):
        (run.run_dir / sub).mkdir(parents=True, exist_ok=True)
    schema_src = Path(args.schema_dir) if args.schema_dir else C.SCHEMA_DIR
    for fname in C.SCHEMA_FILES.values():
        shutil.copyfile(schema_src / fname, run.schema_dir / fname)

    def rel(p: Path) -> str:
        try:
            return p.resolve().relative_to(run.root.resolve()).as_posix()
        except ValueError:
            return p.as_posix()

    matters: list[dict[str, Any]] = []
    for r in sorted(records, key=lambda r: r["benchmark_matter_id"]):
        mid = r["benchmark_matter_id"]
        is_pilot = mid in pilots
        matters.append({
            "benchmark_matter_id": mid,
            "role": "pilot" if is_pilot else "not_started",
            "state": "selected",
            "state_history": [{"state": "selected", "at": at, "validated_by": SCRIPT_NAME, "note": "init"}],
            "owner_agents": {"research": None, "verification": None, "document_design": None, "red_team": None},
            "artifact_dir": f"pilot/{mid}" if is_pilot else f"full/{mid}",
            "selection_reason": reasons.get(mid),
        })

    manifest = {
        "run_id": args.run_id,
        "created": at,
        "description": args.description or "legal-qa-v1 benchmark run; all artifacts status=unverified until lawyer sign-off",
        "source_dataset": {
            "selected_matters_path": rel(matters_path),
            "selected_questions_path": rel(questions_path),
            "selected_matters_sha256": matters_sha,
            "selected_questions_sha256": questions_sha,
            "matter_count": len(records),
            "question_count": len(flat_rows),
        },
        "schema_versions": C.schema_hashes(run.schema_dir),
        "state_machine": {"ordered_states": C.ORDERED_STATES, "failure_states": C.FAILURE_STATES},
        "matters": matters,
        "agents": [],
        "events": [{"at": at, "matter": None, "event": "init", "detail": f"run initialised with pilots {','.join(pilots) or '(none)'}"}],
    }

    for mid in pilots:
        flat = [q for q in flat_rows if q.get("benchmark_matter_id") == mid]
        source = build_source_record(
            by_matter[mid], flat, matters_sha, questions_sha, args.run_id, rel(matters_path), rel(questions_path)
        )
        mdir = run.run_dir / f"pilot/{mid}"
        (mdir / "synthetic-documents").mkdir(parents=True, exist_ok=True)
        C.write_json(mdir / "source.json", source)

    run.save_manifest(manifest)
    print(f"initialised {run.run_dir} with {len(matters)} matters, pilots: {', '.join(pilots) or '(none)'}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# stage validators
# ---------------------------------------------------------------------------

def validate_predicates(matter_dir: Path, schema_dir: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    source = C.read_json_if_exists(matter_dir / "source.json") or {}
    matter = source.get("benchmark_matter_id") or matter_dir.name
    preds = C.read_json_if_exists(matter_dir / "predicates.json")
    verified = C.read_json_if_exists(matter_dir / "verified-authorities.json")
    if preds is None:
        errors.append("predicates.json: file missing")
    else:
        errors += C.validate_against_schema(preds, "predicate", schema_dir)
        if preds.get("benchmark_matter_id") != matter:
            errors.append(f"predicates.json: benchmark_matter_id {preds.get('benchmark_matter_id')!r} != {matter!r}")
        known_auth = {a.get("authority_id"): a for a in (verified or {}).get("authorities") or []}
        if verified is None:
            errors.append("verified-authorities.json: file missing; cannot check predicate authorities")
        qids = set(C.source_question_ids(source))
        seen: set[str] = set()
        for p in preds.get("predicates") or []:
            pid = p.get("predicate_id")
            if pid in seen:
                errors.append(f"duplicate predicate_id {pid}")
            seen.add(pid)
            for aid in p.get("authority_ids") or []:
                a = known_auth.get(aid)
                if a is None:
                    errors.append(f"{pid}: authority {aid} is not in verified-authorities.json")
                elif p.get("necessity") == "indispensable" and a.get("verification_status") != "verified":
                    errors.append(f"{pid}: indispensable predicate relies on {aid} with verification_status {a.get('verification_status')!r}")
            for q in p.get("benchmark_question_ids") or []:
                if qids and q not in qids:
                    errors.append(f"{pid}: question {q} is not in source.json")
            if p.get("necessity") == "indispensable" and p.get("status") == "unresolved":
                warnings.append(f"{pid}: indispensable predicate is unresolved in the scenario")
            if p.get("status") == "synthetic_needed" and p.get("potentially_decisive"):
                warnings.append(f"{pid}: potentially decisive predicate needs a synthetic fact; lawyer review required")
    return C.report(matter, errors, warnings, validator=SCRIPT_NAME, stage="predicates_defined")


def validate_document_specs(matter_dir: Path, schema_dir: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    source = C.read_json_if_exists(matter_dir / "source.json") or {}
    matter = source.get("benchmark_matter_id") or matter_dir.name
    specs = C.read_json_if_exists(matter_dir / "document-specs.json")
    preds = C.read_json_if_exists(matter_dir / "predicates.json")
    if specs is None:
        errors.append("document-specs.json: file missing")
    else:
        errors += C.validate_against_schema(specs, "document-spec", schema_dir)
        if specs.get("benchmark_matter_id") != matter:
            errors.append(f"document-specs.json: benchmark_matter_id {specs.get('benchmark_matter_id')!r} != {matter!r}")
        known = {p.get("predicate_id"): p for p in (preds or {}).get("predicates") or []}
        if preds is None:
            errors.append("predicates.json: file missing; cannot check predicate references")
        qids = set(C.source_question_ids(source))
        filenames: dict[str, str] = {}
        doc_ids: set[str] = set()
        field_ids: set[str] = set()
        for d in specs.get("documents") or []:
            did = d.get("document_id")
            if did in doc_ids:
                errors.append(f"duplicate document_id {did}")
            doc_ids.add(did)
            fname = d.get("public_filename") or ""
            if fname in filenames:
                errors.append(f"{did}: public_filename {fname!r} also used by {filenames[fname]}")
            filenames[fname] = did
            if C.LABEL_LEAK_RE.search(fname):
                errors.append(f"{did}: public_filename {fname!r} leaks a label word")
            for pid in d.get("supports_predicate_ids") or []:
                if pid not in known:
                    errors.append(f"{did}: supports_predicate_ids {pid} is not in predicates.json")
            for q in d.get("required_for_question_ids") or []:
                if qids and q not in qids:
                    errors.append(f"{did}: question {q} is not in source.json")
            if d.get("necessity") == "indispensable" and not any(
                known.get(pid, {}).get("necessity") == "indispensable" for pid in d.get("supports_predicate_ids") or []
            ):
                errors.append(f"{did}: indispensable document supports no indispensable predicate")
            for f in d.get("particulars") or []:
                fid = f.get("field_id")
                if fid in field_ids:
                    errors.append(f"{did}: duplicate field_id {fid}")
                field_ids.add(fid)
                for pid in f.get("supports_predicate_ids") or []:
                    if pid not in known:
                        errors.append(f"{did} {fid}: supports_predicate_ids {pid} is not in predicates.json")
                if f.get("source_origin") == "unknown":
                    warnings.append(f"{did} {fid}: source_origin unknown; cannot be generated")
        for pid, p in known.items():
            if p.get("necessity") == "indispensable" and p.get("status") != "unresolved":
                if not any(e in doc_ids for e in p.get("evidence_document_ids") or []):
                    errors.append(f"{pid}: indispensable predicate has no evidence document in document-specs.json")
    return C.report(matter, errors, warnings, validator=SCRIPT_NAME, stage="documents_specified")


def validate_review_ready(matter_dir: Path, run_dir: Path, matter: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    audit = C.read_json_if_exists(matter_dir / "consistency-audit.json")
    if audit is None:
        errors.append("consistency-audit.json: file missing (run `audit` first)")
    elif audit.get("passed") is not True:
        errors.append("consistency-audit.json: passed is not true")
    for p in (
        matter_dir / BRP.PACKET_NAME, matter_dir / BRP.APPROVAL_NAME,
        run_dir / "review-packets" / matter / BRP.PACKET_NAME, run_dir / "review-packets" / matter / BRP.APPROVAL_NAME,
    ):
        if not p.exists():
            errors.append(f"{p.relative_to(run_dir).as_posix()}: missing (run `packet` first)")
    approval = C.read_json_if_exists(matter_dir / BRP.APPROVAL_NAME)
    if approval is not None:
        errors += C.validate_against_schema(approval, "lawyer-review")
    return C.report(matter, errors, warnings, validator=SCRIPT_NAME, stage="lawyer_review_pending")


def run_stage_validator(run: Run, matter: str, matter_dir: Path, stage: str) -> dict[str, Any]:
    sdir = run.effective_schema_dir()
    if stage == "issue_mapped":
        return VLM.validate_issue_map(matter_dir, sdir)
    if stage == "authorities_candidate":
        return VLM.validate_candidate_authorities(matter_dir, sdir)
    if stage == "authorities_verified":
        return VLM.validate_matter(matter_dir, run.root, sdir)
    if stage == "predicates_defined":
        return validate_predicates(matter_dir, sdir)
    if stage == "documents_specified":
        return validate_document_specs(matter_dir, sdir)
    if stage == "ledger_built":
        return VML.validate_matter(matter_dir, sdir)
    if stage == "synthetic_bundle_generated":
        return VDB.validate_matter(matter_dir, sdir)
    if stage == "lawyer_review_pending":
        return validate_review_ready(matter_dir, run.run_dir, matter)
    raise PipelineError(f"no validator for stage {stage!r}", EXIT_USAGE)


def cmd_validate(args: argparse.Namespace) -> int:
    run = Run(args.run_id, args.runs_dir, args.root)
    stage = args.stage
    if stage in C.HUMAN_ONLY_STATES:
        print(f"refused: {stage} can only be set by a lawyer, never by code", file=sys.stderr)
        return EXIT_HUMAN_ONLY
    if stage not in C.ORDERED_STATES:
        raise PipelineError(f"{stage!r} is not an ordered state; use `block` for failure states", EXIT_USAGE)
    manifest = run.load_manifest()
    entry = run.matter_entry(manifest, args.matter)
    matter_dir = run.matter_dir(entry)
    at = now_iso(args.now)

    if not C.can_advance(entry["state"], stage, entry["state_history"]):
        base = C.effective_ordered_state(entry["state"], entry["state_history"])
        detail = f"refused to advance to {stage}: current state {entry['state']} (progress {base}); states cannot be skipped"
        run.add_event(manifest, args.matter, "advance_refused", detail, at)
        run.save_manifest(manifest)
        print(detail, file=sys.stderr)
        return EXIT_FAIL

    rep = run_stage_validator(run, args.matter, matter_dir, stage)
    if args.report:
        C.write_json(Path(args.report), rep)
    print(C.dumps_json(rep), end="")
    if not rep["passed"]:
        run.add_event(manifest, args.matter, "validation_failed", f"{stage}: {len(rep['errors'])} error(s); first: {rep['errors'][0]}", at)
        run.save_manifest(manifest)
        return EXIT_FAIL

    entry["state"] = stage
    entry["state_history"].append({
        "state": stage, "at": at, "validated_by": rep.get("validator") or SCRIPT_NAME,
        "note": f"{len(rep['warnings'])} warning(s)",
    })
    run.add_event(manifest, args.matter, "advanced", f"{stage} via {rep.get('validator')}; warnings={len(rep['warnings'])}", at)
    run.save_manifest(manifest)
    return EXIT_OK


def cmd_block(args: argparse.Namespace) -> int:
    if args.state not in C.FAILURE_STATES:
        raise PipelineError(f"{args.state!r} is not a failure state; choose from {C.FAILURE_STATES}", EXIT_USAGE)
    run = Run(args.run_id, args.runs_dir, args.root)
    manifest = run.load_manifest()
    entry = run.matter_entry(manifest, args.matter)
    at = now_iso(args.now)
    entry["state"] = args.state
    entry["state_history"].append({"state": args.state, "at": at, "validated_by": SCRIPT_NAME, "note": args.detail})
    run.add_event(manifest, args.matter, "blocked", f"{args.state}: {args.detail}", at)
    run.save_manifest(manifest)
    print(f"{args.matter} -> {args.state}")
    return EXIT_OK


def cmd_event(args: argparse.Namespace) -> int:
    run = Run(args.run_id, args.runs_dir, args.root)
    manifest = run.load_manifest()
    if args.matter:
        run.matter_entry(manifest, args.matter)
    run.add_event(manifest, args.matter, args.event, args.detail, now_iso(args.now))
    run.save_manifest(manifest)
    print(f"event recorded: {args.event}")
    return EXIT_OK


def cmd_audit(args: argparse.Namespace) -> int:
    run = Run(args.run_id, args.runs_dir, args.root)
    manifest = run.load_manifest()
    entry = run.matter_entry(manifest, args.matter)
    matter_dir = run.matter_dir(entry)
    sdir = run.effective_schema_dir()
    reports = {
        "legal_maps": VLM.validate_matter(matter_dir, run.root, sdir),
        "matter_ledger": VML.validate_matter(matter_dir, sdir),
        "document_bundle": VDB.validate_matter(matter_dir, sdir),
        "predicates": validate_predicates(matter_dir, sdir),
        "document_specs": validate_document_specs(matter_dir, sdir),
    }
    audit = {
        "matter": args.matter,
        "run_id": args.run_id,
        "passed": all(r["passed"] for r in reports.values()),
        "status": "unverified",
        "produced_by": SCRIPT_NAME,
        "error_count": sum(len(r["errors"]) for r in reports.values()),
        "warning_count": sum(len(r["warnings"]) for r in reports.values()),
        "temporal_warnings": reports["legal_maps"].get("temporal_warnings") or [],
        "reports": reports,
    }
    C.write_json(matter_dir / "consistency-audit.json", audit)
    C.write_json(run.run_dir / "audits" / f"consistency-audit-{args.matter}.json", audit)
    print(C.dumps_json({k: v for k, v in audit.items() if k != "reports"}), end="")
    return EXIT_OK if audit["passed"] else EXIT_FAIL


def cmd_packet(args: argparse.Namespace) -> int:
    run = Run(args.run_id, args.runs_dir, args.root)
    manifest = run.load_manifest()
    entry = run.matter_entry(manifest, args.matter)
    matter_dir = run.matter_dir(entry)
    result = BRP.write_packet(matter_dir, run.root, run.run_dir, run.effective_schema_dir(), args.run_id, lint=not args.no_lint)
    print(C.dumps_json({k: v for k, v in result.items() if k != "reports"}), end="")
    return EXIT_OK if result["markdownlint"] in ("skipped", "clean") else EXIT_FAIL


def render_matter(matter_dir: Path) -> tuple[list[str], list[str]]:
    written: list[str] = []
    errors: list[str] = []
    sdir = matter_dir / "synthetic-documents"
    for path in sorted(sdir.glob("*.json")) if sdir.is_dir() else []:
        doc = C.read_json(path)
        text = doc.get("rendered_text") or ""
        expected = C.prefixed_sha256(C.sha256_text(text))
        if doc.get("document_hash") != expected:
            errors.append(f"{path.stem}: document_hash {doc.get('document_hash')} != {expected}")
        if C.SYNTHETIC_MARKER not in text:
            errors.append(f"{path.stem}: rendered_text lacks the synthetic marker")
        C.atomic_write_text(path.with_suffix(".txt"), text)
        written.append(path.with_suffix(".txt").name)
    if not written:
        errors.append("no synthetic-documents/*.json to render")
    return written, errors


def cmd_render(args: argparse.Namespace) -> int:
    run = Run(args.run_id, args.runs_dir, args.root)
    manifest = run.load_manifest()
    entry = run.matter_entry(manifest, args.matter)
    written, errors = render_matter(run.matter_dir(entry))
    print(C.dumps_json({"matter": args.matter, "written": written, "errors": errors, "passed": not errors}), end="")
    return EXIT_OK if not errors else EXIT_FAIL


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

def _mergeable(entry: dict[str, Any]) -> bool:
    return C.state_index(entry["state"]) >= C.state_index(PUBLIC_ORDERED_MIN_STATE)


def gold_record_for_question(
    run: Run, entry: dict[str, Any], source: dict[str, Any], question: dict[str, Any], flat: dict[str, Any] | None,
    issue_map: dict[str, Any], legal_map: dict[str, Any], predicates: dict[str, Any], specs: dict[str, Any],
    sdocs: dict[str, dict[str, Any]], manifest: dict[str, Any],
) -> dict[str, Any]:
    qid = question["benchmark_question_id"]
    matter = source["benchmark_matter_id"]
    q_issue = next((q for q in issue_map.get("questions") or [] if q.get("benchmark_question_id") == qid), None)
    q_legal = next((q for q in legal_map.get("questions") or [] if q.get("benchmark_question_id") == qid), None)
    if q_issue is None or q_legal is None:
        raise PipelineError(f"{qid}: missing from issue-map or legal-map; cannot merge")
    authority_ids = sorted(set((q_legal.get("indispensable_authority_ids") or []) + (q_legal.get("supporting_authority_ids") or [])))
    predicate_ids = sorted(p["predicate_id"] for p in predicates.get("predicates") or [] if qid in (p.get("benchmark_question_ids") or []))
    pred_set = set(predicate_ids)
    indispensable_docs = sorted(
        d["document_id"] for d in specs.get("documents") or []
        if d.get("necessity") == "indispensable"
        and (qid in (d.get("required_for_question_ids") or []) or pred_set.intersection(d.get("supports_predicate_ids") or []))
    )
    filenames = sorted(doc["public_filename"] for doc in sdocs.values())
    background = question.get("effective_background_normalized") or question.get("effective_background_original") or (source.get("matter_background") or {}).get("normalized") or ""
    provenance_src = flat.get("provenance") if flat else None
    return {
        "benchmark_question_id": qid,
        "benchmark_matter_id": matter,
        "run_id": run.run_id,
        "atomic_id": question.get("atomic_id") or (flat or {}).get("atomic_id") or "unknown",
        "public_input": {
            "background": background,
            "question": question.get("question_normalized") or question.get("question_original") or "",
            "document_filenames": filenames,
            "matter_group": matter,
        },
        "private_gold": {
            "issue_map": q_issue,
            "legal_map": q_legal,
            "authority_ids": authority_ids,
            "predicate_ids": predicate_ids,
            "indispensable_document_ids": indispensable_docs,
            "provenance": {
                "source_matter_id": (provenance_src or {}).get("source_matter_id") or source.get("source_matter_id"),
                "part_uid": question.get("part_uid") or (provenance_src or {}).get("part_uid") or "",
                "pdf_page": question.get("pdf_page") if question.get("pdf_page") is not None else (provenance_src or {}).get("pdf_page"),
                "source_quote": question.get("source_quote") or (flat or {}).get("source_quote") or "",
                "selected_questions_path": manifest["source_dataset"]["selected_questions_path"],
            },
        },
        "pipeline_state": entry["state"],
        "lawyer_validation_status": "validated" if entry["state"] == "lawyer_validated" else "pending",
    }


def authority_summary(verified: dict[str, Any] | None) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    missing: list[str] = []
    for a in (verified or {}).get("authorities") or []:
        st = a.get("verification_status") or "unknown"
        by_status[st] = by_status.get(st, 0) + 1
        v = a.get("verification") or {}
        tier = str(v.get("source_tier")) if v.get("source_tier") is not None else "none"
        by_tier[tier] = by_tier.get(tier, 0) + 1
        if v.get("omitted_authority_needed"):
            missing.append(f"{a.get('authority_id')}: {v['omitted_authority_needed']}")
        if st in ("unresolved", "original_judgment_required") and v.get("notes"):
            missing.append(f"{a.get('authority_id')}: {v['notes']}")
    return {"by_status": dict(sorted(by_status.items())), "by_tier": dict(sorted(by_tier.items())), "missing_source_packages": missing}


def scan_public_for_private_fields(paths: list[Path]) -> list[str]:
    leaks: list[str] = []
    for p in paths:
        text = C.read_text(p)
        for m in PRIVATE_FIELD_RE.finditer(text):
            leaks.append(f"{p.name}: {m.group(0)}")
    return leaks


def cmd_merge(args: argparse.Namespace) -> int:
    run = Run(args.run_id, args.runs_dir, args.root)
    manifest = run.load_manifest()
    public_dir = run.run_dir / "public" / "input"
    private_gold = run.run_dir / "private" / "gold"
    private_audit = run.run_dir / "private" / "audit"
    audits = run.run_dir / "audits"
    for d in (public_dir, private_gold, private_audit, audits):
        d.mkdir(parents=True, exist_ok=True)

    gold_rows: list[dict[str, Any]] = []
    public_rows: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {}
    unresolved: dict[str, list[dict[str, Any]]] = {}
    summary_matters: dict[str, Any] = {}
    public_doc_paths: list[Path] = []
    state_counts: dict[str, int] = {}

    for entry in manifest["matters"]:
        state_counts[entry["state"]] = state_counts.get(entry["state"], 0) + 1
        matter = entry["benchmark_matter_id"]
        matter_dir = run.matter_dir(entry)
        verified = C.read_json_if_exists(matter_dir / "verified-authorities.json")
        preds = C.read_json_if_exists(matter_dir / "predicates.json")
        specs = C.read_json_if_exists(matter_dir / "document-specs.json")
        ledger = C.read_json_if_exists(matter_dir / "matter-ledger.json")
        summary_matters[matter] = {
            "state": entry["state"],
            "role": entry["role"],
            "authorities": len((verified or {}).get("authorities") or []),
            "predicates": len((preds or {}).get("predicates") or []),
            "documents": len((specs or {}).get("documents") or []),
            "synthetic_additions": len((ledger or {}).get("synthetic_additions") or []),
            "merged": _mergeable(entry),
        }
        if verified is not None:
            coverage[matter] = authority_summary(verified)
            unres = [
                {"authority_id": a.get("authority_id"), "verification_status": a.get("verification_status"),
                 "title": a.get("title"), "notes": (a.get("verification") or {}).get("notes")}
                for a in verified.get("authorities") or []
                if a.get("verification_status") not in ("verified", "rejected")
            ]
            if unres:
                unresolved[matter] = unres
        if not _mergeable(entry):
            continue

        source = C.read_json_if_exists(matter_dir / "source.json")
        issue_map = C.read_json_if_exists(matter_dir / "issue-map.json")
        legal_map = C.read_json_if_exists(matter_dir / "legal-map.json")
        if not all([source, issue_map, legal_map, preds, specs]):
            raise PipelineError(f"{matter}: state {entry['state']} but artifacts are missing; cannot merge")
        sdocs = VDB.load_synthetic_documents(matter_dir, [])
        flat_by_id = {q["benchmark_question_id"]: q for q in source.get("flat_questions") or []}
        for question in source.get("questions") or []:
            rec = gold_record_for_question(
                run, entry, source, question, flat_by_id.get(question["benchmark_question_id"]),
                issue_map, legal_map, preds, specs, sdocs, manifest,
            )
            errors = C.validate_against_schema(rec, "gold-question", run.effective_schema_dir())
            if errors:
                raise PipelineError(f"{rec['benchmark_question_id']}: gold record invalid: " + "; ".join(errors))
            gold_rows.append(rec)
            public_rows.append({"benchmark_question_id": rec["benchmark_question_id"], **rec["public_input"]})
        for did, doc in sorted(sdocs.items()):
            text = doc.get("rendered_text") or ""
            if C.prefixed_sha256(C.sha256_text(text)) != doc.get("document_hash"):
                raise PipelineError(f"{did}: document_hash does not match rendered_text; refusing to publish")
            target = public_dir / "documents" / matter / doc["public_filename"]
            C.atomic_write_text(target, text)
            public_doc_paths.append(target)

    C.write_jsonl(private_gold / "gold-questions.jsonl", gold_rows)
    C.write_jsonl(public_dir / "questions.jsonl", public_rows)
    C.write_json(audits / "run-manifest.json", manifest)
    C.write_json(audits / "source-coverage.json", {"run_id": run.run_id, "status": "unverified", "matters": coverage})
    C.write_json(audits / "unresolved-authorities.json", {"run_id": run.run_id, "status": "unverified", "matters": unresolved})
    C.write_json(audits / "pipeline-summary.json", {
        "run_id": run.run_id,
        "status": "unverified",
        "state_counts": dict(sorted(state_counts.items())),
        "merged_matters": sorted(m for m, s in summary_matters.items() if s["merged"]),
        "gold_question_count": len(gold_rows),
        "public_document_count": len(public_doc_paths),
        "matters": summary_matters,
    })
    for name in ("run-manifest.json", "source-coverage.json", "unresolved-authorities.json", "pipeline-summary.json"):
        shutil.copyfile(audits / name, private_audit / name)

    leaks = scan_public_for_private_fields([public_dir / "questions.jsonl", *public_doc_paths])
    if leaks:
        raise PipelineError("public output contains private field names: " + "; ".join(leaks))
    print(f"merged {len(gold_rows)} gold questions from {len([m for m in summary_matters.values() if m['merged']])} matter(s); {len(public_doc_paths)} public documents")
    return EXIT_OK


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--run-id", required=True)
        p.add_argument("--runs-dir", type=Path, default=None, help=f"Default {C.RUNS_DIR}")
        p.add_argument("--root", type=Path, default=None, help="Repo root used to resolve relative source paths.")
        p.add_argument("--now", default=None, help="Pin timestamps (ISO string) for reproducible output.")

    p = sub.add_parser("init", help="create a run directory and manifest")
    common(p)
    p.add_argument("--source-dir", type=Path, default=None)
    p.add_argument("--schema-dir", type=Path, default=None)
    p.add_argument("--pilot", default="", help="Comma-separated matter ids, e.g. M001,M006")
    p.add_argument("--reason", action="append", help='Mxxx="why this matter is a pilot" (repeatable)')
    p.add_argument("--description", default=None)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="validate one stage and advance the matter if it passes")
    common(p)
    p.add_argument("--matter", required=True)
    p.add_argument("--stage", required=True)
    p.add_argument("--report", default=None)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("block", help="park a matter in a failure state")
    common(p)
    p.add_argument("--matter", required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--detail", required=True)
    p.set_defaults(func=cmd_block)

    p = sub.add_parser("event", help="append an audit event")
    common(p)
    p.add_argument("--matter", default=None)
    p.add_argument("--event", required=True)
    p.add_argument("--detail", required=True)
    p.set_defaults(func=cmd_event)

    p = sub.add_parser("audit", help="run every validator and write consistency-audit.json")
    common(p)
    p.add_argument("--matter", required=True)
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("packet", help="build the lawyer review packet and blank approval.json")
    common(p)
    p.add_argument("--matter", required=True)
    p.add_argument("--no-lint", action="store_true")
    p.set_defaults(func=cmd_packet)

    p = sub.add_parser("render", help="write synthetic-documents/<DOC>.txt and check hashes")
    common(p)
    p.add_argument("--matter", required=True)
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("merge", help="coordinator-only: build public/private outputs and audits")
    common(p)
    p.set_defaults(func=cmd_merge)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
