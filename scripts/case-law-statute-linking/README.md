# Case-law → statute linking

Resolves the statute citations already extracted by
`case-law-information-extraction` into `(case, statute section)` links,
graded by how much to trust each one. This is the "first stage" of
connecting case law to statutes — a deterministic citation-parsing
pipeline, not a retrieval model (see
`scripts/legal-statute-retrieval/README.md` for the retrieval-based
follow-on task built on top of this pipeline's output).

## Run it

```sh
python scripts/case-law-statute-linking/run_pipeline.py
```

Runs stage 0 → alias proposals → stage 2 in order and prints one summary
(band counts, top unresolved reasons, pending alias proposals). It does
**not** run `case-law-information-extraction`'s LLM rule extraction — that
costs NVIDIA credits and is invoked manually; the orchestrator only checks
`rules.csv` already exists.

To draw a human-review sample after a run:

```sh
python scripts/case-law-statute-linking/build_review_sample.py
```

## Pipeline stages

| Script | Does |
| --- | --- |
| `00_build_statute_index.py` | Builds `statute_index.csv` (source_id → official_title/act_number/year/section_count), `statute_sections.csv` (every section number each statute actually has), and refreshes `alias_seed.csv`'s scaffold rows (hand-edited `aliases` column is preserved across runs). |
| `propose_aliases.py` | Derives a candidate acronym for every statute from its title's initials, drops any that collide between two statutes, and writes survivors to `output/proposed_aliases.csv` for a human to copy into `alias_seed.csv` by hand. **Never writes to the live alias table.** |
| `02_resolve_links.py` | The actual resolver — see below. Produces `resolved_links.csv` and `candidate_guesses.csv`. |
| `build_review_sample.py` | Draws a stratified, deterministic sample of resolved links into `review-sample.csv` with a blank `lawyer_verdict` column, for a precision spot-check. |
| `01_audit_existing_resolution.py`, `audit_statute_links.py` | Older, read-only diagnostics kept for reference; superseded by the summary `run_pipeline.py` now prints. |

## How resolution works

For every rule with a verbatim citation, two **independent** resolvers run
and their results are cross-checked — this is the piece that closes the
gaps found while building this:

1. **Name-alias matching** (`match_act`). The citation and every alias
   fragment are normalized (lowercased, punctuation stripped, spaced-out
   initials collapsed) before a word-boundary match, so `"CPC"`,
   `"C.P.C."`, and `"C. P. C."` all resolve the same way instead of only
   the spelled-out `"Civil Procedure Code"` matching. Word-boundary
   matching (not substring containment) stops a short alias from firing
   inside an unrelated word — but a short alias that happens to spell an
   ordinary word (e.g. `"to"` for "Trusts Ordinance") will still match a
   genuine standalone occurrence of that word; that risk is exactly why
   `propose_aliases.py` routes new acronyms through human review instead
   of adding them automatically.
2. **Act/Ordinance-No.-of-year matching** (`match_act_number`). A whole
   class of citations — `"Ordinance No. 22 of 1871, s. 3"` — carries no
   statute name at all, so (1) can never resolve them. This looks up the
   `(number, year)` pair directly against `statute_index.csv` (confirmed a
   unique key across the registry: 73 pairs, 0 collisions), independent of
   any name match.

**Where the two disagree** — the name path and the number path resolve to
different statutes for the same citation — the link is not silently
decided either way. It's routed to `review` with
`reason=name-number-mismatch:<A>-vs-<B>`, because a disagreement between
two otherwise-trustworthy signals is a real anomaly worth a person's
attention (a mis-extracted citation, a genuinely ambiguous cite, or a
still-missing alias), not something to resolve by fiat.

Every emitted link keeps a band:

| Band | Meaning |
| --- | --- |
| `verified` | Act matched (by either path, in agreement) and the section exists and the section number is echoed in the citation text. |
| `review` | Act matched but the section wasn't found in that statute, the citation named an Act with no section number, or the two resolver paths disagreed. |
| `unresolved` | Neither resolver matched an Act in the catalogue. |

`02_resolve_links.py` also asserts `rules.csv` has the columns this stage
expects before processing, so a future change to the extraction schema
fails loudly here instead of silently producing an empty or wrong
`resolved_links.csv`.

## What this measurably fixed

Two rounds of hardening, both measured against the real judgment text
before being built, not assumed. This pipeline only ever sees the 5,121
conveyancing-flagged cases (the other 4,056 of the full 9,177-case corpus
are out of scope by design — upstream extraction never runs on them). Full
detail, the complete issues list, and what fraction of that 5,121 is
actually linked (short answer: 7.2% verified — the ceiling is set upstream
by extraction/citation yield, not by this stage) are in
**[`COVERAGE-AND-ISSUES.md`](COVERAGE-AND-ISSUES.md)**.

**Round 1** (name-alias matching only, 9 hardcoded full statute names,
unnormalized substring matching → normalization + word-boundary matching +
a number+year resolver): 450→486 verified, 276→239 unresolved. Driven by
two gaps: 41 judgment files use `CPC`/`C.P.C.` with no normalization to
catch it, and 91 of the then-276 unresolved rows were bare `"Ordinance/Act
No. N of YYYY"` citations with no name to match at all (47 immediately
resolvable against data stage 0 already computed but nothing used).

**Round 2** (this pass — mask an amending instrument's own section number
out of the base Act's link; detect and abstain on citations naming two
different Acts instead of guessing; add one missing regionally-qualified
alias): 486→462 verified. Verified *dropped* on purpose — 23 of round 1's
verified rows were multi-Act citations silently and wrongly attributed to
one Act (confirmed by hand, e.g. section 44 of the Evidence Ordinance
wrongly filed under the Partition Ordinance); they're now correctly in
`review` instead of quietly wrong. Round 2 is a precision fix, round 1 was
mostly a recall fix — the two numbers aren't comparable on their own.

## What this does not do

- Does not re-run `case-law-information-extraction`'s LLM extraction, and
  never will automatically — that pipeline costs NVIDIA credits and stays
  a manual, separate step.
- Does not resolve citations to statutes that aren't in the registry at
  all (`out-of-catalogue`) — that needs acquiring the missing statute
  text, not better citation parsing.
- No fuzzy/ML name matching (edit-distance, embeddings). The two
  deterministic paths above already recovered a measured, zero-false-
  positive-risk gain; a fuzzy layer adds false-positive risk without
  evidence it's needed yet.
- `propose_aliases.py` never writes to the live alias table. A person
  reviews `proposed_aliases.csv` and copies chosen entries into
  `alias_seed.csv`'s `aliases` column by hand.
- Does not split a genuine multi-Act citation into two correct links —
  abstaining to `review` (round 2) stops it from being silently wrong, it
  doesn't resolve both Acts. That needs citation segmentation, a bigger
  piece of work than either round attempted.

## Status

Everything here is `status=unverified`, same as every other derived
artifact in this repo. `review-sample.csv`'s `lawyer_verdict` column is
blank until a lawyer fills it in — nothing in `resolved_links.csv` should
be presented as a confirmed citation until that happens.
