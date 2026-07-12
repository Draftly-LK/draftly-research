# Legal Source Registry

This registry tracks the legal sources needed for Draftly's conveyancing MVP.
The CSV file in this folder is the operational tracker:

```text
data/legal-sources/manifests/source-registry.csv
```

## Storage Model

Actual source files are stored once under `data/legal-sources/library/`.
Topic folders under `data/legal-sources/topics/` link back to those shared files.

## Status Values

- `downloaded`: a usable local file has been collected.
- `needs-official-source`: a source is identified, but an official PDF still needs to be found.
- `needs-manual-review`: the source requirement is unclear or may be outside Draftly's scope.
- `gated-or-not-public`: the source appears unavailable without access restrictions.
- `possible-curriculum-typo`: the curriculum entry appears inconsistent and must be checked.

## Current Pass

The library currently contains 40 registry-tracked local sources. Official PDFs
have been downloaded from RGD, Parliament, IRD, documents.gov.lk, and the
Department of the Registrar of Companies where available.

The remaining 26 source rows require an official or directly downloadable public
copy, and one row remains under manual review. Several older consolidated statutes
are publicly discoverable, but their archival download endpoint currently returns
server-side source rather than a PDF; those files are deliberately not stored until
a valid copy is available.

## Source Priority

1. Department of Government Printing / Parliament official PDFs.
2. Official institution PDFs, such as Registrar General's Department.
3. Laws of Sri Lanka / LawNet / LawLanka consolidated text.
4. Manual review backlog if no reliable public source is found.
