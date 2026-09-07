"""Render a lawyer review packet and an empty approval record for one matter.

The packet is a plain Markdown file a reviewing lawyer reads top to bottom:
the past-paper background and questions, the issues the pipeline identified,
every authority with the exact excerpt the verifier read and where it read
it, the draft gold answers with a claim-to-authority matrix, the predicates
with their counterfactuals, the document bundle and its decisive particulars,
every synthetic addition, and whatever the validators still flag. Nothing in
it is presented as settled law; every section is marked unverified.

`approval.json` is generated with every approval `false`, the reviewer fields
`null` and `overall_status: pending`. Code never fills reviewer fields; only a
human does, and the lawyer-review schema enforces that pending packets stay
blank.

Output is deterministic (same inputs, same bytes) and lint-clean under
`markdownlint-cli2` (blank lines around headings, lists, tables and fences;
no inline HTML). The packet is written into the matter directory and copied
to `<run>/review-packets/<matter>/`.

    python scripts/legal-qa-pipeline/build_review_packets.py --matter-dir <dir> [--run-dir <dir>] [--root <repo>]
"""

from __future__ import annotations

import re

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lqa_common as C  # noqa: E402
import validate_document_bundles as VDB  # noqa: E402
import validate_legal_maps as VLM  # noqa: E402
import validate_matter_ledgers as VML  # noqa: E402

SCRIPT_NAME = "build_review_packets.py"
PACKET_NAME = "lawyer-review-packet.md"
APPROVAL_NAME = "approval.json"


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def cell(value: Any) -> str:
    """One table cell: no pipes, no newlines, never empty."""
    if value is None:
        return "-"
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(v) for v in value) if value else "-"
    if isinstance(value, dict):
        value = "; ".join(f"{k}={v}" for k, v in value.items() if v not in (None, "", [])) or "-"
    text = C.normalize_ws(str(value)).replace("|", "\\|")
    return text or "-"


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["_None recorded._", ""]
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join([" --- "] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(cell(v) for v in r) + " |")
    out.append("")
    return out


def code(value: Any) -> str:
    """Inline code span for paths and URLs, so markdownlint never sees a bare URL."""
    if value in (None, ""):
        return "-"
    return "`" + C.normalize_ws(str(value)).replace("`", "'") + "`"


_BARE_URL = re.compile(r"(?<![`<(\[])(https?://[^\s`<>)\]]+)")


def wrap_bare_urls(text: str) -> str:
    """Angle-bracket any URL that free text (verifier notes, reasons) left bare."""
    return _BARE_URL.sub(r"<>", text)


def heading(level: int, text: str) -> list[str]:
    return ["#" * level + " " + text, ""]


def paragraph(text: str | None) -> list[str]:
    return [C.normalize_ws(text) if text else "_Not available._", ""]


def bullets(items: list[str]) -> list[str]:
    if not items:
        return ["_None._", ""]
    return [f"- {C.normalize_ws(i)}" for i in items] + [""]


def quote(text: str | None) -> list[str]:
    if not text:
        return ["_Not available._", ""]
    return [f"> {line}" if line else ">" for line in str(text).strip().splitlines()] + [""]


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _authority_rows(verified: dict[str, Any] | None, indispensable: set[str]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for a in (verified or {}).get("authorities") or []:
        v = a.get("verification") or {}
        title = a.get("title")
        if a.get("section"):
            title = f"{title}, s. {a['section']}" + (f"({a['subsection']})" if a.get("subsection") else "")
        if a.get("case_citation"):
            title = f"{title} {a['case_citation']}"
        period = f"{v.get('effective_from') or '?'} to {v.get('effective_to') or 'in force/unknown'}" if v else "-"
        rows.append([
            a.get("authority_id"),
            "indispensable" if a.get("authority_id") in indispensable else (v.get("necessity_assessed") or a.get("necessity_claimed") or "-"),
            title,
            v.get("exact_excerpt") if v else "-",
            code(v.get("source_path")) if v else "-",
            v.get("locator") if v else "-",
            period,
            v.get("applicable_version_for_matter_date") if v else "-",
            a.get("verification_status"),
            v.get("source_tier") if v else "-",
        ])
    return rows


def _indispensable(legal_map: dict[str, Any] | None, verified: dict[str, Any] | None) -> set[str]:
    if legal_map is None and verified is None:
        return set()
    return VLM._indispensable_ids(legal_map or {}, verified or {})


def build_packet(
    matter_dir: Path, root: Path, schema_dir: Path | None = None, run_id: str | None = None
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Return (markdown, approval record, combined validator report)."""
    matter_dir = Path(matter_dir)
    source = C.read_json_if_exists(matter_dir / "source.json") or {}
    matter = source.get("benchmark_matter_id") or matter_dir.name
    issue_map = C.read_json_if_exists(matter_dir / "issue-map.json")
    verified = C.read_json_if_exists(matter_dir / "verified-authorities.json")
    legal_map = C.read_json_if_exists(matter_dir / "legal-map.json")
    predicates = C.read_json_if_exists(matter_dir / "predicates.json")
    specs = C.read_json_if_exists(matter_dir / "document-specs.json")
    ledger = C.read_json_if_exists(matter_dir / "matter-ledger.json")
    sdocs = VDB.load_synthetic_documents(matter_dir, [])
    audit = C.read_json_if_exists(matter_dir / "consistency-audit.json")

    reports = {
        "legal_maps": VLM.validate_matter(matter_dir, root, schema_dir),
        "matter_ledger": VML.validate_matter(matter_dir, schema_dir),
        "document_bundle": VDB.validate_matter(matter_dir, schema_dir),
    }
    combined = {
        "matter": matter,
        "passed": all(r["passed"] for r in reports.values()),
        "status": "unverified",
        "reports": reports,
    }

    run_id = run_id or legal_map and legal_map.get("run_id") or source.get("run_id") or "-"
    indispensable = _indispensable(legal_map, verified)
    facts = {f.get("fact_id"): f for f in (ledger or {}).get("source_facts") or []}
    preds = {p.get("predicate_id"): p for p in (predicates or {}).get("predicates") or []}

    md: list[str] = []
    md += heading(1, f"Lawyer review packet: {matter}")
    md += paragraph(
        f"Run `{run_id}`. Every statement below is machine-assembled and status=unverified until you sign it off. "
        "Nothing here is legal advice or verified legal fact. Please check each section and record your decision in the approval fields at the end."
    )
    md += heading(2, "1. Source (past paper)")
    md += heading(3, "1.1 Original background")
    md += quote((source.get("matter_background") or {}).get("original"))
    md += heading(3, "1.2 Normalised background")
    md += quote((source.get("matter_background") or {}).get("normalized"))
    md += heading(3, "1.3 Questions")
    md += table(
        ["Question", "Atomic id", "Part", "Page", "Marks", "Text"],
        [[q.get("benchmark_question_id"), q.get("atomic_id"), q.get("part_uid"), q.get("pdf_page"), q.get("marks"), q.get("question_normalized") or q.get("question_original")]
         for q in source.get("questions") or []],
    )

    md += heading(2, "2. Issues identified")
    if issue_map:
        md += paragraph(issue_map.get("matter_summary"))
        md += table(
            ["Party", "Name in source", "Role", "Capacity", "Uncertainties"],
            [[p.get("party_ref"), p.get("name_as_in_source"), p.get("role"), p.get("legal_capacity"), p.get("capacity_uncertainties")] for p in issue_map.get("parties") or []],
        )
        md += table(
            ["Date in source", "ISO", "Event", "Legal significance"],
            [[d.get("date_as_in_source"), d.get("iso_date"), d.get("event"), d.get("legal_significance")] for d in issue_map.get("relevant_dates") or []],
        )
        md += table(
            ["Question", "Primary issue", "Secondary issues", "Domain", "Conclusion required", "Depends on unresolved facts"],
            [[q.get("benchmark_question_id"), q.get("primary_issue"), q.get("secondary_issues"), q.get("legal_domain"), q.get("required_legal_conclusion"),
              ("yes: " + "; ".join(q.get("unresolved_fact_dependencies") or [])) if q.get("answer_depends_on_unresolved_facts") else "no"]
             for q in issue_map.get("questions") or []],
        )
    else:
        md += paragraph(None)

    md += heading(2, "3. Authorities (as verified by the pipeline)")
    md += paragraph(
        f"Matter reference date: {(verified or {}).get('matter_reference_date') or 'not stated'} "
        f"({(verified or {}).get('matter_reference_date_basis') or 'no basis recorded'}). "
        "Excerpts are verbatim copies from the source path shown; please confirm each one supports the proposition it is used for."
    )
    md += table(
        ["Authority", "Necessity", "Title", "Exact excerpt", "Source path", "Locator", "Effective period", "Version for matter date", "Verification status", "Tier"],
        _authority_rows(verified, indispensable),
    )
    notes_rows = [[a.get("authority_id"), (a.get("verification") or {}).get("notes")] for a in (verified or {}).get("authorities") or [] if (a.get("verification") or {}).get("notes")]
    if notes_rows:
        md += heading(3, "3.1 Verifier notes")
        md += table(["Authority", "Notes"], notes_rows)
    neg = (verified or {}).get("negative_retrieval") or []
    if neg:
        md += heading(3, "3.2 Searches that found nothing usable")
        md += table(["Query", "Method", "Corpus", "Result"], [[n.get("query"), n.get("method"), n.get("corpus"), n.get("result")] for n in neg])

    md += heading(2, "4. Draft gold answers")
    md += paragraph("Drafts only. Issue / rule / application / conclusion, followed by the reasoning chain the pipeline recorded.")
    for n, q in enumerate((legal_map or {}).get("questions") or [], start=1):
        qid = q.get("benchmark_question_id")
        g = q.get("gold_answer_draft") or {}
        md += heading(3, f"4.{n} {qid}")
        md += paragraph(f"Issues: {'; '.join(q.get('issues') or [])}. Legal hop count: {q.get('legal_hop_count')}. Confidence (pipeline self-report): {q.get('confidence')}. Status: {q.get('status')}.")
        md += table(
            ["Part", "Draft"],
            [["Issue", g.get("issue")], ["Rule", g.get("rule")], ["Application", g.get("application")], ["Conclusion", g.get("conclusion")]],
        )
        md += table(
            ["Step", "Reasoning", "Authorities", "Scenario facts"],
            [[s.get("step"), s.get("text"), s.get("authority_ids"), s.get("relies_on_scenario_fact_ids")] for s in q.get("reasoning_chain") or []],
        )

    md += heading(2, "5. Claim-to-authority matrix")
    claim_rows: list[list[Any]] = []
    for q in (legal_map or {}).get("questions") or []:
        for c in q.get("answer_claims") or []:
            excerpts = "; ".join(f"{e.get('authority_id')}: \"{C.normalize_ws(e.get('excerpt'))}\"" for e in c.get("supporting_excerpts") or [])
            claim_rows.append([
                c.get("claim_id"), c.get("claim_type"), c.get("claim_text"), c.get("support_strength"),
                c.get("supporting_authority_ids"), excerpts or c.get("scenario_fact_basis"), c.get("verification_status"),
            ])
    md += table(["Claim", "Type", "Claim text", "Support", "Authorities", "Excerpts / fact basis", "Verification"], claim_rows)

    md += heading(2, "6. Predicates")
    md += table(
        ["Predicate", "Name", "Description", "Expected", "Type", "Necessity", "Polarity", "Authorities", "Facts", "Evidence documents", "Status", "Counterfactual effect", "Potentially decisive"],
        [[p.get("predicate_id"), p.get("predicate"), p.get("description"), p.get("expected_value"), p.get("predicate_type"), p.get("necessity"), p.get("polarity"),
          p.get("authority_ids"), p.get("supporting_fact_ids"), p.get("evidence_document_ids"), p.get("status"), p.get("counterfactual_effect"), p.get("potentially_decisive")]
         for p in preds.values()],
    )

    md += heading(2, "7. Document bundle")
    md += table(
        ["Document", "Type", "Roles", "Necessity", "Public filename", "For questions", "Supports predicates", "Inclusion reason", "Generation status", "Rendered"],
        [[d.get("document_id"), d.get("document_type"), d.get("document_role"), d.get("necessity"), d.get("public_filename"), d.get("required_for_question_ids"),
          d.get("supports_predicate_ids"), d.get("inclusion_reason"), d.get("generation_status"), "yes" if d.get("document_id") in sdocs else "no"]
         for d in (specs or {}).get("documents") or []],
    )
    distractors = [[d.get("document_id"), d.get("distractor_rationale")] for d in (specs or {}).get("documents") or [] if d.get("necessity") == "distractor"]
    if distractors:
        md += heading(3, "7.1 Distractor rationale")
        md += table(["Document", "Why it cannot create an alternative correct answer"], distractors)

    md += heading(2, "8. Decisive particulars")
    decisive_rows: list[list[Any]] = []
    for d in (specs or {}).get("documents") or []:
        for f in d.get("particulars") or []:
            if f.get("legal_relevance") == "decisive":
                fact = facts.get(f.get("value_source")) or {}
                decisive_rows.append([
                    d.get("document_id"), f.get("field_id"), f.get("field_name"), f.get("value_source"), fact.get("value", "-"),
                    f.get("source_origin"), f.get("supports_predicate_ids"), f.get("decisive_generation_justification"),
                ])
    md += table(["Document", "Field", "Name", "Value source", "Ledger value", "Origin", "Supports predicates", "Justification (synthetic decisive only)"], decisive_rows)

    md += heading(2, "9. Synthetic additions")
    md += paragraph("Facts that are not in the past paper and not derived from law. Neutral additions must not be able to change any answer; decisive additions need your explicit approval.")
    md += table(
        ["Fact", "Field", "Value", "Origin", "Reason", "Could affect", "Legal review required"],
        [[a.get("fact_id"), facts.get(a.get("fact_id"), {}).get("field"), facts.get(a.get("fact_id"), {}).get("value"), facts.get(a.get("fact_id"), {}).get("origin"),
          a.get("reason"), a.get("could_affect"), a.get("legal_review_required")]
         for a in (ledger or {}).get("synthetic_additions") or []],
    )

    md += heading(2, "10. Counterfactual checks")
    md += paragraph("For each predicate, what the pipeline believes would change if the predicate had the opposite value. Please confirm or correct.")
    md += table(
        ["Predicate", "Expected value", "If reversed", "Questions affected", "Potentially decisive"],
        [[p.get("predicate_id"), p.get("expected_value"), p.get("counterfactual_effect"), p.get("benchmark_question_ids"), p.get("potentially_decisive")] for p in preds.values()],
    )

    md += heading(2, "11. Outstanding uncertainties and validator output")
    for n, (key, label) in enumerate((("legal_maps", "Legal maps"), ("matter_ledger", "Matter ledger"), ("document_bundle", "Document bundle")), start=1):
        rep = reports[key]
        md += heading(3, f"11.{n} {label} ({'passed' if rep['passed'] else 'FAILED'})")
        md += heading(4, "Errors")
        md += bullets(rep["errors"])
        md += heading(4, "Warnings")
        md += bullets(rep["warnings"])
    temporal = reports["legal_maps"].get("temporal_warnings") or []
    md += heading(3, "11.4 Temporal applicability")
    md += bullets(temporal)
    fact_conflicts = [f"{c.get('fact_ids')}: {c.get('description')} ({c.get('resolution')})" for c in (ledger or {}).get("fact_conflicts") or []]
    source_conflicts = [f"{c.get('authority_id')}: {c.get('description')}" for c in (verified or {}).get("source_conflicts") or []]
    md += heading(3, "11.5 Recorded conflicts")
    md += bullets(fact_conflicts + source_conflicts)
    md += heading(3, "11.6 Consistency audit")
    if audit is None:
        md += paragraph("No consistency-audit.json recorded for this matter yet.")
    else:
        md += paragraph(f"consistency-audit.json passed: {audit.get('passed')}.")

    md += heading(2, "12. Approval")
    md += paragraph("Record your decision in `approval.json` next to this packet (fields below). This file is generated blank and is never filled by code.")
    md += bullets([
        "reviewer_id: (your identifier)",
        "review_date: (ISO date)",
        "background_approved: true/false",
        "issues_approved: true/false",
        "authorities_approved: true/false",
        "predicates_approved: true/false",
        "document_bundle_approved: true/false",
        "gold_answers_approved: true/false",
        "required_corrections: list of {target, correction, severity}",
        "overall_status: approved / corrections_required / rejected",
    ])

    approval = {
        "matter_id": matter,
        "reviewer_id": None,
        "review_date": None,
        "background_approved": False,
        "issues_approved": False,
        "authorities_approved": False,
        "predicates_approved": False,
        "document_bundle_approved": False,
        "gold_answers_approved": False,
        "required_corrections": [],
        "overall_status": "pending",
    }
    text = "\n".join(md).rstrip("\n") + "\n"
    return text, approval, combined


LINT_CONFIG = Path(__file__).resolve().parent / "markdownlint-packet.jsonc"


def lint_markdown(path: Path) -> str | None:
    """Run markdownlint-cli2 if available; return its output when it complains, else None.

    Uses the package's own config (same rules as the repo's, minus the repo
    globs) so a packet written to any directory is judged the same way.
    """
    exe = shutil.which("npx")
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "--no-install", "markdownlint-cli2", "--config", str(LINT_CONFIG), str(path)],
            capture_output=True, text=True, timeout=120, cwd=str(path.parent),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0:
        return ""
    return (proc.stdout or "") + (proc.stderr or "")


def write_packet(
    matter_dir: Path, root: Path | None = None, run_dir: Path | None = None,
    schema_dir: Path | None = None, run_id: str | None = None, lint: bool = False,
) -> dict[str, Any]:
    matter_dir = Path(matter_dir)
    root = Path(root) if root else C.ROOT
    run_dir = Path(run_dir) if run_dir else matter_dir.parents[1]
    text, approval, combined = build_packet(matter_dir, root, schema_dir, run_id)
    text = wrap_bare_urls(text)
    schema_errors = C.validate_against_schema(approval, "lawyer-review", schema_dir)
    if schema_errors:
        raise RuntimeError("generated approval.json violates lawyer-review schema: " + "; ".join(schema_errors))

    C.atomic_write_text(matter_dir / PACKET_NAME, text)
    C.write_json(matter_dir / APPROVAL_NAME, approval)
    packet_dir = run_dir / "review-packets" / (approval["matter_id"])
    C.atomic_write_text(packet_dir / PACKET_NAME, text)
    existing = packet_dir / APPROVAL_NAME
    if existing.exists():
        prior = C.read_json(existing)
        if prior.get("reviewer_id") is not None:
            # A human has started filling this in; never overwrite their work.
            combined["approval_preserved"] = True
        else:
            C.write_json(existing, approval)
    else:
        C.write_json(existing, approval)

    lint_result = lint_markdown(matter_dir / PACKET_NAME) if lint else None
    combined["packet_path"] = str(matter_dir / PACKET_NAME)
    combined["review_packet_copy"] = str(packet_dir / PACKET_NAME)
    combined["markdownlint"] = "skipped" if lint_result is None else ("clean" if lint_result == "" else lint_result)
    return combined


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matter-dir", required=True, type=Path)
    ap.add_argument("--run-dir", type=Path, default=None, help="Defaults to two levels above the matter dir.")
    ap.add_argument("--root", type=Path, default=None)
    ap.add_argument("--schema-dir", type=Path, default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--no-lint", action="store_true", help="Skip the markdownlint-cli2 pass.")
    args = ap.parse_args(argv)
    result = write_packet(args.matter_dir, args.root, args.run_dir, args.schema_dir, args.run_id, lint=not args.no_lint)
    print(C.dumps_json({k: v for k, v in result.items() if k != "reports"}), end="")
    if result["markdownlint"] not in ("skipped", "clean"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
