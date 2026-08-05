# Draftly

Lawyer-in-the-loop platform for Sri Lankan legal drafting and review workflows.
This repository holds the research side: the legal corpus, the extraction
pipelines, and the retrieval engine. Everything it produces is
`status=unverified` until a lawyer signs it off.

## Corpus status

| Layer | Holdings |
| --- | --- |
| Statutes | 57 statutes, 18 amendments, converted to markdown |
| Section index | 45 statutes, 3,547 section entries (see limitations) |
| Reported case law | 3,703 CommonLII judgments (NLR / SLR, with editor headnotes) |
| Unreported case law | 5,474 Supreme Court and Court of Appeal judgments (no headnotes) |
| Case-to-statute mentions | 14,665 body-text links, unverified |
| Unresolved citations | 62,385 awaiting disambiguation |

## Case-law rule recovery

`notebooks/04_headnote_rule_recovery.ipynb` recovers the legal rule from
reported judgments by reading the NLR/SLR headnote layout directly. It is
deterministic, verbatim, and abstains rather than emit a non-rule.

- 3,521 of 3,703 judgments yield a rule (95.1%); 182 abstain and fall to the
  bounded LLM track.
- 2,037 rules open with an explicit `Held`. The rest are proposition-form
  headnotes, where the editor states the rule directly without a marker — for
  our purposes the more useful form, because the case facts are already
  stripped.

Part II of the same notebook turns that flat output into queryable structure:

- **Topic index** — 11,739 distinct terms split out of the catchword lists,
  covering 3,461 cases. The splitter masks bound compounds (`co-owner`,
  `Roman-Dutch`, `judgment-debtor`) before splitting, because separator dashes
  and hyphens are the same character in this corpus.
- **Graded statute links** — 2,275 links, each carrying a confidence grade and
  the character distance from the section number to the statute name.
- **Section bundles** — 531 `(statute, section)` groups holding every judgment
  whose headnote says that section governs it, in date order. 150 have three or
  more judgments, 27 have ten or more. Civil Procedure Code s.247 alone carries
  46 judgments spanning 1895 to 1997.

Bundles invert the corpus from "what does this case say?" to "what have the
courts held about this section?", which is the question a conveyancer asks.

Outputs land in `evaluation/runs/headnote-recovery-v1/structured/`
(gitignored): `rule_cards.jsonl`, `section_bundles.jsonl`, `topic_index.json`,
`statute_links_v2.csv`.

## Statute link grades

Every link carries one of six grades, so a failure says which system is at
fault instead of collapsing into a single "not found":

| Grade | Count | Meaning |
| --- | --- | --- |
| `in-index` | 970 | section verified against the section index |
| `gap-in-index` | 525 | plausible section, our index lacks it |
| `out-of-catalogue` | 344 | statute cited is not in the catalogue |
| `statute-not-indexed` | 285 | statute has no section index at all |
| `name-only` | 140 | statute named, no pinpoint section |
| `out-of-range` | 11 | section beyond the statute's last section |

Read that as a work list, not a score. Only 11 links are probably wrong; 810
are our catalogue being incomplete.

The Civil Procedure Code accounts for 943 of the 1,957 pinpoint links (43%) —
it is procedural, so every civil case travels through it regardless of subject,
and it has 840 sections against the Wills Ordinance's 9. 452 of its links are
blocked on our own index.

## Known limitations

**Two section indexes disagree.** `data/legal-sources/derived/statute-section-index.json`
holds 514 CPC sections; the live BM25 index the engine queries holds 103, all
marked `parsed`. Same source PDF, two extractions, 5x apart. Nothing that joins
cases to sections is trustworthy until one of them is authoritative and the
other is derived from it.

**Years are being read as section numbers.** The highest "section" recorded is
1896 for the Evidence Ordinance, 1941 for Registration of Documents, 1977 for
the Partition Law. Plausibility checks against those ceilings are meaningless.

**Section headings are truncated.** CPC s.4 is recorded as `is made special`,
s.9 as `actions: in what` — fragments of the marginal note, cut by a fixed
window.

**The index has no temporal dimension.** It answers "does section N exist?",
not "what did section N say on the date of this judgment?". The corpus spans
more than a century and the CPC was amended in 2024, so a consolidated 2024 PDF
proves the current wording and nothing about the text a 1981 court applied.

**Case law is deliberately excluded from the retrieval engine.** Five separate
guards enforce it (`ALLOWED_KINDS`, two runtime checks in `corpus.py`, a schema
`CHECK`, and the answering prompt). Serving case law is a scope decision, not a
missing feature.

**Nothing has been scored.** Every `metrics.json` reports
`scored_questions: 0` and `labelled_answers: 0`. `evaluation/retrieval-gold.csv`
has zero rows and `expected_case_ids` is empty everywhere. Recovery rates are
yield, not accuracy.

**Extraction error classes carried forward.** The `Held` marker is not anchored
to sentence start, so ordinary uses of "held" as a verb can be mistaken for it.
36 recovered rules open with case facts rather than a ruling, 17 of them in
1980-99. Both are documented in notebook 04 section 6 with the fixes that were
tried and rejected.

**Unreported SC/CoA extraction has not run.** The pilot in
`notebooks/05_courts_judgment_extraction.ipynb` builds the envelope and the
conveyancing gate, but Stage 3 returned `401 UNAUTHENTICATED`, so zero rules
have been extracted from the 5,474 judgments and the quote-grounding gate has
never executed.

## Next steps

Ordered by what unblocks what.

1. **Rebuild the statute section index.** Fix `section_parser.py` against the
   CPC first (103 of 840 sections found, 452 blocked links). Pick one index and
   derive the other from it. Bound section numbers so years cannot enter, and
   add a build assertion — `sections_found >= 0.8 * highest_section_number` —
   so a thin index fails loudly instead of quietly.
2. **Model statutes temporally.** `sections.jsonl` with one record per section
   *version* (`valid_from`, `valid_to`, source document) plus `actions.csv` for
   amendment events (`inserted | amended | replaced | repealed`). Then a
   citation resolves against the case date, and no answer may present a
   provision as applicable unless its version is temporally compatible.
3. **Build the evaluation gold set (~50 questions).** Roughly 30 auto-mined by
   masking citations in real judgment paragraphs — the 14,665 links generate
   these for free — plus 20 lawyer-written. Fill `expected_case_ids`. Nothing
   can be measured, tuned, or reported until this exists.
4. **Complete the dataset layer.** `authority.csv` (court, level, binding
   rank, reported), `aliases.csv`, `edges.csv` (one unified edge list),
   `actions.csv`, `sections.jsonl`. All five are specified in
   `project Management/retrieval-engine-methodology.md` section 9.4 and none
   exist yet.
5. **Build authority ranking** — Supreme Court binding, Court of Appeal binding
   on courts below, High Court persuasive; a ranking signal and a display
   label, never a filter. This is the project's most novel component relative to
   the literature and it is currently unbuilt.
6. **Get lawyer sign-off.** `review-sample.csv` (60 rows) for headnote rules, a
   separate sample for the 1980-99 cohort, and the 74 rows in
   `evaluation/runs/caselaw-ablation-v1/lawyer-labels.csv` whose seven verdict
   columns are all blank. The pre-registered criterion is
   `lawyer_legal_precision >= 0.9`; the full 3,179-case extraction run is gated
   behind it.
7. **Fix the Gemini credentials and re-run the SC/CoA pilot**, confirm the
   quote-grounding gate rejects an injected fabricated quote, then measure cost
   per case before scaling.
8. **Resolve the 62,385 unresolved citations** with a bounded LLM pass:
   deterministic pre-filter, candidates from the closed catalogue, an abstain
   option, and validation that the section exists in that act.
9. **Acquire the missing statutes** — Partition Ordinance No. 10 of 1863 and
   Partition Act No. 16 of 1951 (344 links point at statutes not in the
   catalogue).
10. **Then decide whether case law enters the retrieval engine**, and if so
    extend the answering contract first: a statute section is binding text, a
    case rule is unverified and possibly overruled.

## Statutes-Only Q&A Demo

The current demo searches 57 statutes and 18 amendments. It does not use case
law, deed templates, or historical validity rules. Gemini answers are limited to
retrieved sections, and each retained claim is checked against its citations.

Create `.env` with `GEMINI_API_KEY`, then run:

```powershell
uv sync
uv run python -m draftly.retrieval build
uv run streamlit run apps/statute-retrieval/app.py
```

Open `http://localhost:8501`. The command-line interfaces are:

```powershell
uv run python -m draftly.retrieval search "What makes a deed valid?"
uv run python -m draftly.retrieval ask "What makes a deed valid?"
uv run python -m draftly.retrieval evaluate
uv run python -m draftly.retrieval evaluate-questions
```

The retrieval evaluation uses ten unverified development labels. The
`evaluate-questions` command runs all 18 exam questions and 73 subquestions from
`src/questions.md`, but it does not report legal correctness without lawyer gold
labels.

## Writing Style

Project-facing prose should be checked with the local avoid-ai-writing skill before it
is treated as final.

Use:

```text
.agents/skills/avoid-ai-writing/SKILL.md
```

This applies to README edits, proposal text, report sections, project descriptions,
emails, and public-facing documentation.
