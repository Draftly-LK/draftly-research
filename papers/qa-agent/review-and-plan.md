# Statute-Level QA Agent — Review and Upgrade Plan

Reviewed: `src/draftly/retrieval/` (engine) + `apps/statute-retrieval/` (UI), 2026-07-19.
Corpus: 57 statutes + 18 amendments → 3,468 section nodes (SQLite FTS5, fingerprinted).
Companion research notes: `notes-agentic-rag.md`, `notes-graph-rag.md`, `notes-legal-qa.md` (same folder).

## What the current agent does

```text
question → deterministic parse (parts, marks) → per-part subqueries
        → BM25 (FTS5) + direct section lookup + hand-coded source hints
        → RRF fusion → top-10 evidence → one Gemini call (JSON schema)
        → citation gate (claims must cite retrieved section IDs)
        → LLM entailment verifier per claim → verified answer / abstain
```

## Strengths (keep — these already match the literature)

1. **Citation-gated generation.** Every claim must cite a retrieved section ID;
   unknown citations are dropped, ungrounded claims omitted. This is the core
   defence the legal-hallucination literature demands.
2. **Claim-level entailment verification.** A second LLM pass checks each claim
   against its cited text and drops failures — Self-RAG/CRAG-style reflection,
   already implemented.
3. **Deterministic question decomposition.** Exam parts parsed by rule, per-part
   subqueries, part coverage measured. No LLM needed for structure.
4. **Honest evaluation harness.** `qa_evaluation.py` refuses to claim legal
   correctness without gold labels; resumable; fingerprinted corpus.
5. **Abstention as a first-class outcome** with known-corpus-gap detection.

## Gaps vs the state of the art

1. **Retrieval is single-shot and lexical-only.** One BM25 pass per subquery; if
   the evidence is missed, the verifier can only *reject* claims — nothing
   retries with a better query (the corrective/agentic loop in CRAG, FLARE,
   Search-o1 is absent). A part with zero verified claims just fails.
2. **No structure exploitation.** The corpus has 1,728 internal section
   cross-references, 53 amendment→principal-target aliases, and 61
   interpretation/definition sections — none used at query time. Statutes are
   graphs ("subject to section 5…", amendment modifies principal s.28); the
   graph-RAG line (HippoRAG, GraphRAG, SAT-Graph) shows multi-hop evidence
   assembly is where structure pays. A question about Notaries s.31 should
   automatically pull the sections s.31 references and the 2022/2024 amendment
   nodes that target it.
3. **Hand-coded knowledge that will not scale.** `QUERY_EXPANSIONS`,
   `SOURCE_HINT_TERMS`, `SOURCE_HINT_SECTION_SEEDS`, `_TOPIC_RULES` are
   hand-curated for known question shapes — brittle, silently overfits the two
   past papers we have, and is invisible to evaluation.
4. **No dense/semantic channel.** Pure token matching misses paraphrase
   ("remote execution" vs "outside Sri Lanka", "sinking fund" vs "reserve").
   Hybrid BM25+embedding with RRF is the uncontroversial 2024+ baseline.
5. **Global evidence pool, per-part competition.** Top-10 sections across the
   whole question; a 4-part question where part 4 needs an obscure section loses
   its slot to parts 1–3. Evidence should be allocated per part.
6. **Amendment composition is left to the model.** Base + amendment retrieved as
   separate chunks with a note; the prompt asks the model to keep them
   distinguishable. The alias metadata could pair them deterministically.

## Upgrade design (implemented in this repo)

The plan follows what the collected papers support, adapted to a *closed* corpus
where determinism is an advantage:

1. **`graph.py` — deterministic statute graph.** Nodes = section IDs. Edges:
   (a) intra-statute cross-references parsed from bodies, (b) amendment
   alias → principal target sections, (c) definition/interpretation sections of
   the same statute (weak edges). Query-time: seed with fused retrieval hits,
   run personalized-PageRank-style expansion (HippoRAG mechanism, deterministic
   seeds/graph, no LLM), merge high-scoring neighbours into evidence.
2. **`embeddings.py` — hybrid dense channel.** Gemini embedding API over all
   3,468 sections, cached to SQLite keyed by corpus fingerprint; cosine top-k
   fused with BM25 via RRF. Falls back to lexical-only when no API key.
3. **Corrective retrieval loop in `answering.py`.** After verification, any part
   with no verified claim triggers one targeted retry: LLM rewrites that part's
   query (grounded in the part text), retrieval reruns with the rewrite +
   graph expansion, generation reruns for the missing parts only, then
   re-verification. Bounded (1 retry per part, capped total).
4. **Per-part evidence allocation.** Each part gets its own evidence budget in
   the prompt; shared sections deduplicated.
5. **Evaluation on `src/questions.md`** (18 exam questions, 2025+2026 papers):
   objective gold labels derived from sections explicitly named in questions,
   plus part-coverage/verified-claim metrics, baseline vs upgraded.

Everything stays inside the existing contracts: same `StatuteAnswer` shape, same
citation gate, same verifier, same honest-evaluation policy.
