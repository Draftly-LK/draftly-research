# Case-Law Corpus — Acquisition & Access Notes

How Draftly's Sri Lankan conveyancing case law is collected, what is actually
obtainable from the internet, and what is not.

## What we have

### 1. Public-domain volumes from the Internet Archive (bulk full text)

`internet-archive/` (gitignored — rebuildable) holds **33 Ceylon law-report
volumes** downloaded as full text from the Internet Archive, via
`scripts/harvest_ia_caselaw.py`. These are historical, **public-domain**
(`NOT_IN_COPYRIGHT`) reports — including **New Law Reports vol. 1 (1896)**, the
Ceylon Law Reports, Court of Appeal Cases of Ceylon, and Supreme Court reports
spanning **1839–1913**. ~32 MB of OCR'd text, all conveyancing-rich.

Tracked manifests (these ARE in git):

- `manifests/case-law-ia-manifest.csv` — every harvested volume: identifier,
  title, year, rights, local text path, char count, IA detail URL.
- `manifests/case-law-ia-conveyancing.csv` — each volume scored for conveyancing
  relevance (per-topic keyword hit counts), ranked. 26,843 total conveyancing
  keyword hits across the set; every volume is relevant (Ceylon case law is
  heavily land/property).

Rebuild: `python scripts/harvest_ia_caselaw.py` then
`python scripts/filter_conveyancing_caselaw.py`.

### 2. CommonLII harvest — Supreme Court + Court of Appeal (NLR + SLR era)

`commonlii/<db>/<year>/<n>.txt` (gitignored — rebuildable) holds the full text
of conveyancing-matched judgments harvested from CommonLII via
`scripts/harvest_commonlii_caselaw.py`. CommonLII hosts **LKSC** (Supreme Court,
1878–2012) and **LKCA** (Court of Appeal, 1809–2010) — i.e. the cases reported in
the **New Law Reports (pre-1978)** and **Sri Lanka Law Reports (1978+)**.

Access note: CommonLII sits behind Cloudflare **User-Agent gating** (not a JS
challenge) — the default curl/urllib UA gets 403, but a normal browser UA passes.
The harvester sends a browser UA, single-threaded and rate-limited (0.25 s), and
is resumable (skips already-saved cases). For internal research use only.

Tracked manifests:

- `manifests/case-law-commonlii-index.csv` — EVERY case seen (complete citation
  index: db, year, case_no, citation, title, url).
- `manifests/case-law-commonlii-conveyancing.csv` — the conveyancing-matched
  subset (≥3 strong land-law keyword hits) with local text paths.

### 3. Citation index (LawLanka digest pilot)

`registration-of-documents-digest/` + `manifests/case-law-citations.csv` — a
Codex pilot: 76 conveyancing citations (61 NLR + 15 SLR) for the Registration of
Documents topic, extracted from a public LawLanka related-cases digest. **These
are citations only, all `unverified`** — no judgment text was obtained, and the
statute/section links are tentative until checked against report text.

## What is NOT obtainable from the internet (and why)

The comprehensive modern digital sources are not usable for automated
collection — this is a hard limit, not a gap in effort:

- **CommonLII / WorldLII** (`commonlii.org/lk`) — RESOLVED: the Cloudflare block
  turned out to be User-Agent gating, not a JS challenge, so a browser-UA request
  passes. Now harvested (see section 2). Bulk/full-text obtained for internal
  research use.
- **LawNet** (`lawnet.gov.lk`) — official Ministry of Justice site — is
  **effectively dead over HTTP**: the root returns the 14-byte string
  `root directory` and all report/PDF paths 404. Its TLS cert is also broken.
- **LawLanka** — commercial/subscription; only citation listings were reachable,
  and its terms are restrictive.
- **Modern SLR (1978–present)** — in copyright (Council of Law Reporting); not
  freely downloadable.

**Net:** the internet-obtainable slice via permitted automated means is the
Internet Archive's public-domain historical volumes (done above) plus the
citation index. Getting the full modern NLR/SLR text requires the **official
data route** — a university/research request to the Ministry of Justice/LawNet,
or to AustLII (who operate CommonLII and license data feeds) — or manual
in-browser download. Those are human/official actions, not automatable here.

## Copyright & use

Raw judgment text is public record; the IA volumes are `NOT_IN_COPYRIGHT`.
SLR **headnotes/digests** are Council of Law Reporting copyright — fine for
internal retrieval/eval, do not republish as a public dataset.

## Next steps

- Segment the IA volumes into per-case records (citation, parties, headnote,
  statutes-cited) and link to statute sections + topics (the graph/GT-Link
  layer). Segmentation of noisy OCR is a later NLP task; the volumes + relevance
  index make it tractable.
- Pursue the official data request for modern NLR/SLR in parallel.
