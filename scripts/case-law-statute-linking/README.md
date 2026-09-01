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

Before (name-alias matching only, 9 hardcoded full statute names,
unnormalized substring matching): 450 verified / 38 review / 276 unresolved
(764 rows).

After (normalization + word-boundary matching + the number+year resolver):
**486 verified / 40 review / 239 unresolved** (765 rows) — 36 more verified
links, 37 fewer unresolved, from data the corpus already had. Two things
drove it, both measured against the real judgment text before being
built, not assumed:

- **41 judgment files** contain a section number next to `CPC`/`C.P.C.` —
  none of these citations resolved before, because the alias table had no
  normalization step.
- **91 of the 276 previously-unresolved rows** were bare
  `"Ordinance/Act No. N of YYYY"` citations; **47 of those** are
  immediately resolvable against data `00_build_statute_index.py` already
  computes (`act_number`/`year` in `statute_index.csv`) but that nothing
  downstream used until now. The remaining ~44 cite an Act genuinely absent
  from the registry (`out-of-catalogue`) — a data-acquisition gap (see
  root README's "Next steps"), not something this resolver can fix.

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

## Status

Everything here is `status=unverified`, same as every other derived
artifact in this repo. `review-sample.csv`'s `lawyer_verdict` column is
blank until a lawyer fills it in — nothing in `resolved_links.csv` should
be presented as a confirmed citation until that happens.
