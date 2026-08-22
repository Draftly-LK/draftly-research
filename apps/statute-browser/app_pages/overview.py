import altair as alt
import streamlit as st
from shared import actions, caveats, sections, statutes, totals

st.title("Statutes, sections and amendments")
st.caption(
    "Every statute the corpus holds structure for, how many sections each has, "
    "and when those sections were changed."
)

counts = totals()
statute_frame = statutes()
section_frame = sections()
action_frame = actions()

row = st.container(horizontal=True)
row.metric("Statutes", counts["statutes"], help="Statutes present in the section index.")
row.metric("Sections", f"{counts['sections']:,}")
row.metric(
    "Sections amended",
    f"{counts['amended_sections']:,}",
    delta=f"{counts['amended_sections'] / counts['sections']:.0%} of sections",
    delta_color="off",
)
row.metric("Amending Acts", counts["amending_acts"])
row.metric(
    "Amendment actions",
    counts["actions"],
    delta=f"{counts['operation_known']} say what changed",
    delta_color="off",
)

caveats()

if counts["statutes"] - counts["in_registry"]:
    st.warning(
        f"{counts['statutes'] - counts['in_registry']} of {counts['statutes']} statutes "
        "(SRC091-SRC112) are **index-only**: the corpus holds their section numbers and "
        "headings but no registry row and no verified text, so nothing can be cited from "
        "them. Their titles come from a proposed topic mapping, not the registry.",
        icon=":material/info:",
    )

st.subheader("When sections changed")
year_counts = (
    action_frame.dropna(subset=["amending_year"])
    .assign(decade=lambda f: (f["amending_year"] // 10 * 10).astype(int))
    .groupby("decade")
    .size()
    .reset_index(name="actions")
)
st.altair_chart(
    alt.Chart(year_counts)
    .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
    .encode(
        x=alt.X("decade:O", title="Decade of the amending Act"),
        y=alt.Y("actions:Q", title="Section-level amendments"),
        tooltip=[
            alt.Tooltip("decade:O", title="Decade"),
            alt.Tooltip("actions:Q", title="Amendments"),
        ],
    )
    .properties(height=220)
)

st.subheader("Most-amended statutes")
top = (
    statute_frame[statute_frame["amended_sections"] > 0]
    .nlargest(15, "amended_sections")
    .sort_values("amended_sections")
)
st.altair_chart(
    alt.Chart(top)
    .mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2)
    .encode(
        x=alt.X("amended_sections:Q", title="Sections with at least one amendment"),
        y=alt.Y("statute:N", title=None, sort=None),
        tooltip=[
            alt.Tooltip("statute:N", title="Statute"),
            alt.Tooltip("sections:Q", title="Sections"),
            alt.Tooltip("amended_sections:Q", title="Amended"),
            alt.Tooltip("amending_acts:Q", title="Amending Acts"),
            alt.Tooltip("first_change:Q", title="First change", format="d"),
            alt.Tooltip("last_change:Q", title="Last change", format="d"),
        ],
    )
    .properties(height=28 * len(top))
)

st.subheader("All statutes")
controls = st.container(horizontal=True)
order = controls.segmented_control(
    "Order", ["Oldest first", "Newest first", "A to Z"], default="Oldest first",
    label_visibility="collapsed",
)
search = controls.text_input(
    "Filter statutes",
    placeholder="registration, notaries, land...",
    label_visibility="collapsed",
)

if order == "A to Z":
    statute_frame = statute_frame.sort_values("statute", kind="stable")
else:
    statute_frame = statute_frame.sort_values(
        ["dated_year", "statute"],
        ascending=[order == "Oldest first", True],
        kind="stable",
        na_position="last",
    )

table = statute_frame
if search:
    needle = search.strip().lower()
    table = table[
        table["statute"].str.lower().str.contains(needle, regex=False)
        | table["topics"].str.lower().str.contains(needle, regex=False)
        | table["amending_act_list"].str.lower().str.contains(needle, regex=False)
    ]

st.caption(
    f"{len(table)} of {len(statute_frame)} statutes. **Dated** is the year of enactment "
    "where the registry holds one, and the commencement year otherwise; 7 statutes have "
    "neither and sort last."
)
event = st.dataframe(
    table[
        [
            "dated_year",
            "statute",
            "act_no",
            "year",
            "commencement",
            "sections",
            "amended_sections",
            "amending_acts",
            "first_change",
            "last_change",
            "in_registry",
            "topics",
        ]
    ],
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "dated_year": st.column_config.NumberColumn("Dated", format="%d", width="small", pinned=True),
        "statute": st.column_config.TextColumn("Statute", pinned=True, width="large"),
        "act_no": st.column_config.TextColumn("No.", width="small"),
        "year": st.column_config.NumberColumn("Enacted", format="%d", width="small"),
        "commencement": st.column_config.TextColumn("Commenced", width="small"),
        "sections": st.column_config.NumberColumn("Sections", width="small"),
        "amended_sections": st.column_config.NumberColumn("Amended", width="small"),
        "amending_acts": st.column_config.NumberColumn("Amending Acts", width="small"),
        "first_change": st.column_config.NumberColumn("First change", format="%d", width="small"),
        "last_change": st.column_config.NumberColumn("Last change", format="%d", width="small"),
        "in_registry": st.column_config.CheckboxColumn("In registry", width="small"),
        "topics": st.column_config.TextColumn("Curriculum topics", width="medium"),
    },
)

selected_rows = event["selection"]["rows"]
if selected_rows:
    picked = table.iloc[selected_rows[0]]
    st.session_state["selected_source_id"] = picked["source_id"]
    st.info(
        f"**{picked['statute']}** selected. Open **Statute browser** to see its "
        f"{picked['sections']} sections and their amendment timeline.",
        icon=":material/menu_book:",
    )

st.subheader("Download")
download = st.container(horizontal=True)
download.download_button(
    "Statutes",
    statute_frame.to_csv(index=False).encode("utf-8"),
    "draftly-statutes.csv",
    "text/csv",
    icon=":material/download:",
)
download.download_button(
    "Sections",
    section_frame.to_csv(index=False).encode("utf-8"),
    "draftly-sections.csv",
    "text/csv",
    icon=":material/download:",
)
download.download_button(
    "Amendment actions",
    action_frame.to_csv(index=False).encode("utf-8"),
    "draftly-amendment-actions.csv",
    "text/csv",
    icon=":material/download:",
)
st.caption("Exports carry the same `status=unverified` as the source artifacts.")
