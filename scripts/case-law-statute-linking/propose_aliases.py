"""Propose acronym aliases for statute names -- for human review only.

The CPC/C.P.C./CPC gap in the name-alias matcher isn't specific to the
Civil Procedure Code: any statute with a multi-word title can plausibly be
cited by its initials. Hand-listing every one is how the matcher ended up
with only 9 entries. This derives a candidate acronym for every statute in
`statute_index.csv` from the initials of its official title, drops any
candidate that collides with another statute's acronym (or with an alias
that's already live), and writes the rest to `proposed_aliases.csv` for a
person to skim and copy the good ones into `alias_seed.csv`'s `aliases`
column by hand.

This script never writes to the live alias table. A short acronym can be
risky even without colliding with another statute -- e.g. "Trusts
Ordinance" derives to "to", an ordinary English word that could false-match
inside unrelated text -- and that judgment call belongs to a person, not a
collision-count heuristic.

Usage:
    python scripts/case-law-statute-linking/propose_aliases.py
"""

from __future__ import annotations

import csv
import importlib.util
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE_DIR = ROOT / "scripts" / "case-law-statute-linking"
STAGE_OUT = STAGE_DIR / "output"
STATUTE_INDEX = STAGE_OUT / "statute_index.csv"
ALIAS_SEED = STAGE_OUT / "alias_seed.csv"
OUT = STAGE_OUT / "proposed_aliases.csv"

# Filler words that don't carry identifying meaning; "act"/"ordinance"/"code"
# stay IN the word list deliberately -- "Civil Procedure Code" needs its
# trailing "Code" to derive "cpc", and "Trusts Ordinance" needs "Ordinance"
# to derive "to", matching the abbreviations actually seen in judgments.
STOPWORDS = {"of", "the", "and", "for", "no"}
WORD_RE = re.compile(r"[A-Za-z]+")


def _load_resolver_module():
    """Reuse 02_resolve_links.py's normalize_fragment and load_alias rather
    than reimplementing normalization a second way that could drift out of
    sync with the live matcher."""
    spec = importlib.util.spec_from_file_location("lsl_resolver", STAGE_DIR / "02_resolve_links.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def derive_acronym(official_title: str) -> str:
    words = [w for w in WORD_RE.findall(official_title) if w.lower() not in STOPWORDS]
    return "".join(w[0] for w in words).lower()


def propose(statute_index_path: Path = STATUTE_INDEX, alias_seed_path: Path = ALIAS_SEED) -> list[dict[str, str]]:
    resolver = _load_resolver_module()

    with statute_index_path.open("r", encoding="utf-8-sig", newline="") as handle:
        statutes = list(csv.DictReader(handle))

    live_aliases = resolver.load_alias(alias_seed_path if alias_seed_path.exists() else None)
    live_fragments_by_sid: dict[str, set[str]] = defaultdict(set)
    for fragment, sid in live_aliases:
        live_fragments_by_sid[sid].add(fragment)

    candidates: dict[str, list[str]] = defaultdict(list)  # acronym -> [source_id, ...]
    proposals: list[dict[str, str]] = []
    for row in statutes:
        acronym = derive_acronym(row["official_title"])
        if len(acronym) < 2:
            continue  # a 1-letter "acronym" is too generic to ever be safe
        candidates[acronym].append(row["source_id"])
        proposals.append(
            {
                "source_id": row["source_id"],
                "official_title": row["official_title"],
                "proposed_acronym": acronym,
            }
        )

    rows: list[dict[str, str]] = []
    for proposal in proposals:
        acronym = proposal["proposed_acronym"]
        source_id = proposal["source_id"]
        colliding = [sid for sid in candidates[acronym] if sid != source_id]
        already_live = acronym in {
            frag for sid, frags in live_fragments_by_sid.items() if sid != source_id for frag in frags
        }
        if already_live:
            colliding.append("already-live-alias-of-another-statute")
        rows.append(
            {
                "source_id": source_id,
                "official_title": proposal["official_title"],
                "proposed_acronym": acronym,
                "collision": ";".join(sorted(set(colliding))) or "none",
            }
        )
    return rows


def run() -> int:
    if not STATUTE_INDEX.exists():
        raise SystemExit(f"{STATUTE_INDEX} not found -- run 00_build_statute_index.py first.")

    rows = propose()
    clean = [row for row in rows if row["collision"] == "none"]

    STAGE_OUT.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_id", "official_title", "proposed_acronym", "collision"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"  statutes considered      : {len(rows):,}")
    print(f"  proposals with no collision (candidates for human review) : {len(clean):,}")
    print(f"  proposals dropped due to a collision                      : {len(rows) - len(clean):,}")
    print(f"\n  wrote {OUT.relative_to(ROOT)}")
    print("  nothing here is live -- copy chosen entries into alias_seed.csv's aliases column by hand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
