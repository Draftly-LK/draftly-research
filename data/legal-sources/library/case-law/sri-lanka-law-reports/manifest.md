# Sri Lanka Law Reports Index

## Public Index

- [Sri Lanka Law Reports on LawLanka](https://lankalaw.net/sri-lanka-law-reports/)
- [Sri Lanka Law Reports year/volume index on LawLanka](https://www.lawlanka.com/lal_v2/viewSlrYearWise?menuValue=lawReport)
- [Sri Lanka Law Reports preview index on Iuris Scientia](https://iuris.lk/legal-library/slr)

## Modern SLR Discovery Snapshot

`data/legal-sources/manifests/slr-modern-index.csv` records the public SLR
year/volume tables found during the 2012-2026 scan. The companion
`data/legal-sources/manifests/slr-modern-cases.csv` stores case-title references
only, not full report text.

Local copies of the public LawLanka volume index pages are stored under:

```text
data/legal-sources/library/case-law/sri-lanka-law-reports/lawlanka-index/
```

This folder contains:

- `downloaded-indexes.json` - local download manifest for the public index pages.
- `slr-modern-index.csv` - local copy of the volume-level index.
- `slr-modern-cases.csv` - local copy of the case-title reference index.
- `<year>/volume-<n>.html` - downloaded public LawLanka SLR volume table pages.

| Period | Public index result | Notes |
| --- | --- | --- |
| 2012 | Volumes 1-2 found | Public LawLanka volume tables indexed. |
| 2013 | Volumes 1-2 found | Public LawLanka volume tables indexed. |
| 2014 | Volume 1 found | Public LawLanka volume table indexed. |
| 2015 | Volume 1 found | Public LawLanka volume table indexed. |
| 2016 | Volume 1 found | Public LawLanka volume table indexed. |
| 2017 | Volume 1 found | Public LawLanka volume table indexed. |
| 2018 | Not found on LawLanka scan | AI Pazz search results suggest 2018 volumes exist, but full/public index access was not verified. |
| 2019 | Volumes 1-3 found | Public LawLanka volume tables indexed. |
| 2020 | Volumes 1-3 found | Public LawLanka volume tables indexed. |
| 2021 | Volumes 1-3 found | Public LawLanka volume tables indexed. |
| 2022-2026 | SLR volume tables not found on LawLanka scan | Later court judgments and Supreme Court Law Reports exist separately, but should not be labelled SLR unless the SLR report citation is verified. |

## Use in Draftly

Use the index to locate decisions relevant to the legal issue in a matter, such
as title, prescription, deed validity, registration, notarial duties, or
succession. Save each selected judgment separately under the case folder with
its report citation, court, year, source URL, and a short relevance note.

## Scope Note

Sri Lanka Law Reports are a report series, not one statute or one static PDF.
This manifest records the public discovery source while keeping future case
selection specific to the matter being reviewed.

Modern SLR headnotes, digests, pagination, and report formatting may be protected
as report-series publication material. Draftly should store public citation
metadata and source links, but should not republish full modern SLR text unless
an official licence or public-domain source is confirmed.

The public LawLanka volume pages expose case-title tables. Individual case-detail
links redirect to login for unauthenticated access, so full report text was not
downloaded through this route.
