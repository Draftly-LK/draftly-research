# Streamlit Proof of Concept: Title Review and Draft Generation

## Goal

Build a small Streamlit proof of concept that demonstrates Draftly's first workflow:
turning a conveyancing/title document bundle into a lawyer-reviewable title record and
draft outputs.

The POC should not try to solve full legal automation. It should show the product idea:

```text
case documents
-> extracted or manually entered facts
-> lawyer review
-> title-chain view
-> red flags / missing fields
-> relevant statute sections + case law (grounded authority)
-> draft title-related outputs
```

The first case to support should be:

```text
data/raw/case-001-rajagiriya-dalgahawatta-plan-4010-title-chain/
```

This case is the best starting point because it has source documents and lawyer-prepared
target outputs.

### What changed since this plan was first written

The legal corpus that powers the "law" side of the workflow now exists, so the POC
can do more than shuffle a document bundle — it can show the *authority* behind each
check and draft:

- **Statutes:** ~67 Sri Lankan conveyancing statutes/amendments in
  `data/legal-sources/`, organized into 20 curriculum topics with an extracted
  Markdown copy per source.
- **Case law:** the New Law Reports / Sri Lanka Law Reports body has been collected
  from the Internet Archive (public-domain volumes) and CommonLII (Supreme Court +
  Court of Appeal), filtered to a conveyancing subset. See
  `data/legal-sources/library/case-law/README.md` and the manifests under
  `data/legal-sources/manifests/`.
- **Retrieval design (decided):** a navigable topic → subtopic → source-section tree
  (BookRAG-style), with cases linked to the statute sections they cite. This is what
  the POC's "Relevant Law & Authority" panel reads from.

This maps onto the mentor's model: conveyancing has six notarial functions
(examination of title, drafting, execution, stamping, attestation, registration).
The POC targets the first — **examination of title** — plus the draft outputs that
follow from it.

## POC Scope

### In Scope

- Select a case from `data/raw/`.
- List the source documents and target outputs.
- Show document metadata from the case manifest.
- Allow the user to enter or review extracted facts.
- Maintain a verified title record in JSON.
- Show a simple title-chain / pedigree table.
- Show missing fields and possible red flags.
- Generate draft text for:
  - title report summary
  - pedigree / chain-of-title summary
  - AT form style field summary
  - assessor letter draft
- Export generated drafts as Markdown or DOCX.

### Out of Scope for First POC

- Full OCR accuracy.
- Full Sinhala legal NLP.
- Automatic extraction from every scanned PDF.
- Final legal advice.
- Public deployment with real raw documents.
- Multi-user authentication.
- Production database.

## Recommended App Structure

```text
apps/
  streamlit-poc/
    app.py
    requirements.txt
    README.md
    draftly_poc/
      cases.py
      schemas.py
      generators.py
      checks.py
      export.py
      sample_data.py
```

Keep the app simple and local. A single Streamlit app is enough for the proof of
concept.

## Data Structure

Create processed case data separately from raw files. The POC reads from two
places: the private per-case data, and the shared legal corpus.

```text
data/
  raw/                      # private client bundles (never public)
  processed/
    case-001-rajagiriya-dalgahawatta-plan-4010-title-chain/
      case_record.json
      extracted_fields.csv
      red_flags.csv
      generated/
  legal-sources/            # shared corpus (statutes + case law + topics)
    manifests/              # source-registry.csv, case-law manifests
    topics/                 # 20 conveyancing topics
    library-markdown/       # extracted statute text
    library/case-law/       # harvested NLR/SLR (gitignored text, tracked manifests)
```

### case_record.json

The first POC can use manually prepared verified data instead of relying on OCR.

Suggested structure:

```json
{
  "case_id": "case-001-rajagiriya-dalgahawatta-plan-4010-title-chain",
  "case_name": "Rajagiriya Dalgahawatta Plan 4010 Title Chain",
  "property": {
    "land_name": "Dalgahawatta",
    "location": "Rajagiriya, 4th Lane",
    "plan_number": "4010",
    "plan_date": "1979-01-20",
    "surveyor": "G. A. H. Phillipiah",
    "lots": [
      {
        "lot_number": "D",
        "extent": "14.75 perches"
      },
      {
        "lot_number": "C",
        "extent": "undivided 7.20 perches out of 19.54 perches"
      }
    ]
  },
  "title_chain": [
    {
      "deed_no": "2161",
      "deed_type": "Gift Deed",
      "date": "2003-11-25",
      "lot": "D",
      "owner": "REDACTED_OWNER_1",
      "notary": "B. Vernon Mendis",
      "registry_ref": "M 2129 / 202, 270, 271",
      "source_doc": "source-021-sinhala-transfer-deed-no-6286.pdf"
    }
  ],
  "current_owner": "REDACTED_CURRENT_OWNER",
  "review_status": "draft"
}
```

Use placeholders or anonymized names for public/demo data.

## Streamlit Screens

### 1. Case Dashboard

Show:

- case name
- case type
- input document count
- target output count
- privacy warning
- document list

### 2. Document Viewer

Show the selected document name and metadata.

For the first POC, this can be simple:

- list PDFs/images/DOCX files
- open file path or preview rendered first page if easy
- show notes from manifest

### 3. Extracted Facts Review

Show editable fields:

- deed number
- deed date
- deed type
- notary
- owner / transferor / transferee
- plan number
- lot number
- extent
- boundaries
- registry reference
- assessment number

The user should be able to edit fields and mark them:

- pending
- accepted
- corrected
- uncertain

### 4. Title Chain View

Show a table of deeds in chronological order.

Columns:

- date
- deed number
- deed type
- party / owner
- lot
- extent
- registry reference
- source document

Optional visual:

```text
Deed 2161 -> Deed 2327 -> Deed 3023 -> Current Owner
```

### 5. Checks and Red Flags

Start with rule-based checks:

- missing deed number
- missing deed date
- missing notary
- missing plan number
- missing lot extent
- same lot with conflicting extents
- current owner not found in final title-chain node
- source document missing for a title-chain entry

Add the mentor's core "everything must tally" cross-checks — the deed schedule, the
survey plan, and the municipal assessment record must agree:

- plan number differs between deed and survey plan
- lot number or extent differs between deed and survey plan
- assessment number on the deed differs from the municipal record
- a party transfers a lot they never acquired earlier in the chain
- a prior deed is referenced but not uploaded (broken chain link)

Each triggered check can cite the relevant statute section from the corpus (e.g.
Prevention of Frauds Ordinance for deed requisites, Registration of Documents
Ordinance for registration effect), so a red flag comes with its authority.

### 6. Draft Generator

Generate simple draft text from the verified case record.

Outputs:

- title report summary
- pedigree summary
- AT form field summary
- assessor letter draft

For the first POC, use deterministic templates. Do not depend on an LLM for core demo
logic.

### 7. Relevant Law and Authority

The panel that connects the case to the legal corpus. For the current case's topic
(e.g. examination of title, gift deeds, condominium property), show:

- the applicable statute sections, from `data/legal-sources/` (title, act/ordinance
  number, section, and the topic it sits under);
- the leading cases from the harvested NLR/SLR conveyancing subset that cite those
  sections or match the topic;
- a link from each red flag to the section that governs it.

For the first POC this can be a static lookup keyed by the case's topic(s) — no live
retrieval needed. It still demonstrates the core idea: every check and draft is
backed by a citation, not a guess.

## Generation Strategy

Use templates first:

```text
The property known as {land_name}, situated at {location}, is depicted in Plan
No. {plan_number} dated {plan_date}, made by {surveyor}.
```

Then add optional LLM rewriting later if needed.

This keeps the demo reliable and avoids hallucination.

## Recommended Implementation Steps

1. Create `apps/streamlit-poc/`.
2. Add `requirements.txt` with:
   - `streamlit`
   - `pandas`
   - `python-docx`
   - `pydantic`
3. Create a manually prepared `case_record.json` for case 001.
4. Build the Streamlit dashboard.
5. Add editable fact review forms.
6. Add title-chain table and simple red-flag checks (including the tally checks).
7. Add deterministic draft generation.
8. Add the "Relevant Law and Authority" panel — a static topic → statute/case
   lookup built from `data/legal-sources/manifests/`.
9. Add Markdown/DOCX export.
10. Keep all raw legal files private and local.

## Demo Flow

The final demo should be:

1. Open Streamlit app.
2. Select `case-001-rajagiriya-dalgahawatta-plan-4010-title-chain`.
3. Show source documents and target outputs.
4. Open the verified case record.
5. Review extracted property/deed facts.
6. Show the title chain.
7. Show red flags or missing-field checklist.
8. Generate title report / pedigree / AT form / assessor letter draft.
9. Export the draft.

## Future Extensions

- OCR pipeline for scanned Sinhala/English documents.
- Automatic document classification.
- Page-level evidence viewer.
- Field extraction with confidence scores.
- Sinhala/English bilingual draft generation.
- Graph visualization for title chains.
- Lawyer comment and approval workflow.
- Multi-case dashboard.
- Export to DOCX/PDF with legal formatting.
- Anonymized public demo case.

## Privacy and Safety

- Never upload raw case files to a public repo.
- Do not use real names, NICs, addresses, signatures, or stamps in public demos.
- Keep raw files under `data/raw/`.
- Build public examples from anonymized `data/processed/` records.
- Every generated draft must be labeled as lawyer-reviewable, not final legal advice.

## Best First Version

The best first Streamlit POC is not a full OCR system. It is a clean workflow demo:

```text
raw case bundle
-> verified/anonymized facts
-> title-chain table
-> checks
-> generated drafts
```

Once this works, OCR and ML extraction can be added module by module.
