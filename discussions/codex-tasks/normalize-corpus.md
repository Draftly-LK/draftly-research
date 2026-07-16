# Normalize Corpus Task

You are working in the Draftly repo (D:\projects\draftly). Windows; use the
project venv at .venv (docling, pypdfium2, pandas installed). Sri Lankan
conveyancing legal-tech project.

## STEP 0 — LOAD CONTEXT FIRST (do not skip)

Read and follow, in order:

- AGENTS.md
- .agents/context/CONTEXT.md   (esp. "DATA-PREP STATUS", case-law + topics)
- roadmap.md                   (Workstream B = this work)
- notebooks/data_processing_pipeline.ipynb  (Stages 0-5 exist — extend, don't rebuild)
- data/legal-sources/library/case-law/README.md
- scripts/: audit_corpus.py, normalize_topics.py, reconcile_topics.py,
  harvest_courts_caselaw.py, reextract_failed.py, filter_conveyancing_caselaw.py

When done, run the update-context skill (save) and the logbook-entry skill.

## MISSION

Normalize the ENTIRE legal corpus into ONE file-based store the rule-based
retrieval engine reads from: **data/processed/**. Keep working through the steps
until the Definition of Done holds. Do NOT stop half-way. Report progress after
each step.

**data/processed/ IS THE RETRIEVAL ENGINE'S DATA SOURCE.** It must contain the
normalized MARKDOWN/TEXT for EVERY document — statutes, amendments, gazettes,
institution-guides, AND case law — plus the structured records and rule tables.
The engine reads ONLY from data/processed/. Target layout:

```text
data/processed/
  docs/
    statutes/<slug>.md
    amendments/<slug>.md
    gazettes/<slug>.md
    institution-guides/<slug>.md
    case-law/<source>/<id>.md         (commonlii / courts / internet-archive)
  documents.csv        (provenance for everything in docs/: doc_id, source_id?,
                        kind, court?, citation?, origin_url, local_pdf?, text_path,
                        converter, status, retrieved_date)
  cases.jsonl          (per-case records, conforming to documents.csv)
  topics.csv, topic-sources.csv, topics.json     (rule tables, copied in)
  case_statute_section_links.csv
  unresolved_citations.csv
  verification-sample.csv
  README.md
```

data/processed/ is gitignored (rebuildable) — fine; it's the derived store.

## THE NOTEBOOK IS THE RUNNABLE WALKTHROUGH

`notebooks/data_processing_pipeline.ipynb` must be the human-readable, runnable
demonstration of the WHOLE pipeline, so the user can see exactly how all the data
is processed:

- Update it to match the new data/processed/ structure and every step below.
- Each step gets a markdown cell explaining what it does, then a code cell doing it.
- Then **EXECUTE the notebook end-to-end with outputs saved in the .ipynb**, full
  run (SAMPLE_LIMIT = None), e.g.:
  `.venv\Scripts\python -m jupyter nbconvert --to notebook --execute --inplace
  --ExecutePreprocessor.timeout=1800 notebooks/data_processing_pipeline.ipynb`
  (pip install jupyter/nbconvert locally if missing — that's local tooling, allowed.)
- It must run top-to-bottom with NO errors and actually generate the full
  data/processed/ store. Keep the executed outputs in the committed notebook.

## HARD CONSTRAINTS FOR THIS PHASE

- NO Document AI. NO external/paid LLM APIs. NO cloud calls for OCR or extraction.
- Use LOCAL OCR only for scanned PDFs — Tesseract (sin+eng) or Surya, or docling's
  local OCR. Manage memory (page-by-page, ~150 DPI, no full-page image rendering)
  to avoid the std::bad_alloc that killed earlier docling runs.
- NO SQLite / no database. File-based only: markdown/text + JSONL + CSV.
- Deterministic first (regex/rules). Where a step needs "understanding", FLAG the
  item for a later bounded pass — do not call an external model.
- Grounding: never fabricate citations, sections, parties, links. If unsure,
  mark status=unverified.
- Privacy: do NOT read or copy from data/raw/. Public corpus only.
- Run `npx markdownlint-cli2` on Markdown you create; .agents/** is exempt.
- Do NOT commit. Leave changes for the user to review.

## WORK — in this exact order

1. **Fix the CommonLII join problem (~47 rows fail to join).** Diagnose (CSV
   quoting/commas in titles, BOM/encoding, missing text_file paths, citation-dedup
   collisions, blank citations). Fix so 100% of conveyancing rows load. Report root
   cause + before/after counts.

2. **Build data/processed/ as the normalized store (all docs).** Populate
   data/processed/docs/ with clean MARKDOWN for EVERY document (statutes,
   amendments, gazettes, institution-guides, case law) from library-markdown/ and
   the case-law text. Write documents.csv (provenance for every doc); make
   cases.jsonl conform. Copy rule tables in. Add data/processed/README.md.
   VERIFY every documents.csv row points to a real, non-empty markdown file; report
   any with no text (→ OCR in step 4); spot-check quality.

3. **Section-level citation edges.** Upgrade case_statute_links from statute-level
   to true section-level (tie each "section N / s.N" to the CORRECT act by
   proximity/context, deterministic). Output case_statute_section_links.csv
   {case_id, source_id, section, confidence, evidence_snippet}; keep low-confidence
   flagged, not dropped.

4. **Docling-first, local-OCR-fallback converter.** Build scripts/convert_to_text.py:
   PDF → docling (born-digital) → if empty/failure → LOCAL OCR (Tesseract/Surya);
   HTML → markdownify → markdown. Run it to clear the ~80 needs-ocr backlog
   (10 scanned statutes + ~70 scanned CoA judgments) into markdown under
   data/processed/docs/. Leave a clearly DISABLED Document-AI branch as a future
   option (do not call it). Update conversion-registry.csv statuses. Re-verify the
   store is complete.

5. **Flag unresolved citation passages.** Where section↔act pairing can't be
   resolved deterministically, write them to unresolved_citations.csv for a later
   bounded pass. Do NOT call an external LLM now.

6. **Lawyer-verification sample.** Produce verification-sample.csv — ~30
   case↔statute-section links with evidence snippet + citation — for a lawyer to
   confirm before links are treated as retrieval authority. Note links are
   "unverified" until signed off.

After each step: re-run scripts/audit_corpus.py; report deltas.

## DEFINITION OF DONE (keep working until ALL hold)

- audit_corpus.py: 0 hard inconsistencies; every conveyancing case loads/joins.
- data/processed/docs/ holds clean markdown for EVERY document; documents.csv
  provenance complete; every row → a real non-empty markdown file (needs-ocr
  backlog cleared via LOCAL OCR; anything still unreadable logged, not dropped).
- cases.jsonl conforms; rule tables + case_statute_section_links.csv +
  unresolved_citations.csv + verification-sample.csv all in data/processed/.
- The retrieval engine could run using ONLY data/processed/.
- **The notebook is updated to the new structure AND executed end-to-end with
  outputs saved, runs with no errors, and generated the full data/processed/ store.**
- update-context (save) run; logbook-entry generated; markdownlint clean; nothing committed.

If something genuinely cannot be finished locally (e.g. an OCR engine won't
install), STOP that item, log the blocker honestly in CONTEXT.md, and continue
the rest — do not fake results.
