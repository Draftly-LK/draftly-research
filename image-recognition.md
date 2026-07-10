# Digitizing Draftly Legal Document Bundles

## Current Understanding

The current case folders contain real Sri Lankan legal/property workflow documents.
They are not simple text files. Most of them are scanned PDFs or photographed pages,
and many contain Sinhala, English, stamps, signatures, handwriting, tables, old deed
formats, and low-quality scan artifacts.

The documents include:

- deeds and deed copies
- survey plans and plan-related pages
- municipal or assessment records
- registry or official extract-style pages
- legal letters
- title reports
- pedigrees / chain-of-title documents
- Abstract of Title / AT form documents
- assessor letters
- identity/supporting images
- building/site photos
- litigation/court-related documents

The important point is that Draftly should not only OCR these documents. The real value
is turning a messy document bundle into a structured, lawyer-reviewable case record.

## Why Plain OCR Is Not Enough

Many PDFs are image-only scans, so normal PDF text extraction gives little or no useful
text. Even when text is extracted, Sinhala OCR can be noisy, and legal documents often
depend on layout, tables, stamps, names, dates, deed numbers, plan numbers, lot numbers,
and boundaries.

So the digitization goal should be:

```text
raw document bundle
-> page images
-> OCR text
-> document classification
-> extracted legal/property facts
-> source evidence links
-> lawyer review/correction
-> verified structured case record
-> draft generation
```

This is what makes Draftly more than a scanner or a template filler.

## Recommended Folder Workflow

Keep raw files unchanged:

```text
data/
  raw/
    case-001-.../
      inputs/
      target_outputs/
      manifest.md
```

Create processed artifacts separately:

```text
data/
  processed/
    case-001-.../
      pages/
      ocr_text/
      extracted_fields/
      review/
      verified/
```

Suggested meaning:

- `pages/`: rendered page images from PDFs.
- `ocr_text/`: OCR output per page.
- `extracted_fields/`: machine-extracted fields before review.
- `review/`: lawyer/user correction notes.
- `verified/`: final corrected structured data for the case.

## Step-by-Step Digitization Pipeline

### 1. Preserve Raw Evidence

Never edit the original PDFs/images. Treat `data/raw/` as the private evidence archive.
If a scan needs cleanup, create a processed copy.

### 2. Convert PDFs Into Page Images

Many PDFs are scanned. Each page should be rendered as an image before OCR.

Example output:

```text
processed/case-001/pages/
  source-021-page-001.jpg
  source-021-page-002.jpg
```

### 3. Classify Each Document

Before extracting fields, label what each document is.

Useful document classes:

- deed
- gift deed
- deed of transfer
- survey plan
- assessment record
- municipal receipt
- registry extract
- title report
- pedigree
- AT form
- assessor letter
- identity document
- legal letter
- litigation document
- site/building photo
- other

### 4. Run OCR

Use different OCR strategies depending on the document type.

Recommended baseline tools:

- **PaddleOCR**: good open-source OCR baseline, worth testing for Sinhala/English scans.
- **EasyOCR**: easy to run and useful for quick experiments.
- **Google Document AI**: strong paid baseline, useful for comparison if budget/privacy
  allows.
- **Direct DOCX/PDF text extraction**: use this whenever documents already contain text.

For this project, OCR should be treated as one module, not the whole system.

### 5. Extract Legal and Property Fields

After OCR, extract structured fields such as:

- deed number
- deed date
- deed type
- notary name
- grantor / transferor
- grantee / transferee
- property name
- plan number
- plan date
- surveyor name
- lot number
- extent
- boundaries
- assessment number
- street/address
- owner name
- registration reference
- document date

### 6. Store Evidence for Every Extracted Fact

Every extracted value should point back to its source.

Example:

```csv
case_id,doc_id,page,field_name,value,evidence_note,confidence,review_status
case-001,source-023,1,plan_number,4010,Survey plan title block,0.92,pending
case-001,source-021,1,deed_number,6286,First page deed heading,0.88,pending
```

This evidence tracking is important because lawyers need to verify the source, not just
trust the model.

### 7. Link Facts Across Documents

This is the core Draftly value.

Examples:

- A deed refers to a plan number.
- A title report paragraph refers to a deed number.
- A pedigree node refers to a deed, owner, and lot.
- A municipal assessment document refers to an assessment number and property owner.

Suggested link table:

```csv
case_id,source_doc,source_field,target_doc,target_field,relationship,review_status
case-001,source-021,deed_number,target-001,title_report_reference,mentioned_in,pending
case-001,source-023,plan_number,source-021,plan_number,same_as,pending
```

### 8. Human Review and Correction

The system should show extracted facts and evidence to a lawyer or reviewer.

Each extracted field can have a status:

- `pending`
- `accepted`
- `corrected`
- `rejected`
- `uncertain`

The reviewed data becomes the verified case record.

## Suggested Data Files

For each case, maintain these files:

```text
processed/case-001/verified/
  documents.csv
  extracted_fields.csv
  fact_links.csv
  red_flags.csv
  case_record.json
```

### documents.csv

```csv
case_id,doc_id,file_path,doc_type,role,language,page_count,notes
case-001,source-023,inputs/source-023-survey-plan-no-4010.pdf,survey_plan,input,English,2,Plan No. 4010
```

### extracted_fields.csv

```csv
case_id,doc_id,page,field_name,value,evidence_note,review_status
case-001,source-023,1,plan_number,4010,Plan title block,pending
```

### fact_links.csv

```csv
case_id,from_doc,from_field,to_doc,to_field,relationship,review_status
case-001,source-023,plan_number,source-021,plan_number,same_plan,pending
```

### red_flags.csv

```csv
case_id,flag_type,description,evidence,status
case-001,missing_document,Previous deed mentioned but not found,source-021 page 1,pending
```

## Recommended MVP Approach

Start with one strong case first, especially the case that has both source documents and
clean target outputs.

For the MVP:

1. Convert scanned PDFs to page images.
2. Run OCR on each page.
3. Manually classify document types.
4. Extract a small set of important fields.
5. Let a human correct the extracted fields.
6. Build a verified case record.
7. Generate or compare outputs such as title report, pedigree, AT form, or assessor
   letter.

Do not try to solve every legal document type at once. The first target should be a
small, well-reviewed dataset with strong evidence links.

## Privacy Rules

These files contain real legal and personal information.

- Do not push raw files to GitHub.
- Do not use real documents in public demos.
- Keep `data/raw/` private.
- Create anonymized copies before sharing with anyone outside the team.
- Remove or replace real names, NICs, addresses, deed numbers, signatures, stamps, and
  identifiable photos in demo datasets.

## Best Summary

The best way to digitize these documents is not simply:

```text
PDF -> OCR text
```

The better Draftly workflow is:

```text
case bundle
-> page images
-> OCR
-> document classification
-> field extraction
-> fact linking
-> source evidence
-> lawyer verification
-> structured case record
-> draft generation
```

That is the path that makes Draftly a legal document understanding and drafting system,
not just an OCR tool.
