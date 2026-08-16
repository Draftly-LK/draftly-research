# OCR and field-extraction benchmark

Draftly has to choose between Gemini, an open-source OCR engine, and image
preprocessing for reading scanned Sri Lankan conveyancing documents. Until now every
claim came from a different set of documents, so the options were never actually
compared. This directory puts them on the same pages, with the same field
definitions, output schema, and normalization rules.

It answers four separate questions, and deliberately does not average them together:

1. Which engine reads the text most accurately?
2. Which pipeline extracts critical legal fields most accurately?
3. Does preprocessing or cropping actually improve results?
4. Can the system show where every value came from?

## Quick start

```powershell
# Offline. No API key, no spend. Proves the harness measures correctly.
uv run python -m pytest ocr-benchmark/test_ocr_bench.py -q
uv run python ocr-benchmark/runner.py stub

# Plan and cost a real run without calling anything.
uv run python ocr-benchmark/runner.py A --dry-run

# The comparison.
uv run python ocr-benchmark/runner.py A B D
uv run python ocr-benchmark/score.py

# One matter at a time, which is how you should start.
uv run python ocr-benchmark/runner.py A --case platform
```

Then open `ocr_benchmark.ipynb`. It only reads results, so it is free to re-run.

## The corpus

`cases/` holds one directory per matter — 4 matters, 38 documents, 282 pages, in
PDFs and photographed JPEG pages. Only `platform-case-001` is labelled (37 fields
across 4 documents); the rest still contribute transcripts, cross-run agreement,
provenance and cost without contributing a field score.

Documents are identified as `<matter>/<filename>`, because every bundle contains a
`source-001-...`. Splits are taken by matter and never by page: pages from one
transaction repeat the same parcels, parties and extents, so splitting by page
contaminates the test set. See `cases/README.md`.

## The runs

| Run | What it tests |
| --- | --- |
| A | Gemini on the original page. Closest to production, at production's 200 DPI. |
| B | Gemini on a preprocessed page. Isolates the value of preprocessing. |
| C | Box engine reading the page end to end. Open-source baseline. |
| D | Gemini page, then each critical field re-read from its own crop. |
| E | Detector supplies regions, Gemini reads them. Local spatial grounding. |
| F | Gemini and the box engine both read; disagreements are adjudicated. |
| stub | Deterministic offline reader over a synthetic fixture. No spend. |

Ablations are overrides on a run, not separate pipelines:

```powershell
uv run python ocr-benchmark/runner.py A --ablation dpi       # 150 / 200 / 300 / 400
uv run python ocr-benchmark/runner.py B --ablation variant   # original / rotated / deskew / full
```

## Why the stub run matters

`render.synthetic_page()` draws known text at known boxes and returns its own ground
truth. `engines.stub_read_page` reads it back perfectly, so the clean stub run must
score 100% with 0.00 CER. If it does not, the harness is wrong and no model result
from it should be believed. `--stub-noise 0.25` corrupts characters at a known rate
to prove the metrics actually move.

This is also why a reviewer with no API key can run everything end to end.

## Scoring rules

- **Critical identifiers are exact match only. Never fuzzy.** `00030085091` against
  `00030085090` is a failure whatever the string similarity says, because the legal
  result is completely wrong. `schemas/critical-fields.json` declares which of the
  38 registry keys are critical — the platform's `FieldDef` carries no such flag, so
  it is a research-side overlay.
- **Two normalizers are reported.** `platform` is byte-identical to the platform's
  `eval_extraction._norm`, so the headline number is directly comparable to
  production's own golden-set figure; a test pins the parity and fails on drift.
  `strict` keeps case and punctuation, because stripping commas is right for money
  and wrong for a cadastral number.
- **Values stay strings end to end.** A prediction that arrives as a JSON number is
  recorded as an error, not a value: `"0021"` decoding to `21` would pass a fuzzy
  check and be legally wrong.
- **Missing is not wrong.** `N/A`, `unknown`, and `undetected` collapse to a miss.
- **No expectation means `no_label`**, never a scored empty value.
- **Ambiguous labels are excluded** from accuracy denominators and reported
  separately. If the document itself cannot be read, label it `ambiguous` rather
  than inventing ground truth.

One thing worth knowing: the platform normalizer does **not** strip currency
prefixes, so an expectation of `Rs.4,819,500/=` does not match a prediction of
`4819500`. That is production's real behaviour, kept deliberately rather than
quietly improved, because diverging would make the numbers incomparable. A test
documents it.

## What is measurable without ground truth

There are no OCR region transcripts or annotated boxes yet, and building the
annotation tooling was out of scope. These still work today:

- critical-field accuracy against the 37 labelled fields in the bundle's
  `expected-fields.json`
- **invented-value rate** — a returned value that appears nowhere in the page text.
  This is the metric that protects lawyers and it needs no labels at all.
- **cross-run agreement** — the fastest way to find the pages worth annotating first,
  plus a check on whether agreement predicts correctness
- **provenance plausibility** — does the returned box actually contain the value
- cost, latency, and routing accuracy

CER and WER by language and text type report `no-ground-truth` until transcripts
exist. Three hand-typed pages (one Sinhala, one English, one Sinhala/Tamil) dropped
into `labels/ocr-region/` would make that chart real; the schema is already the
permanent one.

## Privacy

The documents are real client files: real names, NICs, addresses, and consideration
amounts.

- `cases/`, `renders/`, `runs/`, and `labels/` are gitignored. `reports/` is tracked
  and holds aggregates only.
- `normalize.assert_no_raw_values` raises if a value-bearing column is written to a
  tracked path, so the rule is enforced in code rather than by memory.
- `config.assert_inputs_private` refuses to start if the resolved input directory sits
  inside the repo without a gitignore rule.
- `config.INPUTS` defaults to `cases/`. Point it at a bundle elsewhere with
  `DRAFTLY_OCR_BENCH_INPUTS` if you would rather not keep a working copy.
- **Clear notebook outputs before committing.** The provenance preview renders client
  pages.

## Spend controls

`DRAFTLY_OCR_MAX_CALLS` (default 400) and `DRAFTLY_OCR_MAX_USD` (default 5.00) are
hard stops, not warnings. Usage accumulates in `runs/gemini-usage.json`, keyed per
page, so re-running a partially completed benchmark never pays twice. `--dry-run`
prints the plan and page count without calling anything.

## Known blockers

- **Gemini credentials.** The `GEMINI_API_KEY` in `.env` starts with `AQ.` and is
  rejected with `401 UNAUTHENTICATED`; AI Studio keys start with `AIza`. The Vertex
  route also fails, because `aiplatform.googleapis.com` is not enabled on project
  `draftly-502319`. Runs A, B, D, E and F need one of those two fixed. The root
  README already carries this as an open item.
- **Box engine licence.** Runs C, E and F need a box-producing engine. Surya is
  GPL-3.0, and the platform explicitly rejected PyMuPDF for being AGPL
  (`rasterizer_pypdfium.py`), so this needs a ruling before it influences a product
  decision. `rapidocr` (Apache-2.0, ONNX, no torch) is already installed and is the
  default detector; its Latin-only recognition is a real limitation for Sinhala, but
  runs E and F only need its boxes since Gemini does the reading. Install Surya with
  `uv sync --extra surya`; there is no GPU here, so expect it to be slow.

## Layout

```text
config.py       paths, models, spend caps, the privacy assertion
contract.py     the adapter output every runner returns, and the bbox convention
render.py       pypdfium2 rendering, preprocessing variants, crops, synthetic fixture
normalize.py    platform-parity normalization, CER/WER, grounding, the privacy guard
engines.py      stub / Gemini / detector engines behind one interface
runner.py       executes runs. spends money.
score.py        scores runs. spends nothing.
viz.py          the charts
schemas/        field vocabulary, criticality overlay, annotation schemas
```

Each run writes `runs/<variantId>/` containing `config.json` (the full
reproducibility manifest: model, prompt hashes, preprocessing hash, commit, dataset
fingerprint), `raw-responses.jsonl` (written before normalization),
`results.jsonl`, `metrics.json`, `predictions.csv`, and `mismatches.csv`.

## A caution about the current size

The corpus is 282 pages across 4 matters, which clears the 100–200 page target. The
*labelled* portion does not: 37 fields on 4 documents in a single matter. Field
accuracy therefore still rests on one matter, and the Wilson intervals in the
notebook are wide on purpose.

Labelling a second and third matter is what turns this from a working harness into
a decision, because it is the only way to see whether a configuration generalises
across matters rather than fitting the quirks of one bundle.

When you inspect errors, fix the pipeline. Never edit the expectations to match the
model.
