# Provisional Topic Mapping for Additional Statutes

## Status and evidence boundary

The mappings below are proposed retrieval classifications for `SRC091` through
`SRC112`. They are not verified statements of each statute's legal effect.

All 22 sources are currently marked `index-only` in
`manifests/source-registry.csv`. The corpus has section numbers and marginal
headings in `derived/statute-section-index.json`, but it does not hold verified
full statutory text for these sources. Keep the mappings provisional until the
authoritative texts and source metadata have been checked.

## Recommended mapping

| Source | Proposed topics |
| --- | --- |
| SRC091 — Insolvency Ordinance | 05 Formation of Deeds; 09 Examination of Title |
| SRC092 — Housing and Town Improvement Ordinance | 16 Local Authority/UDA Regulations |
| SRC093 — Agrarian Services Act | 09 Examination of Title; 18 Other Laws |
| SRC094 — Estate Duty Ordinance | 14 Last Wills; 18 Other Laws |
| SRC095 — Primary Courts Procedure Act | 18 Other Laws |
| SRC096 — Judicature Act | 18 Other Laws |
| SRC097 — Debt Conciliation Ordinance | 09 Examination of Title; 17 Drafting of Deeds |
| SRC098 — Kandyan Marriages Ordinance | 10 Special Laws |
| SRC099 — Ceiling on Housing Property Law | 05 Formation of Deeds; 09 Examination of Title; 16 Local Authority/UDA Regulations |
| SRC100 — Village Communities Ordinance | 16 Local Authority/UDA Regulations |
| SRC101 — Administration of Justice Law | 18 Other Laws |
| SRC102 — Agricultural Lands Law | 09 Examination of Title; 18 Other Laws |
| SRC103 — Married Women's Property Ordinance | 01 Introduction to Conveyancing; 05 Formation of Deeds; 10 Special Laws |
| SRC104 — Rent Restriction Act | 17 Drafting of Deeds; 18 Other Laws |
| SRC105 — Service Tenures Ordinance | 11 Temple/Devala/Nindagam Properties |
| SRC106 — Interpretation Ordinance | 18 Other Laws |
| SRC107 — Business Names Registration Ordinance | 05 Formation of Deeds; 18 Other Laws |
| SRC108 — Land Registration Ordinance | 11 Temple/Devala/Nindagam Properties |
| SRC109 — Money Lending Ordinance | 17 Drafting of Deeds; 18 Other Laws |
| SRC110 — Paddy Lands Act | 09 Examination of Title; 17 Drafting of Deeds |
| SRC111 — Abolition of Fideicommissa and Entails Act | 05 Formation of Deeds; 09 Examination of Title; 14 Last Wills; 15 Trust Deeds; 17 Drafting of Deeds |
| SRC112 — Marriage Registration Ordinance | 05 Formation of Deeds; 18 Other Laws |

## Review notes

- `SRC108` needs a title check before assignment. Its indexed section 1 heading
  identifies the source as the Temple Lands Registration Ordinance, while the
  registry currently calls it the Land Registration Ordinance.
- Direct matches based on explicit subject headings are stronger than secondary
  workflow mappings such as title-examination or deed-formation relevance.
- Do not change these sources from `index-only` merely because a topic has been
  assigned.
- After approval, update the `topics` column in `source-registry.csv`, run
  `scripts/reconcile_topics.py`, and then run `scripts/audit_corpus.py`.
