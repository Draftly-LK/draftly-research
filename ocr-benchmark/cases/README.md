# Benchmark cases — local only

One directory per matter. Everything in here except this README is ignored by git.

```text
cases/
├── platform-case-001/                        7 docs,  26 pages  — labelled
├── research-case-001-rajagiriya-dalgahawatta/ 24 docs, 62 pages  — unlabelled
├── research-case-002-maharagama-assessment/   6 docs, 26 pages  — unlabelled
└── research-case-003-sc-fr-319-2024/          1 doc, 168 pages  — unlabelled
```

38 documents, 282 pages. Both PDFs and photographed pages (JPEG) are first-class
inputs; a photo counts as one page.

## Why one directory per matter

The matter is the unit everything groups by. Splits must be taken by matter and
never by page, because pages from the same transaction repeat the same parcel
numbers, parties and extents — if they straddle a train/test boundary the test set
is contaminated and the scores are meaningless.

Document filenames repeat across matters (every bundle has a `source-001-...`), so
documents are identified as `<matter>/<filename>` throughout.

## Labels

A matter is scored only if it contains `expected-fields.json`, in the shape:

```json
{ "<filename>.pdf": { "kind": "<registry kind>", "fields": { "<factKey>": "<value>" } } }
```

Right now only `platform-case-001` has one, covering 37 fields across 4 documents.
The other three matters still run: they contribute transcripts, cross-run
agreement, provenance and cost, they just do not contribute a field score. That is
deliberate — unlabelled documents are useful long before anyone has annotated them.

## Privacy

These are real client documents: real names, NICs, addresses and consideration
amounts. Do not commit them, paste values into docs or tickets, or use them in
demos or screenshots. `config.assert_inputs_private()` refuses to start if the
resolved input directory is not covered by a gitignore rule, and
`normalize.assert_no_raw_values()` refuses to write any transcribed value into a
shareable path.

The originals live in `draftly-platform/inputs/` and `data/raw/` respectively; these
are working copies. To read a bundle in place instead, set:

```powershell
$env:DRAFTLY_OCR_BENCH_INPUTS = "D:\path\to\bundle"
```

`target_outputs/` from the research matters is deliberately not copied here — those
are lawyer-prepared deliverables, not benchmark inputs.
