import altair as alt
import pandas as pd
import streamlit as st
from shared import caveats, sections, statute_labels, statutes, versions

CURRENT_YEAR = 2026

statute_frame = statutes()
labels = statute_labels(statute_frame)
label_by_id = {source_id: label for label, source_id in labels.items()}

st.title("Statute browser")

preselected = st.session_state.get("selected_source_id")
options = list(labels)
index = options.index(label_by_id[preselected]) if preselected in label_by_id else 0

with st.sidebar:
    st.header("Statute")
    chosen_label = st.selectbox("Statute", options, index=index, label_visibility="collapsed")
    source_id = labels[chosen_label]
    st.session_state["selected_source_id"] = source_id

    st.header("Sections")
    only_amended = st.toggle("Only sections that changed", value=False)
    needle = st.text_input(
        "Find a section",
        placeholder="section number or heading text",
    )

meta = statute_frame[statute_frame["source_id"] == source_id].iloc[0]
statute_sections = sections()[sections()["source_id"] == source_id]
statute_versions = versions()[versions()["source_id"] == source_id]

st.subheader(meta["statute"])
badges = []
if meta["act_no"] and pd.notna(meta["year"]):
    badges.append(f":blue-badge[No. {meta['act_no']} of {meta['year']}]")
if meta["commencement"]:
    badges.append(f":gray-badge[Commenced {meta['commencement']}]")
badges.append(
    ":green-badge[In registry]" if meta["in_registry"] else ":orange-badge[Index-only, no verified text]"
)
badges.append(
    ":gray-badge[Amendment history known]"
    if meta["history"] == "known"
    else ":red-badge[Amendment history unknown]"
)
st.markdown(" ".join(badges))
if meta["topics"]:
    st.caption(f"Curriculum topics: {meta['topics']}")

row = st.container(horizontal=True)
row.metric("Sections", len(statute_sections))
row.metric("Sections changed", int((statute_sections["amendments"] > 0).sum()))
row.metric("Amending Acts", meta["amending_acts"])
row.metric(
    "Change span",
    f"{meta['first_change']}-{meta['last_change']}" if pd.notna(meta["first_change"]) else "--",
)

caveats()

if not meta["in_registry"]:
    st.warning(
        "This statute is index-only. Section numbers and headings are held, but no "
        "registry row and no verified text, so nothing here can be cited.",
        icon=":material/gpp_maybe:",
    )
if meta["history"] == "unknown":
    st.warning(
        "No amendment history was harvested for this statute. Every section shows a "
        "single version -- that means **unknown**, not **unchanged**.",
        icon=":material/help:",
    )

sections_tab, timeline_tab = st.tabs(
    [":material/list: Sections", ":material/timeline: Amendment timeline"]
)

with sections_tab:
    table = statute_sections
    if only_amended:
        table = table[table["amendments"] > 0]
    if needle:
        query = needle.strip().lower()
        table = table[
            table["section"].str.lower().str.startswith(query)
            | table["heading"].str.lower().str.contains(query, regex=False)
            | table["amending_acts"].str.lower().str.contains(query, regex=False)
        ]

    st.caption(
        f"{len(table)} of {len(statute_sections)} sections. "
        "Select a row to see that section's version history."
    )
    event = st.dataframe(
        table[["section", "heading", "amendments", "amending_acts", "current_since", "heading_source"]],
        hide_index=True,
        height=420,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "section": st.column_config.TextColumn("s.", pinned=True, width="small"),
            "heading": st.column_config.TextColumn("Marginal-note heading", width="large"),
            "amendments": st.column_config.NumberColumn("Changes", width="small"),
            "amending_acts": st.column_config.TextColumn("Amended by", width="medium"),
            "current_since": st.column_config.NumberColumn(
                "Current since", format="%d", width="small"
            ),
            "heading_source": st.column_config.TextColumn("Heading from", width="small"),
        },
    )

    picked_rows = event["selection"]["rows"]
    if picked_rows:
        section = table.iloc[picked_rows[0]]["section"]
        history = statute_versions[statute_versions["section"] == section]

        st.markdown(f"#### Section {section} -- version history")
        st.caption(table.iloc[picked_rows[0]]["heading"] or "No heading recorded.")

        if len(history) == 1:
            single = history.iloc[0]
            if single["amendment_history"] == "known":
                st.success(
                    "No amendment recorded for this section. Its text is the original, "
                    f"in force since {single['valid_from_date'] or single['valid_from_year']}.",
                    icon=":material/check_circle:",
                )
            else:
                st.warning(
                    "No amendment history held for this statute, so nothing is known "
                    "about whether this section changed.",
                    icon=":material/help:",
                )
        else:
            for version in history.itertuples():
                start = version.valid_from_date or f"{version.valid_from_year}"
                end = "current" if version.is_current else str(version.valid_to_year)
                marker = ":material/bookmark: " if version.is_current else ""
                opened = version.amending_provisions or "original enactment"
                text = (
                    ":green-badge[text held]"
                    if version.text_available
                    else ":orange-badge[wording not in corpus]"
                )
                st.markdown(
                    f"{marker}**v{version.version_no}** &nbsp; `{start} - {end}` &nbsp; "
                    f"opened by {opened} &nbsp; {text}"
                )

with timeline_tab:
    changed = statute_versions[
        statute_versions["section"].isin(
            statute_sections[statute_sections["amendments"] > 0]["section"]
        )
    ]
    if changed.empty:
        st.info(
            "No section of this statute has a recorded amendment.",
            icon=":material/info:",
        )
    else:
        chart_data = changed.assign(
            start=changed["valid_from_year"].astype("Int64"),
            end=changed["valid_to_year"].fillna(CURRENT_YEAR).astype("Int64"),
            state=changed["is_current"].map({True: "Current", False: "Superseded"}),
            opened_by=changed["amending_acts"].replace("", "original enactment"),
        )
        undated = int(chart_data["start"].isna().sum())
        chart_data = chart_data.dropna(subset=["start"])
        # statute_sections already arrives in section order.
        order = statute_sections[statute_sections["amendments"] > 0]["section"].tolist()
        caption = (
            f"{len(order)} sections with a recorded change. Each bar is one version; "
            "a boundary is the amending Act's year, not a commencement date."
        )
        if undated:
            caption += (
                f" {undated} original version{'s are' if undated > 1 else ' is'} not drawn: "
                "this statute has no commencement date, so those bars have no start."
            )
        st.caption(caption)
        st.altair_chart(
            alt.Chart(chart_data)
            .mark_bar(height=11, cornerRadius=2)
            .encode(
                x=alt.X("start:Q", title="Year", scale=alt.Scale(zero=False, nice=False)),
                x2="end:Q",
                y=alt.Y("section:N", title="Section", sort=order),
                color=alt.Color(
                    "state:N",
                    title=None,
                    scale=alt.Scale(
                        domain=["Superseded", "Current"], range=["#c9ccd4", "#2b6cb0"]
                    ),
                ),
                tooltip=[
                    alt.Tooltip("section:N", title="Section"),
                    alt.Tooltip("version_no:Q", title="Version"),
                    alt.Tooltip("start:Q", title="From", format="d"),
                    alt.Tooltip("end:Q", title="To", format="d"),
                    alt.Tooltip("opened_by:N", title="Opened by"),
                    alt.Tooltip("state:N", title="State"),
                ],
            )
            .properties(height=max(200, 22 * len(order)))
        )
