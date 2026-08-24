# Statute automation: how one statute gets from a source to a finalized tree

This is the working procedure for taking a single statute from whatever we hold
of it to an accepted canonical tree in `library/finalized/`. It is written from
the Land (Restrictions on Alienation) Act No. 38 of 2014, which went the whole
way through and hit most of the problems on the list.

Do one statute at a time, all the way to the end. A half-finished statute is
worse than an untouched one, because nothing in it says which half is finished.

Everything produced here is `status=unverified` until a lawyer signs it off. The
word "verified" below never means legally verified.

## Step 0: gather everything first

Before parsing anything, collect every copy of the statute and every amending
instrument we can reach. Parsing what you happen to have and looking for the
rest later is how the 2018 amendment ended up missing half its sections without
anything saying so.

```powershell
# What the registry already holds
uv run python -c "import csv;[print(r['source_id'],r['official_title'],r['local_pdf_path']) for r in csv.DictReader(open('data/legal-sources/manifests/source-registry.csv',encoding='utf-8-sig')) if r['source_id']=='SRC021']"

# Which amending instruments the statute's own header block names
uv run python scripts/extract_amendment_chains.py

# Fetch those amending Acts from the parliamentary archive
uv run python scripts/download_amendment_chain_acts.py

# Look for a LankaLaw HTML edition of the principal statute
uv run python scripts/harvest_lankalaw_consolidated.py match --all-primary
uv run python scripts/harvest_lankalaw_consolidated.py fetch --apply

# Look for LankaLaw HTML of each amending Act
uv run python scripts/harvest_lankalaw_amendments.py

# Look for a CommonLII edition, for anything between 1956 and 2006
uv run python scripts/harvest_commonlii_statutes.py --only SRC023
```

The amendment chain is the list to work against. It is printed at the front of
every consolidated statute and names every instrument folded into the text, so
it tells you how many amending Acts you are looking for before you start
looking.

## Step 1: if it is older than 1956 and nothing turns up, it probably is not online

The date of the instrument predicts whether a standalone copy exists at all.

| Era | What is usually reachable |
| --- | --- |
| Before 1956 | Rarely a standalone document. Look in the revised-edition compendium volumes (`legislative-enactments-1980-volume-*.pdf` and the 1956 revised edition) and expect to extract the statute out of a larger PDF. |
| 1956 to 2006 | CommonLII's `num_act` series covers this range. |
| Roughly 1960 to 2009 | LankaLaw publishes standalone Act HTML without a subscription. |
| 2006 onward | The parliamentary archive and the Government Printer PDFs. |

If a pre-1956 instrument does not appear after a real search, record that it was
searched for and stop looking. Write the negative result down. An empty
`Own text` cell in the RUBRIK that nobody can explain will be searched for again
by the next person.

Two things that cost time before, worth knowing:

LankaLaw's A to Z index is incomplete. Two further indexes,
`/consolidated-statutes-upto-2006/` and `/consolidated-acts-2025/`, hold statutes
the A to Z page never lists, including Notaries, Prevention of Frauds, Wills and
the Civil Procedure Code. `FLAT_INDEXES` in `harvest_lankalaw_consolidated.py`
covers both.

CommonLII serves one page per section, not one page per Act. The harvester
stitches them back together, and the join is where text goes missing. Check the
assembled file against the section count before parsing it.

The subscription seat authenticates but does not unlock everything. Login through
`scripts/lawlanka-section-index/fetch.py` succeeds, and `actFullView` still
answers some Acts with "You are a Free/Promotional User" and a page that stops
partway. Always check a fetched page for that banner before trusting it:

```powershell
Select-String -Path "data/legal-sources/library/amendments/html/*.html" -Pattern "Free/Promotional User" -List
```

## Step 2: take HTML where it exists, but check it is whole

HTML is the better source when it is complete, because LankaLaw's semantic
classes carry the structure directly and the inline amendment markers survive.

```powershell
uv run python scripts/build_canonical_statutes.py
uv run python scripts/build_canonical_amendments.py
```

Complete is the operative word. Both Land (Restrictions on Alienation)
amendments had HTML, both were truncated behind the subscription wall, and the
truncation is silent. The 2017 page dropped its section 3 and the 2018 page
dropped sections 3 and 4, including the one that moves section 5A's operative
date. A tree built from a truncated page is not visibly wrong. It is just short.

So before parsing an HTML page, count what it should contain. The amendment
chain gives the expected instruments; the printed Act gives the expected section
count. If the page has fewer sections than the Act has, prefer the PDF.

A section count will not catch every kind of truncation. CommonLII lays a
section out as tables nested inside tables, one per subsection and paragraph, so
a non-greedy `<table>(.*?)</table>` stops at the first inner close and keeps only
the opening limb. Every section still arrives, which is why the count looks
right; seventeen of the twenty-five in the Tea and Rubber Estates Act had lost
everything after their first paragraph, and section 3 ended on the words
"obtained by the transferor, and". Counting the tags instead recovered
subsections 22 to 50 and paragraphs 9 to 40 from the same cached pages. When a
source nests its markup, match the outer element by balancing the tags, and read
the last provision of a long section before believing the extraction.

## Step 3: decide which edition you are holding

Ask whether the document is the Act as enacted or a consolidated reprint, and
record the answer in `edition.kind`. The two are different documents and must
never overwrite each other.

A consolidated text has been edited by whoever published it. It carries the
amendment chain at the front, inline markers such as `[2, 21 of 2018]` in the
margin, and text that already reflects every amendment. The original does not.
Where both exist, hold both: `--edition original` writes a separate file, and
`finalize_statute.py` gives the consolidated copy a `-consolidated` suffix while
naming the folder from the original.

Prefer the Government Printer over a private republisher. LankaLaw is a private
republisher and its `edition.caveat` says so. Where a Government Printer PDF
exists with a text layer, parse that instead, and say who published it in
`edition.publisher` rather than leaving a default in place.

Then pick the parser by what the document is:

```powershell
# Principal statute, LankaLaw HTML
uv run python scripts/build_canonical_statutes.py

# Principal statute, two-column PDF with a text layer
uv run python scripts/parse_consolidated_pdf.py --source-id SRC021
uv run python scripts/parse_consolidated_pdf.py --source-id SRC012 --edition original

# Amending Act, Government Printer PDF
uv run python scripts/parse_amendment_pdf.py --number 3 --year 2017 `
    --pdf data/legal-sources/library/amendments/incoming/3-2017-land-restriction-on-alienation-act-amendment.pdf `
    --amends SRC021 --show
```

If the PDF is a scan with no text layer, read it with the offline OCR pass first.
It runs locally on CPU, costs nothing and sends nothing anywhere, which is what
makes it usable on the private files in `data/raw/` as well:

```powershell
uv run python scripts/ocr_scanned_act.py `
    --pdf data/legal-sources/library/amendments/21-2018-land-restrictions-on-alienation-amendment-act.pdf `
    --out data/legal-sources/library/amendments/ocr/21-2018-land-restrictions-on-alienation-amendment.txt

uv run python scripts/parse_amendment_pdf.py --number 21 --year 2018 `
    --ocr-text data/legal-sources/library/amendments/ocr/21-2018-land-restrictions-on-alienation-amendment.txt `
    --amends SRC021 --show
```

OCR output goes to a sidecar, never into the corpus, so a machine's reading of
an image is never mistaken for source text.

## Step 4: the review loop, up to five passes

Write the tree, then read it against the print, then fix what is wrong and write
it again. Five passes is the cap. Most statutes converge in two or three.

Each pass is:

1. Run the parser.
2. Run the coverage check. This is the stopping rule, not a spot check.
3. Read the structure: section list, headings, one full section at each depth.
4. Fix the cause in the parser, not the symptom in the output.
5. Go again.

```powershell
uv run python scripts/check_parse_coverage.py --source-id SRC021
uv run python scripts/check_parse_coverage.py --source-id SRC021 --fail-over 1.0
uv run python scripts/check_parse_coverage.py `
    --tree data/legal-sources/library/finalized/38-2014-land-restrictions-on-alienation-act/3-2017-land-restrictions-on-alienation-amendment.json `
    --pdf data/legal-sources/library/amendments/incoming/3-2017-land-restriction-on-alienation-act-amendment.pdf
```

Read the coverage number, but check what it counted first. Run against a scan
with no text layer it reports `0 words in the source, 0 unmatched (0.00%)` and
passes, which is how the Tea and Rubber Estates Act cleared a gate that had
never read a word of it. Zero words is not coverage. If the source word count is
zero or implausibly small, the check has told you the source needs OCR, not that
the tree is good.

Break out of the loop when all of these hold:

- Unmatched words are under about 0.5% for a text-layer source, and every
  remaining word is accounted for. Read the list; do not just read the number.
  On the Land Restrictions Act the last seven words were the amendment chain
  header, which belongs in metadata rather than the body.
- Every section has a heading, or the ones without one are listed and explained.
- Section numbers run in order with no invented or duplicated sections.
- Enumerators nest at the right depth, and the depth was decided by context
  rather than by the token. `(i)` after `(h)` continues the alphabet; `(i)`
  after `(b)` opens a roman sub-list one level down.
- Provisos are their own nodes rather than trailing text inside the provision
  they qualify.
- Definitions are separate nodes with a `term`, and none of them is truncated.
  Watch for two run together in one printed entry. State Land (Claims) prints
  `" claim " means ... and " claimant" means any person making a claim;` as a
  single entry, and a parser that splits on the opening quote keeps the first
  term and loses the second. Splitting on a quote alone also breaks inside a
  definition, because the closing quote of one term and the opening quote of the
  next look the same: that cost the Tea and Rubber Estates Act its definition of
  "partition action". Split on the quoted term plus its defining verb.
- Cross-references have balanced brackets and name a title the registry knows.
- No internal reference points past the last section. This one check catches a
  whole class of error and costs nothing. "section 333 of that Code" in the
  Thesawalamai Pre-emption Ordinance became an internal reference to a section
  333 of a fourteen-section Ordinance; "section 35 of that Ordinance" did the
  same in a nine-section one, and "section 11 (2) (a) of the Land Settlement
  Ordinance" in a seven-section one. The words "that Ordinance", "that Code" and
  "the said Ordinance" all point outward, and a parser that requires
  `section N of the <Name>` to be contiguous will not see them.
- Section 1 does not cross-reference anything. It declares the short title, so a
  reference from it to the statute itself is an artefact.
- No section repeats its first subsection in its own `text` or `raw_text`. Where
  a section has children, its own text should be the words before the list, or
  nothing at all.

Do not keep going round after five passes. If it has not converged, the residue
is usually not a parsing problem: it is a printing artefact that geometry cannot
resolve. Record it by hand instead (see Step 5) and move on.

Things that went wrong before and are worth checking for directly:

- Text lost at a column boundary. A wrapped line in a full-width region looks
  exactly like a marginal note beside a provision. This is the failure that the
  coverage check exists to catch.
- A sentence torn in half at its own cross-reference, because a line began with
  `(a)` where the previous line ended with the word "paragraph".
- A marginal note read as body text, or body text read as a marginal note.
- A running header or the Publications Bureau imprint parsed as a section. A
  section 118 in a four-page Act is this.
- On a Government Printer Act, the marginal note sits in the outer margin and so
  swaps sides from one page to the next. Assuming one side loses every section on
  half the pages.
- A marginal note landing inside a sentence rather than beside it. Land Grants
  section 13 reads "any State land transferred under disposition. section 3 is
  situated", where "disposition." is the note. Execution of Deeds section 3 has
  "by such Judge, Copies or extracts how obtained. Commissioner, or Justice", and
  that note was the section's second heading, so it was lost from the headings as
  well as corrupting the text. Grep the body for a full stop followed by a
  lower-case word.
- A citation read as a structural label. "subject to the provisions of
  subsections (2) and (3)" produced a real subsection (2) node, and "subsection
  (4) or subsection (5) of section 3" produced four phantom subsections in a
  section that has none. Mask citation runs before detecting enumerators. Mask
  the whole run, head included: matching a bare "and (n)" also swallows genuine
  list items, because paragraph (b) of a section often opens "..., and (b)".
- `(i)` placed by its token rather than by its neighbours. `(i)` after `(h)`
  continues the alphabet; `(i)` followed by `(ii)` opens a roman sub-list. The
  rule in the list above is right, and it is worth testing directly: section 8 of
  the Tea and Rubber Estates Act put `(i)` beside paragraph (b) and hung (ii) and
  (iii) underneath it.

## Step 5: what to do with what the parser cannot fix

Two kinds of residue are legitimate, and both are recorded rather than silently
absorbed.

An error in the source stays in the text and gets a note. The 2017 Act prints
"under and indenture of lease", which is a typographical error for "under an
indenture". The tree keeps the printed wording and
`data/processed/amendment-overrides.json` records the reading. The corpus says
what the Act says.

An error in a machine's reading gets corrected, not annotated. This is the
opposite rule and the distinction matters. Where a scan was read by OCR, the
corrected wording goes in `text` and in every target label and operation, the
machine's version stays in `raw_text`, and `corrections` lists each character
that differs. Recording an OCR misreading in a notes field while still using it
as the value produces a wrong value with a footnote attached: the 2018 Act read
`(ht)` for `(h)` and the amendment target said `3(1)(ht)`, which is not a
provision that exists.

Hand corrections live in two files, keyed by identifier:

- `data/processed/canonical-overrides.json` for principal statutes. Holds
  `section_headings`, `long_title`, `publisher`, `editorial_notes`,
  `quality_notes`, `checked_against` and `verification_status`. A corrected
  heading keeps the damaged reading in `heading_raw`, so the correction stays
  visible rather than becoming an assumption.
- `data/processed/amendment-overrides.json` for amending Acts, in the same shape.

A tree corrected by hand carries `provenance.hand_corrected: true`.
`finalize_statute.py` leaves those files alone on a re-run, so a routine rebuild
cannot throw the corrections away.

## Step 6: vetting before anything is called finished

Check these against the printed document, not against the tree.

Structure. Every section present and in order. Every heading matching its
marginal note. Every subsection, paragraph and subparagraph at the depth the
print puts it. Provisos attached to what they qualify.

Text. Coverage under the threshold with the residue explained. Definitions
complete. No words lost at a wrap, and no words gained from a running header.

Amendments. Every instrument in the chain either parsed or explained. Every
inline marker resolved to a real operation and target rather than left as
`unknown`. The operations in the principal statute agreeing with the amending
Act's own instructions: these are two independent sources, and where they agree
you have a genuine cross-check. On the Land Restrictions Act the marker on
section 5A said it came from section 2 of Act No. 3 of 2017, and that Act's own
text said its section 2 inserts 5A.

Metadata. `edition.kind` and `edition.publisher` describing the document you
actually parsed. `citation.type` set. Long title and preamble captured; recitals
are the only place a statute says why it exists. Dates in ISO form with the
printed wording kept alongside. `source_location` recording which pages the text
came from.

Three metadata checks are worth calling out separately, because each of them has
been wrong more often than it has been right.

Read section 1 and compare the short title it declares with the registry's
`official_title`. They disagree more often than not, and the registry is usually
the one that is wrong. Section 1 of what the corpus calls the Execution of Deeds
Ordinance cites it as the Deeds and Documents (Execution before Public Officers)
Ordinance, and the string "Execution of Deeds Ordinance" appears nowhere on the
page. Others: State Lands (Claims) is State Land (Claims); Tesawalamai is
Thesawalamai; Land Registers (Reconstructed Folios) is an Ordinance and not an
Act. Correct the finalized tree, record the registry form under
`alternate_titles`, and leave `source-registry.csv` alone until someone has
checked that `build_statute_tiers.match_curriculum` still matches on the new
title. That column is a matching key as well as a label.

Take the commencement from the date the statute prints at its head, in brackets,
and cross-check `data/processed/statute_commencement.csv`. The CSV has no row at
all for most of the statutes finalized so far, and where it does have one it can
be wrong: it dates the Matrimonial Rights and Inheritance Ordinance to
1876-06-29 where the page says 29 June 1877. The gap between the citation year
and the commencement year is normal and is not evidence of an error on its own.
Ordinance No. 2 of 1958 commenced in December 1957, No. 17 of 1852 in July 1853.

Check which instrument in the chain is the principal one. The header block lists
the principal first and the amending instruments after it, and the head date
belongs to the principal. Where the registry's citation year is later than the
head date, the two have been swapped. The corpus records the Jaffna Ordinance as
No. 58 of 1947 amended by No. 1 of 1911; the page lists 1 of 1911 first, dates
itself 17 July 1911, and carries five markers reading `[n, 58 of 1947]`. It is
the 1911 Ordinance, and 58 of 1947 is what amended it.

Provenance. The registry's `sha256` matching the file on disk. If a better copy
has replaced the one the registry describes, update the row.

```powershell
# The registry hash should match the file it names
uv run python -c "import hashlib,pathlib;p=pathlib.Path('data/legal-sources/library/statutes/38-2014-land-restrictions-on-alienation-act-consolidated-2024.pdf');print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

Then set `verification_status`. Use `structurally_verified` when the structure,
headings, targets and metadata have been checked line by line against the print.
Leave it `unverified` when the wording rests on a single OCR reading with no
second source. Legal effect is never verified by any of this.

## Step 7: assemble the finalized package

```powershell
uv run python scripts/finalize_statute.py --source-id SRC021 `
    --slug 38-2014-land-restrictions-on-alienation-act `
    --amendment 3-2017 --amendment 21-2018 `
    --statute-note "No original-edition text is held. The registry's Government Printer PDF of the Act as enacted is a scan with no text layer."
```

Two folders come out, both named from the principal instrument:

```text
library/finalized/<no>-<year>-<slug>/           the canonical JSON, nothing else
library/finalized-sources/<no>-<year>-<slug>/   every file those trees were read from
```

`finalized/` is the layer to build on. `data/processed/canonical-*` is
regenerated output and moves under anyone standing on it.

`finalized-sources/` answers the other question, which is what was actually read
to produce the tree. Its `manifest.json` carries the size, SHA-256 and origin
path of each file. Where a tree came from OCR, the scan is carried next to the
transcript, so the package never documents a reading with no original. Both
folders are rebuilt wholesale, which is what stops a source that has been
dropped, such as a truncated page replaced by a better one, from sitting there
indefinitely still looking like evidence.

## Step 8: write it up in the RUBRIK

Nothing is finished until `apps/statute-browser/RUBRIK.md` says so. The RUBRIK is
the index of record for what is held, where it is, and how far along it is.

Merge the finalized tree into the section index first. Nothing else does this,
and until it happens a statute with an accepted tree still reports "sections not
extracted" and cannot be retrieved or cited. Merge from `finalized/` rather than
from the raw parse, so the index gets the reviewed headings and not the damaged
ones the review just fixed.

```powershell
uv run python scripts/merge_html_sections_into_index.py --source-id SRC023
uv run python scripts/build_actions.py
uv run python scripts/build_section_versions.py
uv run python apps/statute-browser/build_statute_tiers.py
uv run python apps/statute-browser/build_statutes_by_date.py
uv run python apps/statute-browser/build_rubrik.py
```

`PRIMARY-STATUES.md`, `SECONDARY-STATUES.md` and `STATUTES-BY-DATE.md` are
generated from the same index and go stale the moment it changes, and
`test_statute_browser.py` asserts a statute count that moves when a statute is
extracted. Regenerate all of them in the same pass or the test suite will fail on
someone else's branch.

It is generated, so do not hand-edit it. It reads the registry, the section
index, the amendment chains, the download reports, the canonical directories and
`finalized/`, which means anything you want it to say has to be true in those
files first. If the RUBRIK reports an amendment as "not published as HTML" after
you have downloaded it, the download report is what needs updating, not the
RUBRIK.

Each statute's entry should end up showing the canonical structure counts, the
finalized path, every source file, and every amending instrument with what it
does. Check the entry after regenerating. A statute that is finished and a
statute that is untouched should not look alike.

Finally:

```powershell
npx markdownlint-cli2
uv run pytest tests apps/statute-browser -q
```

## The whole thing, in order

```text
gather sources + chain
        |
   pre-1956 and nothing found? -> record the negative result, stop looking
        |
   HTML available and complete? -> parse HTML     else -> parse PDF
        |                                                     |
        |                                          no text layer? -> OCR to a sidecar first
        |                                                     |
   which edition is this? record it, keep original and consolidated apart
        |
   +--> parse ---> check coverage ---> read the structure ---> fix the parser
   |                                                                |
   +--------------- up to 5 passes, break when it converges --------+
        |
   record what the parser cannot fix: source errors annotated, OCR errors corrected
        |
   vet: structure, text, amendments, metadata, provenance
        |
   set verification_status
        |
   finalize_statute.py  ->  finalized/ + finalized-sources/ + manifest
        |
   merge into the section index, then regenerate everything that reads it
        |
   build_rubrik.py  ->  markdownlint  ->  pytest
```

## One thing this procedure does not cover

An amendment marker is only found if the regex recognises its shape, and several
shapes are not recognised. `MARKER` in `scripts/parse_lankalaw_html.py` wants a
comma straight after a single section number, so `[ 2 ; 3, Law 23 of 1978]` never
matched and the Land Registers (Reconstructed Folios) Ordinance was recorded as
having no amendments at all. Across the twenty-eight HTML editions there are 105
bracketed spans carrying a year that the regex does not match: semicolon lists,
`[§ 3,30 of 1999]`, doubled brackets, a full stop for the comma, subsection
targets like `[57(1), 18 of 1965]`, and repeal notes such as `[Section 201 is
repealed by Ordinance No. 21 of 1927]`, of which the Civil Procedure Code alone
has twenty. Until that is fixed, "Amendments: none recorded" in the RUBRIK means
the regex found nothing, which is not the same as there being nothing. Check the
page for bracketed spans by hand before accepting a statute as unamended.

## Scripts this uses

| Script | What it does |
| --- | --- |
| `scripts/extract_amendment_chains.py` | Reads the chain block at the front of a consolidated statute. |
| `scripts/download_amendment_chain_acts.py` | Fetches the chain's amending Acts from the parliamentary archive. |
| `scripts/harvest_lankalaw_consolidated.py` | Finds and fetches LankaLaw HTML for principal statutes. |
| `scripts/harvest_lankalaw_amendments.py` | Same, for amending Acts. |
| `scripts/harvest_commonlii_statutes.py` | Assembles a CommonLII Act from its per-section pages. Cached, so a re-run is free. |
| `scripts/parse_commonlii_statute.py` | Parses that assembly into a canonical tree, inferring depth from the enumerators. |
| `scripts/merge_html_sections_into_index.py` | Folds a finalized tree into the section index. Without this a finished statute still reads "not extracted". |
| `scripts/lawlanka-section-index/fetch.py` | Cached, rate-limited, single-session fetcher. Credentials from `.env`. |
| `scripts/build_canonical_statutes.py` | Parses LankaLaw HTML into canonical trees. |
| `scripts/build_canonical_amendments.py` | Same, for amending Acts. |
| `scripts/parse_consolidated_pdf.py` | Parses a two-column statute PDF with a text layer. |
| `scripts/parse_amendment_pdf.py` | Parses a Government Printer amending Act, PDF or OCR sidecar. |
| `scripts/ocr_scanned_act.py` | Offline OCR of a scan, laid back out into columns. |
| `scripts/check_parse_coverage.py` | Counts what the tree lost against its source. The loop's stopping rule. |
| `scripts/finalize_statute.py` | Assembles `finalized/` and `finalized-sources/` with a manifest. |
| `apps/statute-browser/build_rubrik.py` | Regenerates the RUBRIK. |
