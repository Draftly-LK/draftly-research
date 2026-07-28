# Draftly Software Requirements Specification

**Project:** Draftly: A Lawyer-in-the-Loop Legal Practice Platform for Sri
Lankan Law

**Module:** In23-S5-CS3501 Data Science and Engineering Project

**Group:** 06

**Prepared by:** Dhanapala D.H.N., Dilshan A.D.L., De Silva B.K.P.

**Document version:** 0.3

**Date:** 29 July 2026

**Document identifier:** DRAFTLY-SRS-0.3

## Revision history

| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 28 Jul 2026 | 0.1 | Initial requirements draft | Group 06 |
| 28 Jul 2026 | 0.2 | Reframed the specification around the complete product and defined V0 to V3 release boundaries | Group 06 |
| 29 Jul 2026 | 0.3 | Defined Draftly as a notarial and conveyancing product and stated the V0 document-processing boundary | Group 06 |

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the required behaviour
and quality attributes of Draftly, a lawyer-in-the-loop platform for
Sri Lankan legal work. It describes the complete product direction and the
shared foundation on which successive releases will be built.

The first release, V0, is specified in the greatest detail because it is the
initial implementation and evaluation scope. V0 supports matters governed by
the Registration of Title Act, No. 21 of 1998 (RTA). Later releases extend the
same product to wider conveyancing and notarial work. The product name remains
Draftly across all releases; V0, V1, V2, and V3 are release identifiers rather
than separate products.

This document is intended for the project supervisors, evaluators, domain
experts, developers, testers, and future maintainers. It is the source against
which the software architecture, test plan, implementation, and evaluation
are to be traced.

### 1.2 Scope

Draftly is a matter-centred legal work platform. It helps a legal professional
turn an unstructured bundle of client documents into a verified matter record,
identify missing or conflicting information, find the governing Sri Lankan
legal authority, and prepare reviewable legal documents. Every consequential
fact and output remains subject to professional review.

The platform addresses a difficult part of legal work that occurs before a
document is signed: reading client-specific records, identifying the correct
facts, reconciling details across documents, locating the applicable law, and
transferring approved information into a draft without losing its source.
Draftly is therefore broader than a document template tool and broader than a
legal search service. Search and drafting are two capabilities within a
controlled matter environment.

V0 focuses on RTA matters because they provide a bounded but demanding first
case. The documents may be digital, scanned, photographed, typed, printed in
older formats, bilingual, or partly handwritten. Names, parcel identifiers,
extents, boundaries, title references, interests, and attestation particulars
must agree across several records. Human reading and repeated retyping make
this work slow and expose it to transcription and consistency errors.

V0 uses Google Cloud Document AI to perform OCR and document-quality analysis
for supported printed and clearly scanned documents. Handwriting, severe
degradation, blur, glare, damaged pages, and unsupported scripts may produce
unreliable output. They are explicit V0 limitations, not promised automatic
capabilities. The system retains those documents for lawyer review and manual
entry. Later releases may improve this boundary only after testing by document
class and language.

At the date of this SRS, the published Enterprise Document OCR language list
does not explicitly list Sinhala [23]. The Sinhala interface and Sinhala export
requirements do not imply reliable Sinhala source-document OCR. Sinhala source
documents are routed to lawyer review and manual entry unless a separately
tested processor is approved for that document class.

The release scope is:

| Release | Product scope | Status in this SRS |
| --- | --- | --- |
| V0 | Initial RTA matter workbench for examination of title, drafting, execution, and attestation; Google Document AI processing for supported documents; lawyer verification; checks; grounded research; approved RTA forms; export and audit | Current implementation and evaluation scope |
| V1 | Additional RTA document classes and forms, improved review tools, and tested expansion of difficult-document processing, including selected handwriting or degraded scans where measured quality is acceptable | Planned next release |
| V2 | Wider Sri Lankan conveyancing and notarial coverage, including deed registration, condominium and special-area requirements, historical title relationships where applicable, and broader checks and templates | Planned conveyancing expansion |
| V3 | Mature notarial and conveyancing platform capabilities, including richer collaboration, organisation knowledge, registry and office integrations, configurable legal content, operational reporting, and larger deployments | Planned product maturity |

All releases share five product rules:

1. Every extracted fact must retain a link to its source evidence.
2. Machine output is a candidate until an authorised legal professional
   verifies or approves it.
3. Legal claims must cite retrievable authority or the system must state that
   authority is insufficient.
4. A final draft may use only approved wording and verified matter facts.
5. Corrections, approvals, overrides, and exports must remain auditable.

V0 does not perform autonomous legal decision-making, give legal advice
directly to members of the public, replace a notary's statutory duties, submit
instruments for registration, or guarantee the legal validity of a matter. It
does not claim reliable automated reading of every handwritten or damaged
document. Unsupported material must be retained for human review and manual
entry rather than silently discarded.

### 1.3 Definitions, acronyms, and abbreviations

| Term | Definition |
| --- | --- |
| Approval | An explicit decision by an authorised lawyer that permits a draft or other controlled output to proceed |
| Audit event | An immutable record of a significant action, its actor, time, affected object, and reason where required |
| Bim Saviya | The Sri Lankan title-registration programme associated with the RTA |
| Candidate fact | Information extracted or suggested by the system but not yet verified by a lawyer |
| Conveyancing | Legal work connected with the transfer, ownership, interests, and registration of land or property |
| Evidence span | The page, region, text range, image area, or excerpt from which a fact or claim was obtained |
| Grounded answer | An answer whose legal claims are linked to retrievable supporting authority |
| Google Document AI | The external Google Cloud service selected for V0 OCR and document-quality analysis |
| Matter | A controlled legal work area containing the documents, people, facts, issues, authorities, drafts, decisions, and history for one engagement |
| OCR | Optical Character Recognition |
| Particular | A structured item of information required for a legal task or document, such as a party name, title number, or parcel extent |
| PDPA | Personal Data Protection Act, No. 9 of 2022 |
| Prescribed form | A form or instrument format required by legislation or an applicable gazette |
| RTA | Registration of Title Act, No. 21 of 1998 |
| Source authority | A statute, regulation, gazette, judgment, or other legally recognised source used to support a rule or answer |
| Verification | A lawyer's confirmation or correction of a candidate fact against its evidence |
| V0, V1, V2, V3 | Successive releases of the same Draftly product |

### 1.4 References

The following external sources inform this specification. Web sources were
last accessed on 28 July 2026.

[1] Parliament of the Democratic Socialist Republic of Sri Lanka,
"Registration of Title Act, No. 21 of 1998," 1998. [Online]. Available:
<https://documents.gov.lk/view/act/1998/4/21-1998_E.pdf>.

[2] Registrar General's Department, Sri Lanka, "Registration of subsequent
transactions relating to title certificates," 2026. [Online]. Available:
<https://www.rgd.gov.lk/web/index.php/en/services/document-land-registration/title/transactions>.

[3] Government of Sri Lanka, "Gazette Extraordinary No. 2308/27,"
1 December 2022. [Online]. Available:
<https://rgd.gov.lk/web/images/ActsPDF/title/2308-27_E.pdf>.

[4] Parliament of the Democratic Socialist Republic of Sri Lanka,
"Notaries (Amendment) Act, No. 31 of 2022," 2022. [Online]. Available:
<https://documents.gov.lk/view/acts/2022/10/31-2022_E.pdf>.

[5] Parliament of the Democratic Socialist Republic of Sri Lanka,
"Notaries (Amendment) Act, No. 6 of 2024," 2024. [Online]. Available:
<https://documents.gov.lk/view/act/2024/1/06-2024_E.pdf>.

[6] Parliament of the Democratic Socialist Republic of Sri Lanka,
"Personal Data Protection Act, No. 9 of 2022," 2022. [Online]. Available:
<https://www.documents.gov.lk/view/act/2022/3/09-2022_E.pdf>.

[7] Parliament of the Democratic Socialist Republic of Sri Lanka,
"Electronic Transactions Act, No. 19 of 2006," 2006. [Online]. Available:
<https://documents.gov.lk/view/act/2006/5/19-2006_E.pdf>.

[8] ISO, "ISO/IEC/IEEE 29148:2018, Systems and software engineering, Life
cycle processes, Requirements engineering," 2018, confirmed 2024. [Online].
Available: <https://www.iso.org/standard/72089.html>.

[9] World Wide Web Consortium, "Web Content Accessibility Guidelines
(WCAG) 2.2," W3C Recommendation, 12 December 2024. [Online]. Available:
<https://www.w3.org/TR/WCAG22/>.

[10] Harvey, "Getting Started with Harvey," 2026. [Online]. Available:
<https://help.harvey.ai/articles/getting-started-with-harvey>.

[11] Harvey, "Assistant," 2026. [Online]. Available:
<https://www.harvey.ai/platform/assistant>.

[12] Legora, "Portal: AI-native workspace for law firms and in-house teams,"
2026. [Online]. Available: <https://legora.com/product/portal>.

[13] Thomson Reuters, "CoCounsel Legal," 2026. [Online]. Available:
<https://legal.thomsonreuters.com/en/products/cocounsel-legal>.

[14] LexisNexis, "Lexis+ with Protege: Legal AI solution for drafting and
research," 2026. [Online]. Available:
<https://www.lexisnexis.com/en-us/products/lexis-plus-ai.page>.

[15] LawLanka, "Sri Lanka Acts and Case Laws," 2026. [Online]. Available:
<https://www.lawlanka.com/>.

[16] AI Pazz, "AI-powered Sri Lanka legal research platform," 2026. [Online].
Available: <https://www.aipazz.com/>.

[17] Paralegal.lk, "A search engine for Sri Lankan law," 2026. [Online].
Available: <https://www.paralegal.lk/>.

[18] LawCeylon, "Sri Lanka Acts, Laws and Case Law Reports System," 2026.
[Online]. Available: <https://lawceylon.lk/>.

[19] C. Samarawickrama, M. de Almeida, N. de Silva, G. Ratnayaka, and
A. S. Perera, "Party Identification of Legal Documents using Co-reference
Resolution and Named Entity Recognition," in *2020 IEEE 15th International
Conference on Industrial and Information Systems*, 2020, pp. 494-499,
doi: 10.1109/ICIIS51140.2020.9342720.

[20] K. Sugathadasa, B. Ayesha, N. de Silva, A. S. Perera,
V. Jayawardana, D. Lakmal, and M. Perera, "Legal Document Retrieval using
Document Vector Embeddings and Deep Learning," in *Intelligent Computing*,
2018, pp. 160-175, doi: 10.1007/978-3-030-01177-2_12.

[21] P. Lewis et al., "Retrieval-Augmented Generation for
Knowledge-Intensive NLP Tasks," in *Advances in Neural Information Processing
Systems 33*, 2020. [Online]. Available:
<https://papers.neurips.cc/paper_files/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html>.

[22] Y. Huang, T. Lv, L. Cui, Y. Lu, and F. Wei, "LayoutLMv3:
Pre-training for Document AI with Unified Text and Image Masking," in
*Proceedings of the 30th ACM International Conference on Multimedia*, 2022,
pp. 4083-4091, doi: 10.1145/3503161.3548112.

[23] Google Cloud, "Document AI processor list," 2026. [Online]. Available:
<https://docs.cloud.google.com/document-ai/docs/processors-list>.

[24] Google Cloud, "Document AI supported files and document scan resolution,"
2026. [Online]. Available:
<https://docs.cloud.google.com/document-ai/docs/file-types>.

[25] Google Cloud, "Document AI security and compliance," 2026. [Online].
Available:
<https://docs.cloud.google.com/document-ai/docs/security>.

### 1.5 Document overview

Section 2 explains the product context, the problem, user groups, product
family, constraints, and dependencies. Section 3 states the functional and
non-functional requirements. Section 4 defines V0 acceptance criteria,
traceability expectations, and matters that require later confirmation.

## 2. Overall description

### 2.1 Product perspective

Draftly is one notarial and conveyancing product with a shared matter model.
Its releases use the same controlled foundation for documents, evidence,
verified facts, legal authority, review, drafting, permissions, and audit.

The product is intended to complement legal research services and ordinary
office software. Research services help users find law. Word processors help
users write. Document-management systems store files. Draftly connects these
activities to a specific matter and preserves the evidence and professional
decisions that support the resulting work.

V0 is the first release of this product family. It applies the common
foundation to RTA matters and establishes whether the core approach works
under a clear legal boundary. Later releases reuse the foundation for wider
conveyancing regimes and notarial tasks.

### 2.2 Problem context

Sri Lankan notarial and conveyancing work frequently begins with records that
were not created for machine processing. A matter may contain scanned deeds,
photographs of pages, forms, certificates, plans, identity records,
correspondence, and handwritten additions. The documents may mix Sinhala and
English, contain older terminology, or have poor image quality.

The legal professional must identify facts, compare them across documents,
understand their legal effect, and prepare an output. In RTA conveyancing, a
small mismatch in a name, title number, parcel identifier, extent, boundary,
registered interest, or attestation particular can stop a transaction or
require further evidence.

General-purpose AI can produce fluent text but cannot be treated as an
authority or as a verifier of client facts. Draftly therefore separates
candidate machine output from lawyer-approved information and makes evidence
inspection part of the product.

### 2.3 Product objectives

Draftly is intended to:

- reduce repeated manual reading and retyping while preserving lawyer control;
- create a structured and evidence-linked record of each matter;
- identify missing, inconsistent, or unsupported information before drafting;
- provide access to applicable Sri Lankan authority with pinpoint evidence;
- prepare editable outputs from approved content and verified facts;
- preserve review, correction, approval, and export history;
- support Sinhala and English legal work;
- remain extensible across conveyancing regimes and notarial tasks without
  weakening the common verification and audit rules; and
- measure document processing, retrieval, checking, and drafting performance
  against lawyer-reviewed data.

### 2.4 Major product functions

Across the product family, Draftly provides:

- secure accounts, roles, organisations, and matter access;
- matter creation and document organisation;
- Google Document AI processing of supported digital, printed, scanned, and
  photographed documents;
- document classification and structured information extraction;
- source-linked lawyer verification and correction;
- cross-document entity and fact linking;
- missing-evidence and consistency checks;
- grounded search and question answering over Sri Lankan legal sources;
- approved-template drafting from verified information;
- lawyer review, versioning, approval, and export;
- history, audit, content governance, and system administration;
- bilingual interaction and accessible use; and
- release-specific conveyancing and notarial capabilities.

### 2.5 Product evolution

#### 2.5.1 V0: initial RTA release

V0 covers examination of title, drafting, execution, and attestation for
supported RTA matters. It starts with common transactions under the prescribed
RTA forms and supports the verified particulars required for those
transactions. Registration itself remains outside V0 because submission to
the public authority introduces additional legal, procedural, and integration
requirements.

V0 accepts the documents available to the lawyer, reports what is missing,
extracts what it can read, and exposes uncertainty. It must not require the
lawyer to pretend that an unreadable document was successfully processed.
Manual transcription and verification remain valid completion paths.

#### 2.5.2 V1: expanded conveyancing

V1 is planned to add RTA document classes and forms and improve the review of
difficult source material. It may support selected handwriting or degraded
scans only where testing shows acceptable results for the relevant document
class and language. Material outside the tested boundary will continue to use
manual review and entry.

#### 2.5.3 V2: wider conveyancing and notarial coverage

V2 is planned to broaden the legal regimes and instruments supported by the
same matter foundation. Expected areas include deed registration, condominium
property, special-area requirements, historical title relationships where
legally relevant, and additional notarial instruments, checks, and templates.

#### 2.5.4 V3: mature notarial and conveyancing platform

V3 is planned to support wider adoption across notarial and conveyancing
practices. Likely areas include organisation knowledge, richer collaboration,
configurable legal content, integrations with registry, document, and office
systems, client or external spaces with controlled access, operational
reporting, and larger deployment capacity.

### 2.6 Existing systems and product position

Publicly documented legal technology shows several established product
patterns:

| System group | Publicly documented emphasis | Relevance to Draftly |
| --- | --- | --- |
| LawLanka, Paralegal.lk, and LawCeylon | Sri Lankan legislation, judgments, legal reports, and search [15], [17], [18] | Confirms demand for accessible Sri Lankan legal information. Draftly places that research inside a client-matter environment rather than treating search as the complete product |
| AI Pazz | Sri Lankan legal research and general AI-assisted research and drafting [16] | Provides a relevant local comparison. Draftly's distinct focus is evidence from a client's matter documents, lawyer-verified facts, RTA-specific checks and forms, and controlled approval history |
| Harvey | Assistant, persistent document collections, review tables, reusable legal tasks, drafting, history, citations, and organisation controls [10], [11] | Shows the value of persistent context, source inspection, structured review, and editable work product |
| Legora | Shared legal workspace, document review, grounded answers, editing, and controlled collaboration [12] | Shows how document analysis and collaboration can remain connected to the work product |
| CoCounsel Legal | Research, analysis, and drafting grounded in Westlaw, Practical Law, organisation knowledge, and matter workspaces [13] | Shows the importance of authoritative sources and matter continuity |
| Lexis+ with Protege | Legal research, drafting, analysis, source verification, and secure document collections built around LexisNexis content [14] | Shows the value of combining legal authority, internal documents, drafting, and verification |

Draftly does not attempt to copy the branding or interface of these products.
Its product position is specific to Sri Lankan practice: bilingual
client-document understanding, local legal authority, evidence-linked
verification, RTA and later Sri Lankan conveyancing and notarial rules, and
lawyer approval before use.

The comparison is based only on public product information. It is not a
procurement assessment and does not claim access to non-public product
behaviour.

### 2.7 User classes and characteristics

| User class | Characteristics and responsibilities | Earliest release |
| --- | --- | --- |
| Lawyer or notary | Owns the matter, verifies facts, resolves legal issues, approves wording and outputs, and remains professionally responsible | V0 |
| Legal clerk or assistant | Uploads and organises documents, enters data, prepares candidate work, and responds to missing-information requests; cannot give final legal approval | V0 |
| Senior reviewer | Reviews important findings and drafts, approves controlled outputs, and inspects evidence and history | V0 |
| Legal content maintainer | Maintains approved source mappings, rules, templates, terminology, and version dates under domain-expert control | V0 |
| Administrator | Manages accounts, roles, organisation settings, security policy, and service configuration; cannot silently alter lawyer-approved legal content | V0 |
| External collaborator or client | Receives limited, permission-controlled access to selected files or work products | V3 |
| Auditor or compliance reviewer | Reviews immutable access and decision records without changing matter content | V3 |

Users may work primarily in English, Sinhala, or both. Legal users are not
assumed to have technical training. The interface must support careful review
rather than optimise only for speed.

### 2.8 Operating environment

V0 is intended to operate as a secure browser-based application on current
desktop versions of major browsers and to support common office document and
image formats used in legal practice. Server-side processing may run in an
approved cloud or controlled self-hosted environment, subject to the privacy
requirements in Section 3.5.

Mobile and tablet access may support document capture and review, but V0
approval and full drafting are desktop-priority tasks. Later releases may
expand mobile support after usability and security testing.

### 2.9 Constraints

- Legal responsibility remains with the qualified professional.
- No legal rule, prescribed wording, or Sinhala legal term may be activated
  without authorised human review.
- V0 is limited to selected RTA matters and supported document types.
- Google Document AI is the selected V0 OCR and quality-analysis service
  [23]-[25].
- Reliable automatic extraction from handwriting, severely degraded scans,
  and unsupported scripts is outside the V0 capability boundary.
- Material outside that boundary must remain available for lawyer review and
  manual entry.
- Client documents contain confidential and personal data.
- External AI, OCR, translation, or speech providers may be used only when
  their data handling satisfies the approved privacy policy.
- The system must distinguish legal authority from client evidence and from
  machine-generated suggestions.
- Future releases must preserve the verification, grounding, approval, and
  audit rules established in V0.

### 2.10 Assumptions and dependencies

- Domain experts will approve the V0 matter schema, rules, terminology, forms,
  evaluation labels, and acceptance decisions.
- Official and lawfully accessible legal sources will remain available for
  the supported functions.
- Demonstration and evaluation data will be synthetic, anonymised, or used
  with documented permission.
- Users will have lawful authority to upload and process the matter documents
  they provide.
- External-service availability and cost may change; critical matter data must
  remain exportable and recoverable without dependence on one provider.
- Google Document AI must remain available in an approved processing region
  and satisfy the privacy controls in Section 3.5.
- Each later release will define its detailed scope and acceptance tests before
  implementation.

## 3. Specific requirements

### 3.1 Functionality

Requirement statements use "shall" for mandatory behaviour. Each requirement
is tagged with the earliest planned release. A later release inherits all
applicable earlier requirements unless an approved change replaces them.

#### 3.1.1 Identity, roles, and access

- **FR-01 [V0]:** The system shall authenticate every user before displaying
  confidential matter information.
- **FR-02 [V0]:** The system shall authorise each matter action by role and
  explicit matter membership.
- **FR-03 [V0]:** A legal clerk may prepare matter content but shall not verify
  a legal fact or approve a final output unless separately authorised as a
  lawyer.
- **FR-04 [V0]:** The system shall record account creation, deactivation,
  role changes, and matter-access changes as audit events.
- **FR-05 [V0]:** An unauthorised request shall reveal neither matter content
  nor the existence of private documents.
- **FR-06 [V3]:** The system shall support organisation-level policies,
  ethical walls, delegated administration, and external access with expiry.

#### 3.1.2 Matter management

- **FR-07 [V0]:** An authorised user shall be able to create, open, archive,
  and resume a matter.
- **FR-08 [V0]:** A matter shall record its legal area, governing regime,
  transaction or instrument type, parties, responsible professionals, status,
  and privacy-safe reference.
- **FR-09 [V0]:** The system shall show the known information, missing
  evidence, unresolved conflicts, pending reviews, available drafts, and
  recent activity for a matter.
- **FR-10 [V0]:** Matter state shall survive sign-out, browser closure, and
  interruption without loss of verified information or approval history.
- **FR-11 [V0]:** The user shall be able to search and filter assigned matters
  without exposing matters outside that user's authority.
- **FR-12 [V2]:** A matter shall additionally record relevant prior
  instruments, historical title relationships, registration references,
  condominium or special-area particulars, and other regime-specific
  information where applicable.

#### 3.1.3 Document intake and preservation

- **FR-13 [V0]:** The system shall accept supported digital documents, scans,
  photographs, and image files individually or in a batch.
- **FR-14 [V0]:** Each uploaded document shall receive a stable identifier,
  version, uploader, timestamp, detected language, and processing status.
- **FR-15 [V0]:** Replacing a document shall create a new version and preserve
  the earlier version in the audit history.
- **FR-16 [V0]:** The system shall identify unreadable, incomplete, duplicate,
  password-protected, corrupt, or unsupported files and provide a recovery
  action.
- **FR-17 [V0]:** A processing failure shall not remove the original upload.
- **FR-18 [V0]:** The system shall allow manual classification and manual data
  entry when automatic processing is unavailable or unreliable.
- **FR-19 [V1]:** The system shall evaluate selected handwriting,
  degraded-scan, and legacy-format classes separately. Automated support shall
  be enabled only for a class and language that passes its approved accuracy
  and safety tests.

#### 3.1.4 Document classification and extraction

- **FR-20 [V0]:** The system shall classify each supported document into an
  approved document class and display the detected class for confirmation.
- **FR-21 [V0]:** The system shall extract approved particulars only when the
  document class and language are included in the approved V0 support matrix;
  other documents shall route to manual review and entry.
- **FR-22 [V0]:** Every candidate fact shall include its extracted value,
  extraction method, confidence or quality indicator, and at least one evidence
  span.
- **FR-23 [V0]:** The system shall preserve the original script and wording of
  an extracted value; normalised values shall be stored separately.
- **FR-24 [V0]:** The system shall not mark a low-confidence or handwritten
  value as verified merely because extraction completed.
- **FR-25 [V0]:** The system shall report when a required value was not found.
- **FR-26 [V1]:** Extraction coverage shall be configurable by legal regime,
  document class, language, and approved model version.

#### 3.1.5 Evidence-linked verification

- **FR-27 [V0]:** A user reviewing a candidate fact shall be able to open the
  supporting document at the relevant page or image region.
- **FR-28 [V0]:** Verification states shall distinguish at minimum
  unreviewed, verified, corrected, conflicting, and blocked information.
- **FR-29 [V0]:** Only an authorised lawyer shall be able to assign verified
  or corrected status to a fact used in a final legal output.
- **FR-30 [V0]:** A correction shall preserve the extracted value, corrected
  value, reviewer, time, reason where required, and evidence.
- **FR-31 [V0]:** Conflicting values from different documents shall remain
  visible until a lawyer resolves or formally accepts the conflict.
- **FR-32 [V0]:** A manual fact shall record its author, reason, and source
  note or missing-source status.
- **FR-33 [V0]:** Batch verification shall be allowed only after the user has
  been shown the affected facts and their evidence.

#### 3.1.6 Structured matter record

- **FR-34 [V0]:** The system shall maintain a structured RTA matter record
  covering the current title, parcel, parties, current instrument, registered
  interests or encumbrances, supporting evidence, and required particulars.
- **FR-35 [V0]:** The system shall link references to the same person, parcel,
  title, plan, instrument, or organisation while preserving the original
  values from each source.
- **FR-36 [V0]:** The system shall distinguish current verified information
  from historical, superseded, disputed, and unverified information.
- **FR-37 [V0]:** Deleting or replacing a document shall prevent that version
  from supplying new output while retaining its historical references.
- **FR-38 [V1]:** The matter record shall support approved historical title
  relationships and additional conveyancing regimes without changing the
  identity of existing evidence or audit events.
- **FR-39 [V2]:** The common matter record shall support additional
  conveyancing regimes and notarial instrument types without weakening
  evidence, verification, approval, or audit controls.

#### 3.1.7 Matter guidance and legal tasks

- **FR-40 [V0]:** The system shall organise V0 matter activity around
  examination of title, drafting, execution, and attestation.
- **FR-41 [V0]:** For each supported task, the system shall present the
  required information, missing evidence, applicable approved authority, open
  findings, and available user decisions.
- **FR-42 [V0]:** The system shall not require users to tick a generic intake
  checklist before documents are accepted. It shall accept available
  documents and report what remains missing.
- **FR-43 [V0]:** A mandatory blocked task shall require new evidence or an
  authorised override with a recorded reason.
- **FR-44 [V0]:** Task definitions, legal anchors, applicability conditions,
  and allowed decisions shall be versioned and approved by an authorised
  content maintainer.
- **FR-45 [V2]:** Wider conveyancing support shall organise title
  investigation, authority and capacity, instrument preparation, execution,
  attestation, and registration-readiness requirements for each approved
  regime.

#### 3.1.8 Checks and missing evidence

- **FR-46 [V0]:** The system shall evaluate approved deterministic checks over
  verified or explicitly selected matter information.
- **FR-47 [V0]:** V0 checks shall cover required-document completeness, party
  identity and capacity, title and parcel references, cadastral and plan
  details, extent and boundary consistency, current instrument particulars,
  interests or encumbrances, form selection, execution evidence, and
  attestation completeness where applicable.
- **FR-48 [V0]:** Each finding shall identify its type, severity, affected
  facts, supporting evidence, applicable authority or business rule, status,
  and responsible user.
- **FR-49 [V0]:** The system shall distinguish a failed check from a check
  that could not run because information is missing.
- **FR-50 [V0]:** A lawyer may resolve, accept, or override a finding only
  through an explicit action that records the decision and reason.
- **FR-51 [V0]:** A machine-generated suggestion shall not create a legal
  finding unless an approved deterministic rule supports it.
- **FR-52 [V1]:** The check catalogue shall expand by conveyancing regime and
  effective legal date.
- **FR-53 [V2]:** Checks shall support approved deed-registration,
  condominium, special-area, historical-title, and instrument-specific
  requirements included in the V2 scope.

#### 3.1.9 Legal search and grounded assistance

- **FR-54 [V0]:** The system shall search an approved corpus of Sri Lankan
  statutes, amendments, gazettes, and case-law material.
- **FR-55 [V0]:** A user shall be able to search independently or within the
  context of an authorised matter.
- **FR-56 [V0]:** Each legal claim in a generated answer shall link to
  retrievable supporting text and identify the source.
- **FR-57 [V0]:** The user shall be able to inspect the exact cited passage
  without losing the question or answer context.
- **FR-58 [V0]:** The system shall distinguish binding, persuasive,
  historical, repealed, superseded, and unverified candidate authority where
  that status is known.
- **FR-59 [V0]:** If available evidence does not support all or part of an
  answer, the unsupported part shall be withheld and labelled as insufficient
  authority.
- **FR-60 [V0]:** An extracted case rule shall remain marked unverified until
  a qualified reviewer approves it for use.
- **FR-61 [V0]:** The system shall never present model confidence as legal
  correctness or authority.
- **FR-62 [V0]:** Search and answering shall preserve the difference between
  public legal authority and confidential matter evidence.
- **FR-63 [V2]:** Conveyancing research shall organise authority by legal
  regime, transaction or instrument type, and effective date, with citations
  suitable for lawyer review.

#### 3.1.10 Draft preparation and templates

- **FR-64 [V0]:** The system shall prepare supported RTA instruments and
  related work products from approved templates.
- **FR-65 [V0]:** The approved transfer form shall be the first supported V0
  transaction for evaluation. Any additional RTA form shall require separate
  domain approval and acceptance tests.
- **FR-66 [V0]:** Prescribed or approved legal wording shall be protected from
  unauthorised alteration.
- **FR-67 [V0]:** Matter particulars inserted by the system shall reference
  verified or corrected facts.
- **FR-68 [V0]:** The system shall block approval while a mandatory
  placeholder, unresolved required fact, or blocking finding remains.
- **FR-69 [V0]:** The user shall be able to inspect the source of a
  system-inserted fact from the draft.
- **FR-70 [V0]:** Every saved draft version shall preserve its content,
  template version, linked facts, author, and timestamp.
- **FR-71 [V0]:** The user shall be able to compare versions and restore an
  earlier version without deleting intervening history.
- **FR-72 [V1]:** The template catalogue shall expand to additional
  conveyancing regimes and outputs under versioned domain approval.
- **FR-73 [V2]:** The template catalogue shall support approved
  deed-registration, condominium, special-area, and other notarial or
  conveyancing instruments while preserving source links and lawyer control.

#### 3.1.11 Review, approval, and export

- **FR-74 [V0]:** Only an authorised lawyer shall be able to give final
  approval to a legal draft.
- **FR-75 [V0]:** Approval shall record the approver, version, time, and
  outstanding non-blocking warnings.
- **FR-76 [V0]:** Any edit after approval shall create a new unapproved
  version.
- **FR-77 [V0]:** Approved work products shall be exportable to common office
  and fixed-layout formats.
- **FR-78 [V0]:** An export shall identify the approved version and shall not
  expose internal confidence scores, private system notes, or hidden
  placeholders.
- **FR-79 [V0]:** Sinhala and English text shall render correctly in exported
  documents.
- **FR-80 [V0]:** Export does not constitute execution, attestation, filing,
  or registration unless a later approved integration explicitly supports
  that act.

#### 3.1.12 History, audit, and content governance

- **FR-81 [V0]:** The system shall keep an append-only audit history for
  uploads, processing runs, fact changes, verification, findings, overrides,
  legal-source use, drafts, approvals, exports, permissions, and approved
  content changes.
- **FR-82 [V0]:** An audit event shall identify the actor, action, object,
  time, and before-and-after references where applicable.
- **FR-83 [V0]:** Ordinary users shall not be able to edit or delete audit
  events.
- **FR-84 [V0]:** Legal rules, source mappings, terminology, and templates
  shall have draft, reviewed, active, suspended, and retired states.
- **FR-85 [V0]:** Activating or retiring controlled legal content shall
  require an authorised user and shall create an audit event.
- **FR-86 [V0]:** A legal-content version shall record its effective date and
  the authority or approval on which it depends.
- **FR-87 [V3]:** Organisation administrators shall be able to configure
  controlled content and retention policy without changing immutable matter
  history.

#### 3.1.13 Language and communication

- **FR-88 [V0]:** The supported V0 path shall provide English and Sinhala
  interface text.
- **FR-89 [V0]:** The system shall preserve source-language text and shall
  label translated content as a translation.
- **FR-90 [V0]:** Sinhala legal terminology used in controlled content shall
  require domain review.
- **FR-91 [V1]:** If voice dictation or playback is included, it shall be
  enabled only for tasks that pass language-specific accuracy, privacy, and
  usability tests.
- **FR-92 [V3]:** Notifications and external sharing shall minimise personal
  information and respect matter permissions.

#### 3.1.14 Collaboration and integrations

- **FR-93 [V1]:** Authorised users shall be able to assign reviews, add
  comments, and record requests for missing documents within a matter.
- **FR-94 [V1]:** Collaboration shall preserve the distinction between a
  comment, a candidate fact, a verified fact, and an approved legal decision.
- **FR-95 [V3]:** External document, email, office, registry, or practice
  systems shall connect through authenticated and auditable interfaces.
- **FR-96 [V3]:** An integration failure shall not corrupt the matter record or
  bypass approval controls.
- **FR-97 [V3]:** The system shall support controlled export of organisation
  knowledge without exposing one client's confidential matter to another.

### 3.2 Usability

- **USE-01 [V0]:** A new legal user shall be able to create a matter, upload a
  small document set, identify processing status, and begin verification
  within 15 minutes using on-screen guidance.
- **USE-02 [V0]:** Evidence for a fact, finding, legal claim, or inserted draft
  value shall be reachable in no more than two user actions.
- **USE-03 [V0]:** The interface shall use consistent names and states across
  documents, facts, findings, legal sources, and drafts.
- **USE-04 [V0]:** Legally significant actions such as verification,
  override, approval, and export shall use explicit labels and confirmation
  where reversal is not immediate.
- **USE-05 [V0]:** Error messages shall state what failed, what information was
  preserved, and what the user can do next.
- **USE-06 [V0]:** The core V0 path shall conform to WCAG 2.2 Level AA [9],
  including keyboard operation, visible focus, sufficient contrast, labelled
  controls, status not conveyed by colour alone, and support at 200 percent
  zoom.
- **USE-07 [V0]:** English and Sinhala layouts shall remain usable without
  clipped text or hidden actions.
- **USE-08 [V0]:** A dashboard summary or conversational answer shall not be
  the only way to inspect evidence, verification state, legal authority, or
  approval state.

### 3.3 Reliability and availability

- **REL-01 [V0]:** No accepted upload, verified fact, correction, approval, or
  audit event shall be lost after the system confirms completion.
- **REL-02 [V0]:** Long-running document processing shall be resumable or
  safely repeatable after interruption.
- **REL-03 [V0]:** Repeated submission of the same processing request shall not
  create conflicting duplicate records.
- **REL-04 [V0]:** Failure of an OCR, search, translation, speech, or language
  service shall produce a visible reduced-capability state and a recovery
  option.
- **REL-05 [V0]:** Failure of a generative component shall never cause an
  uncited answer or unverified fact to be treated as approved.
- **REL-06 [V0]:** Backups shall preserve matter data, controlled content, and
  audit history, and restoration shall be tested before external evaluation.
- **REL-07 [V0]:** Critical defects include cross-matter disclosure, silent
  data loss, corrupted evidence links, approval bypass, invented authority
  presented as valid, and export containing unverified mandatory facts.
- **REL-08 [V3]:** Production availability and disaster-recovery targets shall
  be defined from deployment and client requirements before V3 release.

### 3.4 Performance

- **PERF-01 [V0]:** Excluding file processing and answer generation, 95 percent
  of ordinary page and matter operations shall respond within two seconds on
  the reference deployment.
- **PERF-02 [V0]:** A legal search shall return its first result page within
  three seconds under the reference test load.
- **PERF-03 [V0]:** A generated grounded answer shall show progress and either
  complete, partially answer, fail, or abstain within 60 seconds under the
  reference test configuration.
- **PERF-04 [V0]:** Upload acceptance shall be acknowledged within two seconds;
  document processing may continue asynchronously with visible per-document
  status.
- **PERF-05 [V0]:** A typical V0 matter set of up to 15 supported documents
  shall reach review or an explicit failure state within 10 minutes on the
  reference processing environment.
- **PERF-06 [V0]:** Performance tests shall report the hardware, network,
  document sizes, concurrency, and percentile used for each result.
- **PERF-07 [V3]:** V3 capacity targets shall be defined from measured
  organisation usage rather than extrapolated from V0 measurements alone.

### 3.5 Security and privacy

- **SEC-01 [V0]:** All client-to-server communication shall use encrypted
  transport.
- **SEC-02 [V0]:** Confidential data, backups, and stored documents shall be
  encrypted at rest in the approved deployment.
- **SEC-03 [V0]:** Access control shall be enforced on the server for every
  matter and document request.
- **SEC-04 [V0]:** Authentication secrets, service credentials, and encryption
  keys shall not be stored in source code, client-visible data, or ordinary
  logs.
- **SEC-05 [V0]:** Logs, analytics, notifications, screenshots, and error
  reports shall exclude raw identity numbers, signatures, complete addresses,
  and unnecessary client-document content.
- **SEC-06 [V0]:** Development and demonstration environments shall not use
  identifiable client documents.
- **SEC-07 [V0]:** External processing shall transmit only the minimum content
  required for the approved purpose.
- **SEC-08 [V0]:** Where an external provider supports data-retention or model
  training controls, the most restrictive available settings shall be used
  for client data.
- **SEC-09 [V0]:** The system shall record the provider, purpose, time, and
  matter reference for external processing of confidential content.
- **SEC-10 [V0]:** The system shall support retention periods, lawful deletion,
  access review, and export revocation appropriate to the applicable PDPA
  obligations and policies in force at deployment [6].
- **SEC-11 [V0]:** Automated tests shall verify cross-matter isolation,
  permission enforcement, upload validation, approval gates, and protection
  against common web vulnerabilities.
- **SEC-12 [V3]:** Organisation deployments shall support stronger identity,
  audit, key-management, and network controls where required by the client.

### 3.6 Legal-output safety and accuracy

- **SAFE-01 [V0]:** The system shall identify its outputs as drafts for
  professional review until an authorised lawyer approves them.
- **SAFE-02 [V0]:** The system shall not represent itself as a lawyer or offer
  final legal advice directly to the public.
- **SAFE-03 [V0]:** A legal answer without sufficient retrievable authority
  shall be withheld in full or in part.
- **SAFE-04 [V0]:** A factual statement about a client matter shall not be
  treated as verified solely because a model generated or extracted it.
- **SAFE-05 [V0]:** Prescribed wording shall be activated only after comparison
  with an authoritative source and approval by the responsible domain expert.
- **SAFE-06 [V0]:** Legal rules and forms shall be versioned by effective date
  so that a later change does not silently rewrite earlier matter history.
- **SAFE-07 [V0]:** Evaluation shall report false positives, false negatives,
  abstentions, unsupported claims, and lawyer disagreements rather than a
  single aggregate accuracy score.
- **SAFE-08 [V0]:** Any invented citation, materially unsupported legal claim,
  cross-matter disclosure, or mandatory unverified fact in an approved export
  shall be treated as a release-blocking failure.

### 3.7 Supportability and maintainability

- **SUP-01 [V0]:** The system shall separate user interface, matter services,
  document processing, legal retrieval, controlled legal content, and storage
  through documented interfaces.
- **SUP-02 [V0]:** Data exchanged between components shall be validated against
  versioned schemas.
- **SUP-03 [V0]:** Legal rules, templates, terminology, and source mappings
  shall be maintainable as controlled content without requiring application
  code changes for ordinary updates.
- **SUP-04 [V0]:** Each deterministic check shall have positive, negative,
  missing-input, and boundary tests.
- **SUP-05 [V0]:** Automated tests shall cover critical access, verification,
  citation, approval, versioning, and export controls.
- **SUP-06 [V0]:** A deployment shall record application version, controlled
  content version, model or service version where relevant, and database
  migration version.
- **SUP-07 [V0]:** System monitoring shall detect failed processing jobs,
  service errors, storage problems, and unusual access without recording
  unnecessary client content.
- **SUP-08 [V1]:** New conveyancing regimes and notarial instrument types
  shall extend the common matter, evidence, approval, and audit contracts
  rather than bypass them.

### 3.8 Design constraints

- **DC-01 [V0]:** Draftly shall be delivered as a browser-based system with
  server-enforced security.
- **DC-02 [V0]:** The architecture shall keep confidential matter documents
  separate from the public legal-source corpus.
- **DC-03 [V0]:** The verified matter record shall be the authoritative source
  for generated matter facts.
- **DC-04 [V0]:** Deterministic checks shall remain separate from generative
  text production.
- **DC-05 [V0]:** Google Document AI shall be isolated behind a controlled
  document-processing interface so that failure or later replacement does not
  change the verified matter record.
- **DC-06 [V0]:** The system shall store original evidence and generated
  derivatives separately.
- **DC-07 [V0]:** Audit history shall be append-only for ordinary application
  users.
- **DC-08 [V0]:** Except for the selected Google Document AI dependency, the
  SRS does not mandate the visual design, programming framework, component
  library, model vendor, or database product. Those choices belong in the
  software architecture document and may change if all requirements remain
  satisfied.
- **DC-09 [V0]:** No third-party product name, logo, screenshot, proprietary
  text, or distinctive interface asset shall be copied into Draftly.

### 3.9 Online user documentation and help

- **HELP-01 [V0]:** The product shall include help for matter creation,
  document upload, failed processing, fact verification, findings, legal
  citations, drafting, approval, export, and privacy controls.
- **HELP-02 [V0]:** Help shall distinguish candidate machine output from
  lawyer-approved information.
- **HELP-03 [V0]:** Contextual help shall explain why an action is blocked and
  identify the next permitted action.
- **HELP-04 [V0]:** User guidance shall be available in English and Sinhala for
  the supported V0 path.
- **HELP-05 [V0]:** Administrator and legal-content maintenance guidance shall
  be separated from ordinary matter-user help.

### 3.10 Purchased and external components

- **EXT-01 [V0]:** V0 shall use Google Document AI for OCR and
  document-quality analysis of supported documents [23], [24]. No other
  commercial component is mandatory by product name.
- **EXT-02 [V0]:** Before an external component processes matter data, its
  assessment shall record:

  - data location, retention, deletion, and training use;
  - confidentiality and access controls;
  - availability, quota, cost, and exit arrangements;
  - supported languages and document formats;
  - auditability and incident notification; and
  - licence and acceptable-use restrictions.

- **EXT-03 [V0]:** An external component shall not become the system of record
  for verified facts or approval history.
- **EXT-04 [V0]:** Every critical function that depends on an external
  component shall have an approved replacement or manual fallback.

### 3.11 Interfaces

#### 3.11.1 User interfaces

The exact navigation and screen layout are design decisions.

- **UI-01 [V0]:** The user interface shall provide access to accounts,
  assigned matters, documents, extracted information, evidence, findings,
  legal sources, drafts, review decisions, exports, and history according to
  the user's permissions.
- **UI-02 [V0]:** The current matter and user role shall remain clear during
  matter work.
- **UI-03 [V0]:** Machine, human-reviewed, corrected, conflicting, and blocked
  states shall be visibly distinct.
- **UI-04 [V0]:** Evidence shall be viewable alongside the information it
  supports.
- **UI-05 [V0]:** A capability planned for a future release shall not be
  displayed as a working function.
- **UI-06 [V0]:** A significant action shall show its consequence before
  confirmation.
- **UI-07 [V0]:** The interface shall remain usable in English and Sinhala.

#### 3.11.2 Hardware interfaces

- **HW-01 [V0]:** V0 shall require no specialised user hardware beyond a
  desktop-class computer, display, keyboard, pointing device, and network
  connection.
- **HW-02 [V0]:** The system shall accept document images created by an
  ordinary camera or scanner. A microphone and speakers are optional for later
  voice capabilities.

#### 3.11.3 Software interfaces

The system may connect to:

- Google Document AI for V0 OCR and document-quality analysis;
- a legal-source retrieval service;
- approved language-model, translation, or speech services;
- protected object storage;
- an identity service;
- office-document conversion software; and
- future registry, document-management, email, or practice systems.

- **SWI-01 [V0]:** Each enabled software interface shall authenticate
  requests, validate messages, handle timeout and failure, and avoid
  transmitting more confidential content than required.
- **SWI-02 [V0]:** A provider-specific interface shall not be the only means
  of recovering verified matter data or approval history.

Detailed protocols belong in the software architecture document.

#### 3.11.4 Communications interfaces

- **COM-01 [V0]:** Browser and service communication shall use HTTPS with a
  currently supported transport-security configuration.
- **COM-02 [V0]:** Background processing that uses asynchronous messaging
  shall authenticate publishers and consumers.
- **COM-03 [V0]:** Unencrypted transfer protocols shall not be used for
  confidential matter content.

### 3.12 Database and information requirements

- **DATA-01 [V0]:** The system shall store matters, users, memberships,
  documents, document versions, evidence spans, facts, fact versions, entities,
  findings, legal-source references, drafts, approvals, and audit events.
- **DATA-02 [V0]:** Original documents shall be stored in protected document
  storage; the matter database shall store controlled references rather than
  public file locations.
- **DATA-03 [V0]:** Corrections shall create new versions linked to the
  superseded value.
- **DATA-04 [V0]:** Derived search indexes and extraction outputs shall be
  rebuildable without changing the verified matter record.
- **DATA-05 [V0]:** Every evidence link shall remain resolvable to the correct
  document version.
- **DATA-06 [V0]:** Data export and deletion shall preserve records that must
  lawfully remain while removing data that is no longer authorised.
- **DATA-07 [V0]:** Backup and restoration shall preserve relationships among
  documents, evidence, facts, decisions, and audit history.
- **DATA-08 [V1]:** Schema evolution shall preserve V0 matter meaning and
  shall use documented migrations.

### 3.13 Licensing, legal, copyright, and notices

- **LEG-01 [V0]:** The system shall process personal and confidential
  information in a manner designed to support compliance with the PDPA and
  applicable directions in force at deployment [6].
- **LEG-02 [V0]:** Prescribed RTA forms and requirements shall be taken from
  authoritative legislation and gazettes [1]-[5].
- **LEG-03 [V0]:** Electronic records used inside the platform shall be
  handled consistently with the Electronic Transactions Act [7]. V0 shall not
  depend on electronic execution of an instrument excluded from that Act;
  exported instruments are prepared for lawyer review and the legally required
  method of execution, attestation, and registration.
- **LEG-04 [V0]:** Restricted editorial headnotes, case summaries, commercial
  database content, and published law-report content shall not be republished
  without permission.
- **LEG-05 [V0]:** Open-source and commercial dependencies shall be used under
  their applicable licences.
- **LEG-06 [V0]:** The product shall display that machine-assisted outputs
  require review by a qualified legal professional.

### 3.14 Applicable standards

- ISO/IEC/IEEE 29148:2018 guides the quality, identification, traceability, and
  change control of requirements [8].
- WCAG 2.2 Level AA applies to the core web interface [9].
- The RTA, applicable gazettes, and notarial legislation govern the legal
  content activated for V0 [1]-[5].
- The PDPA governs applicable personal-data processing obligations [6].
- The Electronic Transactions Act informs electronic records and
  communications [7].
- **STD-01 [V0]:** Secure web-development, dependency-management, backup, and
  incident-response practices shall be documented and tested before external
  use.

## 4. Supporting information

### 4.1 V0 acceptance criteria

V0 shall not be accepted solely because a scripted demonstration completes.
Acceptance requires evidence for the following:

1. **Document handling:** every supported test document reaches review or an
   explicit recoverable failure state; originals remain available.
2. **Google Document AI:** the processor type, processor version, processing
   region, input quality, and service outcome are recorded for each evaluation
   run; a service failure routes the document to retry or manual review.
3. **Classification:** performance is reported by document class on a
   lawyer-reviewed holdout, including precision, recall, F1, and confusion
   counts.
4. **Extraction:** mandatory particulars are evaluated separately from
   optional particulars; results report exact or normalised match, precision,
   recall, F1, and abstentions.
5. **Handwriting and poor scans:** V0 does not claim reliable automatic
   extraction from handwriting or severely degraded pages. Such material shall
   not be accepted automatically and shall route to human review or manual
   entry.
6. **Evidence:** every accepted machine-extracted particular opens the correct
   document version and source location.
7. **Verification control:** no mandatory unverified fact appears in an
   approved export.
8. **Checks:** each activated check has approved authority or business-rule
   status and is evaluated against lawyer-labelled cases.
9. **Legal research:** every retained claim has a resolvable citation; lawyer
   review measures whether the citation supports the claim and whether the
   answer uses the correct authority.
10. **Abstention:** unsupported questions and unreadable facts produce an
   explicit abstention or blocked state rather than fabricated content.
11. **Drafting:** approved wording is preserved, required fields use verified
    facts, no hidden placeholder remains, and the lawyer can trace inserted
    particulars to evidence.
12. **Export:** English and Sinhala content renders correctly, the approved
    version is identifiable, and reopening the exported file does not corrupt
    content.
13. **Security and privacy:** tests show no cross-matter access, no approval
    bypass, no exposed credentials, and no identifiable client data in
    demonstration material or ordinary logs.
14. **Usability and accessibility:** a legal user completes the core V0 tasks,
    and the interface passes the defined keyboard, zoom, language, and
    WCAG 2.2 AA checks.
15. **Audit:** uploads, corrections, findings, overrides, approvals, exports,
    permissions, and controlled-content changes appear in an immutable history.

Numerical thresholds shall be approved in the test plan after the holdout set,
document classes, and error costs are agreed with the domain expert. Results
shall include counts and confidence intervals where appropriate, not only
percentages.

### 4.2 Product-level success criteria

The product direction is successful when the shared foundation can support a
new conveyancing regime or notarial instrument type without weakening
evidence, verification, grounding, approval, privacy, or audit controls. V1,
V2, and V3 shall each define their own release-specific acceptance criteria
before implementation.

Across releases, evaluation should measure:

- time required for representative legal tasks compared with current manual
  preparation;
- document classification and extraction quality by language and document
  class;
- correctness of source links and cross-document relationships;
- precision and recall of deterministic findings;
- legal support and authority correctness of retrieved answers;
- factual and template correctness of drafts;
- abstention quality and reviewer disagreement;
- accessibility, security, privacy, and recovery behaviour; and
- lawyer-rated usefulness without treating satisfaction as a substitute for
  legal correctness.

### 4.3 Traceability

Each requirement identifier shall map to:

- one or more design components in the software architecture document;
- one or more test cases in the test plan;
- an implementation or configuration item;
- an acceptance result or an explicitly recorded deferral; and
- the release in which the requirement becomes binding.

Requirement changes shall record the reason, approver, affected release,
affected tests, and compatibility impact.

### 4.4 Items requiring confirmation

The following matters require formal confirmation before SRS approval or the
relevant release:

1. The complete V0 document-class, language, file-format, and image-quality
   boundary. Handwriting and severely degraded pages remain outside reliable
   automatic extraction unless a narrow class passes separate testing.
2. The Google Document AI processor version and approved processing region
   used for V0.
3. The exact RTA forms and transaction types included in V0 after the first
   approved transfer form.
4. The lawyer-approved V0 rule, terminology, and template catalogue.
5. Numerical acceptance thresholds and the size and composition of the
   lawyer-reviewed holdout.
6. Retention, deletion, hosting, and external-processing policy for real
   client matters.
7. The professional-conduct review required before use on a live notarial
   matter.
8. The detailed scope of V1, V2, and V3 before implementation begins.

Sections 1 to 3 and the approved V0 criteria in Section 4.1 are normative for
the initial release. The later-release descriptions define the product roadmap;
their detailed requirements become binding when each release scope is set.
