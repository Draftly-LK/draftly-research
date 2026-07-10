# Draftly DSE Project — Full Conversation Handover

## 1. Initial context

The discussion was about selecting and refining a **DSE project** for the University of Moratuwa. The important distinction established earlier was:

* **DNN project** = pure research paper / deep learning research.
* **DSE project** = ML + Software Engineering product, full software lifecycle, demoable at a symposium/exhibition.

The final DSE project direction became a legal-tech product named:

# **Draftly**

A lawyer-in-the-loop legal document drafting and review platform for Sri Lankan legal workflows.

---

## 2. Final project identity

### Project Short Name

**Draftly**

### Project Title

**Draftly: A Lawyer-in-the-Loop Platform for Title Examination and Conveyancing Document Drafting in Sri Lanka**

Alternative broader title used earlier:

**Draftly: A Lawyer-in-the-Loop Legal Document Drafting and Review Platform for Sri Lankan Legal Workflows**

### Core idea

Draftly is not meant to be another legal search engine. It is meant to help lawyers with the **document preparation workflow**.

The system should take uploaded legal/property documents, extract facts, link facts across documents, build a structured case/title record, check inconsistencies, and generate lawyer-reviewable drafts.

---

## 3. Broader product vision

The product should eventually support many Sri Lankan legal drafting workflows:

```text
Conveyancing documents
Deeds of Transfer
Deeds of Gift
Revocation of Gift
Mortgage Bonds
Lease Agreements
Power of Attorney documents
Title Reports
Pedigree / Chain-of-Title Reports
Abstract of Title Deed / AT Forms
Certificates of Ownership
Assessor / Municipal ownership transfer letters
Complaints / plaints / පැමිණිලි
Affidavits
Petitions
Statements of Objections
Legal notices
Attorney letters
Certificates / declarations
```

But the project should not try to implement all of these at once. The architecture can support many workflows, while the first concrete use case should be narrower.

---

## 4. Main use case selected

The concrete use case selected was:

# **Conveyancing Title Documentation**

This includes generating and supporting:

```text
Title report
Pedigree / chain-of-title graph
Abstract of Title Deed / AT form
Certificate of Ownership
Assessor / municipal ownership transfer letter
Schedule to a new deed
Missing document checklist
Red-flag / inconsistency report
```

This was chosen because the user uploaded real examples of all these document types and supporting source documents.

---

## 5. Key explanation of the use case

The strongest explanation developed was:

> For example, when a lawyer prepares an **Abstract of Title Deed / AT form** or the **Schedule to a new deed**, the required information is usually not written from scratch. It is derived from previous deeds, survey plans, assessment records, and other supporting documents. Currently, this is mostly done manually, or sometimes by giving the documents to a broad/general-purpose LLM. Our idea is to streamline this process through a dedicated system that extracts the relevant legal and property facts, shows evidence from the source documents, allows the lawyer to verify or correct the extracted facts, and then generates the required draft documents.

Follow-up paragraph:

> In this use case, the system would not simply fill a fixed template from text boxes. It would process the uploaded document bundle, extract and link legal/property facts across the documents, build a **chain-of-title/pedigree**, highlight missing or inconsistent information, and generate lawyer-reviewable drafts such as **title reports, AT forms, ownership certificates, assessor letters, and deed schedules**.

Important English translation:

* **උපලේඛනය** = **Schedule**
* More specifically in legal/deed context: **Schedule to the Deed** or **property schedule**

---

## 6. Problem being solved

Sri Lankan conveyancing/title-documentation workflows are still highly manual. A lawyer/notary has to inspect:

```text
Old deeds
Current deed
Gift deeds
Survey plans
Assessment records
Municipal receipts
Land registry/path-iru extracts
Identity documents
Previous title reports
Certificates
```

Then the lawyer manually prepares:

```text
Title report
Pedigree
Abstract of title deed
Certificate of ownership
Assessor letter
Ownership transfer bundle
New deed schedule
```

The difficult part is **not only typing the final document**. The hard part is:

```text
Reading prior deeds
Identifying deed numbers, dates, parties, notaries
Understanding survey plans and lot numbers
Tracing ownership over time
Resolving name variants
Checking if the latest owner actually derives title from the previous owner
Checking if extents, plan numbers, lot numbers, and boundaries match
Checking if documents are missing
Preparing multiple outputs from the same verified facts
```

This is why Draftly is more than template filling.

---

## 7. What the system should take as input

For the conveyancing title-documentation use case, the system should accept a **property matter bundle**.

### Input document types

```text
Current deed
Previous deeds
Gift deeds
Deeds of transfer
Survey plan / condominium plan
Land registry extract / path-iru
Assessment register extract
Municipal assessment receipts
Client/property details
NIC/passport details, preferably entered manually or anonymized
Existing title reports, if available
Existing pedigree documents, if available
```

### Fields to extract from deeds

```text
Deed type
Deed number
Date of deed
Prior registration reference
Grantor / transferor / vendor
Grantee / transferee / purchaser
Consideration
Notary name
Attestation date
Property schedule
Plan number
Lot number
Extent
Boundaries
Witnesses
Land registry stamp/details
```

### Fields to extract from survey plans

```text
Plan number
Survey date
Surveyor name
Land name
Lot number
Extent
Boundaries
Scale
Location
District/province
Boundary table
```

### Fields to extract from municipal/assessment documents

```text
Municipal council
Assessment number
Street name
Owner name
Annual value
Rate percentage
Payment details
Receipt number
Account number
Property type
Date
```

### Fields to extract from registry/path-iru documents

```text
Land registry office
Volume / folio
Registration references
Owners
Encumbrances
Discharge references
Prior registrations
Remarks
```

---

## 8. What the system should do internally

Full pipeline:

```text
Create legal/property matter
→ Upload supporting documents
→ Classify document types
→ OCR and layout-aware extraction
→ Extract entities and relations
→ Link facts across documents
→ Build ownership graph / chain of title
→ Detect inconsistencies and missing documents
→ Show evidence/provenance to lawyer
→ Lawyer verifies or corrects facts
→ Generate lawyer-reviewable drafts
→ Lawyer edits/approves
→ Export DOCX/PDF
→ Maintain audit trail/version history
```

### Core system tasks

```text
Document classification
OCR
Layout-aware information extraction
Named entity recognition
Relation extraction
Entity resolution
Cross-document linking
Chain-of-title reconstruction
Consistency checking
Draft generation
Source/evidence traceability
Lawyer review and editing
Versioning
Export
```

---

## 9. What the system should output

### Main outputs

```text
Extracted field summary
Pedigree / chain-of-title graph
Draft title report
Abstract of Title Deed / AT form
Certificate of Ownership
Assessor / municipal ownership transfer letter
Deed schedule
Missing document checklist
Red-flag / inconsistency report
DOCX/PDF exports
```

### Example extracted field summary

```text
Deed No: 3023
Date: 2008.06.12
Nature: Gift Deed
Notary: B. Vernon Mendis
Property: Lot C and Lot D, Plan No. 4010
Owner: Sandhya Rani Jayatilaka
Registration: M 3147 / 200, 201, 202
```

### Example red flags

```text
Previous deed mentioned but not uploaded
Owner name differs across documents
Extent in deed differs from survey plan
Plan number mismatch
Lot number mismatch
Missing registration reference
Undischarged mortgage or encumbrance
A person transfers land they never acquired in the chain
```

---

## 10. Why this is not just template filling

Dr. Nisansa asked:

> Can you explain how this project would differ from template filling? What happens more than a person filling text boxes in a web page and a PDF is generated where 90% of the text is from template?

The answer developed:

The template is only the final output layer. The actual work happens before generation.

Draftly should:

```text
Read uploaded deeds/plans/records
Extract structured facts
Link facts across documents
Resolve parties and properties
Build a chain-of-title graph
Detect missing links and inconsistencies
Show source evidence
Allow lawyer verification
Generate multiple documents from the verified structured record
```

The project can be evaluated with measurable ML/software metrics, so it is not merely form filling.

### Short version used later

> We agree that legal IR has a clearer novelty path. For our project, the evaluation can go beyond whether a PDF was generated. We can evaluate document classification accuracy, key-field extraction accuracy, chain-of-title construction, consistency-checking performance, and time saved compared to manual work. If needed, we can narrow the scope further to only the **conveyancing/title-documentation workflow** and treat other legal drafting types as future extensions.

---

## 11. Relationship to SigmaLaw

The user uploaded/pasted details about Dr. Nisansa’s **SigmaLaw** project.

SigmaLaw focuses on legal NLP tasks such as:

```text
Legal information extraction
Legal sentiment analysis
Party identification
Coreference resolution
Legal document retrieval
Legal case retrieval
Winning party prediction
Sentence classification
Semantic similarity
Ontology population
Legal embeddings
```

Important positioning:

Draftly aligns with the broader legal NLP area of SigmaLaw but is different because it focuses on **practical drafting and workflow automation**, especially conveyancing/title-documentation.

Suggested wording:

> This project also aligns with the broader legal NLP direction of SigmaLaw, while focusing on a more practical workflow: lawyer-in-the-loop legal document drafting and review rather than legal search, sentiment analysis, or case analytics.

At the end of the response to Dr. Nisansa, the user wanted to say only:

> Thank you again for pointing this out. We will also go through the papers under the SigmaLaw project to better understand the previous work in this area.

---

## 12. Similar / existing Sri Lankan legal platforms discussed

The user wanted to avoid building another legal search engine because Sri Lanka already has platforms such as:

```text
LawLanka
AI PAZZ
Paralegal.lk
LawCeylon
```

These were positioned as mainly supporting:

```text
Legal search
Case law access
Legislation access
Legal references
```

Draftly differs because it targets:

```text
Client-specific deed bundles
Title examination
Pedigree/chain reconstruction
Draft document generation
Workflow automation
```

Safer wording recommended:

> Based on our preliminary review, these platforms mainly focus on legal research and legislation retrieval. We have not found an end-to-end system that reads a client’s own prior deed bundle and reconstructs the chain of title for Sri Lankan conveyancing workflows.

---

## 13. Domain validation / contacts

The user discussed contacting lawyers/notaries/legal-domain people.

Names mentioned:

```text
Mr. Anura Danarathne, PC, LL.M. Commercial Law (Deakin)
Mr. Madhawa Wijayasriwardena, Attorney-at-Law
Ms. Aruni Sakunthala Gunarathne, Attorney-at-Law
Mr. Ishan Rathnapala, Senior State Counsel at the Attorney General’s Department Sri Lanka and Visiting Lecturer at Sri Lanka Law College
```

Claim used carefully:

```text
We have started validating the problem by speaking to lawyers and people familiar with conveyancing.
Their initial feedback suggests this is a real practical problem.
They mentioned lawyers/notaries still spend significant time manually drafting/preparing repeated documents.
They are willing to support with domain feedback and validation.
```

Caution preserved:

Only say someone was contacted if they actually were contacted. Otherwise use:

```text
We have contacted or are in the process of consulting...
```

or

```text
We have identified and started reaching out to...
```

---

## 14. Uploaded legal/conveyancing document sets analyzed

### Set 1: Earlier output documents

Files included:

```text
AT-form (2).doc
Boralesgamuwa UC - Affidavit.pdf
Boralesgamuwa UC - Limited Statement of Objections.pdf
CamScanner 04-24-2026 15.07.pdf
DR. RAMYA HARIDOSS assessor letter.docx
DR.RAMYA HARIDOSS padigee.docx
DR.RAMYA HARIDOSS padigee.docx.pdf
හිමිකම් වාර්තාව.docx
```

### Classification of Set 1

| Document                        | Meaning                                                    | Input/output role                           |
| ------------------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| AT-form                         | Abstract of Title Deed to insert names in assessment books | Output                                      |
| Assessor letter                 | Letter to Chief Assessor requesting ownership transfer     | Output                                      |
| Pedigree                        | Chain-of-title / ownership-chain document                  | Output                                      |
| Title report / හිමිකම් වාර්තාව  | Full title report                                          | Output                                      |
| Boralesgamuwa UC affidavit      | Court affidavit                                            | Not core conveyancing, useful later         |
| Limited Statement of Objections | Litigation/court objection document                        | Not core first use case                     |
| CamScanner legal bundle         | Court/legal scanned bundle                                 | OCR test / possible later litigation module |

### Key insight

These documents show the **outputs** lawyers manually prepare. They prove the product can generate:

```text
Title report
Pedigree
AT form
Certificate
Assessor letter
```

---

## 15. Real example from first property set: Ramya Haridoss / Superior Homes

Earlier documents showed a condominium/title workflow.

Important examples:

```text
Present owner: DR. RAMYA HARIDOSS alias DR. RAMYA HARIDASS
Assessment No: 115-3/1
Location: Kollupitiya Lane Extension, Colombo 3
Property: Condominium Parcel CPF3P1
Residential complex: SUPERIOR HOMES
Deed of Transfer No: 896
Date: 01.03.2025
Grantor: Superior Constructions Pvt Ltd
Consideration: Rs. 45,000,000
Floor area: 170.01 sq.m / 1830 sq.ft
```

The pedigree showed a chain involving:

```text
Gamini Kristoper Renad Wijesinghe
Kadil Kanthi Mery Peris
Dilkanthi Maree Peris
Gamini Kristoper Barnad Wijesinghe
Elisabeth Maree Herath Nee Wijesinghe
Superior Constructions Pvt Ltd
DR. RAMYA HARIDOSS / HARIDASS
```

This helped define how the system should generate:

```text
Pedigree / chain-of-title
Title report
AT form
Assessor letter
Certificate of ownership
```

---

## 16. Uploaded image/PDF set with source documents

The user uploaded many images and a 29-page CamScanner PDF.

Document types identified:

```text
Municipal payment/assessment receipts
Assessment register/title extract style tables
Old deed of transfer copies
Sinhala transfer deeds
English transfer deeds
Survey plans
Certificate of ownership
Abstract of Title Deed forms
NIC/identity document images
```

Important classification:

### Input evidence documents

```text
Old deed copies
Current deed copies
Survey plans
Municipal receipts
Assessment register/title extract pages
NIC/identity document
Registry/path-iru extracts
```

### Generated output documents

```text
Pedigree
Title report
Abstract of title deed
Certificate of ownership
Assessor letter
Document checklist
Red-flag report
```

Important privacy warning:

These documents include real names, NICs, addresses, deed numbers, signatures, stamps, and legal records. They should not be uploaded publicly to GitHub/Hugging Face/demo repositories. Use anonymized or synthetic versions for development and exhibition.

---

## 17. Uploaded Set 20–25: Dalgahawatta / Plan 4010 property chain

Files:

```text
20.pdf
21.docx
22.pdf
23.pdf
24.pdf
25.pdf
```

### What each file was

| File    | Type                                       | Role                          |
| ------- | ------------------------------------------ | ----------------------------- |
| 20.pdf  | Sinhala Deed of Transfer No. 6286          | Input                         |
| 21.docx | Clean Sinhala title report + pedigree text | Output / target generation    |
| 22.pdf  | OCR/PDF version of same title report       | Output sample + OCR challenge |
| 23.pdf  | English Deed of Transfer No. 1383          | Input                         |
| 24.pdf  | Survey Plan No. 4010                       | Input                         |
| 25.pdf  | Sinhala Gift Deed No. 2327                 | Input                         |

### Property chain details from this set

Location/property details:

```text
Western Province
Colombo District
Salpiti Korale
Kotte Municipal Council area
Welikada East, Rajagiriya, 4th Lane
Land name: Dalgahawatta
Plan No: 4010
Plan date: 1979.01.20
Surveyor: G. A. H. Phillipiah
```

Key land portions:

```text
Lot D — 14.75 perches
Lot C — undivided 7.20 perches out of 19.54 perches
```

Deeds in title report:

```text
Gift Deed No. 2161 — 2003.11.25 — Lot D
Gift Deed No. 2327 — 2004.10.14 — Lot C
Gift Deed No. 3023 — 2008.06.12 — Lots D + C
```

Land Registry references:

```text
Delkanda Land Registry
M 2129 / 202, 270, 271
M 1400 / 221
M 3147 / 200, 201, 202
```

Important insight:

This set is ideal because it contains both:

```text
Source documents:
- deeds
- gift deed
- survey plan

Target output:
- clean title report
- pedigree text
```

This makes it useful for supervised evaluation.

---

## 18. ML / Data Science components defined

Draftly’s data science component includes:

```text
OCR for scanned Sinhala/English legal documents
Document classification
Named entity recognition
Relation extraction
Layout-aware information extraction
Table extraction from survey plans/forms
Entity resolution across name variants
Cross-document linking
Chain-of-title reconstruction
Defect/inconsistency detection
Grounded document generation
Clause-level provenance
Evaluation against lawyer-verified ground truth
```

### Possible model comparisons

```text
Rule-based extraction
Transformer-based extraction
Hybrid rule + ML extraction
OCR baselines
LLM-based extraction with validation
Graph-based title-chain construction
```

### Evaluation metrics

```text
Document classification accuracy
OCR extraction accuracy
Named-entity recognition F1 score
Key-field extraction accuracy
Relation extraction accuracy
Chain-of-title reconstruction accuracy
Defect-detection precision/recall
Draft correctness assessed by lawyers
Clause-level provenance correctness
Time saved compared to manual preparation
```

---

## 19. Software Engineering components defined

Draftly’s software engineering component includes:

```text
Web-based matter dashboard
User accounts and roles
Legal matter creation
Document upload and management
Document processing pipeline
Template library
Guided intake forms
Extracted fact review UI
Evidence/provenance viewer
Ownership graph / pedigree viewer
Consistency/red-flag dashboard
Lawyer review/edit workspace
Version history
Audit trail
DOCX/PDF export
Access control
Privacy/security handling
Deployment and testing
Documentation
```

Suggested generic domain model:

```text
Matter
 ├── Matter type: Conveyancing / Litigation / Municipal / Other
 ├── Parties
 ├── Documents
 ├── Extracted facts
 ├── Templates
 ├── Drafts
 ├── Review comments
 └── Final exports
```

---

## 20. Project form answers created

### Project Short Name

```text
Draftly
```

### Project Title

```text
Draftly: A Lawyer-in-the-Loop Legal Document Drafting and Review Platform for Sri Lankan Legal Workflows
```

or narrower:

```text
Draftly: A Lawyer-in-the-Loop Platform for Title Examination and Conveyancing Document Drafting in Sri Lanka
```

### Tentative project description

A concise version:

```text
Draftly is a Machine Learning + Software Engineering product that supports Sri Lankan lawyers in preparing repeated legal documents. Existing legal-tech platforms mainly focus on legal search, case law, and legislation access. Our focus is different: we aim to support the practical drafting and document-preparation workflow.

The system will allow lawyers or legal clerks to create a legal matter, enter structured client/case/property details, upload supporting documents, and generate lawyer-reviewable drafts using approved templates. The first use case will focus on conveyancing and title-documentation workflows, such as title reports, pedigrees, abstract of title deeds, ownership certificates, and assessor letters. The platform will be designed so that it can later support other legal drafting workflows such as complaints/plaints, affidavits, petitions, statements of objections, and legal notices.

The system will not provide final legal advice or replace lawyers. It will act as a lawyer-in-the-loop assistant that extracts key information, organizes facts, checks missing fields or inconsistencies, and generates editable drafts for lawyer review and approval.
```

### Tentative outputs

```text
1. Web-based legal matter management dashboard
2. Document upload and management module
3. OCR and information extraction pipeline for deed/title-related documents
4. Guided form interface for client, case, and property details
5. Template-based legal document generation module
6. Draft title report
7. Pedigree / chain-of-title view
8. Abstract of title deed
9. Certificate of ownership draft
10. Assessor / municipal ownership transfer letter
11. Missing-document checklist
12. Red-flag / inconsistency report
13. Lawyer review and approval workflow
14. Exportable DOCX/PDF drafts
15. Final documentation: SRS, architecture diagrams, DB design, API docs, testing report, deployment guide
```

---

## 21. Name exploration

Names considered:

```text
Law Desk AI
LegalDraft LK
LexDraft LK
DraftLaw LK
DeedFlow LK
TitleFlow LK
NotaryFlow LK
ConveyDraft LK
Lawra
Lexa
Notra
Drafter
Legora
Jura
Docura
Lexly
Notely
Drafta
Legis
Carta
Writly
Lawly
Notaro
```

The recommendation from the list was **Legora**, but the final user decision was:

# **Draftly**

Reasoning:

```text
Simple
Easy to remember
Broad enough for legal drafting
Not limited to conveyancing
Works for deeds, title reports, complaints, affidavits, petitions, notices, etc.
```

---

## 22. Email to Dr. Thanuja / lecturer about additional details

The user wanted an email after submitting the Google Form, to share additional details that did not fit in the form.

Final style: shorter paragraphs, bold important phrases, scan-friendly.

Core content:

```text
Subject: Additional Details on Draftly DSE Project Proposal

Dear Dr. Thanuja,

I hope you are doing well.

We have submitted our DSE project idea through the Google Form, but we wanted to share a few additional details that we could not fully include there.

Our proposed project is Draftly, a lawyer-in-the-loop legal document drafting and review platform for Sri Lankan legal workflows. The broader idea is to support lawyers in preparing repeated legal documents such as conveyancing documents, title reports, pedigrees, assessor letters, complaints/plaints, affidavits, petitions, statements of objections, and legal notices.

For the MVP/use case, we are planning to focus mainly on conveyancing and title-documentation workflows...
```

The user later wanted the ending not to ask for suitability directly, but to say:

```text
We have shared these additional details to give a clearer picture of the problem we are trying to solve, the validation we have done so far, and the intended project scope. We kindly request you to consider these points when reviewing our project idea for DSE.
```

---

## 23. Email/response to Dr. Nisansa’s concern

Dr. Nisansa replied:

```text
A considerable number of my students have worked in legal domain tasks.

Can you explain how this project would differ from template filling? Because legal IR, even though have been tried before, does have a novelty component that one can claim. No matter how good the other people's search engine is, one can always try to do better. In the proposed project, can you explain to me what would happen more than a person filling text boxes in a web page and a PDF is generated where 90% of the text is from template?

-regards
Nisansa de Silva, PhD
Department of Computer Science & Engineering,
Faculty of Engineering,
University of Moratuwa
```

### Full answer direction

The answer should:

1. Acknowledge the concern.
2. Agree that pure template filling is not enough.
3. Explain that template generation is only the final layer.
4. Give the AT form / Schedule example.
5. Explain document bundle processing, extraction, linking, chain construction, consistency checking, source evidence.
6. Mention evaluation beyond PDF generation.
7. Say scope can be narrowed to conveyancing/title-documentation.
8. Say you will read SigmaLaw papers.

### Important paragraphs developed

```text
Thank you very much for your feedback. Your concern is valid, and we understand that if the system only collects values through text boxes and fills a fixed PDF template, it would not be strong enough as an ML and Software Engineering project.

Our intended project is not limited to template filling. The template-based document generation will only be the final output layer. The main work we want to focus on is the earlier workflow: understanding uploaded legal/property documents, extracting structured information, linking related facts across documents, identifying inconsistencies, and then generating lawyer-reviewable drafts.
```

Then the AT/Schedule example:

```text
For example, when a lawyer prepares an Abstract of Title Deed / AT form or the Schedule to a new deed, the required information is usually not written from scratch. It is derived from previous deeds, survey plans, assessment records, and other supporting documents. Currently, this is mostly done manually, or sometimes by giving the documents to a broad/general-purpose LLM. Our idea is to streamline this process through a dedicated system that extracts the relevant legal and property facts, shows evidence from the source documents, allows the lawyer to verify or correct the extracted facts, and then generates the required draft documents.

In this use case, the system would not simply fill a fixed template from text boxes. It would process the uploaded document bundle, extract and link legal/property facts across the documents, build a chain-of-title/pedigree, highlight missing or inconsistent information, and generate lawyer-reviewable drafts such as title reports, AT forms, ownership certificates, assessor letters, and deed schedules.
```

Then the short evaluation paragraph:

```text
We agree that legal IR has a clearer novelty path. For our project, the evaluation can go beyond whether a PDF was generated. We can evaluate document classification accuracy, key-field extraction accuracy, chain-of-title construction, consistency-checking performance, and time saved compared to manual work. If needed, we can narrow the scope further to only the conveyancing/title-documentation workflow and treat other legal drafting types as future extensions.
```

Final line user wanted:

```text
Thank you again for pointing this out. We will also go through the papers under the SigmaLaw project to better understand the previous work in this area.
```

---

## 24. Project idea document reviewed

The user uploaded/pasted a project idea document titled:

```text
Draftly
A Lawyer-in-the-Loop Platform for Automated Title Examination and Conveyancing Document Drafting in Sri Lanka
Group 06
Himath N., De Silva B. K. P., Lahiru D.
Supervisor: Dr. Nisansa de Silva
In23-S5-CS3501 | Project Idea | Wednesday, 8 July 2026
Department of Computer Science and Engineering
University of Moratuwa, Sri Lanka
```

Sections included:

```text
1. Introduction
2. Proposed Solution
2.1 Research Novelty: Beyond Template Population
2.2 Key Features
2.3 System Architecture
2.4 Data Science Component
2.5 Software Engineering Component
2.6 Evaluation and Objectives
2.7 Demonstration at the Symposium
3. Datasets
4. Similar Projects
5. Scope and Team Responsibilities
```

### Review verdict

The document was judged:

```text
Strong idea-wise
Almost submission-ready
Good at answering the template-filling concern
Clear DS + SE components
Good symposium demo story
Slightly too ambitious / polished for a brief idea document
```

### Recommended edits

```text
1. Change “Supervisor” to “Proposed Supervisor” unless officially accepted.
2. Soften claims like “None of them...” to “Based on our preliminary review...”
3. Focus first demo on title report/pedigree/AT form; keep full deed drafting secondary.
4. Add bounded scope earlier: small number of deed types and bounded chain depth.
5. Add dataset annotation details: extracted entities, deed-to-deed links, party relationships, property/lot references, lawyer-verified final chain.
6. Shorten if submission expects “brief proposed solution.”
```

### Better title recommendation

Instead of:

```text
A Lawyer-in-the-Loop Platform for Automated Title Examination and Conveyancing Document Drafting in Sri Lanka
```

Use:

```text
Draftly: A Lawyer-in-the-Loop Platform for Title Examination and Conveyancing Document Drafting in Sri Lanka
```

Reason: “Automated title examination” may sound like replacing the lawyer, while “lawyer-in-the-loop” already conveys safety.

---

## 25. Project idea document key content

The introduction said:

```text
In Sri Lanka, conveyancing still depends heavily on manual work, but the hard part is not typing the final deed. Before any document can be drafted, a lawyer or notary must read a stack of prior deeds and reconstruct the chain of title: who owned the land, how it changed hands, how it was subdivided or amalgamated over the decades, and whether there are any breaks, competing claims or undischarged mortgages along the way.
```

Core one-line summary from the document:

```text
Draftly reads a client’s uploaded prior deeds, reconstructs and checks the chain of title, and produces reviewable draft documents for a lawyer to approve — automating the examination work, not just the final typing.
```

Key features:

```text
Information extraction from scanned, historical and code-mixed deeds
Chain-of-title reconstruction
Consistency and defect detection
Grounded, source-traceable draft generation
OCR
Lawyer review/editing workspace
Version history and audit trail
Approved-template management
Word/PDF export
```

Architecture layers:

```text
Document Processing Layer
Title Reasoning Layer
Drafting Layer
Review Workflow Layer
Web Application Layer
```

Team responsibilities:

```text
Document understanding — Data Science
Title reasoning — Data Science
Grounded drafting — Data Science / SE
Platform and review workflow — Software Engineering
```

---

## 26. LaTeX title block edit

User had:

```latex
{\normalsize
\textbf{Group 06}\\[0.3em]
Dhanapala D.H.N., Dilshan A.D.L., De Silva B.K.P.
}\\[0.1em]

{\normalsize
\textbf{Supervisor:} Dr. Nisansa de Silva\\[1em]
Department of Computer Science and Engineering\\
University of Moratuwa, Sri Lanka
}\\[0.8em]
```

Wanted to add teaching assistant Ovindu A.

Suggested version:

```latex
{\normalsize
\textbf{Group 06}\\[0.3em]
Dhanapala D.H.N., Dilshan A.D.L., De Silva B.K.P.
}\\[0.1em]

{\normalsize
\textbf{Supervisor:} Dr. Nisansa de Silva\\
\textbf{Teaching Assistant:} Ovindu A.\\[1em]
Department of Computer Science and Engineering\\
University of Moratuwa, Sri Lanka
}\\[0.8em]
```

Safer if supervisor not confirmed:

```latex
\textbf{Proposed Supervisor:} Dr. Nisansa de Silva\\
\textbf{Teaching Assistant:} Ovindu A.\\[1em]
```

If full name known, use:

```latex
\textbf{Teaching Assistant:} Ovindu Atukorala\\[1em]
```

---

## 27. Overleaf / repo / Codex discussion

The user asked whether ChatGPT can connect to Overleaf.

Answer:

```text
Cannot directly connect to Overleaf from here.
```

Ways to work:

```text
Download Overleaf ZIP and upload here
Paste specific .tex sections
Use GitHub sync and share repo link
Generate LaTeX here and copy-paste into Overleaf
```

The user also asked earlier whether ChatGPT/Codex can connect to repo to code this.

Answer direction:

```text
If user shares GitHub repo link, we can inspect structure and guide code changes.
Alternatively, generate a strong Codex/Cursor prompt.
Recommended repo structure:
deedflow-lk / draftly
  apps/
    web/
    api/
    ml-service/
  packages/
    shared/
  docs/
    srs.md
    architecture.md
    data-schema.md
  samples/
    README.md
  docker-compose.yml
  README.md
```

Suggested stack:

```text
Next.js + FastAPI + PostgreSQL
or React + FastAPI + PostgreSQL
```

MVP modules:

```text
Matter creation
Document upload
Document type selection
Guided form
Template-based draft generation
Title report generation
Pedigree/chain-of-title view
Export DOCX/PDF
```

---

## 28. Important privacy and dataset notes

The real documents contain sensitive information:

```text
Real names
NIC/passport information
Addresses
Assessment numbers
Deed numbers
Land registry references
Signatures
Stamps
Legal property data
```

Therefore:

```text
Do not publish raw documents on GitHub, Hugging Face, or public demo.
Use anonymized copies.
Replace names, NICs, addresses, deed numbers.
Blur signatures/stamps/faces.
Create synthetic versions that preserve structure.
For demo, use fake owners and fake deed chains.
```

Dataset plan:

```text
Collect anonymized historical deeds, title reports, survey plans, assessor letters, ownership certificates, and lawyer-approved templates from supporting practitioners.
Build annotated dataset with entities, relations, deed-to-deed links, title chain ground truth.
Use lawyer-verified chains as evaluation ground truth.
```

---

## 29. Symposium/exhibition demo plan

Best demo story:

```text
User creates a conveyancing/title matter.
User uploads historical deeds + survey plan + assessment document.
System classifies documents.
System extracts key fields.
System displays extracted facts with source evidence.
Lawyer corrects/approves.
System builds chain-of-title graph.
System flags missing documents or inconsistencies.
System generates draft title report + AT form + assessor letter.
User exports DOCX/PDF.
```

This gives a clear ML + SE demonstration.

---

## 30. Current state / decisions made

Final decisions:

```text
Project name: Draftly
Main scope: Lawyer-in-the-loop legal document drafting and review platform
Concrete use case: Conveyancing title documentation
Primary outputs: Title report, pedigree, AT form, certificate of ownership, assessor letter, deed schedule
Not just template filling: extraction + linking + title reasoning + consistency checking + lawyer review
Relationship to SigmaLaw: aligned legal NLP area, but focused on drafting/workflow automation
Use real documents only privately; anonymize for demo/dataset
```

---

## 31. Pending tasks / next steps

### Immediate

```text
Finalize reply to Dr. Nisansa explaining how Draftly differs from template filling.
Go through SigmaLaw papers.
Update project idea document based on feedback.
Change “Supervisor” to “Proposed Supervisor” if not confirmed.
Add Teaching Assistant line in LaTeX.
Soften claims about existing tools.
```

### Project document improvements

```text
Shorten if needed for “Project Idea” format.
Add bounded scope earlier.
Make dataset annotation plan more concrete.
Clarify that deed drafting is secondary to title-documentation outputs for first version.
Add data privacy/anonymization note.
```

### Technical planning

```text
Decide stack: Next.js + FastAPI + PostgreSQL recommended.
Create GitHub repo.
Create SRS.
Create architecture diagram.
Design database schema.
Design document upload and processing flow.
Prepare Codex prompt if coding with Codex/Cursor.
```

### Dataset / ML

```text
Anonymize sample documents.
Define label schema.
Annotate entities:
  - parties
  - deed numbers
  - dates
  - notaries
  - plan numbers
  - lot numbers
  - extents
  - boundaries
  - registration refs
Annotate deed-to-deed links.
Create lawyer-verified chain-of-title ground truth.
Build baseline extraction pipeline.
```

### Demo

```text
Create fake/anonymized property case.
Prepare 3–5 source documents:
  - previous deed
  - current deed/gift deed
  - survey plan
  - assessment record
  - registry/path-iru extract if available
Generate:
  - title report
  - pedigree
  - AT form
  - assessor letter
  - checklist/red-flag report
```

---

## 32. Final mental model for continuing

The most important framing to preserve:

> Draftly is not a form-filling PDF generator. It is a lawyer-in-the-loop system that turns an unstructured legal/property document bundle into a verified structured title record, checks that record, and generates multiple legal drafts from it.

Core pipeline:

```text
Documents → Extraction → Linking → Title graph → Checks → Lawyer verification → Drafts
```

Core differentiator:

```text
The output is not typed by the user into text boxes.
It is derived from uploaded deeds, plans, registry/assessment records, and verified source evidence.
```

Core first use case:

```text
Conveyancing title documentation:
AT form + Schedule to new deed + title report + pedigree + ownership certificate + assessor letter
```
