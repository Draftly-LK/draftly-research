"""Bring `data/legal-sources/library/amendments` onto `<no>-<year>-<slug>`.

The folder carries three naming habits at once: the 82 files fetched from the
Act archive already use `<no>-<year>-<slug>`, the 19 curated ones use
`<slug>-act-<no>-<year>`, and the 48 staged under `incoming/` use
`<slug>-amendment-<no>-<year>`. This normalises all of them, and the mirrored
`parsed/*.json`, onto the same pattern as the statutes folder.

Where a registry row owns the file, its official title and Act number decide the
name. Otherwise the name is rebuilt from the existing filename.

One trap this handles: some names carry the principal statute's number as well
as the amending Act's, as in `bank-of-ceylon-ordinance-53-1938-amendment-54-2000`.
The amending instrument is the *last* pair, and every pair is stripped out of
the slug so neither number is left stranded in the middle of the name.

    uv run python scripts/rename_amendment_library_files.py            # dry run
    uv run python scripts/rename_amendment_library_files.py --apply
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
AMENDMENTS = REPO_ROOT / "data/legal-sources/library/amendments"
SUBDIRS = ("", "incoming", "parsed")
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"

NUMBER_YEAR = re.compile(r"(?:^|-)(\d{1,3})-(1[89]\d{2}|20\d{2})(?=-|$)")
ALREADY_OK = re.compile(r"^\d{1,3}-(1[89]\d{2}|20\d{2})-")


def slugify(text: str) -> str:
    slug = text.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", slug)).strip("-")


def read_registry() -> list[dict[str, str]]:
    with REGISTRY.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def target_stem(stem: str, registry_row: dict[str, str] | None) -> tuple[str | None, str]:
    """Return (new_stem, reason-if-skipped)."""
    if registry_row:
        number, year = registry_row["act_or_ordinance_no"], registry_row["year"]
        if number and year.isdigit() and year != "0":
            return f"{int(number)}-{year}-{slugify(registry_row['official_title'])}", ""
        return None, f"{registry_row['source_id']} has no Act number or year"

    pairs = NUMBER_YEAR.findall(stem)
    if not pairs:
        return None, "no Act number and year in the filename, and no registry row"
    # The amending instrument is the last pair; earlier ones name the principal.
    number, year = pairs[-1]
    slug = slugify(NUMBER_YEAR.sub("-", stem))
    if not slug:
        return None, "nothing left for a slug once the numbers are removed"
    return f"{int(number)}-{year}-{slug}", ""


def plan() -> tuple[list[tuple[Path, Path]], list[tuple[str, str]]]:
    owners = {}
    for row in read_registry():
        for column in ("local_pdf_path", "local_parsed_path"):
            path = row.get(column) or ""
            if path and "library/amendments/" in path:
                owners[Path(path).name] = row

    moves, skips = [], []
    for subdir in SUBDIRS:
        directory = AMENDMENTS / subdir if subdir else AMENDMENTS
        if not directory.exists():
            continue
        for file in sorted(directory.iterdir()):
            if file.is_dir() or file.suffix.lower() not in {".pdf", ".json", ".md"}:
                continue
            new_stem, reason = target_stem(file.stem, owners.get(file.name))
            if not new_stem:
                if not ALREADY_OK.match(file.stem):
                    skips.append((str(file.relative_to(AMENDMENTS)), reason))
                continue
            if new_stem == file.stem:
                continue
            target = file.with_name(new_stem + file.suffix)
            if target.exists():
                skips.append(
                    (
                        str(file.relative_to(AMENDMENTS)),
                        f"target {target.name} already exists; resolve by hand",
                    )
                )
                continue
            moves.append((file, target))

    clashes = [
        name
        for name, count in collections.Counter(t for _, t in moves).items()
        if count > 1
    ]
    if clashes:
        raise SystemExit(f"two files would take the same name: {clashes}")
    return moves, skips


def rewrite_registry(moves: list[tuple[Path, Path]], apply: bool) -> bool:
    """Byte-level swap so the file's CRLF endings and quoting are untouched."""
    raw = REGISTRY.read_bytes()
    original = raw
    for source, target in moves:
        raw = raw.replace(
            f"/amendments/{source.parent.name}/{source.name}".replace(
                f"/amendments/{AMENDMENTS.name}/", "/amendments/"
            ).encode(),
            f"/amendments/{target.parent.name}/{target.name}".replace(
                f"/amendments/{AMENDMENTS.name}/", "/amendments/"
            ).encode(),
        )
        raw = raw.replace(
            f"/amendments/{source.name}".encode(), f"/amendments/{target.name}".encode()
        )
    if raw != original and apply:
        REGISTRY.write_bytes(raw)
    return raw != original


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="perform the renames")
    args = parser.parse_args()

    moves, skips = plan()
    print(f"{len(moves)} files to rename\n")
    for source, target in moves:
        print(f"  {source.relative_to(AMENDMENTS)}\n    -> {target.name}")

    print(f"\n{len(skips)} skipped:")
    for name, reason in skips:
        print(f"  {name}\n    {reason}")

    changed = rewrite_registry(moves, apply=args.apply)
    print(f"\nregistry needs updating: {changed}")

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
            if "not under version control" in result.stderr:
                source.rename(target)
                continue
            print(f"git mv failed for {source.name}: {result.stderr.strip()}", file=sys.stderr)
            return 1
    print(f"\nrenamed {len(moves)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
