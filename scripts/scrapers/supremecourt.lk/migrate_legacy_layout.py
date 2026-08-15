"""One-off, idempotent reorg: move already-downloaded Supreme Court PDFs into
an SCLR subfolder, ahead of adding a second (SCOA / Court of Appeal) source.

Before: data/supremecourt.lk/<year>/<filename>.pdf
After:  data/supremecourt.lk/SCLR/<year>/<filename>.pdf

Moves files on disk (no re-downloading) and adds a `source` column to
manifest.csv, defaulting every existing row to SCLR (the only source that
existed before this change). Anything under data/supremecourt.lk/ that isn't
a 4-digit year directory (e.g. .DS_Store, an already-migrated SCLR/SCOA dir)
is left untouched.

Safe to re-run: once every legacy year-dir has moved and every manifest row
carries a source, it's a no-op.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "data" / "supremecourt.lk"
MANIFEST = OUT_DIR / "manifest.csv"
LEGACY_SOURCE = "SCLR"

NEW_FIELDS = [
    "source", "year", "date", "case_no", "parties", "judge", "pdf_url",
    "filename", "status", "sha256", "downloaded_at",
]


def migrate_files() -> int:
    moved = 0
    if not OUT_DIR.exists():
        return moved
    dest_root = OUT_DIR / LEGACY_SOURCE
    for entry in sorted(OUT_DIR.iterdir()):
        if not entry.is_dir() or not entry.name.isdigit() or len(entry.name) != 4:
            continue  # not a legacy year directory (e.g. SCLR/, SCOA/, .DS_Store)
        dest_dir = dest_root / entry.name
        dest_dir.mkdir(parents=True, exist_ok=True)
        for pdf in sorted(entry.glob("*.pdf")):
            target = dest_dir / pdf.name
            if target.exists():
                pdf.unlink()  # already present under SCLR/<year>/ from a prior partial migration
            else:
                pdf.rename(target)
            moved += 1
        remaining = list(entry.iterdir())
        if not remaining:
            entry.rmdir()
        else:
            print(f"  [note] {entry} left in place, still contains: {[p.name for p in remaining]}")
    return moved


def migrate_manifest() -> int:
    if not MANIFEST.exists():
        return 0
    with MANIFEST.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    updated = 0
    for row in rows:
        if not row.get("source"):
            row["source"] = LEGACY_SOURCE
            updated += 1
    with MANIFEST.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=NEW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in NEW_FIELDS})
    return updated


def main() -> None:
    moved = migrate_files()
    updated = migrate_manifest()
    print(f"DONE moved={moved} pdf(s) into {LEGACY_SOURCE}/, tagged {updated} manifest row(s) with source={LEGACY_SOURCE}")


if __name__ == "__main__":
    main()
