"""Offline checks for the statute browser. No network, no spend.

Run from the repo root:

    uv run pytest apps/statute-browser/test_statute_browser.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from loader import (  # noqa: E402
    corpus_totals,
    load_actions,
    load_sections,
    load_statutes,
    load_versions,
    section_sort_key,
)


def test_sections_sort_the_way_a_statute_prints_them():
    unsorted = ["103", "12B", "2", "12", "12A", "13", "1"]
    assert sorted(unsorted, key=section_sort_key) == ["1", "2", "12", "12A", "12B", "13", "103"]


def test_non_numeric_labels_sort_last():
    assert section_sort_key("Schedule") > section_sort_key("999")


def test_every_indexed_section_has_at_least_one_version():
    sections = load_sections()
    versions = load_versions()
    section_keys = set(zip(sections["source_id"], sections["section"]))
    version_keys = set(zip(versions["source_id"], versions["section"]))
    assert section_keys == version_keys


def test_exactly_one_current_version_per_section():
    versions = load_versions()
    current = versions[versions["is_current"]].groupby(["source_id", "section"]).size()
    assert current.eq(1).all()


def test_no_tuple_columns_survive_into_the_frames():
    """Arrow cannot serialize tuples, so a stray sort key breaks every chart."""
    for frame in (load_statutes(), load_sections(), load_versions(), load_actions()):
        for column in frame.columns:
            sample = frame[column].dropna().head(50)
            assert not any(isinstance(value, tuple) for value in sample), column


def test_only_a_first_version_may_have_an_unknown_start():
    """339 sections of 7 index-only statutes have no commencement date at all."""
    versions = load_versions()
    unknown_start = versions[versions["valid_from_year"].isna()]
    assert unknown_start["version_no"].eq(1).all()


def test_version_intervals_run_forward_and_do_not_overlap():
    versions = load_versions()
    for _, history in versions.groupby(["source_id", "section"], sort=False):
        history = history.sort_values("version_no")
        starts = history["valid_from_year"].tolist()
        ends = history["valid_to_year"].tolist()
        known = [year for year in starts if pd.notna(year)]
        assert known == sorted(known)
        for start, end in zip(starts, ends):
            if pd.notna(end) and pd.notna(start):
                assert end >= start
        for previous_end, next_start in zip(ends[:-1], starts[1:]):
            assert previous_end == next_start


def test_only_the_last_version_is_open_ended():
    versions = load_versions()
    for _, history in versions.groupby(["source_id", "section"], sort=False):
        history = history.sort_values("version_no")
        assert history["valid_to_year"].iloc[:-1].notna().all()
        assert pd.isna(history["valid_to_year"].iloc[-1])
        assert history["is_current"].iloc[-1]


def test_superseded_versions_never_claim_to_hold_text():
    """Only the current wording is in the corpus -- see the module docstring."""
    versions = load_versions()
    assert not versions[~versions["is_current"]]["text_available"].any()


def test_every_action_referenced_by_a_version_exists():
    versions = load_versions()
    known = set(load_actions()["action_id"])
    referenced = {action for row in versions["created_by_actions"] for action in row}
    assert referenced <= known


def test_index_only_statutes_are_flagged_and_still_titled():
    statutes = load_statutes()
    index_only = statutes[~statutes["in_registry"]]
    assert len(index_only) == 22
    assert (index_only["source_id"] >= "SRC091").all()
    assert not index_only["statute"].eq(index_only["source_id"]).any()


def test_statute_section_counts_match_the_section_table():
    statutes = load_statutes().set_index("source_id")["sections"]
    counted = load_sections().groupby("source_id").size()
    assert statutes.sort_index().equals(counted.sort_index())


def test_statutes_with_no_amending_act_report_unknown_history():
    statutes = load_statutes()
    assert (statutes[statutes["amending_acts"] == 0]["history"] == "unknown").all()
    assert (statutes[statutes["amending_acts"] > 0]["history"] == "known").all()


def test_pages_read_columns_the_loader_actually_produces():
    """Guards the row-selection detail panels, which no render test can click."""
    expected = {
        "statutes": {"statute", "act_no", "year", "commencement", "in_registry", "topics",
                     "sections", "amended_sections", "amending_acts", "amending_act_list",
                     "first_change", "last_change", "history", "source_id"},
        "sections": {"source_id", "section", "heading", "heading_source", "amendments",
                     "amending_acts", "current_since"},
        "versions": {"source_id", "section", "version_no", "valid_from_date", "valid_from_year",
                     "valid_to_year", "is_current", "text_available", "amendment_history",
                     "amending_acts", "amending_provisions"},
        "actions": {"amending_act_label", "amending_year", "amending_section", "target_section",
                    "operation", "verbatim", "statute", "source_id", "action_id"},
    }
    frames = {
        "statutes": load_statutes(),
        "sections": load_sections(),
        "versions": load_versions(),
        "actions": load_actions(),
    }
    for name, columns in expected.items():
        assert columns <= set(frames[name].columns), name


def test_a_registry_year_of_zero_is_treated_as_missing():
    """SRC029 carries year "0" in the registry, which is a gap, not the year 0."""
    statutes = load_statutes().set_index("source_id")
    assert pd.isna(statutes.loc["SRC029", "year"])
    assert statutes.loc["SRC029", "dated_year"] == 1896
    assert statutes.loc["SRC029", "date_source"] == "commenced"
    assert (load_statutes()["year"].dropna() > 1500).all()


def test_every_statute_is_dated_or_explicitly_undated():
    statutes = load_statutes()
    assert set(statutes["date_source"]) <= {"enacted", "commenced", "unknown"}
    undated = statutes[statutes["date_source"] == "unknown"]
    assert undated["dated_year"].isna().all()
    assert statutes[statutes["date_source"] != "unknown"]["dated_year"].notna().all()


def test_statutes_by_date_file_is_current():
    """Regenerate with `uv run python apps/statute-browser/build_statutes_by_date.py`."""
    from build_statutes_by_date import OUTPUT, render

    assert OUTPUT.exists()
    assert OUTPUT.read_text(encoding="utf-8") == render()


def test_every_curriculum_statute_resolves_to_a_registry_row():
    from build_statute_tiers import match_curriculum

    matched, unmatched = match_curriculum()
    assert not unmatched, [e["title"] for e in unmatched]
    assert len(matched) == 56


def test_primary_and_secondary_partition_the_corpus():
    from build_statute_tiers import match_curriculum

    matched, _ = match_curriculum()
    named = {entry["source_id"] for entry in matched}
    corpus = set(load_statutes()["source_id"])
    primary = named & corpus
    secondary = corpus - named
    assert primary | secondary == corpus
    assert not (primary & secondary)
    # These counts track the section index and move when a statute is extracted.
    # 39 before the LankaLaw HTML parse was merged in, 40 after the Execution of
    # Deeds Ordinance, 45 once every accepted tree in library/finalized followed,
    # 46 once the National Housing Development Authority Act (SRC075, previously
    # unmatched to any curriculum topic in the section index at all) was finalized.
    assert len(primary) == 46
    assert len(secondary) == 27


def test_statute_tier_files_are_current():
    """Regenerate with `uv run python apps/statute-browser/build_statute_tiers.py`."""
    from build_statute_tiers import (
        PRIMARY_OUT,
        SECONDARY_OUT,
        match_curriculum,
        render_primary,
        render_secondary,
    )

    matched, unmatched = match_curriculum()
    assert PRIMARY_OUT.read_text(encoding="utf-8") == render_primary(matched, unmatched)
    assert SECONDARY_OUT.read_text(encoding="utf-8") == render_secondary(matched)


@pytest.mark.parametrize("key", ["statutes", "sections", "actions", "amending_acts"])
def test_corpus_totals_are_non_zero(key):
    assert corpus_totals()[key] > 0
