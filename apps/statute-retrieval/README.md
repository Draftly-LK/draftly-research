# Statute Retrieval App

Q&A-first Streamlit interface for the statutes-only Draftly retrieval slice.

Scope:

- Includes 57 statutes and 18 amendments from `data/processed/`.
- Excludes case law, report volumes, gazettes, institution guides, graph ranking, and temporal validity.
- Gemini answers are shown only when every generated claim cites retrieved statute evidence.

Commands:

```powershell
uv run python -m draftly.retrieval build
uv run python -m draftly.retrieval search "What makes a deed valid?"
uv run python -m draftly.retrieval evaluate
uv run streamlit run apps/statute-retrieval/app.py
```

Set `GEMINI_API_KEY` in `.env` to enable generated answers. Without it, the app shows evidence-only retrieval results.
