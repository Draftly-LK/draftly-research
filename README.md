# Draftly

Lawyer-in-the-loop platform for Sri Lankan legal drafting and review workflows.

## Statutes-Only Q&A Demo

The current demo searches 57 statutes and 18 amendments. It does not use case
law, deed templates, or historical validity rules. Gemini answers are limited to
retrieved sections, and each retained claim is checked against its citations.

Create `.env` with `GEMINI_API_KEY`, then run:

```powershell
uv sync
uv run python -m draftly.retrieval build
uv run streamlit run apps/statute-retrieval/app.py
```

Open `http://localhost:8501`. The command-line interfaces are:

```powershell
uv run python -m draftly.retrieval search "What makes a deed valid?"
uv run python -m draftly.retrieval ask "What makes a deed valid?"
uv run python -m draftly.retrieval evaluate
uv run python -m draftly.retrieval evaluate-questions
```

The retrieval evaluation uses ten unverified development labels. The
`evaluate-questions` command runs all 18 exam questions and 73 subquestions from
`src/questions.md`, but it does not report legal correctness without lawyer gold
labels.

## Writing Style

Project-facing prose should be checked with the local avoid-ai-writing skill before it
is treated as final.

Use:

```text
.agents/skills/avoid-ai-writing/SKILL.md
```

This applies to README edits, proposal text, report sections, project descriptions,
emails, and public-facing documentation.
