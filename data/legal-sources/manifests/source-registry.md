# Legal Source Registry

This registry tracks the legal sources needed for Draftly's conveyancing MVP.
The CSV file in this folder is the operational tracker:

```text
data/legal-sources/manifests/source-registry.csv
```

## Storage Model

Actual source files are stored once under `data/legal-sources/library/`.
Topic folders under `data/legal-sources/topics/` link back to those shared files.
Extracted Markdown working copies are stored separately under
`data/legal-sources/library-markdown/`.

## Status Values

- `downloaded`: a usable local file has been collected.
- `indexed-html`: a reliable public HTML source has been recorded locally, but
  no clean standalone public PDF has been found yet.
- `indexed-reference`: a local manifest records public source pages or indexes,
  but the source is not a single downloadable PDF.
- `bibliographic-only`: a copyrighted textbook or reference is recorded by
  citation only; no source text is stored.
- `needs-official-source`: a source is identified, but an official PDF still needs to be found.
- `needs-manual-review`: the source requirement is unclear or may be outside Draftly's scope.
- `gated-or-not-public`: the source appears unavailable without access restrictions.
- `possible-curriculum-typo`: the curriculum entry appears inconsistent and must be checked.

## Current Pass

The registry currently records 90 source entries:

- 83 downloaded/local entries
- 3 indexed-reference entries
- 1 indexed HTML-only entry
- 1 bibliographic-only textbook entry
- 1 source still needing an official public source
- 1 curriculum term needing manual review

Those rows resolve to 66 unique registry PDF paths, and the full library
currently contains 76 readable PDF files. Multiple source rows can correctly
point to the same consolidated statute, legislative volume, or local manifest.
Official or institution PDFs have been collected from RGD, Parliament, IRD,
documents.gov.lk, CBSL, the Department of the Registrar of Companies, the
Western Province Department of Revenue, and the Ministry of Plantation
Industries where available.

One registry entry is intentionally awaiting manual review: the unresolved
`CRS` curriculum reference. The local-authority collection contains official
national model by-laws and the government gazette archive; each case must still
record the property authority and verify its applicable adoption or
modification notice.

## Source Priority

1. Department of Government Printing / Parliament official PDFs.
2. Official institution PDFs, such as Registrar General's Department.
3. Laws of Sri Lanka / LawNet / LawLanka consolidated text.
4. Manual review backlog if no reliable public source is found.
