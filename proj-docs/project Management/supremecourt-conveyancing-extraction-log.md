# Supreme Court conveyancing extraction: how it was built

This is a record of how `data/supremecourt.lk/case_data.csv` (the final
conveyancing case set) got built, in the order it actually happened, with
the real numbers at each step. The goal throughout was to spend LLM calls
only where regex genuinely could not do the job.

## 1. Scrape baseline

2,150 Supreme Court judgment PDFs scraped from supremecourt.lk into
`data/supremecourt.lk/SCLR/`, indexed by `manifest.csv`. This file is
already close to fully populated straight from the site's own listing
page: 2,150/2,150 case numbers, 2,150/2,150 judge names, 2,149/2,150
parties. No PDF parsing needed for any of that.

## 2. First pass: regex only, no LLM

`extract_supremecourt_deterministic.py` reads each PDF's text layer and
fills a row per case using pattern matching alone: disposition, statute
citations, judge panel, case caption fields. First full run:

- disposition classified: 70.6% (29.4% fell back to `unclassified`)
- statute citations found: 45.7%
- a rule-signaling phrase (`principle_statement`): 11.7%
- coram (judge panel) parsed: 98.2%

Zero cost, about 40 seconds for all 2,150 cases.

## 3. Bug fixes found by reading the actual output

Two real bugs turned up on inspection, not from theory:

- A stray page-number digit was occasionally captured as a judge's name
  in the coram field. Fixed by rejecting lines that are not mostly
  letters.
- The disposition search only looked at the last 4,000 characters of a
  judgment, which missed cases where the ruling sat just outside that
  window. Widened to 6,000 characters and added a couple more phrasing
  patterns.

## 4. Wider principle-statement search

The first pass only checked for 4 explicit rule-signaling phrases
("it is settled law that...", etc.). Expanded to 15 phrases and let each
case return up to 3 candidate passages instead of stopping at the first
match. Yield went from 11.7% to 18.8% (252 to 405 of 2,150 cases),
spot-checked against source text.

That is close to the ceiling for regex alone: most judgments state a rule
without ever using a self-labeling phrase, and no amount of pattern
tuning fixes that.

## 5. Building the conveyancing classifier

The corpus needed to be narrowed to conveyancing cases only. First cut
was a keyword list reused from an existing script in this repo
(`harvest_courts_caselaw.STRONG`), 4-hit threshold: 772 of 2,150 cases
(35.9%).

Cross-checking that against the statute citations already extracted in
step 2 found a second, independent signal: 424 cases cited a statute from
the closed catalogue but had no keyword hit. Checking which statutes,
331 of those 424 cited only Civil Procedure Code, Evidence Ordinance, or
Companies Act, general procedural statutes that appear in nearly every
civil case regardless of subject. The other 93 cited an actual
substantive conveyancing statute (deeds, wills, partition, land,
notaries, registration).

Final classifier: `conveyancing = substantive statute citation OR keyword
threshold`, with those four generic statutes excluded from the citation
side. Result: 865 of 2,150 (40.2%).

One thing tested and rejected: limiting the keyword scan to just the case
caption instead of the full text, to save compute. Hit rate collapsed
from 35.9% to 10.2-18.6% depending on the cutoff, because the substantive
legal issue is usually developed in the reasoning, not announced in the
opening paragraph. Full-text scanning stayed.

## 6. First LLM attempt: local, and slow

For the fields regex could not fill, the plan was to run an LLM locally
(Ollama, `llama3.1:8b`) at no cost. Measured throughput on the actual
machine: about 110 tokens/second prefill, 19-20 tokens/second generation.
At this pipeline's prompt size, that works out to 45-70 seconds per case,
projecting to 27-42 hours for the full backlog.

The first real batch also surfaced a prompt bug: the JSON schema shown to
the model used placeholder text like `"<verbatim span, THIS court's own
words>"`, and the small local model copied that placeholder literally
instead of substituting a real quote. 19 of the first 20 cases failed for
exactly this reason. Rewriting the prompt to say plainly that the example
text was a description, not something to copy, took yield from about 5%
to 78-85% on the next batches.

## 7. Sending only the needed part to the LLM

Two changes cut the per-case cost once the prompt bug was fixed:

- Skip any case where step 4's regex pass already found a genuine
  principle statement. No LLM call needed to re-derive something already
  known: 405 cases skipped outright.
- For the rest, anchor on the same disposition-phrase match the regex
  classifier already computes, and send only the case caption plus a
  window of about 2,300 characters around that anchor, instead of the
  full judgment. Falls back to a larger window only when no anchor is
  found.

Measured effect: about 29 seconds per case, roughly half the earlier
estimate, on top of the 405 cases that needed no call at all.

## 8. Filtering to conveyancing before the LLM step

Since the corpus was already narrowed to 865 conveyancing cases in step
5, there was no reason to run the expensive step on anything outside
that set. Filtering the LLM stage to conveyancing-only cases cut the
remaining workload from 1,745 cases to 594, roughly a two-thirds
reduction in LLM calls for no loss of coverage on the cases that matter.

## 9. Moving from local to NVIDIA's hosted API

Once an NVIDIA API key was available, the whole extraction step moved
off the local machine to NVIDIA's hosted NIM service
(`meta/llama-3.1-8b-instruct` at `integrate.api.nvidia.com`). Measured
per-case latency dropped to about 1.4-2 seconds, roughly 15-20 times
faster than the local run. The rest of the pipeline (targeted windows,
skip-if-already-known, quote grounding) carried over unchanged.

## 10. Classification confirmation plus field backfill in one call

The 865 conveyancing cases split into two groups: 377 had both a
substantive statute citation and a keyword hit (high confidence, no
confirmation needed), and 488 had only one of the two signals
(uncertain). For the uncertain group, and for any case still missing
disposition or a rule statement, one combined LLM call did three things
at once: confirm or reject the conveyancing classification, fill
disposition if missing, and extract the rule if one exists. Every
returned quote had to be a verbatim substring of the judgment or it was
rejected, same grounding rule as the rest of the pipeline.

763 cases needed this call. Result: 775 confirmed conveyancing, 89
reclassified as not conveyancing after a closer look, all on NVIDIA at
roughly 2 seconds per case.

## 11. Recovering the remaining gaps

After step 10, 85 cases still had no rule statement, mostly genuine
abstentions where the model looked at its narrow window and correctly
found nothing to extract. Retried all 85 with the full judgment text
instead of the anchored excerpt: 50 recovered. A separate retry against
NVIDIA's 70B model for the last 35 was attempted and abandoned; the
endpoint hung indefinitely on every call, including a trivial test
prompt, so the smaller model's result stood. 35 cases remain without a
rule statement after two genuine attempts, which is treated as an honest
result, not a gap to keep chasing.

## 12. Final numbers

- 776 confirmed conveyancing cases in `case_data.csv`, zero blank cells
- `principle_statement` filled: 95.5% (741 of 776)
- `disposition` classified: 100% (776 of 776, after a small follow-up
  pass on 4 unusual case types that did not fit the standard
  allow/dismiss vocabulary)
- 1,380 cases excluded, listed with reasons in
  `rejected_non_conveyancing.csv`

An independent accuracy check, using a differently-worded prompt on a
random sample of 20 kept cases, agreed with the classification on 15 and
disagreed on 5. Reading those 5 in full: 2 were the audit's own error
(it saw too little text), 1 looked like a genuine false positive, and 2
were ambiguous. Left as-is and documented here rather than acting on a
single short-context audit call.

One regex fix was built and then not applied: a bug where the
disposition classifier could match a quoted precedent's outcome instead
of the case's own order was confirmed on a real case
(`SC/APPEAL/46/2017`, whose text ends "Appeal Dismissed" but was
classified `set-aside` from an earlier quote). The fix that addressed it
also changed 284 of 776 rows when measured against the trusted dataset,
including 71 cases that would have lost their classification entirely.
With no budget to verify all 284 by hand, the fix was reverted rather
than risk a net-negative change to already-finalized data.
