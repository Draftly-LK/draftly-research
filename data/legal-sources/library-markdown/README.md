# Legal Source Markdown Library

## Purpose

This folder stores Markdown extracted from the original legal-source files in
`data/legal-sources/library/`.

The original PDFs, gazettes, forms, and source manifests stay in `library/`.
The extracted Markdown lives here so Draftly can build search, review, and
retrieval workflows without modifying the source files.

## Folder Layout

```text
data/legal-sources/library-markdown/
  statutes/
  amendments/
  gazettes/
  case-law/
  institution-guides/
  textbooks/
  crs/
  _review/
```

## Conversion Stack

Use this order:

1. Docling as the default converter.
2. Marker as the fallback or comparison converter.
3. Unstructured for chunking cleaned Markdown into retrieval-ready sections.

## Tracking

Every conversion should be recorded in:

```text
data/legal-sources/manifests/conversion-registry.csv
```

Each Markdown file should keep the source relationship clear through the
registry row, not by duplicating provenance in every extracted file.

## Quality Rule

Do not treat extracted Markdown as legal authority. The PDF or original source
manifest remains the authoritative source. Markdown is a working copy for
search, extraction, review, and downstream modelling.
