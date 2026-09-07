# statutory-qa-v1

A scenario-based statutory retrieval benchmark for Sri Lankan conveyancing
law, with the frozen corpus it is scored against and the retrieval experiments
run on it. Everything here is `status=unverified`: the gold labels were
produced by a research agent and checked by an independent verification agent
(both Claude Opus 5), and no lawyer has signed anything off. Every file that
carries a label says so.

The paper draft that reads these files is `research-paper/neurips_2026.tex`.
The plan is `research-paper/plan.md`.

## Layout

```text
corpus/          frozen structured corpus (acts, sections, provisions, typed edges, manifest)
candidates/      keep/enrich candidate pool, matters, Tier A / Tier B queues
annotations/     per-matter legal maps, verification reports, merged proposed gold
reserved/        questions that need case law or common law (not scored)
benchmark/       private-gold, public-input, development/test ids (+ extended set)
review/          lawyer review packets and the empty approval forms
audits/          candidate funnel, gold funnel, authority coverage, validation report, disagreements
experiments/     configs, raw rankings, metrics, tables, figures, error analysis, model caches
schemas/         legal-map JSON schema
```

## Corpus

Built by `scripts/statutory-qa/build_corpus.py` from the finalized statute
trees under `data/legal-sources/library/finalized/`. One consolidated edition
per enactment; amending Acts with text are kept as separate documents.

| Item | Count |
| --- | ---: |
| principal enactments | 52 |
| amending Acts | 60 |
| sections (retrieval unit) | 4,557 |
| provisions (sub-section nodes) | 17,854 |
| typed edges | 6,346 |

Edge types: `defines` 3,780, `procedurally_requires` 1,153,
`cross_references` 847, `amends` 329, `qualifies` 131, `excepts` 106. The
manifest records the corpus fingerprint and per-file hashes.

## Benchmark funnel

| Stage | Questions | Matters |
| --- | ---: | ---: |
| atomic past-paper questions | 667 | |
| keep or enrich candidates | 210 | |
| quarantined for background-boundary problems | 18 | 18 |
| Tier B (OCR quality, low confidence) sent to manual review | 66 | |
| Tier A researched by agents | 144 | 92 |
| statute-only after research and verification | 106 | |
| reserved (needs case law or common law) | 38 | |
| blocked (missing authority, temporal, ambiguity) | 36 | |
| verification sent back to legal review | 27 | |
| main benchmark (proposed gold) | 50 | 40 |
| extended set (main + legal-review questions whose indispensable provisions verified) | 73 | 61 |
| lawyer approved | 0 | 0 |

Most blocks are stamp duty questions: the charging Acts leave the rate to a
Gazette Order that is not in the corpus, so the arithmetic cannot be sourced.

## Gold set (main, 50 questions)

- 23 statutes carry an indispensable provision; the Notaries Ordinance (19
  questions), Matrimonial Rights and Inheritance Ordinance (12), Prevention
  of Frauds Ordinance (9) and Registration of Documents Ordinance (9) dominate.
- 84 distinct indispensable sections. Indispensable sections per question:
  1 (3), 2 (16), 3 (7), 4 (8), 6 (10), 7 (4), 8 (1), 11 (1).
- Hop counts: 1 (1), 2 (10), 3 (22), 4 (15), 5 (2).
- 25 keep and 25 enrich questions; 17 questions need more than one Act.
- Indispensable provision decisions: 49 verified, 26 partially verified.
- Split by matter with seed 13: development 8 matters / 10 questions, test
  32 matters / 40 questions.

Across all 92 annotated matters the agents recorded 1,328 provisions (769
verified, 230 partially verified, 16 unresolved, 1 rejected, 312 left as
proposed on matters that never reached verification because no question was
statute-only) and 149 researcher/verifier disagreements for a lawyer.

## Retrieval systems and results

Systems are in `scripts/statutory-qa/sq_retrieval.py`; metrics in
`experiments/metrics/main-test/summary.json`; tables in
`experiments/tables/main-test/`. Hyper-parameters were chosen on the
development split (`experiments/configs/tune-dev.selected.json`; most
settings tie on 8 matters). See the paper for the result tables and the
error analysis.

## Commands

```powershell
uv run python scripts/statutory-qa/select_candidates.py
uv run python scripts/statutory-qa/build_corpus.py
uv run python scripts/statutory-qa/search_corpus.py search "notary attest outside district"
uv run python scripts/statutory-qa/validate_legal_map.py M001
uv run python scripts/statutory-qa/build_gold.py
uv run python scripts/statutory-qa/split_dataset.py
uv run python scripts/statutory-qa/run_retrieval.py --run tune-dev --split dev --tune
uv run python scripts/statutory-qa/select_tuned.py --tune-run tune-dev
uv run python scripts/statutory-qa/run_retrieval.py --run main-test --split test --systems all --config-overrides "<selected json>"
uv run python scripts/statutory-qa/evaluate.py --run main-test
uv run python scripts/statutory-qa/make_paper_numbers.py --run main-test
uv run pytest tests/test_statutory_qa.py -q
```

The research and verification agents are driven by the prompts in
`scripts/statutory-qa/prompts/`; each matter directory holds the agent's
legal map, its notes and the verifier's report.

## What is not here

No case-law retrieval, no common-law material, no answer-generation scoring,
no OCR, no client documents. Questions whose complete answer needs case law
or Roman-Dutch law are in `reserved/` and are not scored.
