"""Join the four generated structure artifacts into the tables the browser renders.

Read-only. Nothing here writes; the artifacts below stay the single source of
truth and are produced by `scripts/build_*.py`, not by this app.

    statute-section-index.json   sections + marginal-note headings + amendment markers
    actions.csv                  one amending instrument x one target section
    section_versions.jsonl       those actions turned into dated version intervals
    statute_commencement.csv     a real commencement date for the first version

What the joined view can and cannot say, restated from
`scripts/build_section_versions.py` because the UI has to carry these caveats:

  * `operation` is unknown on 853 of 872 actions. A version boundary means
    "something changed here", not "the section was replaced".
  * Only the current version's text is held. Earlier versions are dated but
    their wording is not in the corpus.
  * Every boundary after the first is keyed to the amending Act's YEAR, not its
    commencement date.
  * 22 statutes (SRC091-SRC112) are index-only: section numbers and headings
    but no registry row and no verified text. They are marked `in_registry=False`
    and their titles come from `extra-statues-to-topics.md`, a proposed mapping.

Nothing here is verified. Every row is status=unverified.
"""

from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SECTION_INDEX_JSON = REPO_ROOT / "data/legal-sources/manifests/statute-section-index.json"
SOURCE_REGISTRY_CSV = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
EXTRA_STATUTES_MD = REPO_ROOT / "data/legal-sources/extra-statues-to-topics.md"
ACTIONS_CSV = REPO_ROOT / "data/processed/actions.csv"
SECTION_VERSIONS_JSONL = REPO_ROOT / "data/processed/section_versions.jsonl"
COMMENCEMENT_CSV = REPO_ROOT / "data/processed/statute_commencement.csv"
TOPICS_CSV = REPO_ROOT / "data/processed/topics.csv"

_SECTION_PART = re.compile(r"(\d+)|(\D+)")
_EXTRA_ROW = re.compile(r"^\|\s*(SRC\d+)\s*[-—–]\s*([^|]+?)\s*\|")


def section_sort_key(section: str) -> tuple[int, str, int]:
    """Sort `12`, `12A`, `12B`, `103` the way a statute prints them.

    Returns (leading number, alpha suffix, tiebreak) so that `12A` sorts after
    `12` and before `13`, and a wholly non-numeric label sorts last.
    """
    parts = [(int(num) if num else 0, alpha or "") for num, alpha in _SECTION_PART.findall(section)]
    if not parts:
        return (10**9, section, 0)
    lead_num = parts[0][0]
    if not section[:1].isdigit():
        return (10**9, section, 0)
    suffix = "".join(alpha for _, alpha in parts).strip()
    return (lead_num, suffix, len(parts))


def _read_csv_skipping_comments(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        rows = [line for line in handle if not line.startswith("#")]
    return list(csv.DictReader(rows))


@lru_cache(maxsize=1)
def _index_only_titles() -> dict[str, str]:
    """Titles for SRC091-SRC112, which no longer have a registry row.

    Source is the proposed topic mapping, not a verified registry entry.
    """
    if not EXTRA_STATUTES_MD.exists():
        return {}
    titles: dict[str, str] = {}
    for line in EXTRA_STATUTES_MD.read_text(encoding="utf-8").splitlines():
        match = _EXTRA_ROW.match(line.strip())
        if match:
            titles[match.group(1)] = match.group(2).strip()
    return titles


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict[str, str]]:
    if not SOURCE_REGISTRY_CSV.exists():
        return {}
    return {row["source_id"]: row for row in _read_csv_skipping_comments(SOURCE_REGISTRY_CSV)}


@lru_cache(maxsize=1)
def _commencement() -> dict[str, str]:
    if not COMMENCEMENT_CSV.exists():
        return {}
    return {
        row["source_id"]: row.get("commencement", "")
        for row in _read_csv_skipping_comments(COMMENCEMENT_CSV)
    }


@lru_cache(maxsize=1)
def _topic_names() -> dict[str, str]:
    if not TOPICS_CSV.exists():
        return {}
    rows = _read_csv_skipping_comments(TOPICS_CSV)
    return {row["topic_id"]: row.get("name") or row.get("slug", "") for row in rows if row.get("topic_id")}


@lru_cache(maxsize=1)
def _section_index() -> dict[str, list[dict]]:
    return json.loads(SECTION_INDEX_JSON.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _statute_names_from_actions() -> dict[str, str]:
    names: dict[str, str] = {}
    for row in _read_csv_skipping_comments(ACTIONS_CSV):
        name = (row.get("statute_name") or "").strip()
        if name and row["source_id"] not in names:
            names[row["source_id"]] = name.title()
    return names


def statute_title(source_id: str) -> str:
    registry_row = _registry().get(source_id)
    if registry_row and registry_row.get("official_title"):
        return registry_row["official_title"]
    return _index_only_titles().get(source_id) or _statute_names_from_actions().get(source_id, source_id)


@lru_cache(maxsize=1)
def load_actions() -> pd.DataFrame:
    """One row per amending instrument touching one section of a principal Act."""
    frame = pd.DataFrame(_read_csv_skipping_comments(ACTIONS_CSV))
    frame["amending_year"] = pd.to_numeric(frame["amending_year"], errors="coerce").astype("Int64")
    frame["amending_act_label"] = frame.apply(
        lambda row: f"No. {row['amending_act_no']} of {row['amending_year']}"
        if row["amending_act_no"] and pd.notna(row["amending_year"])
        else (row["amending_act"] or "unrecorded"),
        axis=1,
    )
    frame["statute"] = frame["source_id"].map(statute_title)
    return frame


@lru_cache(maxsize=1)
def load_versions() -> pd.DataFrame:
    """One row per version interval of one section, with the Acts that opened it."""
    records = [
        json.loads(line)
        for line in SECTION_VERSIONS_JSONL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    frame = pd.DataFrame.from_records(records)

    actions = load_actions().set_index("action_id")
    act_label = actions["amending_act_label"].to_dict()
    act_section = actions["amending_section"].to_dict()

    def label_for(action_ids: list[str]) -> str:
        labels = [act_label.get(a, a) for a in action_ids]
        return ", ".join(dict.fromkeys(labels))

    def cites_for(action_ids: list[str]) -> str:
        cites = [
            f"s.{act_section[a]} of {act_label.get(a, a)}"
            for a in action_ids
            if act_section.get(a)
        ]
        return "; ".join(dict.fromkeys(cites))

    frame["amending_acts"] = frame["created_by_actions"].apply(label_for)
    frame["amending_provisions"] = frame["created_by_actions"].apply(cites_for)
    frame["statute"] = frame["source_id"].map(statute_title)
    frame["sort_key"] = frame["section"].map(section_sort_key)
    frame["valid_to_year"] = frame["valid_to_year"].astype("Int64")
    frame["valid_from_year"] = frame["valid_from_year"].astype("Int64")
    # `scripts/build_section_versions.py` leaves valid_from_year null on 1,713 first
    # versions that do carry a commencement date. Backfill rather than lose the bar.
    from_date_year = pd.to_numeric(
        frame["valid_from_date"].str.slice(0, 4), errors="coerce"
    ).astype("Int64")
    frame["valid_from_year"] = frame["valid_from_year"].fillna(from_date_year)
    # sort_key holds tuples, which Arrow cannot serialize -- sort by it, then drop it.
    # Callers can rely on the frame arriving in statute-then-section order.
    return (
        frame.sort_values(["source_id", "sort_key", "version_no"], kind="stable")
        .drop(columns=["sort_key"])
        .reset_index(drop=True)
    )


@lru_cache(maxsize=1)
def load_sections() -> pd.DataFrame:
    """One row per section: heading, provenance, and its amendment summary."""
    versions = load_versions()
    per_section = versions.groupby(["source_id", "section"], sort=False)
    version_count = per_section.size()
    current = versions[versions["is_current"]].set_index(["source_id", "section"])
    current_since = current["valid_from_year"].to_dict()
    current_history = current["amendment_history"].to_dict()
    changed_acts = (
        versions[versions["amending_acts"] != ""]
        .groupby(["source_id", "section"], sort=False)["amending_acts"]
        .apply(lambda values: ", ".join(dict.fromkeys(", ".join(values).split(", "))))
    )

    rows = []
    for source_id, entries in _section_index().items():
        for entry in entries:
            section = entry["section"]
            key = (source_id, section)
            markers = entry.get("amendment_markers") or []
            since = current_since.get(key)
            rows.append(
                {
                    "source_id": source_id,
                    "statute": statute_title(source_id),
                    "section": section,
                    "sort_key": section_sort_key(section),
                    "heading": entry.get("heading", ""),
                    "heading_source": entry.get("heading_source", ""),
                    "present_in": ", ".join(entry.get("present_in", [])),
                    "amendments": len(markers),
                    "versions": int(version_count.get(key, 1)),
                    "amending_acts": changed_acts.get(key, ""),
                    "current_since": int(since) if since is not None and pd.notna(since) else pd.NA,
                    "history": current_history.get(key, "unknown"),
                }
            )

    frame = pd.DataFrame(rows)
    frame["current_since"] = frame["current_since"].astype("Int64")
    return (
        frame.sort_values(["source_id", "sort_key"], kind="stable")
        .drop(columns=["sort_key"])
        .reset_index(drop=True)
    )


def _registry_year(registry_row: dict[str, str]):
    raw = (registry_row.get("year") or "").strip()
    return int(raw) if raw.isdigit() and raw != "0" else pd.NA


@lru_cache(maxsize=1)
def load_statutes() -> pd.DataFrame:
    """One row per statute in the section index, with its amendment footprint."""
    sections = load_sections()
    actions = load_actions()
    registry = _registry()
    commencement = _commencement()
    topic_names = _topic_names()

    acts_per_statute = (
        actions.groupby("source_id")["amending_act_label"].agg(lambda values: sorted(set(values))).to_dict()
    )
    year_span = actions.dropna(subset=["amending_year"]).groupby("source_id")["amending_year"]
    first_year = year_span.min().to_dict()
    last_year = year_span.max().to_dict()

    rows = []
    for source_id, group in sections.groupby("source_id", sort=False):
        source_id = str(source_id)
        registry_row = registry.get(source_id, {})
        topic_ids = [t for t in (registry_row.get("topics") or "").split(";") if t]
        amending_acts = acts_per_statute.get(source_id, [])
        rows.append(
            {
                "source_id": source_id,
                "statute": statute_title(source_id),
                "act_no": registry_row.get("act_or_ordinance_no", ""),
                # The registry writes "0" for a year it does not hold (SRC029 and 15 others).
                "year": _registry_year(registry_row),
                "source_type": registry_row.get("source_type", "index-only"),
                "in_registry": source_id in registry,
                "commencement": commencement.get(source_id, ""),
                "topics": ", ".join(topic_names.get(t, t) for t in topic_ids),
                "sections": len(group),
                "amended_sections": int((group["amendments"] > 0).sum()),
                "amending_acts": len(amending_acts),
                "amending_act_list": ", ".join(amending_acts),
                "first_change": first_year.get(source_id, pd.NA),
                "last_change": last_year.get(source_id, pd.NA),
                "history": "known" if len(amending_acts) else "unknown",
                "pdf_path": registry_row.get("local_pdf_path", ""),
                "url": registry_row.get("preferred_source_url", ""),
            }
        )

    frame = pd.DataFrame(rows)
    frame["year"] = frame["year"].astype("Int64")
    frame["first_change"] = frame["first_change"].astype("Int64")
    frame["last_change"] = frame["last_change"].astype("Int64")

    # A statute is dated by its year of enactment where the registry holds one, and
    # otherwise by its commencement year. 7 index-only statutes have neither.
    commencement_year = pd.to_numeric(
        frame["commencement"].str.slice(0, 4), errors="coerce"
    ).astype("Int64")
    frame["dated_year"] = frame["year"].fillna(commencement_year)
    frame["date_source"] = [
        "enacted" if pd.notna(year) else ("commenced" if pd.notna(started) else "unknown")
        for year, started in zip(frame["year"], commencement_year)
    ]
    return frame.sort_values("statute", kind="stable").reset_index(drop=True)


def corpus_totals() -> dict[str, int]:
    statutes = load_statutes()
    sections = load_sections()
    actions = load_actions()
    return {
        "statutes": len(statutes),
        "in_registry": int(statutes["in_registry"].sum()),
        "sections": len(sections),
        "amended_sections": int((sections["amendments"] > 0).sum()),
        "actions": len(actions),
        "amending_acts": actions["amending_act_label"].nunique(),
        "operation_known": int((actions["operation"] != "unknown").sum()),
    }
