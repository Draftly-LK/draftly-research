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
- `indexed-html`: a reliable public HTML source has been recorded locally, but
  no clean standalone public PDF has been found yet.
- `needs-official-source`: a source is identified, but an official PDF still needs to be found.
- `needs-manual-review`: the source requirement is unclear or may be outside Draftly's scope.
- `gated-or-not-public`: the source appears unavailable without access restrictions.
- `possible-curriculum-typo`: the curriculum entry appears inconsistent and must be checked.

## Current Pass

The registry currently records 80 source entries: 79 downloaded/indexed local
entries and one public HTML-only entry. The downloaded rows resolve to 62 unique
registry PDF paths, and the full library currently contains 70 readable PDF
files. Multiple source rows can correctly point to the same consolidated statute
or legislative volume. Official or institution PDFs have been collected from
RGD, Parliament, IRD, documents.gov.lk, CBSL, the Department of the Registrar of
Companies, the Western Province Department of Revenue, and the Ministry of
Plantation Industries where available.

No registry entries are awaiting manual review. The local-authority collection
contains official national model by-laws and the government gazette archive;
each case must still record the property authority and verify its applicable
adoption or modification notice.

## Source Priority

1. Department of Government Printing / Parliament official PDFs.
2. Official institution PDFs, such as Registrar General's Department.
3. Laws of Sri Lanka / LawNet / LawLanka consolidated text.
4. Manual review backlog if no reliable public source is found.
