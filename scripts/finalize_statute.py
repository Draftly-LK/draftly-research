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

Hashes follow `package_integrity.py`: PDFs and other binaries are hashed as
stored (`hash_mode: bytes`); HTML, TXT, MD, CSV and JSON evidence is hashed
with line endings folded to LF (`hash_mode: text-lf`), so a Windows checkout
with `core.autocrlf=true` still verifies. `scripts/verify_finalized_packages.py`
checks every package against its manifest.

    uv run python scripts/finalize_statute.py --source-id SRC021 \
        --slug 38-2014-land-restrictions-on-alienation-act \
        --amendment 3-2017 --amendment 21-2018

    # package an already-accepted tree without regenerating it
    uv run python scripts/finalize_statute.py --source-id SRC031 \
        --slug 7-2007-companies-act --package-only
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_integrity import file_entry  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / "data/legal-sources/library"
FINALIZED = LIBRARY / "finalized"
FINALIZED_SOURCES = LIBRARY / "finalized-sources"
CANONICAL_STATUTES = REPO_ROOT / "data/processed/canonical-statutes"
CANONICAL_AMENDMENTS = REPO_ROOT / "data/processed/canonical-amendments"


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def is_amending(tree: Path) -> bool:
    try:
        document = json.loads(tree.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False
    return document.get("instrument_role") == "amending" or "instrument_id" in document


GENERATED_KEYS = {"statute", "source_id", "note", "status", "files"}
GENERATED_FILE_KEYS = {"file", "role", "edition", "bytes", "sha256", "hash_mode", "copied_from", "used_for"}


def read_previous_manifest(path: Path) -> dict:
    """Hand-added manifest keys, and per-file extras keyed by file name."""
    if not path.exists():
        return {}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    kept = {k: v for k, v in manifest.items() if k not in GENERATED_KEYS}
    kept["files"] = {
        entry["file"]: {k: v for k, v in entry.items() if k not in GENERATED_FILE_KEYS}
        for entry in manifest.get("files", [])
        if isinstance(entry, dict) and "file" in entry
    }
    return kept


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
        "--held-amendment",
        action="append",
        default=[],
        metavar="PATH[=NOTE]",
        help=(
            "an amending instrument held as a file but not parsed into a tree, as "
            "a repo-relative path, optionally followed by =<why it was not parsed>"
        ),
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
    parser.add_argument(
        "--package-only",
        action="store_true",
        help=(
            "leave finalized/<slug>/ untouched and build finalized-sources/<slug>/ "
            "from the trees already accepted there, reading each tree's "
            "edition.local_path. For trees finished by hand after their canonical "
            "parse, which a normal run would overwrite."
        ),
    )
    args = parser.parse_args()

    out_trees = FINALIZED / args.slug
    out_sources = FINALIZED_SOURCES / args.slug

    if args.package_only:
        trees = sorted(p for p in out_trees.glob("*.json") if not is_amending(p))
        amending_trees = sorted(p for p in out_trees.glob("*.json") if is_amending(p))
        if not trees:
            print(f"no accepted tree under {out_trees.relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        if args.amendment:
            print(
                "--amendment is not used with --package-only; amending trees are read from finalized/",
                file=sys.stderr,
            )
            return 1
    else:
        amending_trees = []
        trees = sorted(CANONICAL_STATUTES.glob(f"{args.source_id}-*.json"))
        if not trees:
            print(f"no canonical tree for {args.source_id}", file=sys.stderr)
            return 1

    out_trees.mkdir(parents=True, exist_ok=True)
    out_sources.mkdir(parents=True, exist_ok=True)

    # Keys added to the manifest by hand -- reconciliation tables, notes,
    # retrieval URLs -- outlive a re-run. They are read back before the folder
    # is cleared and written again unless this run supplies a replacement.
    previous = read_previous_manifest(out_sources / "manifest.json")
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
    stale_dirs = (out_sources,) if args.package_only else (out_trees, out_sources)
    for stale in (path for d in stale_dirs for path in d.iterdir()):
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
        tree_name = tree.name if args.package_only else f"{args.slug}{suffix}.json"
        if not args.package_only:
            copy(tree, out_trees / tree_name)

        local_path = document.get("edition", {}).get("local_path", "")
        original = REPO_ROOT / local_path
        if local_path and original.exists():
            name = f"{args.slug}{suffix}{original.suffix}"
            copy(original, out_sources / name)
            files.append(
                file_entry(
                    original,
                    REPO_ROOT,
                    file=name,
                    role="principal statute",
                    edition=kind or "unstated",
                    used_for=f"parsed into {tree_name}",
                )
            )
        elif args.package_only:
            print(
                f"warning: {tree.name} names no readable edition.local_path; "
                "its source is not in the package",
                file=sys.stderr,
            )

    amendment_jobs: list[tuple[str, Path, bool]] = []
    for instrument in args.amendment:
        tree = CANONICAL_AMENDMENTS / f"{instrument}.json"
        if not tree.exists():
            print(f"no canonical tree for amending Act {instrument}", file=sys.stderr)
            return 1
        amendment_jobs.append((instrument, tree, True))
    for tree in amending_trees:
        parts = tree.stem.split("-", 2)
        amendment_jobs.append((f"{parts[0]}-{parts[1]}", tree, False))

    for instrument, tree, from_canonical in amendment_jobs:
        document = json.loads(tree.read_text(encoding="utf-8"))
        # Name the tree after the instrument, not after whatever the source file
        # happened to be called: the same Act reached through a PDF and through
        # HTML must not land here under two names.
        stem = (
            f"{instrument}-{args.slug.split('-', 2)[-1].removesuffix('-act')}-amendment"
            if from_canonical
            else tree.stem
        )
        if from_canonical and f"{stem}.json" not in protected:
            copy(tree, out_trees / f"{stem}.json")

        local_path = document.get("edition", {}).get("local_path", "")
        original = REPO_ROOT / local_path
        if not local_path or not original.exists():
            print(
                f"warning: amending tree {tree.name} names no readable edition.local_path",
                file=sys.stderr,
            )
            continue
        copy(original, out_sources / f"{stem}{original.suffix}")
        files.append(
            file_entry(
                original,
                REPO_ROOT,
                file=f"{stem}{original.suffix}",
                role="amending Act",
                edition=document["edition"].get("kind", ""),
                used_for=f"parsed into {stem}.json",
            )
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
                    file_entry(
                        scan,
                        REPO_ROOT,
                        file=f"{stem}-scan{scan.suffix}",
                        role="amending Act",
                        edition="as_enacted",
                        used_for=(
                            f"image source of {stem}{original.suffix}; no text "
                            "layer, so it was not parsed directly"
                        ),
                    )
                )

    # An instrument in the chain that no tree was built from is still part of the
    # statute's history, and a package that drops it reads as though the chain
    # ended earlier than it did. It keeps its own filename rather than the
    # `<slug>-amendment` form the parsed ones take, so which instruments were
    # actually read stays visible from the directory listing alone.
    for entry in args.held_amendment:
        path_text, _, why = entry.partition("=")
        source = REPO_ROOT / path_text
        if not source.exists():
            print(f"no such held amendment: {path_text}", file=sys.stderr)
            return 1
        copy(source, out_sources / source.name)
        files.append(
            file_entry(
                source,
                REPO_ROOT,
                role="amending Act, held but not parsed",
                edition="as_enacted",
                used_for=why or "not parsed; no tree was built from it",
            )
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
            file_entry(
                source,
                REPO_ROOT,
                role="verification source, not parsed",
                edition="",
                used_for=why or "checked against; nothing here was parsed from it",
            )
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
    for entry in files:
        for key, value in previous.get("files", {}).get(entry["file"], {}).items():
            entry.setdefault(key, value)
    for key, value in previous.items():
        if key not in manifest and key != "files":
            manifest[key] = value
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
