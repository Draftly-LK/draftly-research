from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from draftly.retrieval import StatuteQuery, answer, build_index, search
from draftly.retrieval.corpus import corpus_fingerprint, load_statute_documents, sources_for_ui, topics_for_ui


st.set_page_config(page_title="Draftly statute Q&A", page_icon=":material/balance:", layout="wide")


@st.cache_resource(show_spinner="Building statutes-only index...")
def cached_index(fingerprint: str):
    del fingerprint
    return build_index(force=False)


@st.cache_data(show_spinner=False)
def cached_topics(fingerprint: str):
    del fingerprint
    return topics_for_ui()


@st.cache_data(show_spinner=False)
def cached_sources(fingerprint: str):
    del fingerprint
    return sources_for_ui()


def main() -> None:
    fingerprint = corpus_fingerprint(load_statute_documents())
    stats = cached_index(fingerprint)
    topics = cached_topics(fingerprint)
    sources = cached_sources(fingerprint)

    st.title("Draftly Statute Q&A")
    st.caption(
        "Statutes and amendments only. No case law, deed templates, or point-in-time validity conclusions. "
        "Generated claims are machine-checked against cited text and still require lawyer review."
    )

    with st.sidebar:
        st.header("Search scope")
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
        st.caption(f"{stats.documents} documents | {stats.sections} section nodes")
        if stats.fallbacks:
            st.warning(f"{stats.fallbacks} document fallback nodes were indexed.")

    if "history" not in st.session_state:
        st.session_state.history = []

    with st.form("question_form"):
        question = st.text_area(
            "Question",
            placeholder="Paste one question or a complete multi-part exam question.",
            height=170,
        )
        submitted = st.form_submit_button("Ask", type="primary", icon=":material/search:")

    if submitted:
        if not question.strip():
            st.warning("Enter a question before searching.")
            return
        query = StatuteQuery(text=question, topic_slug=topic_slug, kinds=kinds, source_id=source_id, limit=8)
        with st.status("Analyzing the question and checking statutory evidence...", expanded=False) as status:
            response = answer(query)
            status.update(label="Evidence and answer checks complete", state="complete")
        st.session_state.history.insert(0, question)
        render_answer(response)
    else:
        st.info("Try: What makes a deed of transfer valid?", icon=":material/lightbulb:")

    if st.session_state.history:
        with st.sidebar:
            st.divider()
            st.subheader("Session history")
            for item in st.session_state.history[:8]:
                st.write(item)


def render_answer(response) -> None:
    if response.is_generated:
        outcome_label = "Partial answer" if response.outcome == "partial" else "Answer"
        st.subheader(outcome_label)
        for claim in response.claims:
            citations = " ".join(f"`{citation}`" for citation in claim.citations)
            part = f"**Part {claim.part}:** " if claim.part else ""
            check = " :material/verified:" if claim.verified else ""
            st.markdown(f"- {part}{claim.text} {citations}{check}")
    elif response.abstained:
        st.warning(
            "A reliable cited answer could not be produced from the available statutes and amendments.",
            icon=":material/report:",
        )
    else:
        reason = response.invalid_reason or response.fallback_reason or "generated_answer_unavailable"
        st.warning(f"Showing retrieved evidence only. Reason: `{reason}`")

    if response.missing_information:
        st.error("Missing authority or information:\n\n- " + "\n- ".join(response.missing_information))
    if response.limitations:
        st.warning("Limitations:\n\n- " + "\n- ".join(response.limitations))

    if response.retrieval_queries:
        with st.expander("How the question was searched", icon=":material/account_tree:"):
            for item in response.retrieval_queries:
                st.write(item)

    if response.hits:
        render_evidence(response.hits)


def render_evidence(hits) -> None:
    st.subheader("Evidence")
    for rank, hit in enumerate(hits, start=1):
        title = f"{rank}. {hit.section_id} - {hit.title}"
        with st.expander(title, expanded=rank <= 3):
            st.caption(
                f"{hit.document_type.capitalize()} | {hit.year or 'Year unavailable'} | "
                f"{hit.heading or 'Heading unavailable'}"
            )
            if hit.citation_note:
                st.info(hit.citation_note, icon=":material/info:")
            st.write(hit.excerpt)
            if hit.public_source_url:
                st.link_button("Open public source", hit.public_source_url, icon=":material/open_in_new:")
            st.caption(f"Topics: {', '.join(hit.topics) or 'none'} | Parser: {hit.extraction_confidence}")
            with st.container(border=True):
                st.code(hit.text[:5000], language=None)


if __name__ == "__main__":
    main()
