"""Cached data access and caveat text shared by the browser pages."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from loader import corpus_totals, load_actions, load_sections, load_statutes, load_versions

UNVERIFIED = (
    "Structural data only: section numbers, marginal-note headings, and the years "
    "sections changed. Every row is `status=unverified` and none of it is a "
    "statement of current law until a lawyer signs it off."
)


@st.cache_data(show_spinner="Loading statute structure...")
def statutes() -> pd.DataFrame:
    return load_statutes()


@st.cache_data(show_spinner="Loading sections...")
def sections() -> pd.DataFrame:
    return load_sections()


@st.cache_data(show_spinner="Loading version history...")
def versions() -> pd.DataFrame:
    return load_versions()


@st.cache_data(show_spinner="Loading amendment actions...")
def actions() -> pd.DataFrame:
    return load_actions()


@st.cache_data(show_spinner=False)
def totals() -> dict[str, int]:
    return corpus_totals()


def caveats() -> None:
    """The four limits that decide how far this data can be pushed."""
    with st.expander("What this data can and cannot tell you", icon=":material/warning:"):
        st.markdown(
            f"""
- **A version boundary means "something changed here", not "the section was
  replaced".** `operation` is unknown on {totals()["actions"] - totals()["operation_known"]}
  of {totals()["actions"]} amendment actions -- the source marker names the amending
  Act and its section, not what that section did.
- **Only the current text is held.** Earlier versions are known to exist and are
  dated, but their wording is not in the corpus. Recovering it needs the 1956 and
  1981 revised editions, or the amending Acts themselves.
- **Boundaries after the first are keyed to the amending Act's year**, not its
  commencement date. An Act of 1980 may commence in 1981, so a boundary case
  cannot be settled from the year alone.
- **`history = unknown` is not `unchanged`.** It means no amendment history was
  harvested for that statute.

There is no chapter or part hierarchy in the corpus -- the index is flat sections.

{UNVERIFIED}
"""
        )


def statute_labels(frame: pd.DataFrame) -> dict[str, str]:
    """`Prevention of Frauds Ordinance (No. 7 of 1840)` -> source_id."""
    labels: dict[str, str] = {}
    for row in frame.itertuples():
        cite = ""
        if row.act_no and pd.notna(row.year):
            cite = f" (No. {row.act_no} of {row.year})"
        elif pd.notna(row.year):
            cite = f" ({row.year})"
        labels[f"{row.statute}{cite}"] = row.source_id
    return labels
