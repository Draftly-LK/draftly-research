# Statute Retrieval App

Q&A-first Streamlit interface for the statutes-only Draftly retrieval slice.

Scope:

- Includes 57 statutes and 18 amendments from `data/processed/`.
- Excludes case law, report volumes, gazettes, institution guides, and temporal validity.
- Gemini answers are shown only when every generated claim cites retrieved statute evidence.

## Retrieval architecture (2026-07-19 upgrade)

Three fused channels plus structural expansion (design + literature in
`papers/qa-agent/review-and-plan.md`):

- **Lexical** — SQLite FTS5 BM25 over 3,468 section nodes, with direct
  section-ID lookup and curated source hints.
- **Dense** — Gemini `gemini-embedding-001` vectors (cached per corpus
  fingerprint in `data/processed/retrieval-indexes/`; oversized OCR sections are
  chunk-embedded). Degrades to lexical-only without an API key.
- **Graph** — a deterministic statute graph (section cross-references,
  amendment→principal-target edges, definition edges; ~15.8K edges) expanded
  from the fused hits with personalized PageRank, so amendments and referenced
  sections surface even when no query token matches them.

Channels are fused with reciprocal-rank fusion. Answering adds per-part
evidence quotas, a citation gate (claims must cite retrieved section IDs), a
claim-level entailment verifier, and a bounded corrective retry: any question
part left with no verified claim gets one statutory-vocabulary query rewrite +
re-retrieval + regeneration pass through the same gate.

## Commands

```powershell
uv run python -m draftly.retrieval build
uv run python -m draftly.retrieval search "What makes a deed valid?"
uv run python -m draftly.retrieval evaluate
uv run streamlit run apps/statute-retrieval/app.py

# exam-paper evaluation (baseline vs upgraded ablation)
uv run python evaluation/qa-agent/run_eval.py baseline
uv run python evaluation/qa-agent/run_eval.py upgraded
uv run python evaluation/qa-agent/run_eval.py --score
```

Set `GEMINI_API_KEY` in `.env` to enable generated answers and the dense
channel. Ablation switches: `DRAFTLY_DISABLE_DENSE=1`, `DRAFTLY_DISABLE_GRAPH=1`,
`DRAFTLY_SKIP_CORRECTIVE=1`.
