"""Assemble the accepted package for one statute: the trees and the sources.

Two folders come out of this, both named after the principal instrument:

    library/finalized/<no>-<year>-<slug>/          the canonical JSON, nothing else
    library/finalized-sources/<no>-<year>-<slug>/  every file those trees were read from

`finalized/` is the layer to build on. `data/processed/canonical-*` is
regenerated output and will move under anyone standing on it, which is the whole
reason the accepted copy is taken. `finalized-sources/` answers the other
question -- what was actually read to produce a tree -- with a manifest carrying
the size, the SHA-256 and the path each file was copied from, so a later reader
can tell an accepted tree from a re-run of a since-changed source.

Copies, never moves: the registry still points at the originals.

    uv run python scripts/finalize_statute.py --source-id SRC021 \
        --slug 38-2014-land-restrictions-on-alienation-act \
        --amendment 3-2017 --amendment 21-2018
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / "data/legal-sources/library"
FINALIZED = LIBRARY / "finalized"
FINALIZED_SOURCES = LIBRARY / "finalized-sources"
CANONICAL_STATUTES = REPO_ROOT / "data/processed/canonical-statutes"
CANONICAL_AMENDMENTS = REPO_ROOT / "data/processed/canonical-amendments"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--slug", required=True, help="folder name, from the principal instrument")
    parser.add_argument(
        "--amendment",
        action="append",
        default=[],
        metavar="NO-YEAR",
        help="an amending Act to include, as it is named in canonical-amendments/",
    )
    parser.add_argument(
        "--verification-source",
        action="append",
        default=[],
        metavar="PATH[=NOTE]",
        help=(
            "a file the tree was checked against rather than parsed from, as a "
            "repo-relative path, optionally followed by =<what it settled>"
        ),
    )
    parser.add_argument("--statute-note", default="")
    args = parser.parse_args()

    trees = sorted(CANONICAL_STATUTES.glob(f"{args.source_id}-*.json"))
    if not trees:
        print(f"no canonical tree for {args.source_id}", file=sys.stderr)
        return 1

    out_trees = FINALIZED / args.slug
    out_sources = FINALIZED_SOURCES / args.slug
    out_trees.mkdir(parents=True, exist_ok=True)
    out_sources.mkdir(parents=True, exist_ok=True)
    # Both folders are regenerated wholesale. Clearing them first is what stops a
    # source that has been dropped -- a truncated page replaced by a better one --
    # from sitting in the package indefinitely, still looking like evidence.
    # A tree someone has corrected by hand outlives the parser that produced it.
    # Anything carrying provenance.hand_corrected is kept and not rewritten --
    # otherwise a routine re-run silently throws the corrections away.
    protected: set[str] = set()
    for existing in out_trees.glob("*.json"):
        try:
            if json.loads(existing.read_text(encoding="utf-8")).get("provenance", {}).get(
                "hand_corrected"
            ):
                protected.add(existing.name)
        except (ValueError, OSError):
            pass
    for stale in (*out_trees.iterdir(), *out_sources.iterdir()):
        if stale.is_file() and stale.name not in protected:
            stale.unlink()

    files: list[dict] = []
    statute_title = ""

    for tree in trees:
        document = json.loads(tree.read_text(encoding="utf-8"))
        statute_title = statute_title or document.get("title", "")
        kind = document.get("edition", {}).get("kind", "")
        # The folder is named from the principal instrument, so an edition that
        # is not the original has to say which edition it is.
        # `original_or_unconfirmed_consolidation` is what the builder records
        # when the page gives it nothing to go on. It is an admission that the
        # edition is unknown, not the name of one, so it earns no suffix; the
        # tree's own `edition` block is where that uncertainty is stated.
        suffix = (
            ""
            if kind in ("", "original", "as_enacted", "original_or_unconfirmed_consolidation")
            else f"-{kind}"
        )
        copy(tree, out_trees / f"{args.slug}{suffix}.json")

        original = REPO_ROOT / document["edition"]["local_path"]
        if original.exists():
            name = f"{args.slug}{suffix}{original.suffix}"
            copy(original, out_sources / name)
            files.append(
                {
                    "file": name,
                    "role": "principal statute",
                    "edition": kind or "unstated",
                    "bytes": original.stat().st_size,
                    "sha256": digest(original),
                    "copied_from": original.relative_to(REPO_ROOT).as_posix(),
                    "used_for": f"parsed into {args.slug}{suffix}.json",
                }
            )

    for instrument in args.amendment:
        tree = CANONICAL_AMENDMENTS / f"{instrument}.json"
        if not tree.exists():
            print(f"no canonical tree for amending Act {instrument}", file=sys.stderr)
            return 1
        document = json.loads(tree.read_text(encoding="utf-8"))
        # Name the tree after the instrument, not after whatever the source file
        # happened to be called: the same Act reached through a PDF and through
        # HTML must not land here under two names.
        stem = f"{instrument}-{args.slug.split('-', 2)[-1].removesuffix('-act')}-amendment"
        if f"{stem}.json" not in protected:
            copy(tree, out_trees / f"{stem}.json")

        original = REPO_ROOT / document["edition"]["local_path"]
        copy(original, out_sources / f"{stem}{original.suffix}")
        files.append(
            {
                "file": f"{stem}{original.suffix}",
                "role": "amending Act",
                "edition": document["edition"].get("kind", ""),
                "bytes": original.stat().st_size,
                "sha256": digest(original),
                "copied_from": original.relative_to(REPO_ROOT).as_posix(),
                "used_for": f"parsed into {stem}.json",
            }
        )
        # An OCR sidecar is a reading of something. Carry the scan it was read
        # from, or the package documents a transcript with no original.
        header = original.read_text(encoding="utf-8", errors="replace")[:400] \
            if original.suffix == ".txt" else ""
        scanned = re.search(r"^# OCR of (\S+)", header, re.M)
        if scanned:
            scan = REPO_ROOT / scanned.group(1)
            if scan.exists():
                copy(scan, out_sources / f"{stem}-scan{scan.suffix}")
                files.append(
                    {
                        "file": f"{stem}-scan{scan.suffix}",
                        "role": "amending Act",
                        "edition": "as_enacted",
                        "bytes": scan.stat().st_size,
                        "sha256": digest(scan),
                        "copied_from": scan.relative_to(REPO_ROOT).as_posix(),
                        "used_for": (
                            f"image source of {stem}{original.suffix}; no text "
                            "layer, so it was not parsed directly"
                        ),
                    }
                )

    # A second edition read only to settle what the parsed one got wrong is
    # still evidence, and the package is unreadable without it: every
    # `verified_against_alternate_edition` in the tree points at something, and
    # a URL alone goes dead. It is listed apart from the parsed sources so the
    # distinction between what was read and what was checked survives.
    for entry in args.verification_source:
        path_text, _, why = entry.partition("=")
        source = REPO_ROOT / path_text
        if not source.exists():
            print(f"no such verification source: {path_text}", file=sys.stderr)
            return 1
        copy(source, out_sources / source.name)
        files.append(
            {
                "file": source.name,
                "role": "verification source, not parsed",
                "edition": "",
                "bytes": source.stat().st_size,
                "sha256": digest(source),
                "copied_from": source.relative_to(REPO_ROOT).as_posix(),
                "used_for": why or "checked against; nothing here was parsed from it",
            }
        )

    manifest = {
        "statute": statute_title,
        "source_id": args.source_id,
        "note": (
            "Every source actually used to build the canonical trees in "
            f"library/finalized/{args.slug}. Copies, not moves; the originals "
            "stay where the registry points."
        ),
        "status": "unverified until a lawyer signs it off",
        "files": files,
    }
    if args.statute_note:
        manifest["statute_note"] = args.statute_note
    (out_sources / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"{out_trees.relative_to(REPO_ROOT)}")
    for path in sorted(out_trees.iterdir()):
        print(f"  {path.name}")
    print(f"{out_sources.relative_to(REPO_ROOT)}")
    for path in sorted(out_sources.iterdir()):
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
