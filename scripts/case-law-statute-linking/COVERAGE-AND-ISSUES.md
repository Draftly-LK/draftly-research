# Case→statute linking: coverage and known issues

Full picture of what the deterministic (non-LLM) linking pipeline
(`scripts/case-law-statute-linking/`) has actually done across the whole
case-law corpus, and every issue found while building it across two rounds
of hardening. Every number below came from running the real pipeline against
the real corpus on 2026-09-02, not from an estimate.

## The funnel: how much of the corpus is actually linked

| Stage | Count | Share |
| --- | ---: | ---: |
| Cases in the corpus | 9,177 | 100% |
| Cases with at least one extracted rule | 3,620 | 39.5% of cases |
| Rules with a locatable statute citation | 649 | 15.6% of rules |
| Link rows produced from those citations | 762 | — |
| → `verified` | 462 | 60.6% of link rows |
| → `review` | 61 | 8.0% of link rows |
| → `unresolved` | 239 | 31.4% of link rows |
| Distinct cases with ≥1 `verified` statute link | 369 | **4.0% of all 9,177 cases** |
| Distinct cases with ≥1 `verified` or `review` link | 410 | 4.5% of all 9,177 cases |
| Ungrounded LLM/headnote guesses (no citation at all, kept separate) | 531 | — |

**Read the 4.0% carefully — it is not "96% of cases have no statute link
in them," it's "96% of cases have not been checked yet."** The real
bottleneck is the top of the funnel, not this linking stage: only 39.5% of
cases have had a rule extracted at all, and of those, only 15.6% produced a
locatable citation. This pipeline resolves what it's given close to
completely (462 + 61 = 523 of the 762 link rows, 68.6%, land somewhere
other than `unresolved`) — the ceiling on total coverage is set upstream,
by `case-law-information-extraction`, not by anything in this stage.

## Issues found, and what happened to each

| # | Issue | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Abbreviations (`CPC`, `C.P.C.`) never matched a full statute name | **Fixed** (round 1) — `normalize_fragment` collapses punctuation/spacing before a word-boundary match | 41 judgment files use this form |
| 2 | Bare `"Ordinance/Act No. N of YYYY"` citations have no name to match at all | **Fixed** (round 1) — independent number+year resolver against `statute_index.csv` | 91 of 276 then-unresolved rows were this pattern; 47 immediately recoverable |
| 3 | Acronyms only existed for 9 hand-picked statutes | **Mitigated** (round 1) — `propose_aliases.py` derives one for every statute in the catalogue, gated behind human review | 51 clean proposals waiting in `proposed_aliases.csv`, none promoted yet |
| 4 | An amending instrument's own section number leaked into the cited Act's link | **Fixed** (round 2) — `AMENDING_CLAUSE_RE` masks `"amended by s. N of ..."` before section extraction | 3 confirmed cases (Jaffna Ordinance "6", Courts Ordinance "4", CPC "2") |
| 5 | A citation naming two different Acts had every section number silently attributed to just one | **Fixed** (round 2) — `find_all_name_acts`/`find_all_number_acts` collect every distinct Act signalled; 2+ → abstain to `review` instead of guessing | 13 distinct real citations found this way; 23 previously-`verified` link rows were **actually wrong** and are now correctly flagged, not silently trusted |
| 6 | A more specific alias (`"Jaffna Matrimonial Rights and Inheritance Ordinance"`) wasn't registered, so a shorter, wrong Act's name matched by pure substring | **Fixed** (round 2) — alias added to `alias_seed.csv`, and a general suppression rule added so a matched fragment that's contained in another matched fragment doesn't count as a second Act | 3 real citations now correctly resolve to SRC045 instead of the wrong SRC004 or an unresolved disagreement |
| 7 | True multi-Act citations aren't split into two correct links, only safely flagged | **Documented limitation, not fixed** — would need citation segmentation, out of scope for this round | The 13 citations from #5 land in `review` for a person, not auto-resolved |
| 8 | 44 remaining unresolved numbered citations cite an Act not in our registry at all | **Documented limitation, not fixable here** | `out-of-catalogue` — a data-acquisition gap (root README's "Next steps"), not a linking-logic one |
| 9 | Some abbreviated citations (like `CPC`) never even make it into `rules.csv` | **Documented limitation, out of scope for this pipeline** | 41 files use `CPC`/`C.P.C.`, 0 of those specific citations appear in the extracted rules — an upstream `case-law-information-extraction` gap, unchanged by anything here |

## What "verified" does and doesn't mean

`verified` is an internal-consistency heuristic — the Act matched (by name,
number, or both in agreement), the section exists in that Act's index, and
the section number is echoed in the citation text. All three can hold and
the link can still be substantively wrong in a way none of these checks can
see (e.g. the wrong section text, or a citation that's accurate on its face
but legally superseded — see the retrieval-side temporal analysis in
`scripts/legal-statute-retrieval/README.md`). **No lawyer has checked any of
these links.** `review-sample.csv` (45 rows, stratified across resolver path:
name-alias, number+year, and multi-Act/mismatch) has a blank
`lawyer_verdict` column waiting for exactly that check — nothing here should
be presented as a confirmed citation until it's filled in.

## Round-over-round trend

| | Round 0 (pre-hardening) | Round 1 | Round 2 (current) |
| --- | ---: | ---: | ---: |
| `verified` | 450 | 486 | 462 |
| `review` | 38 | 40 | 61 |
| `unresolved` | 276 | 239 | 239 |

Round 2's `verified` count is *lower* than round 1's, on purpose — 23 of
round 1's `verified` rows were the multi-Act false positives from issue #5,
now correctly demoted to `review`. Coverage numbers alone don't measure
accuracy (a point worth restating from the earlier discussion in this
project): round 1 looked like a bigger win by count, but round 2 is the one
that actually removed confirmed wrong answers rather than just adding new
correct ones.
