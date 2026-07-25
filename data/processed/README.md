# Draftly Processed Legal Corpus

This directory is the rebuildable, file-based input for Draftly's deterministic
retrieval engine. Original PDFs and harvested text remain under
`data/legal-sources/`; they remain authoritative.

## Contents

- `docs/` contains normalized UTF-8 Markdown for each available legal document,
  judgment, or historical report volume.
- `documents.csv` records provenance, conversion, status, checksum, and quality.
- `cases.jsonl` contains CommonLII and official-court records and points only to
  Markdown in this directory.
- `source-registry.csv`, `topics.csv`, `topic-sources.csv`, and `topics.json`
  are the deterministic routing tables.
- `slr-modern-*.csv` contains indexed-only references, not claimed full text.
- `case_statute_section_links.csv` contains deterministic, evidence-backed
  candidate edges; `unresolved_citations.csv` keeps passages the rules could not
  pair safely.
- `verification-sample.csv` is a 30-edge lawyer review sheet. Generated links
  remain unverified until a reviewer completes it.
- `documentai-usage.json` and `documentai-cache/` make the optional OCR fallback
  resumable and enforce its 2,000-page ceiling.

Generated links remain unverified until lawyer sign-off. Rebuild with
`uv run python scripts/build_processed_store.py`.
