# LawChain (from scratch)

An independent implementation of the LawChain architecture, built to benchmark
against the existing `apps/statute-retrieval` engine on the same corpus.

Source: Atukorala, Appuhami, and de Silva, "LawChain: A Resource-Efficient
Blueprint for Legal Information Retrieval in Low-Resource Jurisdictions,"
GlobalSouthML affinity event, ICML 2026
(<https://icml.cc/virtual/2026/78334>). The paper reports Precision@5 = 0.8345
and Recall@5 = 0.9357 on a Sri Lankan legislative Acts deployment; those are
the numbers this implementation is measured against.

Status: implemented (`lawchain/` package + tests). Not yet run end-to-end
with the dense channel enabled in this environment -- see the Neo4j and E5
notes below.

Scope: the 24 finalized statutes in `data/legal-sources/library/finalized/`
only, not the full 57-document corpus the existing engine indexes. The 11
separate amendment-Act JSONs living inside those folders are excluded --
their text is already merged into the 24 consolidated statutes.

## Architecture

1. Layout-aware extraction from the finalized statute JSONs (`extraction.py`)
2. BM25 lexical indexing (`lexical_index.py`)
3. Semantic embeddings, E5-base, local inference (`dense_index.py`)
4. Bounded agentic query expansion via Gemini (`query_expansion.py`)
5. Knowledge graph from structured cross-references/amendments (`graph.py`)
6. Hybrid ranking: RRF fusion + Gemini LLM-as-judge (`ranking.py`)
7. RAG answer generation via Gemini (`generation.py`)

**Deliberate divergence from the paper:** stage 5 uses NetworkX, not Neo4j.
This repo has no Neo4j infrastructure, and
`proj-docs/project Management/retrieval-engine-methodology.md` already
argues against a graph DB at this scale. Decided with the project owner
before implementation.

## Running it

```powershell
$env:PYTHONPATH = "apps/lawchain-from-scratch"
uv run python -m lawchain sources    # verify the 24 resolved statute files
uv run python -m lawchain build
uv run python -m lawchain search "stamp duty" --limit 5
uv run python -m lawchain evaluate   # writes evaluation/runs/lawchain-v1/comparison.json
```

`lawchain` is not part of the installed `draftly` package -- it needs
`apps/lawchain-from-scratch` on `PYTHONPATH` at invocation time. The first
`build` with the dense channel enabled downloads the `intfloat/e5-base-v2`
weights (~440MB) from the Hugging Face Hub; set `LAWCHAIN_DISABLE_DENSE=1`
to skip that channel entirely (lexical + graph only).

## Evaluation

`evaluate` filters the existing engine's gold question set (`GOLD_CSV`) down
to rows whose expected sections all fall within the 24-statute scope here
(3 of the current 10 gold rows qualify), then scores both engines with the
same Precision@5/Recall@1/5/10/MRR/nDCG@10 functions
(`src/draftly/retrieval/evaluation.py`, which gained a `precision_at_5`
metric for this comparison), alongside the paper's own reported
Precision@5 = 0.8345 / Recall@5 = 0.9357 for reference.
