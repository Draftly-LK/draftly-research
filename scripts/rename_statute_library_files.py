"""Rename `data/legal-sources/library/statutes` files to `<no>-<year>-<slug>`.

The folder mixes four naming habits (`-consolidated-2024`, `-english`,
`-cbsl-appendix`, and a already-correct `-<no>-<year>`), so a file name does not
tell you which Act it is. This renames every file that maps to exactly one
registry row carrying an Act number and year, and rewrites the paths in both
copies of `source-registry.csv` in the same pass.

Skipped, and reported rather than guessed at:

  * the Legislative Enactments volumes, which each hold many statutes, so no
    single Act number fits
  * any file two or more registry rows point at
  * rows with no Act number or year (`year` is written as "0" for 16 rows)
  * files on disk the registry does not reference

Renames go through `git mv`, so they are reversible with `git restore`.

    uv run python scripts/rename_statute_library_files.py            # dry run
    uv run python scripts/rename_statute_library_files.py --apply
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUTES_DIR = REPO_ROOT / "data/legal-sources/library/statutes"
PARSED_DIR = STATUTES_DIR / "parsed"
# Only the manifests copy is rewritten. `data/processed/source-registry.csv` and
# `documents.csv` record a per-statute subfolder layout that does not exist on
# disk (74 of their 79 pdf paths are already broken), so they are stale before
# this script runs and rewriting stems in them would not make them resolve.
REGISTRIES = (REPO_ROOT / "data/legal-sources/manifests/source-registry.csv",)
VOLUME_NAME = re.compile(r"^legislative-enactments-\d{4}-volume-\d+$")


def slugify(title: str) -> str:
    slug = title.lower().replace("&", " and ").replace("'", "").replace("’", "")
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", slug)).strip("-")


def read_registry(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


FILENAME_NUMBER_YEAR = re.compile(r"(?:^|-)(\d{1,3})-(1[89]\d{2}|20\d{2})(?:-|$)")


def adopt_orphan(file: Path, rows: list[dict[str, str]]) -> tuple[dict[str, str] | None, str]:
    """Claim a file the registry does not reference, when doing so is an upgrade.

    A dedicated Act PDF that appeared on disk beats a registry row still pointing
    at a compendium volume. Anything else is left for a person: the registry may
    already hold a better source, or the file may be a rival copy.
    """
    candidates = FILENAME_NUMBER_YEAR.findall(file.stem)
    if len(candidates) != 1:
        return None, "not referenced by the registry, and its name has no single Act number and year"
    number, year = candidates[0]
    hits = [
        row
        for row in rows
        if row["act_or_ordinance_no"]
        and row["act_or_ordinance_no"].isdigit()
        and int(row["act_or_ordinance_no"]) == int(number)
        and row["year"] == year
    ]
    if len(hits) != 1:
        return None, f"not referenced by the registry; No. {int(number)} of {year} matches {len(hits)} rows"
    row = hits[0]
    held = Path(row.get("local_pdf_path") or "").stem
    if row["source_type"] != "statute":
        return None, (
            f"not referenced by the registry; No. {int(number)} of {year} is {row['source_id']}, "
            f"an {row['source_type']}, so this file is in the wrong folder"
        )
    if not VOLUME_NAME.match(held):
        return None, (
            f"not referenced by the registry; {row['source_id']} already points at "
            f"{held or 'nothing'}, so this is a rival copy someone must choose between"
        )
    # The number and year alone are not enough to claim a file: a stray digit pair
    # in a name would hand the file to an unrelated Act and rename it beyond
    # recognition. Require the words to agree as well.
    file_words = set(re.sub(r"[^a-z ]", " ", file.stem.replace("-", " ")).split())
    title_words = set(slugify(row["official_title"]).split())
    shared = file_words & title_words
    if len(shared) < 2 or len(shared) < len(title_words) / 2:
        return None, (
            f"not referenced by the registry; its name does not match "
            f"{row['source_id']} {row['official_title']} well enough to claim it"
        )
    return row, ""


def plan() -> tuple[dict[str, str], list[tuple[str, str]], dict[str, str]]:
    """Return (old_stem -> new_stem), (file, reason) skips, and adopted orphans."""
    _, rows = read_registry(REGISTRIES[0])
    adoptions: dict[str, str] = {}

    owners: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in rows:
        path = row.get("local_pdf_path") or ""
        if path and Path(path).parent.name == "statutes":
            owners[Path(path).stem].append(row)

    renames: dict[str, str] = {}
    skips: list[tuple[str, str]] = []
    for file in sorted(STATUTES_DIR.iterdir()):
        if file.is_dir() or file.suffix.lower() not in {".pdf", ".md"}:
            continue
        stem = file.stem
        if VOLUME_NAME.match(stem):
            skips.append((file.name, "compendium volume, holds many statutes"))
            continue
        matched = owners.get(stem) or [
            row
            for row in rows
            if Path(row.get("local_markdown_path") or "").name == file.name
            and Path(row.get("local_markdown_path") or "").parent.name == "statutes"
        ]
        if not matched:
            adopted, reason = adopt_orphan(file, rows)
            if not adopted:
                skips.append((file.name, reason))
                continue
            matched = [adopted]
            adoptions[adopted["source_id"]] = file.name
        if len(matched) > 1:
            ids = ", ".join(row["source_id"] for row in matched)
            skips.append((file.name, f"shared by {len(matched)} registry rows ({ids})"))
            continue
        row = matched[0]
        number, year = row["act_or_ordinance_no"], row["year"]
        if not number or not year.isdigit() or year == "0":
            skips.append((file.name, f"{row['source_id']} has no Act number or year"))
            continue
        new_stem = f"{int(number)}-{year}-{slugify(row['official_title'])}"
        if new_stem != stem:
            renames[stem] = new_stem

    duplicates = [s for s, c in collections.Counter(renames.values()).items() if c > 1]
    if duplicates:
        raise SystemExit(f"two files would take the same name: {duplicates}")

    # A target may already be taken by a different file on disk. That is a real
    # conflict, not a naming detail: dropping the rename keeps both files.
    for old_stem in sorted(renames):
        new_stem = renames[old_stem]
        occupied = [
            file
            for file in STATUTES_DIR.glob(f"{new_stem}.*")
            if file.is_file() and file.stem not in renames
        ]
        if occupied:
            del renames[old_stem]
            skips.append(
                (
                    f"{old_stem}.pdf",
                    f"target {new_stem}.pdf already exists as a different file; "
                    "resolve by hand before renaming",
                )
            )
    return renames, skips, adoptions


def affected_files(renames: dict[str, str]) -> list[tuple[Path, Path]]:
    """Every on-disk file the stem map touches, including parsed/ siblings."""
    moves = []
    for old_stem, new_stem in sorted(renames.items()):
        for directory in (STATUTES_DIR, PARSED_DIR):
            if not directory.exists():
                continue
            for file in sorted(directory.glob(f"{old_stem}.*")):
                moves.append((file, file.with_name(new_stem + file.suffix)))
    return moves


def repoint_adoptions(adoptions: dict[str, str], renames: dict[str, str], apply: bool) -> list[str]:
    """Point an adopting row's local_pdf_path at the file that claimed it."""
    if not adoptions:
        return []
    path = REGISTRIES[0]
    _, rows = read_registry(path)
    raw = path.read_bytes()
    lines = []
    for source_id, filename in adoptions.items():
        stem = Path(filename).stem
        new_name = f"{renames.get(stem, stem)}{Path(filename).suffix}"
        row = next(r for r in rows if r["source_id"] == source_id)
        old_path = row["local_pdf_path"]
        new_path = f"data/legal-sources/library/statutes/{new_name}"
        lines.append(f"{source_id}: {Path(old_path).name} -> {new_name}")
        # Swap the one quoted field rather than rewriting the CSV, which would
        # requote every row and append a trailing newline the original lacks.
        raw = raw.replace(f'"{old_path}"'.encode(), f'"{new_path}"'.encode(), 1)
    if apply:
        path.write_bytes(raw)
    return lines


def rewrite_registries(renames: dict[str, str], apply: bool) -> list[str]:
    """Swap old stems for new ones in every path column. Returns changed files."""
    changed = []
    for path in REGISTRIES:
        if not path.exists():
            continue
        # Read and write bytes. Text mode would normalise this file's CRLF line
        # endings to LF and rewrite all 90 rows instead of the handful of stems.
        original = path.read_bytes()
        updated = original
        for old_stem, new_stem in renames.items():
            updated = re.sub(
                rf"(library/statutes/(?:parsed/)?){re.escape(old_stem)}(\.\w+)".encode(),
                rf"\g<1>{new_stem}\g<2>".encode(),
                updated,
            )
        if updated != original:
            changed.append(str(path.relative_to(REPO_ROOT)))
            if apply:
                path.write_bytes(updated)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="perform the renames")
    args = parser.parse_args()

    renames, skips, adoptions = plan()
    moves = affected_files(renames)

    print(f"{len(renames)} stems to rename, touching {len(moves)} files\n")
    for source, target in moves:
        print(f"  {source.relative_to(STATUTES_DIR)}\n    -> {target.name}")

    print(f"\n{len(skips)} skipped:")
    for name, reason in skips:
        print(f"  {name}\n    {reason}")

    registries = rewrite_registries(renames, apply=args.apply)
    print(f"\nregistry files to update: {', '.join(registries) or 'none'}")

    adopted = repoint_adoptions(adoptions, renames, apply=args.apply)
    if adopted:
        print("\nregistry rows repointed at a dedicated PDF (was a compendium volume):")
        for line in adopted:
            print(f"  {line}")

    if not args.apply:
        print("\nDry run. Re-run with --apply to perform the renames.")
        return 0

    for source, target in moves:
        result = subprocess.run(
            ["git", "mv", str(source.relative_to(REPO_ROOT)), str(target.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            # Files staged into the library outside git are untracked, so git mv
            # refuses them. A plain rename is correct there; git sees a new file.
            if "not under version control" in result.stderr:
                source.rename(target)
                print(f"  {source.name} renamed (untracked, not a git mv)")
                continue
            print(f"git mv failed for {source.name}: {result.stderr.strip()}", file=sys.stderr)
            return 1
    print(f"\nrenamed {len(moves)} files and updated {len(registries)} registry files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
