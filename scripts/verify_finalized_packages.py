"""Check every `finalized-sources/` package against its manifest and its tree folder.

    uv run python scripts/verify_finalized_packages.py            # report, exit 1 on defects
    uv run python scripts/verify_finalized_packages.py --strict   # also fail on legacy entries and warnings
    uv run python scripts/verify_finalized_packages.py --migrate  # add hash_mode to legacy entries

For each package this checks that every listed file exists and matches its
recorded hash (see `package_integrity.py` for the two hash modes), that no
file sits in the folder unlisted, that the folder has a matching
`finalized/<slug>/` with at least one tree, and that the manifest carries a
`statute_note`. It also lists `finalized/` folders that have no package.
Nothing here says anything about the legal text; a clean run means the
package is internally consistent, not that the statute is verified.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_integrity import check_entry, migrate_entry  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / "data/legal-sources/library"
FINALIZED = LIBRARY / "finalized"
FINALIZED_SOURCES = LIBRARY / "finalized-sources"
PIPELINE_STATUSES = {
    "pipeline-finalized, lawyer-unverified",
    "needs_structural_review",
    "blocked_insufficient_local_source",
}
RECONCILIATION_CLASSES = {
    "already_incorporated_in_baseline",
    "applied_from_held_source",
    "held_but_not_applied",
    "known_but_not_held",
    "ambiguous_or_unconfirmed",
}


def verify(finalized: Path = FINALIZED, sources: Path = FINALIZED_SOURCES, migrate: bool = False) -> dict:
    report: dict = {"packages": {}, "errors": [], "warnings": [], "legacy": [], "trees_without_package": []}
    package_slugs = {p.name for p in sources.iterdir() if p.is_dir()} if sources.exists() else set()
    tree_slugs = {p.name for p in finalized.iterdir() if p.is_dir()} if finalized.exists() else set()
    report["trees_without_package"] = sorted(tree_slugs - package_slugs)
    for slug in sorted(package_slugs):
        pdir = sources / slug
        manifest_path = pdir / "manifest.json"
        entry_report = {"files": 0, "ok": 0, "legacy": 0, "problems": []}
        report["packages"][slug] = entry_report
        if not manifest_path.exists():
            report["errors"].append(f"{slug}: no manifest.json")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        changed = False
        listed = set()
        for i, entry in enumerate(manifest.get("files", [])):
            listed.add(entry["file"])
            entry_report["files"] += 1
            status, detail = check_entry(pdir, entry)
            if status == "ok":
                entry_report["ok"] += 1
            elif status == "legacy":
                entry_report["legacy"] += 1
                report["legacy"].append(f"{slug}/{entry['file']}: {detail}")
                if migrate:
                    manifest["files"][i] = migrate_entry(pdir, entry)
                    changed = True
            else:
                entry_report["problems"].append(detail)
                report["errors"].append(f"{slug}: {detail}")
        on_disk = {p.name for p in pdir.iterdir() if p.is_file() and p.name != "manifest.json"}
        for name in sorted(on_disk - listed):
            report["warnings"].append(f"{slug}: {name} is in the folder but not in the manifest")
        if slug not in tree_slugs:
            report["errors"].append(f"{slug}: package has no finalized/{slug}/ tree folder")
        elif not list((finalized / slug).glob("*.json")):
            report["errors"].append(f"{slug}: finalized/{slug}/ holds no tree")
        if not manifest.get("statute_note"):
            report["warnings"].append(f"{slug}: manifest has no statute_note")
        # Keys the September 2026 pass requires of a completed package; see
        # library/finalization-worker-brief.md. Absent keys are warnings, so
        # packages from before that pass still verify.
        for key in ("pipeline_status", "baseline", "amendment_reconciliation", "lawyer_verification"):
            if key not in manifest:
                report["warnings"].append(f"{slug}: manifest has no `{key}`")
        status = manifest.get("pipeline_status")
        if status is not None and status not in PIPELINE_STATUSES:
            report["errors"].append(f"{slug}: pipeline_status {status!r} not in {sorted(PIPELINE_STATUSES)}")
        if manifest.get("lawyer_verification") not in (None, "unverified"):
            report["errors"].append(f"{slug}: lawyer_verification must be 'unverified'")
        for row in manifest.get("amendment_reconciliation", []) or []:
            if row.get("classification") not in RECONCILIATION_CLASSES:
                report["errors"].append(
                    f"{slug}: amendment {row.get('instrument')!r} has classification {row.get('classification')!r}"
                )
            src = row.get("source_path")
            if src and not (REPO_ROOT / src).exists():
                report["errors"].append(f"{slug}: amendment {row.get('instrument')!r} source_path {src} does not exist")
        baseline = manifest.get("baseline")
        if isinstance(baseline, dict):
            if not baseline.get("consolidation_cutoff"):
                report["warnings"].append(f"{slug}: baseline has no consolidation_cutoff (use 'unknown' if unknown)")
            if baseline.get("file") and baseline["file"] not in listed:
                report["errors"].append(f"{slug}: baseline.file {baseline['file']!r} is not a file listed in the manifest")
        if changed:
            manifest_path.write_text(
                json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
            )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--strict", action="store_true", help="fail on legacy entries and warnings too")
    parser.add_argument("--migrate", action="store_true", help="rewrite legacy entries with an explicit hash_mode")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    report = verify(migrate=args.migrate)
    n_pk = len(report["packages"])
    n_files = sum(p["files"] for p in report["packages"].values())
    if not args.quiet:
        print(f"{n_pk} packages, {n_files} manifest entries")
        for line in report["errors"]:
            print(f"ERROR   {line}")
        for line in report["warnings"]:
            print(f"WARN    {line}")
        for line in report["legacy"]:
            print(f"LEGACY  {line}")
        for slug in report["trees_without_package"]:
            print(f"NOPKG   finalized/{slug} has no finalized-sources package")
        print(
            f"errors={len(report['errors'])} warnings={len(report['warnings'])} "
            f"legacy={len(report['legacy'])} trees_without_package={len(report['trees_without_package'])}"
        )
    failed = bool(report["errors"])
    if args.strict:
        failed = failed or bool(report["warnings"] or report["legacy"] or report["trees_without_package"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
