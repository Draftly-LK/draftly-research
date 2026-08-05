# Statute corpus and section-index plan

Status: proposed, 2026-08-05. Owner of the decision: Himath. Execution split in
the phase table at the end.

## The decision

Take the **structure** of the statute book from LawLanka. Leave the **text**.

Section numbers, marginal notes, and the inline `[n, Act of Year]` amendment
markers are facts about a statute. The consolidated body prose is LawLanka's
editorial product, and we already hold the text from official PDFs. So the
scrape targets the index page and stops there.

This is already the rule in `data/legal-sources/conveyancing-source-checklist.md`,
which sets source priority as:

1. Official PDF from the Department of Government Printing or Parliament.
2. Official institution PDF, such as the Registrar General's Department.
3. Consolidated text from Laws of Sri Lanka, LawNet, or LawLanka.
4. Secondary notes for orientation only, never as the authority.

LawLanka sits at priority 3. Nothing below changes that.

## Why we need it

Our section indexes are incomplete, and the two we have disagree with each
other. Measured on the Civil Procedure Code, the most-cited statute in the case
corpus:

| Source | CPC sections found | Headings |
| --- | --- | --- |
| Live BM25 retrieval index | 103 | truncated |
| `derived/statute-section-index.json` | 514 | fragments, e.g. `is made special` |
| PDF coordinate-block extractor (prototype) | 592 | 247 partial |
| LawLanka `consShortTitleView` index page | **797** (734 distinct, up to s.840) | **797 complete** |

One request returned a complete list with full marginal notes:

```text
s.4    Where no provision is made special directions to be given by Court of Appeal.
s.8    Procedure of action to be ordinarily regular. [2, 53 of 1980].
s.9    Institution of actions: in what court. [3, 43 of 2024].
s.247  Action by party claiming right.
s.653  Of sequestration before judgment. [14, 43 of 2024].
s.756  Security to be by bond and with surety. [50, 79 of 1980] [50, 79 of 1988] [12, 14 of 1997]
```

The markers give `actions.csv` for free. `s.756` alone carries a three-step
version chain. The document header lists roughly 40 amending instruments back to
Ordinance No. 2 of 1889, against 26 recoverable from our PDF and zero in
`source-registry.csv`.

Downstream effect: 810 of our 1,957 pinpoint case-to-section links currently
fail because the section is absent from our index, not because the link is
wrong. Only 11 links are genuinely out of range.

## Scope

### What is already covered

`conveyancing-source-checklist.md` lists 104 source rows. 80 match the
registry. Of the 24 that do not, most are deed *types* from the drafting section
(Deed of Transfer, Mortgage Bond, Last Will and Testament) rather than statutes.
The genuine gaps are:

- Tea, Rubber and Coconut Estates (Control of Fragmentation) Act No. 2 of 1958
- Provincial financial statutes
- Stamp-duty gazettes
- Local authority by-laws and gazettes

So the **curriculum scope is close to complete**. The gap is the **case-law
scope**.

### What is missing

Extracting every multi-word statute name from the 3,521 recovered headnotes
gives 453 distinct names. Only 22 are in the catalogue. 102 are cited three or
more times and not held. The head of that list:

| Citations | Name as written in the headnotes |
| --- | --- |
| 136 | partition ordinance |
| 133 | partition act |
| 83 | rent restriction act |
| 69 | courts ordinance |
| 56 | stamp ordinance |
| 44 | inheritance ordinance |
| 41 | income tax ordinance |
| 39 | mortgage ordinance |
| 28 | estate duty ordinance |
| 26 | debt conciliation ordinance |
| 23 | interpretation ordinance |
| 22 | money lending ordinance |
| 21 | land redemption ordinance |
| 18 | penal code |
| 18 | judicature act |

Three groups inside that list are **not** downloads:

- **Name fragments of statutes we already hold.** `frauds ordinance` (77) is the
  Prevention of Frauds Ordinance; `documents ordinance` (71) is the Registration
  of Documents Ordinance. These go to `aliases.csv`. Roughly 150 citations
  resolved by a CSV with no acquisition at all.
- **Regex artifacts** from truncated names: `amendment ordinance` (42),
  `privy council) ordinance` (26), `special provisions) act` (16).
- **Legal systems, not statutes.** `kandyan law` (108), `roman-dutch law` (84),
  `buddhist ecclesiastical law` (22), `english law` (25), `muslim law` (16).
  Around 255 citations that no download will ever satisfy, because their content
  lives in case law and textbooks. They need a distinct node type in the graph.
  Treating them as statutes will produce wrong links. This is a design decision
  to take deliberately, not to discover later.

### The relevance gate

Decide per candidate, not by citation count. For each of the 102:

```text
is it a statute at all?              -> no  : legal system, separate node type
is it a fragment of a held statute?  -> yes : aliases.csv, do not acquire
does it touch land, title, deeds,
succession, registration, tax on a
conveyance, or civil procedure?      -> yes : IN SCOPE
otherwise                            -> OUT, record the reason
```

Use the signals that already exist: `manifests/topics.csv` (20 topics, each with
a keyword list) and the conveyancing gate lexicon in
`notebooks/05_courts_judgment_extraction.ipynb`. Write every in/out decision and
its reason to a CSV so the scope is auditable rather than remembered.

Expected result: 40 to 60 statutes in scope. That is Phase 1.

### The one-hop rule

The Civil Procedure Code references the Judicature Act, the Interpretation
Ordinance, the Stamp Ordinance, the Penal Code and the Evidence Ordinance. Each
of those references a dozen more. Followed transitively, cross-references
converge on most of the 1,774 consolidated enactments LawLanka lists — which is
"all statutes" arriving through the back door.

So: expand one hop from the in-scope set, apply the same relevance gate, then
stop and re-measure before deciding on a second hop. There is also a technical
reason to stay bounded — `retrieval-engine-methodology.md` attributes
double-digit retrieval gains to curated topic partitions, and an unbounded
corpus destroys the scoping property those gains depend on.

## Request budget

| Step | Requests | Yield |
| --- | --- | --- |
| A to Z consolidation index | 26 (already fetched, cache it) | statute name to act-code map, 1,774 entries |
| `consShortTitleView` per in-scope statute | approx. 60 | complete section list, full headings, amendment markers |
| `actsYearWise` sweep | approx. 10 | amendment Acts by year |
| `revisedVersion1981` and `revisedVersion1956` for the top 8 statutes | approx. 16 | temporal anchors |

**Roughly 110 requests for all of Phase 1.**

Do not fetch `consSelectedSection` per section. It returns the entire 712 KB Act
on every call — 734 requests to get what one index page already returned.

## Rules for the run

### Politeness

- One session, one request per second, sequential.
- Cache to disk keyed by URL. Never re-fetch a cached page. The run must be
  resumable and idempotent.
- The account is a single seat with concurrent-session limiting: the site shows a
  "close last session and access from this system?" confirm. Do not run the
  scraper while a person is logged in.

### Credentials

- Rotate the password first. The current one has been pasted into a chat log.
- Read from `.env` as `LAWLANKA_USER` and `LAWLANKA_PASS`. Never in a script,
  never in a notebook cell, never committed.
- Login is a plain form POST to `/lal_v3/login` (not `/lal_v3/userLogin` — the
  page's `checkLogin()` rewrites the action). Fields:
  `userMaster.emailAddress`, `userMaster.password`, `logInDirect`,
  `userSessionFirstName`. No browser or JS engine needed.

### Storage and provenance

- Output to `evaluation/runs/lawlanka-section-index/`, which is gitignored.
- Every record carries `source_url`, `fetched_at`, `sha256`, and
  `retrieved_from: "lawlanka"`.
- Field discipline: LawLanka may populate `section_present` and `heading`. The
  official PDF populates `text`. Scraped text must never overwrite
  gazette-derived text.

### Validation

- The PDF coordinate-block extractor independently recovers 592 of the CPC's 734
  sections. Run both and report agreement per statute.
- Where the two disagree on whether a section exists, **the official PDF wins**.
- Where LawLanka has a section the PDF missed, record
  `heading_source: lawlanka, text_source: none` — a known hole, not a silent
  fill.
- Acceptance gate: the corpus must stay reproducible from official sources
  alone. LawLanka improves heading coverage; it must never become a dependency
  the engine cannot run without.

## Outputs

| File | Shape |
| --- | --- |
| `sections.jsonl` | `source_id, section, heading, heading_source, text_source, present_in[]` |
| `actions.csv` | `target_section, amending_act, amending_section, operation, source_url` |
| `aliases.csv` | `alias, source_id, alias_type` where type is short-title, abbreviation, historic, or fragment |
| `scope-decisions.csv` | `candidate_name, citations, decision, reason` |
| `fetch-log.csv` | `url, status, bytes, fetched_at` |

`operation` is a closed set: `inserted`, `amended`, `replaced`, `repealed`,
`unknown`.

## Out of scope

**Do not scrape the law reports.** `viewNlrVolumeWise`, `viewSlrYearWise`,
`viewSclrYearWise`, `viewScoaYearWise`, and the Case Digest are excluded. We
already hold 9,177 judgments from CommonLII and the official court sites.
Editorial headnotes and digests carry the highest IP exposure on the site and we
would gain nothing.

## Before running

- Permission in writing, attached to the corpus IP review file. Verbal or chat
  permission will not survive a supervisor asking, and the IP review is a
  release gate.
- Add a dated line to `conveyancing-source-checklist.md` recording that LawLanka
  structural data was used under that permission, consistent with the
  checklist's own priority-3 rule.

## Phases

| Phase | Work | Owner |
| --- | --- | --- |
| 0 | Rotate password, permission in writing, run the relevance gate over the 102 candidates | Himath |
| 1 | The approximately 110-request sweep, producing `sections.jsonl`, `actions.csv`, `aliases.csv` | Praveen |
| 2 | Cross-validate against official PDFs, report agreement per statute | Praveen |
| 3 | Pull the 1956 and 1981 revised versions, derive version intervals | Himath |
| 4 | Acquire official PDFs for the in-scope statutes still missing | Praveen |

Phase 0 takes about half an hour and it is what makes the rest defensible.

## Open questions

- How do Kandyan, Roman-Dutch, Muslim, English, and Buddhist ecclesiastical law
  enter the graph? Around 255 citations, no statute to acquire. Needs a node
  type and a decision on what a citation to a legal system resolves to.
- Do we keep `derived/statute-section-index.json` at all, or generate it from
  the retrieval index so there is one authoritative section list rather than
  two?
- The section-number extractor currently reads enactment years as section
  numbers (Evidence Ordinance highest section 1896, Partition Law 1977). Fix
  before any plausibility check depends on those ceilings.
- Which of the 24 unmatched checklist rows are real acquisitions and which are
  drafting templates that belong in the template library instead?
