# Legal Statute Retrieval (LSR) evaluation

Benchmarks the existing statute retrieval engine
(`src/draftly/retrieval/search.py`) on the case→statute retrieval task
formulated by **IL-PCSR** ("Legal Corpus for Prior Case and Statute
Retrieval", Paul et al., EMNLP 2025 — `papers/2025.emnlp-main.738.pdf`):
given a case, mask the statute citation it relies on, and see whether
retrieval recovers the right provision from the citation's surrounding
text alone.

## Why this exists

The repo already links cases to statutes deterministically
(`scripts/case-law-statute-linking/`, `case_statute_links.py`) — it finds
and grades citations that are already written down in a judgment or
headnote. That pipeline cannot say anything about a case that discusses a
provision without naming it, and it never checks what the retrieval engine
itself would find. This adapts IL-PCSR's evaluation methodology to close
that second gap, using the deterministic pipeline's own verified links as
gold data.

## Scope: what was adapted, what wasn't, and why

IL-PCSR covers two tasks — Legal Statute Retrieval (LSR) and Prior Case
Retrieval (PCR, case-to-case) — and its best result comes from a GNN
trained jointly across both, on 6,271 labelled queries.

This implementation covers **LSR only**, with **no trained model**:

- **No PCR.** This repo has no case-to-case citation gold set at all yet;
  adding one is a separate, larger effort (new corpus module, new index,
  new gold-set construction) that wasn't in scope for this pass.
- **No GNN / trained retriever.** The available gold data — 450 verified
  case→statute links after filtering (see below) — is roughly two orders
  of magnitude smaller than IL-PCSR's query set. Training a model on it
  would very likely underperform the existing untrained BM25+dense+graph
  engine while adding a dependency and a maintenance burden. Instead, this
  benchmarks that existing engine as-is, plus an optional, un-trained LLM
  re-ranking pass (Gemini) as the closest analogue to IL-PCSR's
  best-performing configuration.
- The upstream `Exploration-Lab/IL-PCSR` GitHub repo was reviewed but not
  cloned in: it is India-specific (IndianKanoon scraping, a different
  corpus schema, PyTorch/GNN training code) and not a fit to vendor.
  What's reused here is the *task formulation and eval methodology*,
  reimplemented against this repo's own data and conventions.

## Pipeline

### 1. `00_build_lsr_gold.py` — build the gold set

Deterministic, no LLM calls, re-running produces byte-identical output
(same convention as `scripts/build_*.py`).

Inputs:

- `scripts/case-law-statute-linking/output/resolved_links.csv`,
  `band == "verified"` rows only (450 of 764 rows; `review` and
  `unresolved` bands are excluded because their citation wasn't cleanly
  grounded).
- `scripts/case-law-information-extraction/output/rules.csv`, joined by
  `rule_id`, for the verbatim `supporting_quote` and
  `statute_citation_verbatim`.
- `data/processed/cases.jsonl`, joined by `case_id`, for the judgment text
  path and decision year.

Query construction (CLERC/IL-PCSR's masking pattern — mask the citation,
keep the surrounding sentence as the query):

1. Normalize whitespace and drop encoding-artifact characters (the
   extraction input and the committed markdown are not always
   byte-identical — OCR replacement characters and similar drift do occur;
   see `scripts/case-law-information-extraction/README.md`'s grounding
   gate for how the quote was originally verified). Locate the normalized
   `supporting_quote` in the normalized case text.
2. If found: take a ~400-character window on each side and mask the
   `statute_citation_verbatim` phrase within it (`window-citation-masked`),
   or the whole quote if the citation phrase alone can't be isolated
   (`window-quote-masked`).
3. If the quote can't be relocated in the stored text at all, fall back to
   using the quote itself as the query (`held-sentence-fallback`) rather
   than dropping the row.

Measured on the current corpus, the split across the three modes is
**window-citation-masked: 41, window-quote-masked: 32,
held-sentence-fallback: 377** — i.e. the exact-window construction only
succeeds for about 16% of verified links; the rest fall back to the bare
holding sentence as the query. This is a real data-quality limit (the
verbatim match that gated extraction was checked against a different text
snapshot than what's now committed), not a bug in the masking logic, and
it means most LSR queries here are coarser ("does this holding sentence
retrieve the right section") than IL-PCSR's tighter citation-window
queries.

Every row also carries `temporal_status` — `applicable` /
`superseded-since-judgment` / `history-unknown` — computed by
**reusing** `scripts/build_section_versions.py::grade_link()` against
`data/processed/actions.csv`, not reimplemented. This is the direct answer
to "can a query about a 1985 case be satisfied by a section version that
only existed from 2020 onward": it flags every gold row where the section
was in fact amended after the judgment, so those rows can be scored
separately instead of silently blended into the average.

Outputs: `data/processed/lsr_gold.jsonl` (one record per query) and
`data/processed/lsr_gold_skipped.csv` (join failures, if any — currently
none, since `resolved_links.csv`'s `verified` rows always resolved to a
rule, a case, and a case text file on this corpus).

Run: `python scripts/legal-statute-retrieval/00_build_lsr_gold.py`

### 2. `evaluate-lsr` — run the evaluation

`uv run python -m draftly.retrieval evaluate-lsr [--rerank]`

Runs `search()` (the production BM25+dense+graph engine, unmodified) over
every gold query, scores retrieval with the same `recall@k` / `precision@5`
/ `MRR` / `nDCG@10` functions already used for the statutes-only gold set
(`src/draftly/retrieval/evaluation.py`), and reports metrics **overall and
separately per `temporal_status` bucket**. `--rerank` adds one bounded
Gemini call per query that re-orders (never adds to) the existing top-10
candidates — the untrained analogue of IL-PCSR's LLM re-ranking stage — and
degrades to no-op when `GEMINI_API_KEY` is absent, matching the dense
channel's existing degrade behavior.

Output: `evaluation/runs/statute-retrieval-lsr-v1/` (`metrics.json`,
`predictions.csv`, `per-question-scores.csv`, `config.json`), same shape as
the existing `statutes-bm25-v1` run.

## What the first real run showed

On the 450-query gold set (BM25+dense+graph, no re-rank):

| Bucket | Queries | recall@5 | recall@10 | MRR |
| --- | ---: | ---: | ---: | ---: |
| Overall | 450 | 0.198 | 0.231 | 0.142 |
| `applicable` | 273 | 0.213 | 0.238 | 0.150 |
| `superseded-since-judgment` | 147 | 0.136 | 0.170 | 0.101 |
| `history-unknown` | 30 | 0.367 | 0.467 | 0.269 |

`superseded-since-judgment` recall is meaningfully lower than `applicable`
recall. That is consistent with a real, already-documented corpus
limitation rather than a retrieval-method weakness: the index holds only
the *current* text of each section (per README's "Temporal alignment is
measured, not solved"), so a query built from a judgment that predates a
later amendment is, in effect, being asked to match text the court never
saw. The gap is evidence for prioritizing README's "Next steps #2 — model
statutes temporally" (holding per-version text, not just per-version date
ranges), not evidence that the engine itself regressed.

`history-unknown`'s higher score is not a sign that untracked statutes
retrieve better — it's a small bucket (30 queries) drawn from statutes with
no amendment-history rows at all, which skews toward simpler, well-covered
sections; treat it as noise from sample size, not a real effect, until the
set is larger.

## Status and limits

- **`status=unverified`**, same as every other derived artifact in this
  repo. Nothing here has been reviewed by a lawyer, and the label field in
  `metrics.json` says so explicitly.
- **450 queries is a small, indicative sample**, not a statistically robust
  benchmark — treat differences of a few points between configurations as
  noise, not signal, until the gold set grows past a few hundred more rows.
- **The gold set only covers cases with an already-grounded citation.**
  It cannot measure how well the engine does on cases that discuss a
  provision without ever naming it — that would need a different (harder)
  gold-construction method, out of scope here.
- **84% of queries are the coarser `held-sentence-fallback` construction**
  (see above) rather than a tight citation window; recall numbers here are
  not directly comparable to IL-PCSR's own reported numbers, which use a
  cleaner masking process on a different corpus.
