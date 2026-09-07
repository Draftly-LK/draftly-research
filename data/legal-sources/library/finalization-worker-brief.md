# Worker brief: primary-statute finalization pass (September 2026)

Shared instructions for every write-capable worker on the Category 1 to 3
statute pass. The coordinator owns this file. Read it fully, then
`statue-automation.md` in this folder, before touching anything.

## Ground rules

- Everything you produce is `status=unverified`. Never write, say, or imply
  that anything is legally verified. The strongest label you may use is
  `pipeline-finalized, lawyer-unverified`, and only when every acceptance
  criterion below holds.
- Sources are what is on disk under `data/legal-sources/library/`. No web,
  no downloads, no external APIs, no text from memory. If a source is not
  held, say so and stop.
- Never paraphrase statutory text. Transcribe from a held source or leave
  the field empty with a note. Never modernise spelling or punctuation.
  Never invent a schedule, a section, or a heading.
- You may edit only `library/finalized/<your slug>/` and
  `library/finalized-sources/<your slug>/` for the statutes assigned to you.
  You may run parsers that write `data/processed/canonical-statutes/<your
  SRC>-*.json` and `data/processed/canonical-amendments/<your instrument>.json`,
  and OCR sidecars under `library/statutes/ocr/` or `library/amendments/ocr/`
  for your own instruments only.
- Do not edit: `source-registry.csv`, `statute-section-index.json`,
  anything under `scripts/` or `apps/`, `.gitattributes`,
  `canonical-overrides.json`, `amendment-overrides.json`, `RUBRIK.md`,
  `PRIMARY-STATUES.md`, `README.md`, tests, or another worker's folders.
  Return proposed override entries and registry corrections in your report;
  the coordinator merges them.
- Do not run `finalize_statute.py` without `--package-only` on a statute
  whose accepted tree in `finalized/` was finished by hand after its canonical
  parse. A normal run replaces the tree from `data/processed/canonical-*`.
  When in doubt, diff the two first.
- Do not commit. Do not stage. Do not touch git state.
- pdftotext: run it from PowerShell (poppler). Under Git Bash the name
  resolves to an Xpdf build that ignores `-enc UTF-8` and silently loses
  sections.

## Tools

```powershell
uv run python scripts/finalize_statute.py --help
uv run python scripts/finalize_statute.py --source-id SRCxxx --slug <slug> --package-only
uv run python scripts/verify_finalized_packages.py            # all packages
uv run python scripts/validate_finalized_trees.py --slug <slug>
uv run python scripts/check_parse_coverage.py --tree <tree.json> --pdf <pdf>   # or --text <ocr.txt>
uv run python scripts/parse_consolidated_pdf.py --source-id SRCxxx [--edition original]
uv run python scripts/build_canonical_statutes.py --source-id SRCxxx
uv run python scripts/parse_amendment_pdf.py --number N --year YYYY --pdf <pdf> --amends SRCxxx
uv run python scripts/parse_amendment_pdf.py --number N --year YYYY --ocr-text <txt> --amends SRCxxx
uv run python scripts/ocr_scanned_act.py --pdf <pdf> --out <sidecar.txt>
```

Manifest hashes: `scripts/package_integrity.py`. PDFs are hashed as bytes;
HTML, TXT, MD, CSV and JSON are hashed with line endings folded to LF and
carry `hash_mode: text-lf`. Always write manifests through
`finalize_statute.py` or through `package_integrity.file_entry()`, never by
hand-typing a hash.

## Source selection

1. Inspect every held copy before choosing. Record each one you looked at.
2. Prefer the latest consolidated edition actually held, and confirm its
   cutoff from the printed amendment-chain header or inline markers, quoting
   the line. Never infer the cutoff from a filename.
3. Use HTML for structure where it exists, and cross-check it against the
   best PDF. HTML is not automatically newer or more authoritative; several
   LankaLaw HTML editions stop years before the PDF of the same statute.
4. If the chosen baseline predates a held amending Act, apply only operations
   the amending Act's own operative text supports, record each one, and
   never apply an instrument the baseline already incorporates.
5. If two held copies disagree on anything material (number, year, chain,
   section count, wording), record the conflict in the manifest and set
   `needs_structural_review`. Do not choose silently.
6. Accepted trees under `finalized/` are the working baseline. Replace one
   only where a stronger held source demonstrates a specific correction, and
   say what changed.

## Manifest additions (write these into `manifest.json`)

`finalize_statute.py` preserves keys it does not generate, so add these once
the package is built:

```json
"pipeline_status": "pipeline-finalized, lawyer-unverified" | "needs_structural_review" | "blocked_insufficient_local_source",
"baseline": {
  "file": "<file in this package>",
  "edition": "consolidated" | "as_enacted" | "...",
  "publisher": "<as printed, or 'not stated'>",
  "consolidation_cutoff": "Act No. 12 of 2005" | "unknown",
  "cutoff_evidence": "<quoted header line or marker>"
},
"amendment_reconciliation": [
  {"instrument": "47-2011", "title": "<as printed on the title page>",
   "classification": "already_incorporated_in_baseline" | "applied_from_held_source" | "held_but_not_applied" | "known_but_not_held" | "ambiguous_or_unconfirmed",
   "reason": "...", "source_path": "data/legal-sources/library/amendments/..." | null}
],
"statute_note": "<see below>",
"lawyer_verification": "unverified"
```

Every instrument named in the statute's RUBRIK entry, in its header chain,
in the curriculum list, or held on disk under a matching number-year gets one
row. Open the title page of every held file before classifying it; a
number-year match on a filename is not evidence. Exclude files whose title
names another statute and record them as `ambiguous_or_unconfirmed` with the
title you read.

`statute_note` must cover, in this order: principal source selected; other
sources inspected; consolidation cutoff or `unknown`; review performed and
its depth; amendment coverage; OCR or structural weaknesses; missing
sources; unresolved questions; lawyer-verification status.

## OCR

Deterministic extraction first. OCR only for scans with no text layer, via
`ocr_scanned_act.py` to a sidecar. The scan travels in the package beside
the sidecar. Corrected wording goes in `text`, the machine reading stays in
`raw_text`, and each correction is listed under `corrections` with page,
location, original span, proposed reading, confidence, and why a human must
check it. Never fix an OCR error by annotating it while still using the wrong
value.

## Acceptance criteria for `pipeline-finalized, lawyer-unverified`

- Title, number and year reconciled with the registry; curriculum
  discrepancies recorded separately in the note.
- Tree passes `validate_finalized_trees.py --slug <slug>` with zero errors,
  and every remaining warning is documented in the tree or the note.
- Sections, inserted sections, repeals, headings, definitions, hierarchy and
  schedules match the selected source; duplicates, embedded and missing
  provisions are accounted for by name.
- A package exists with the principal source and every held source actually
  used; `verify_finalized_packages.py` reports no error for it.
- `baseline.consolidation_cutoff` is a confirmed value or `unknown`.
- Every known amendment has one reconciliation row; nothing applied twice.
- `statute_note` complete. `lawyer_verification: unverified`.

If any of these fail, set `pipeline_status` to `needs_structural_review`
(the tree exists but has a recorded defect) or
`blocked_insufficient_local_source` (no held source supports a tree), and
set the tree's `verification_status` to match. Do not force it.

## Handoff report (return all of this)

1. Statute and citation.
2. Files inspected, with paths.
3. Selected baseline and why.
4. Consolidation cutoff or `unknown`, with the quoted evidence.
5. Sections, definitions, schedules and hierarchy found.
6. Amendment reconciliation table.
7. Files created or modified.
8. Uncertain passages with source locations.
9. Commands and tests you ran, with results.
10. Proposed `canonical-overrides.json` / `amendment-overrides.json`
    entries and any registry corrections, as JSON, for the coordinator.
11. Recommended status.
12. The sentence: "This output remains lawyer-unverified."
