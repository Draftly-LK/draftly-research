# Final review record

Three review passes over the paper (`research-paper/neurips_2026.tex`), the
dataset README and the plan, run on 5 September 2026 after the main
experiment (`experiments/metrics/main-test/summary.json`). Each pass lists
what was checked and what changed.

## Pass 1: numbers

Checked every hand-typed number in the paper against the metric and audit
files. Macros (`paper-numbers.tex`) are generated and were not re-typed.

- Complete recall by bundle size, all seven systems: matched the breakdown
  in the summary. The prose had quoted only the range of the stronger
  systems for one-section and two-section questions; corrected to the full
  range (0.33 to 1.0 and 0.25 to 0.67).
- Temporal-filter ablation: the prose said two gold provisions were affected.
  The per-question files show one (M084-Q01), and the cause is a gold citation
  to a 2022 amending Act whose section recites the 2019 wording of a Notaries
  Ordinance rule. Sentence rewritten.
- Median bundle size: the test median is between three and four sections, so
  "the median question needs four" was replaced with "half the test questions
  need four or more" (20 of 40).
- Act routing accuracy 0.438, multi-Act test questions 12 of 40, MRR 0.543 to
  0.223, Act identification 0.625 to 0.469, dense C@20 0.188, recall gain
  0.482 to 0.546, 114 missed sections with 2 reachable by one edge, 3,780 of
  6,346 edges, C@20 0.43 versus 0.11 for enrich versus keep: all confirmed.
- Corpus counts in the README and plan were aligned with the rebuilt manifest
  (6,346 edges; 1,153 procedurally-requires; 847 cross-reference; 106
  excepts).

## Pass 2: claims and scope

- No sentence claims lawyer validation. Every gold row carries
  `lawyer_validation_status: pending` (50 of 50). The abstract, benchmark
  section and limitations each say the gold is proposed.
- No sentence claims an improvement or significance. The abstract and the
  title state the negative result; the paired bootstrap intervals that
  include zero are in Appendix B.
- The figure caption that had described a lift was rewritten to describe the
  crossing curves.
- Out-of-scope items are listed in the limitations section and in the README:
  case law, common law, answer-generation scoring, OCR, the product, SPLADE,
  query decomposition, a domain-trained reranker. The abandoned bge-reranker
  run is recorded in the plan's execution record.
- The interim runs `smoke`, `smoke2` and `smoke3` under `experiments/` were
  made on an unfrozen, partly unverified gold set and are not cited anywhere;
  they are kept as the record of the two design decisions taken before the
  gold was frozen (rerank query format, expansion scoring).

## Pass 3: writing and reproducibility

- Avoid-AI-writing scan of the paper, README, plan and prompts: no em dashes,
  no tier-1 vocabulary, no filler transitions, no "not X but Y" pivots.
  Headings are sentence case. Bold appears only in Markdown list labels.
- `uv run pytest tests/test_statutory_qa.py -q`: 15 passed.
- `npx markdownlint-cli2` on the new Markdown: clean apart from MD041 on the
  first line of `research-paper/plan.md`, which is the user's original brief
  and was left as written.
- Every run directory has `configs/<run>.json` (hashes of corpus manifest,
  public input and split file, model names, environment, per-system config),
  `raw-rankings/<run>/*.jsonl`, `metrics/<run>/summary.json` and per-question
  files. The paper reads its numbers through `make_paper_numbers.py`.
- Public input was grepped for provision and section identifiers: none.
- The paper compiles with `latexmk -pdf` without errors or undefined
  references; the body ends on page 4 and references start on page 5.

## Open items for the authors

- Confirm the exact workshop title for `\workshoptitle{}` and the page limit
  with the organisers; the paper is set for four pages plus references and
  appendices.
- Add the architecture figure at the commented placeholder in the Method
  section.
- Lawyer review of the 50 gold questions and the 27 questions the verifier
  sent to legal review (`review/lawyer-review-packets/`).
