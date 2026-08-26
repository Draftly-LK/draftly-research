import altair as alt
import streamlit as st
from shared import actions, caveats

st.title("Amending Acts")
st.caption("The reverse view: one amending Act, and every section it is recorded as touching.")

action_frame = actions()

by_act = (
    action_frame.groupby("amending_act_label")
    .agg(
        year=("amending_year", "max"),
        statutes=("source_id", "nunique"),
        sections=("target_section", "size"),
        statute_list=("statute", lambda values: ", ".join(sorted(set(values)))),
    )
    .reset_index()
    .sort_values(["year", "sections"], ascending=[False, False])
)

row = st.container(horizontal=True)
row.metric("Amending Acts", len(by_act))
row.metric("Section-level changes", len(action_frame))
row.metric("Earliest", int(by_act["year"].min()))
row.metric("Latest", int(by_act["year"].max()))

caveats()

st.subheader("Every amending Act")
st.caption("Select a row to see which sections it touched.")
event = st.dataframe(
    by_act[["amending_act_label", "year", "statutes", "sections", "statute_list"]],
    hide_index=True,
    height=380,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "amending_act_label": st.column_config.TextColumn("Amending Act", pinned=True, width="medium"),
        "year": st.column_config.NumberColumn("Year", format="%d", width="small"),
        "statutes": st.column_config.NumberColumn("Statutes hit", width="small"),
        "sections": st.column_config.NumberColumn("Sections hit", width="small"),
        "statute_list": st.column_config.TextColumn("Principal enactments", width="large"),
    },
)

picked_rows = event["selection"]["rows"]
if picked_rows:
    act_label = by_act.iloc[picked_rows[0]]["amending_act_label"]
    detail = action_frame[action_frame["amending_act_label"] == act_label]

    st.markdown(f"#### {act_label}")
    st.dataframe(
        detail[["statute", "target_section", "amending_section", "operation", "verbatim"]]
        .sort_values(["statute", "amending_section"]),
        hide_index=True,
        column_config={
            "statute": st.column_config.TextColumn("Principal enactment", width="medium"),
            "target_section": st.column_config.TextColumn("Amends s.", width="small"),
            "amending_section": st.column_config.TextColumn("By its s.", width="small"),
            "operation": st.column_config.TextColumn("Operation", width="small"),
            "verbatim": st.column_config.TextColumn("Source marker", width="small"),
        },
    )
    if (detail["operation"] == "unknown").all():
        st.caption(
            "`operation` is unknown for every row above -- the marker names the amending "
            "provision, not what it did. Reading the amending Act itself is the only way to say."
        )

st.subheader("Amending activity over time")
per_year = action_frame.dropna(subset=["amending_year"]).groupby("amending_year").size().reset_index(name="sections")
st.altair_chart(
    alt.Chart(per_year)
    .mark_circle()
    .encode(
        x=alt.X("amending_year:Q", title="Year of the amending Act", scale=alt.Scale(zero=False, nice=False)),
        y=alt.Y("sections:Q", title="Sections amended"),
        size=alt.Size("sections:Q", legend=None, scale=alt.Scale(range=[30, 500])),
        tooltip=[
            alt.Tooltip("amending_year:Q", title="Year", format="d"),
            alt.Tooltip("sections:Q", title="Sections amended"),
        ],
    )
    .properties(height=260)
)
