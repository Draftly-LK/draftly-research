# Atomic question structure classifications

Structure and scenario-quality labels for the 667 atomic questions in
`../atomic-questions.jsonl`. Nothing here is a legal answer. status=unverified.

## Files

- `RUBRIC.md` — the annotation instructions applied to every item.
- `paper-NN.classified.jsonl` — one JSON object per atomic item, in source order.
- `merge_validate.py` — merges the per-paper files into
  `../atomic-classifications.jsonl`, writes `../atomic-classifications.summary.json`,
  and checks vocabulary, verbatim excerpts, and the candidate_action precedence.

## How the labels were produced

Eight LLM annotator passes (two papers each) applied `RUBRIC.md`. Each pass
derived `candidate_action` mechanically from the precedence rules and asserted
that every excerpt is a verbatim substring of the item. `merge_validate.py`
re-checks all of that and reports zero problems.

## Known caveats

- `context_sources` can only name background fields. Where facts sit in
  `group_lead` (P08-Q02-P01) or `stem` (P14-Q09), the item is flagged and, for
  the stem case, routed to `repair`.
- The `review` bucket is dominated by doctrinal questions that inherit an
  irrelevant factual background (flag `doctrinal_question_inherits_background`).
- `repair` items are mostly follow-ups whose antecedent facts were not carried
  into `prior_background` by `restructure_pastpapers.py`.
