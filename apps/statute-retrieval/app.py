from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from draftly.retrieval import StatuteQuery, answer, build_index, search
from draftly.retrieval.corpus import sources_for_ui, topics_for_ui


st.set_page_config(page_title="Draftly Statute Retrieval", page_icon="D", layout="wide")


@st.cache_resource(show_spinner="Building statutes-only index...")
def cached_index():
    return build_index(force=False)


@st.cache_data(show_spinner=False)
def cached_topics():
    return topics_for_ui()


@st.cache_data(show_spinner=False)
def cached_sources():
    return sources_for_ui()


def main() -> None:
    stats = cached_index()
    topics = cached_topics()
    sources = cached_sources()

    st.title("Draftly Statute Q&A")
    st.caption(
        "Scope: searches 57 statutes and 18 amendments only. It excludes case law and does not determine historical validity."
    )

    with st.sidebar:
        st.header("Filters")
        topic_options = {"All topics": None} | {topic["name"]: topic["slug"] for topic in topics}
        selected_topic_name = st.selectbox("Curriculum topic", list(topic_options.keys()))
        topic_slug = topic_options[selected_topic_name]

        kind_label = st.segmented_control("Document type", ["Both", "Statutes", "Amendments"], default="Both")
        kinds = None
        if kind_label == "Statutes":
            kinds = ("statute",)
        elif kind_label == "Amendments":
            kinds = ("amendment",)

        source_options = {"All enactments": None}
        for source in sources:
            label = f"{source['source_id']} - {source['title']} ({source['kind']}, {source['year']})"
            source_options[label] = source["source_id"]
        selected_source_label = st.selectbox("Enactment", list(source_options.keys()))
        source_id = source_options[selected_source_label]

        st.divider()
        st.metric("Indexed documents", stats.documents)
        st.metric("Indexed sections", stats.sections)
        if stats.fallbacks:
            st.warning(f"{stats.fallbacks} document fallback nodes were indexed.")

    if "history" not in st.session_state:
        st.session_state.history = []

    with st.form("question_form"):
        question = st.text_input("Question", placeholder="What makes a deed of transfer valid?")
        submitted = st.form_submit_button("Ask", type="primary")

    if submitted:
        if not question.strip():
            st.warning("Enter a question before searching.")
            return
        query = StatuteQuery(text=question, topic_slug=topic_slug, kinds=kinds, source_id=source_id, limit=8)
        with st.spinner("Searching statutes and amendments..."):
            response = answer(query)
        st.session_state.history.insert(0, question)
        render_answer(response)
    else:
        example = "What makes a deed of transfer valid?"
        st.info(f"Try: {example}")

    if st.session_state.history:
        with st.sidebar:
            st.divider()
            st.subheader("Session history")
            for item in st.session_state.history[:8]:
                st.write(item)


def render_answer(response) -> None:
    if not response.hits:
        st.error("No statute or amendment evidence matched the question.")
        return

    if response.is_generated and not response.abstained:
        st.subheader("Answer")
        for claim in response.claims:
            citations = " ".join(f"`{citation}`" for citation in claim.citations)
            st.markdown(f"- {claim.text} {citations}")
        if response.limitations:
            st.warning(" ".join(response.limitations))
    elif response.abstained:
        st.warning("The model abstained because the retrieved evidence was not enough for a cited answer.")
    else:
        reason = response.invalid_reason or response.fallback_reason or "generated_answer_unavailable"
        st.warning(f"Showing retrieved evidence only. Reason: `{reason}`")

    render_evidence(response.hits)


def render_evidence(hits) -> None:
    st.subheader("Evidence")
    for rank, hit in enumerate(hits, start=1):
        title = f"{rank}. {hit.section_id} - {hit.title}"
        with st.expander(title, expanded=rank <= 3):
            cols = st.columns([1, 1, 1, 2])
            cols[0].metric("Type", hit.document_type)
            cols[1].metric("Year", hit.year or "n/a")
            cols[2].metric("Score", hit.score)
            cols[3].write(hit.heading or "No heading detected")
            st.write(hit.excerpt)
            if hit.public_source_url:
                st.link_button("Open public source", hit.public_source_url)
            st.caption(f"Topics: {', '.join(hit.topics) or 'none'} | Parser: {hit.extraction_confidence}")
            with st.container(border=True):
                st.text(hit.text[:5000])


if __name__ == "__main__":
    main()

