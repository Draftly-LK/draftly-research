# Benchmark cases — local only

This directory holds the documents the benchmark reads. **Nothing in it is
tracked.** The parent `.gitignore` ignores `ocr-benchmark/cases/` and allows only
this README back in.

The source of truth for the smoke bundle is the platform repo:

```text
draftly-platform/inputs/case-001/
```

`config.py` reads that path directly by default, so you do not need a copy here at
all. Point it somewhere else with:

```powershell
$env:DRAFTLY_OCR_BENCH_INPUTS = "D:\path\to\bundle"
```

If you do keep a local mirror in this folder, it stays here. These are real client
documents: real names, NICs, addresses, and consideration amounts. Do not commit
them, paste values into docs or tickets, or use them in demos or screenshots.
`config.py` refuses to start if the resolved input directory is not covered by a
gitignore rule.
