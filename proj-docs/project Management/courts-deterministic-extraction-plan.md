# Court Judgments — Deterministic (No-LLM) Extraction Plan

Scope: the unreported Supreme Court and Court of Appeal judgments under
`data/legal-sources/library/case-law/courts/{sc,coa}`. These have **no editor
headnote**, so the deterministic headnote parser used for CommonLII (notebook
`04`) does not apply. This plan sets out how far we can get on these files with
**regex and rules only — no LLM** — decides which files are worth deep
extraction, and names the one thing regex cannot do.

Companion to `case-law-extraction-plan.md` (the LLM/Track-B plan, already run on
the conveyancing set). This document is the no-LLM route the team asked for.

## Why this plan

We want these judgments searchable and linkable inside the retrieval engine
without paying for, or depending on, an LLM. The question is not "can regex read
a judgment" — it is "which fields come off the page deterministically, at what
recall, and is that enough to be useful". We answered it by running the
extractors over the whole corpus, not by guessing.

## What the corpus actually contains (measured, 2026-07-30)

Ran the Stage-1 extractors + the conveyancing gate over **all 5,474** court text
files (`tmp` analysis → `evaluation/runs/courts-extractability/`). Every file is
usable (>= 200 chars); none were too short to parse.

| Field | Method | Coverage now | Achievable | Notes |
| --- | --- | ---: | ---: | --- |
| `court` | banner + directory | **100.0%** | 100% | trivial, exact |
| `decision_date` | `Decided/Delivered On:` + parse | 72.0% | ~88% | label present in 80%, widened labels 88% |
| `judges` (panel) | `BEFORE … COUNSEL` block | 77.0% | ~95% | the `BEFORE` label itself is present in **98.3%** |
| `authoring_judge` | name after date / first signature | — | ~95% | signature block present in **97.1%** |
| `final_order` | disposition cues in the tail | 71.9% | ~90% | a disposition word is in the tail of **90.0%** |
| `cited_cases` | NLR/SLR/… citation regex | 39.6% | ~45% | many judgments genuinely cite nothing; OCR mangles the rest |
| `statute_links` | `Section N of the <Act>` regex | 68.9% | ~75% | resolves to registry `SRC` ids where the statute is in the catalogue |

Noise is real but bounded: **15.7%** of files carry Unicode Sinhala passages and
**5.9%** carry legacy-font transliteration (ASCII gibberish). Both are body text,
not corruption — flag and keep, never delete. Dispositions break down as
dismissed 2,248 · set-aside 1,362 · allowed 1,005 · affirmed 513 · quashed 376 ·
remitted 116.

## Decision 1 — we do not need deep extraction on every file

The conveyancing gate passes **1,510 of 5,474 files (27.6%)**. The first product
(RTA / Bim Saviya notarial workbench) is conveyancing, so:

- **Deep extraction** runs on the ~1,510 conveyancing judgments.
- The other ~3,960 get the **envelope only** (court, date, judges, disposition,
  citations, statutes) — already computed, effectively free — so they stay
  searchable and can be promoted later without re-scanning.

This keeps the work proportionate and is reversible: the gate is cheap to re-run
if the product scope widens.

## Decision 2 — what "no LLM" can and cannot deliver

**It delivers, to retrieval grade:** the full envelope above, plus three
deterministic proxies for the "meaning" fields —

- `topics` — from the existing statute→topic bridge
  (`case_topic_links.csv` already tags **989 distinct court cases**) *and* the
  keyword lists per topic in `topics.csv`, matched against the judgment text. No
  LLM; expandable by editing the keyword lists.
- `questions_of_law` — the literal enumerated list, present verbatim in **31.7%**
  of judgments ("the questions of law are …"). Regex-liftable where present;
  absent otherwise.
- `candidate_holdings` — sentences carrying a rule cue ("it is settled law…",
  "I hold…", "held that…", "the principle is…"). Present in **74.2%** of
  judgments, mean 2.9 per case. Sampling confirms these surface the real ratio
  (e.g. 1095-99-f: *"the burden of proving prescriptive title falls on the
  defendant"*), alongside some non-ratio sentences (lower-court recitals, fact
  findings). Retrieval-grade, not clean.

**It cannot deliver** one thing: a single clean, deduplicated ratio sentence per
case (`atomic_rules[].statement`). Without a headnote the ratio is embedded in
prose next to obiter, quotations of other cases, and lower-court recitals, and no
regex separates them reliably. This is a **quality gap, not a coverage gap** —
the candidate-holding passages already carry the ratio for search; turning a
passage into a polished rule is what an LLM (or a human curator) adds later.

## The pipeline

1. **Clean / normalise.** Restore ligature filler (`￾` → `-`), strip page
   markers, collapse whitespace; flag Sinhala / legacy-font spans, keep them.
2. **Stage 1 — envelope regex.** The seven fields above, one tolerant extractor
   each (grounded on the label variants actually seen). A missed field is blank,
   never guessed.
3. **Stage 2 — conveyancing gate.** Strong land-statute signal (decisive) or ≥3
   land-lexicon hits. Routes the file to deep vs envelope-only. Cross-checked
   against the topic bridge.
4. **Stage 3 — deterministic meaning (conveyancing files).** Topic tags (from the
   bridge and keyword taxonomy), literal questions-of-law, and candidate-holding
   sentences with attribution filtering (drop "the learned Magistrate held…",
   keep this-court cues "I hold…"/"it is settled law…").
5. **Stage 4 — statute resolution.** Map each `Section N of the <Act>` to its
   registry `SRC` id via `catalogue.py`; keep the verbatim string when it
   resolves to nothing.
6. **Stage 5 — assemble + emit + review queue.** One JSON record per case in the
   target schema (`status: unverified`), plus a CSV review queue of candidate
   holdings for a lawyer to accept/reject into clean rules.

## Hardening backlog (to hit the "achievable" column)

Each item is evidence-backed by the measurements above, in priority order:

- **`decision_date` 72% → ~88%.** Add label variants (`Judgment/Order delivered
  on`, `dated this … day`, `pronounced on`) and loosen the date-format parser
  (spaced/゛trailing-dot forms). Label coverage is already 80–88%.
- **`judges` 77% → ~95%.** The `BEFORE` anchor exists in 98.3%; the loss is in
  the name-splitter. Improve the per-name split and fall back to the signature
  block.
- **`authoring_judge`.** Anchor on the name after the date; fall back to the
  first `JUDGE OF THE …` signature (present in 97.1%).
- **`final_order` 72% → ~90%.** When the sentence-grabber misses but a
  disposition cue is in the tail (90% of files), fall back to the detected
  signals (e.g. "affirmed; dismissed") so the outcome is never blank when known.
- **OCR / Sinhala.** Add a legacy-font transliteration flag to the quality
  metric (it currently only counts U+FFFD, so it under-reports). Leave the text
  as-is for now.

## What the deterministic output is good for

Retrieval-grade structured records for the whole corpus: searchable, statute- and
topic-linked, with candidate-holding passages and citations attached. That is
enough to **wire case law into the retrieval engine** and hand a lawyer a review
queue. The LLM (or human curation) later upgrades candidate holdings into clean
`atomic_rules` — an enhancement layered on top, not a prerequisite.

## Verification

- Envelope: the gate already scores **8/10 with zero disagreement** against the
  hand-labelled pilot (`notebooks/05_courts_judgment_extraction.ipynb`); extend
  the labelled set to ~50 cases and confirm per-field recall matches the targets.
- Meaning proxies: sample 50 candidate-holding sets and record what fraction
  contain the true ratio (recall) and how much non-ratio noise rides along
  (precision), to set the review-queue expectations.
- Scale: run the pipeline over all 5,474 files; deep on the ~1,510 conveyancing
  subset; emit per-case JSON + review queue under a gitignored run directory.
