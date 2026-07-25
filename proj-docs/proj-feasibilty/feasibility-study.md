# FEASIBILITY STUDY

## Draftly: A Lawyer-in-the-Loop Legal Workflow Platform for Sri Lankan Legal Practice

<br><br><br>

**Date:** 23 July 2026

<br><br><br>

**Team Members:**
Dhanapala D.H.N., Dilshan A.D.L., De Silva B.K.P.

**Index Numbers:**
`<Index No 1>`, `<Index No 2>`, `<Index No 3>`

**Mentor:**
Dr. Nisansa de Silva

---

# Table of Contents

1. [Introduction](#1-introduction)

   * [1.1 Overview of the Project](#11-overview-of-the-project)
   * [1.2 Objectives of the Project](#12-objectives-of-the-project)
   * [1.3 The Need for the Project](#13-the-need-for-the-project)
   * [1.4 Overview of Existing Systems and Technologies](#14-overview-of-existing-systems-and-technologies)
   * [1.5 Scope of the Project](#15-scope-of-the-project)
   * [1.6 Deliverables](#16-deliverables)
2. [Feasibility Study](#2-feasibility-study)

   * [2.1 Financial Feasibility](#21-financial-feasibility)
   * [2.2 Technical Feasibility](#22-technical-feasibility)
   * [2.3 Resource and Time Feasibility](#23-resource-and-time-feasibility)
   * [2.4 Risk Feasibility](#24-risk-feasibility)
   * [2.5 Social and Legal Feasibility](#25-social-and-legal-feasibility)
3. [Considerations](#3-considerations)
4. [References](#4-references)

---

# 1. Introduction

## 1.1 Overview of the Project

Draftly is a lawyer-in-the-loop legal workflow platform for Sri Lankan legal
practice. The platform supports two workflow tracks: conveyancing, which is
the first prototype workflow, and litigation, which is a later extension of
the same matter-and-workflow foundation. The initial product is a notarial
workbench for matters under the Registration of Title Act, No. 21 of 1998
(the "Bim Saviya" title-registration programme) [1], covering four notarial
functions: examination of title, drafting, execution, and attestation.

The system accepts an unstructured bundle of property and identity documents
relating to a conveyancing matter — deeds, the current title certificate,
cadastral and survey material, local-authority records, and party identity
documents — and converts it into a verified, structured matter record. Optical
character recognition and field extraction produce candidate facts with source
locations; a qualified lawyer then verifies or corrects every extracted fact
before it is relied upon. Deterministic consistency checks compare the
verified facts across documents, surface missing documents and red flags, and
guided workflow steps connect each stage of the notarial process to the
governing statutory provisions. Finally, the platform generates
lawyer-reviewable draft instruments from prescribed forms, populated only
with verified facts, and maintains a complete version history and audit
trail through to approval and export.

The intended users are practising lawyers and notaries who handle land and
title work, together with their supporting staff. The value to a practice is
faster and more reliable title examination, fewer transcription and
consistency errors, grounded answers to legal questions with pinpoint
citations to statutes and authorities, and a defensible record of who
verified and approved each fact and document. The distinguishing principle of
the platform is that it is neither a form-filling PDF generator nor a legal
search engine: the prescribed form is only the final output layer, and every
generated draft is traceable to a verified record and to the evidence behind
it.

## 1.2 Objectives of the Project

The objectives of the project are to:

* Design and implement a web-based legal workflow platform in which a matter
  progresses from document intake to an approved, exportable draft under
  continuous lawyer supervision.
* Automate the extraction of structured particulars from Sinhala and English
  conveyancing documents using optical character recognition, document
  classification, and layout-aware field extraction, with every extracted
  value carrying its source location.
* Provide a verification workspace in which extracted facts are reviewed
  beside their source evidence and moved through explicit verification states
  before use.
* Implement deterministic consistency checks over the verified matter record,
  including the cross-matching of the deed schedule, survey plan, and
  municipal assessment records, producing missing-document checklists and red
  flags.
* Provide grounded legal question answering over a curated corpus of Sri
  Lankan statutes, gazettes, and case law, in which every claim carries a
  citation and the system abstains explicitly when authority is insufficient.
* Generate draft instruments from prescribed statutory forms, beginning with
  the Form 8 transfer under the title-registration regime, populated
  exclusively from verified facts.
* Maintain versioned drafts, approval gates, document export to standard
  office formats, and a complete audit trail of all actions.
* Provide the interface in both English and Sinhala on the demonstrated
  workflow path.
* Evaluate extraction, checking, retrieval, and drafting quality against a
  lawyer-verified evaluation set before any capability is presented as
  reliable.

## 1.3 The Need for the Project

Conveyancing practice in Sri Lanka is document-heavy, rule-driven, and almost
entirely manual. A single transfer matter requires the practitioner to
assemble and reconcile deeds, title certificates, survey plans, street-line
and assessment records, and identity documents, often spanning several
decades and four coexisting registration regimes. The examination of title
requires that the particulars in these documents tally exactly; a mismatch in
a lot number, extent, boundary, or party name that escapes notice can
invalidate an instrument or expose the practitioner to liability.

The existing process presents several difficulties that the proposed system
addresses:

* **Manual reconciliation.** Cross-checking particulars across a document
  bundle is performed by eye. It is slow, repetitive, and error-prone, and
  the burden falls heavily on junior practitioners.
* **Fragmented sources of law.** The governing rules are spread across
  statutes, amendments, gazettes and prescribed forms, and a large body of
  case law. Locating the provision or authority relevant to a specific step
  of a specific matter is time-consuming, and existing local tools support
  general research rather than step-aware guidance.
* **Transcription risk in drafting.** Particulars are re-typed from source
  documents into instruments. Every re-typing is an opportunity for error,
  and prescribed statutory wording must be reproduced exactly.
* **No systematic record of verification.** Current practice produces no
  structured record of which facts were checked, by whom, and against which
  evidence. This weakens both quality control within a practice and the
  defensibility of the work.
* **Unreliability of generic AI tools.** General-purpose language models
  produce fluent but unverifiable answers and fabricated citations. In legal
  work this failure mode is disqualifying. A system for this domain must
  ground every output in identifiable source documents and statutory
  authority, and must abstain when it cannot.

The proposed system responds to these needs with a verified structured matter
record, deterministic checks, grounded retrieval, and generation that is
constrained to approved templates and verified facts — with a lawyer
approving every consequential step.

## 1.4 Overview of Existing Systems and Technologies

### Existing systems

**Sri Lankan legal research platforms.** LawLanka [2] and LawCeylon provide
commercial access to Sri Lankan legislation and law reports; Paralegal.lk and
AI PAZZ offer search-oriented assistance over local legal content. These
systems serve legal *research*: retrieval of legislation and case law by
query. They do not manage matters, extract or verify facts from client
documents, check cross-document consistency, or generate instruments. The
proposed system uses retrieval as one component inside a verified drafting
workflow rather than as the product itself.

**International legal AI platforms.** Harvey [3] is a prominent
international example of an AI-assisted legal workspace combining document
analysis, drafting assistance, and workflow features for large law firms. Its
design demonstrates the viability of the calm, matter-centred professional
workspace pattern. However, it does not address Sri Lankan law, Sinhala-
language documents, the local registration regimes, or the prescribed forms
that govern local notarial practice, and its commercial positioning is
directed at large international firms rather than local practitioners.

**General-purpose language models.** Consumer chatbots built on large
language models can summarise and draft text, but they lack access to the
governing local sources, provide no provenance, and hallucinate authority.
They offer no matter record, no verification workflow, and no audit trail.

No existing system combines, for the Sri Lankan context: bilingual document
extraction with lawyer verification, deterministic title consistency checks,
grounded question answering over local statutes and case law, and
template-constrained generation of prescribed instruments. This combination
is the gap the proposed system fills.

### Technologies considered

The following technologies are currently selected. The selections may be
adjusted during development where more suitable alternatives are identified;
exact implementation details will be documented in the final report.

* **Frontend:** Next.js (React) with TypeScript [4], with Tailwind CSS and an
  accessible component library, and the Tiptap rich-text editor framework [5]
  for the draft editor. Tiptap provides schema-validated structured
  documents, which allows prescribed statutory wording to be locked while
  schedules and particulars remain editable, and allows facts to be embedded
  as typed nodes that refuse unverified content.
* **Backend:** FastAPI (Python) [6], exposing the document pipeline and the
  retrieval engine over typed HTTP interfaces. The data science components
  are implemented in Python, so a Python web framework allows the engine to
  be served directly.
* **Database:** PostgreSQL [7] for matters, facts, documents, versions, and
  audit records; SQLite full-text indexes are used inside the retrieval
  engine for the statutory corpus.
* **Document processing:** optical character recognition through a tiered
  strategy — local open-source engines for routine material and a cloud
  document-understanding service for difficult scans — with all extraction
  results subject to manual verification. Self-hosted open-source OCR is
  preferred for real client documents for privacy reasons.
* **Retrieval:** a deterministic, rule-based retrieval engine over a curated
  statutory and case-law corpus, using established lexical ranking (BM25)
  [8], a citation graph linking cases to statutory sections, and
  topic-partitioned indexes; bounded large-language-model passes are used
  only for constrained tasks with validated outputs, following
  retrieval-augmented generation principles [9] with claim-level citation
  checking and explicit abstention.
* **Supporting services and tooling:** Git and GitHub for version control and
  continuous integration; Vercel for frontend preview deployments; automated
  testing with Playwright and axe-core for interface and accessibility
  checks; Conventional Commits and code review for change control.

These selections favour stable, widely documented, open-source technologies
with active ecosystems, which satisfies the requirements of maintainability,
security, and low operating cost identified later in this study.

## 1.5 Scope of the Project

The initial system is scoped to matters under the title-registration regime
(Registration of Title Act, No. 21 of 1998), covering examination of title,
drafting, execution, and attestation, with the Form 8 transfer as the first
end-to-end instrument.

### User roles

#### Lawyer / Notary

The lawyer or notary is able to:

* Create and manage matters under the supported registration regime.
* Upload matter documents and monitor their processing states.
* Review extracted facts beside their source evidence, and verify or correct
  each fact; conflicting or unreadable items are flagged for resolution.
* Run and review deterministic consistency checks, missing-document
  checklists, and red flags, and record the resolution of findings.
* Follow guided workflow steps with visible statutory grounding.
* Ask matter-aware legal questions and inspect claim-level evidence, or
  receive an explicit insufficient-authority response.
* Generate drafts from approved templates using verified facts only; edit,
  compare, and restore versions; approve drafts; and export approved drafts
  to standard office formats.
* Inspect the full audit trail of the matter.

### Out of scope for the initial system

* The registration function of notarial practice, historical title-chain
  reconstruction, and pedigree analysis.
* Conveyancing regimes other than title registration (deed registration,
  condominium, and special-area regimes are visible in the interface but
  marked as not yet supported).
* The litigation workflow track.
* Extraction of forms and document classes explicitly excluded from the
  initial pipeline.

These exclusions bound the initial build; the platform architecture treats
them as future extensions of the same matter and workflow foundation.

## 1.6 Deliverables

The main deliverables of the project are:

* A web-based legal workflow application providing matter management,
  document intake and processing, fact verification, consistency checks,
  guided workflow steps, grounded question answering, draft editing with
  version history, approval gates, and export.
* A document-processing pipeline for Sinhala and English matter documents,
  producing structured candidate facts with source locations and confidence
  values.
* A curated and normalised statutory and case-law corpus with a
  deterministic retrieval engine and citation graph serving grounded
  answers.
* A draft-generation module encoding the Form 8 transfer as a fillable,
  schema-validated template with locked prescribed wording, together with
  document export to standard office formats.
* A bilingual (English and Sinhala) user interface on the demonstrated
  workflow path.
* A lawyer-verified evaluation set and evaluation reports covering
  extraction, checking, retrieval, and drafting quality.
* Technical documentation, user documentation, testing reports, deployment
  instructions, and the full source code under version control.

---

# 2. Feasibility Study

## 2.1 Financial Feasibility

The project is financially practical because its cost structure is dominated
by free and open-source components, while its benefits address a genuinely
costly manual process.

### Development costs

| Item | Basis | Expected cost |
| --- | --- | --- |
| Development hardware | Existing personal computers are sufficient; no GPU is required because heavy model inference is consumed as external services and the retrieval engine is deterministic | None additional |
| Software and frameworks | Next.js, FastAPI, PostgreSQL, Tiptap (core), Playwright, and the supporting toolchain are open source | None |
| Cloud document-understanding OCR | Free-tier / trial allocation with a capped page budget; local open-source OCR is the default route | None within the capped budget |
| Language-model usage | Free developer tiers of hosted inference services; the client is provider-agnostic so providers can be exchanged without code changes | None to negligible |
| Frontend hosting for review | Free hobby tier of a deployment platform for preview builds | None |
| Version control and continuous integration | Free tiers for private repositories | None |

### Operational costs

Operational costs during the project period remain within free tiers. A
production deployment beyond the project would introduce modest recurring
costs — managed hosting and database services, storage for client documents,
and paid tiers of OCR or inference services if volumes grow — of the order of
a small monthly subscription, which is low relative to the professional time
the system saves. A domain name and TLS certificate are minor optional costs.

### Expected benefits

* Reduced professional time per matter for examination of title, document
  reconciliation, and drafting.
* Fewer transcription and consistency errors, reducing costly rework and
  professional risk.
* Faster location of governing provisions and authority through grounded,
  step-aware retrieval.
* A defensible verification and audit record, improving quality control
  within a practice.
* A reusable structured corpus and matter-record foundation on which further
  regimes and the litigation track can be added at marginal cost.

Because expected costs during development are effectively limited to already-
available resources and free service tiers, while the addressed process is
expensive in professional time and risk, the financial benefits clearly
justify the costs. The project is financially feasible.

## 2.2 Technical Feasibility

The system is technically feasible because each of its components relies on
stable, well-documented technologies, and because the highest-risk components
have already been validated by working prototypes during the research phase.

### Architecture

The architecture comprises: a Next.js web application (matter workspace,
verification interface, draft editor); a FastAPI service layer exposing the
document pipeline and retrieval engine; a PostgreSQL store for matters,
facts, drafts, versions, and audit records; a document-processing pipeline
(OCR, classification, field extraction with source spans); and a
deterministic retrieval engine over a curated statutory and case-law corpus,
with bounded, validated language-model passes for constrained enrichment
tasks.

### Grounds for technical confidence

* **Stable technologies with strong documentation.** Every core framework —
  Next.js [4], FastAPI [6], PostgreSQL [7], Tiptap [5] — is mature, widely
  deployed, actively maintained, and comprehensively documented, and the
  components interoperate over standard typed HTTP interfaces.
* **Validated prototypes for the hardest components.** During the research
  phase, a normalised corpus of more than nine thousand statutory and
  case-law documents was constructed with verified integrity; a
  statutes-only question-answering prototype produced grounded, claim-cited
  answers with explicit abstention on insufficient authority; and lexical
  retrieval baselines with a citation graph were implemented and measured.
  These prototypes demonstrate that the retrieval and grounding design works
  on the real corpus before full development begins.
* **Deterministic core, bounded model use.** The consistency checks and the
  retrieval ranking are deterministic and reproducible. Language models are
  used only inside bounded tasks (closed choices, validated outputs,
  mandatory citations, abstention), so system correctness is guarded by
  validation layers rather than by model behaviour.
* **Editor enforcement by schema.** The requirement that no unverified fact
  can enter a draft is enforced structurally by the editor's document schema
  rather than by user discipline, which is a proven capability of the
  selected editor framework.
* **OCR is tiered and human-backed.** Sinhala OCR quality on old scans is
  the least predictable element; the design accepts this by routing
  difficult documents through progressively stronger engines and, where
  extraction fails, falling back to manual entry with the same verification
  workflow. The system therefore degrades gracefully rather than failing.
* **Scalability and maintainability.** The chosen stack scales vertically
  and horizontally through conventional means (stateless services, indexed
  relational storage, cacheable retrieval indexes), and the codebase is
  modular with typed contracts between frontend, backend, and engine.

The initially selected technologies may be adjusted during development where
more suitable alternatives are identified. On the evidence of the validated
prototypes and the maturity of the selected technologies, the project is
technically feasible.

## 2.3 Resource and Time Feasibility

### Hardware requirements

* Three development computers (already available).
* No dedicated GPU hardware: model inference is consumed as hosted services
  and the retrieval core is deterministic.
* Cloud compute limited to free-tier hosting for preview deployments and a
  capped cloud OCR budget.
* Ordinary broadband network connections and external backup storage.

### Software requirements

* Operating systems and editors already in use by the team.
* Open-source frameworks and tools: Next.js, FastAPI, PostgreSQL, Tiptap,
  Playwright, Git.
* Free-tier cloud services: repository hosting and continuous integration,
  frontend preview hosting, hosted inference for bounded tasks.
* Project management through the team's existing issue tracker.

### Human resources

* **Three developers**, dividing the work into three parallel workstreams:
  document processing and extraction; data and legal corpus with the
  retrieval engine; and templates, outputs, and the lawyer-facing interface.
* **A domain expert mentor** — a senior practitioner and law lecturer — who
  supplies the syllabus structure, statutes, sample instruments, and worked
  examples, and validates workflow order, terminology, and outputs.
* **An academic supervisor** providing research direction, and project
  mentoring through the module's supervision arrangements.

### Time feasibility

The project period is organised into staged milestones:

1. Requirement gathering, domain study, and feasibility analysis (complete:
   mentor-guided domain model, corpus acquisition, and interface
   specification).
2. Contracts and foundations: the shared matter-record and step-definition
   contracts that all workstreams build against.
3. Engine and content track: retrieval engine hardening, evaluation sets,
   and rule/check catalogue — in parallel with the interface track below.
4. Interface track: the full workspace built against typed mock data,
   matched to the approved interface specification.
5. Integration: the interface wired to the service layer, producing the
   first end-to-end demonstrable path (matter creation through verified
   facts, checks, grounded answers, and an approved exported draft).
6. Completion of the remaining workflows, bilingual polish, evaluation
   against lawyer-verified labels, and hardening.
7. Testing, user evaluation with the mentor, documentation, and final
   reporting.

Because the workstreams are parallel, the highest-risk components already
have working prototypes, and the interface can be developed against mock data
without waiting for the backend, the available time and resources are
sufficient for the planned scope. The staged plan also defines a minimal
demonstrable product early (stage 5), protecting the schedule against
overruns in later stages.

## 2.4 Risk Feasibility

### Requirements risk

**Risk:** The legal-domain requirements are intricate, and misunderstanding
the notarial workflow or statutory requirements would produce an unusable
system.

**Mitigation:** Requirements are grounded in recorded sessions with the
domain expert mentor and in the primary sources themselves; the interface
specification is reviewed with the mentor before implementation; prototypes
are validated with the mentor at each milestone; and changes are managed
through a controlled, documented process.

### Schedule risk

**Risk:** Development tasks, particularly document processing and the
bilingual interface, may take longer than expected.

**Mitigation:** The project is divided into staged milestones with an early
minimal demonstrable product; essential features are prioritised;
workstreams run in parallel behind frozen contracts; progress is monitored
against the issue tracker; and time buffers are maintained for the high-risk
extraction and integration stages.

### Technical integration risk

**Risk:** Components developed in parallel (interface, service layer,
pipeline, engine) may not integrate cleanly.

**Mitigation:** Shared typed contracts are defined and frozen first; the
interface is built against mock data that mirrors the engine's real output
shapes; integration proceeds screen by screen beginning with the component
whose backend is already validated; and integration checkpoints are tested
end to end.

### Data-quality risk

**Risk:** Scanned Sinhala documents, legacy fonts, and degraded source
material may yield poor extraction, and portions of the legal corpus may
contain OCR artefacts.

**Mitigation:** A tiered OCR strategy with recorded per-document processing
status; extraction confidence surfaced to the user; mandatory lawyer
verification before any fact is used; manual-entry fallback for unreadable
fields; known-defective corpus segments quarantined and excluded from
answer evidence until re-extracted; and data-quality checks in the corpus
build pipeline.

### Model-reliability risk

**Risk:** Language-model components may produce plausible but incorrect
output — fabricated citations, misattributed statutes, or rules taken out of
context — which is unacceptable in legal work.

**Mitigation:** Models are confined to bounded tasks with closed choices and
validated outputs; every generated claim must carry a citation that resolves
against the corpus; an entailment-style verifier checks claims against the
cited evidence; the system abstains explicitly when authority is
insufficient; all machine-generated legal links and rules remain marked
unverified until reviewed by a lawyer; and measured evaluation gates any
capability before it is presented as reliable. Machine confidence is never
displayed as legal approval.

### Security risk

**Risk:** Unauthorised access to matters and client documents.

**Mitigation:** Authentication with role-based access control; protected
document storage; encryption in transit; audit logging of all consequential
actions; secure coding practices and dependency review; and security testing
before deployment.

### Privacy risk

**Risk:** Conveyancing bundles contain sensitive personal data — identities,
addresses, and property particulars — whose exposure would be a serious
breach.

**Mitigation:** Real client material is confined to a restricted research
store and is never committed to shared repositories or demonstrations; all
demonstration and evaluation content is synthetic or anonymised while
preserving document structure; self-hosted processing is preferred for real
client documents; access is restricted by role; and data minimisation and
retention rules are applied in line with the Personal Data Protection Act,
No. 9 of 2022 [10].

### External-service risk

**Risk:** Hosted OCR and inference services may impose quota limits, change
pricing, or become unavailable; free-tier quotas have been exhausted
mid-task during the research phase.

**Mitigation:** The inference client is provider-agnostic behind a standard
interface, so providers can be exchanged without code changes; local
open-source fallbacks exist for OCR and can exist for inference; long-running
jobs are checkpointed and resumable; cloud usage is budgeted and metered
against a recorded ceiling; and the demonstration path runs fully on local
data without live external dependencies.

### Performance risk

**Risk:** Retrieval over a large corpus, document processing, and dense
review screens may become slow as data grows.

**Mitigation:** Persistent precomputed indexes for retrieval; asynchronous
background processing for OCR and extraction with visible progress states;
database indexing and query review; caching of static corpus content; and
performance testing on realistic matter sizes.

### User-adoption risk

**Risk:** Practitioners may distrust automated assistance or find a new
workflow burdensome relative to established manual practice.

**Mitigation:** The system is designed around the profession's own workflow
as described by the domain mentor; every automated output is traceable to
evidence and subject to explicit lawyer approval; the interface accepts
documents and reports what is missing rather than imposing checklists;
usability evaluation is conducted with the mentor; and the bilingual
interface removes a language barrier to adoption.

## 2.5 Social and Legal Feasibility

### Social feasibility

The system is socially beneficial and acceptable on the following grounds:

* **It assists rather than replaces professional judgment.** Every
  consequential action — verification, approval, waiver, export — is
  reserved to a qualified lawyer. The platform removes clerical burden, not
  professional responsibility, and therefore complements rather than
  threatens the profession's role.
* **Language inclusion.** A bilingual English and Sinhala interface, with
  correct rendering of Sinhala script and typography, serves the actual
  working languages of the profession and its clients.
* **Accessibility.** The interface targets recognised accessibility
  guidance [11]: full keyboard operability, sufficient colour contrast,
  status communicated by icon and label rather than colour alone, and
  screen-reader-compatible structure.
* **Transparency and fairness.** Every automated output displays its
  evidence and its verification status; uncertainty is shown honestly,
  including explicit refusal to answer without authority. Clients of a
  practice benefit from faster service and from work products with a
  documented verification trail.
* **Digital literacy.** The interface follows familiar document-and-review
  patterns, and guided steps explain each stage of the workflow, keeping the
  system usable for practitioners with modest technical backgrounds.

### Legal feasibility

* **Data protection.** The processing of personal data in matter documents
  is designed for compliance with the Personal Data Protection Act, No. 9 of
  2022 [10]: data minimisation, purpose limitation, role-restricted access,
  security safeguards, and retention controls. Real client data is excluded
  from development artefacts entirely.
* **Confidentiality.** The design respects the confidentiality obligations
  of legal practice through access control, audit trails, and the preference
  for self-hosted processing of client documents.
* **Sources of law.** The statutory corpus is assembled from official and
  public sources; judgments are public records obtained from official and
  publicly accessible repositories. Editorial material from commercial law
  reports (such as headnotes) is subject to third-party copyright and is
  used only internally for research and never republished.
* **Prescribed forms and statutory wording.** Prescribed wording from the
  governing statute and gazetted forms [1] is reproduced exactly and locked
  against editing; the drafting of legal wording in templates remains a
  human responsibility, and generated drafts are instruments *prepared for*
  and approved by a qualified professional, so the system does not practise
  law or offer legal advice to the public.
* **Licensing.** All selected frameworks, libraries, and fonts carry
  permissive open-source licences compatible with the project's use.
* **Electronic documents.** Exported instruments follow existing practice
  (printed, executed, and attested conventionally), so the system does not
  depend on the electronic-execution questions surrounding instruments
  excluded from the Electronic Transactions Act, No. 19 of 2006 [12];
  the platform's electronic records serve internal workflow and audit
  purposes.
* **Liability for accuracy.** The verification architecture — evidence-side
  review, explicit verification states, deterministic checks, citation
  gates, abstention, and lawyer approval before export — is itself the
  mitigation of liability risk arising from inaccurate automated output.

The system can therefore be developed and operated in a socially responsible
and legally compliant manner.

---

# 3. Considerations

## 3.1 Performance

The system should respond within interactive limits on the matter workspace,
process document bundles asynchronously with visible progress states, and
serve retrieval queries from persistent precomputed indexes. Database queries
over matters, facts, and audit records are indexed; corpus content is static
and cacheable. The initial deployment targets a small number of concurrent
users per practice, with an architecture (stateless services, relational
storage, separable engine) that scales conventionally as usage grows.

## 3.2 Security

Security requirements include authenticated access, role-based authorisation
for every function, encrypted transport, protected document storage, input
validation, session management, audit logging of all consequential actions,
secure backups, and protection against common web vulnerabilities. Actions
with legal significance are attributable to identified users.

## 3.3 Privacy

The system collects only the data required for the matter at hand, restricts
access by role, records processing purposes, supports retention and deletion
policies, and keeps real client material out of development, demonstration,
and evaluation artefacts. These practices are aligned with the Personal Data
Protection Act, No. 9 of 2022 [10].

## 3.4 Usability

The interface is a calm, dense professional workspace: consistent navigation
around a persistent matter context, review tables that place every extracted
value beside its evidence, meaningful processing and verification states with
plain-language labels, guidance that reports what is missing rather than
demanding checklists, and clear confirmation of every consequential action.

## 3.5 Accessibility

The interface targets recognised accessibility guidance [11]: complete
keyboard operability of the core path, visible focus indication, sufficient
colour contrast verified against the design tokens, status never encoded by
colour alone, text alternatives and accessible labels, correct behaviour at
enlarged text sizes (including Sinhala script), and respect for
reduced-motion preferences.

## 3.6 Reliability

Document processing is resumable and reports failure states explicitly with
recovery paths (retry, replace, manual entry). Drafts are versioned with
restore; the audit log preserves a consistent history; backups protect matter
data; and the demonstration path operates without live external
dependencies.

## 3.7 Maintainability

The codebase is modular — interface, service layer, pipeline, and engine are
separated by typed contracts — under version control with continuous
integration, automated checks (type checking, linting, interface smoke
tests), code review, and documented conventions. Templates, rules, and the
statutory corpus are versioned data, maintainable without code changes.

## 3.8 Scalability

Growth in matters, documents, and corpus size is accommodated through
indexed relational storage, precomputed retrieval indexes, asynchronous
processing queues, cacheable static content, and horizontally scalable
stateless services. New regimes, forms, and eventually the litigation track
extend existing structures rather than requiring redesign.

## 3.9 Accuracy

Accuracy is treated as a measured property, not an assumption: extraction,
checks, retrieval, and drafting are evaluated against a lawyer-verified
evaluation set; extraction confidence is displayed but never treated as
approval; every generated claim must cite resolvable authority and is
checked against its evidence; the system abstains when authority is
insufficient; and all machine-generated links and rules remain unverified
until human review. Manual correction is available at every stage.

## 3.10 Ease of Use

Common tasks are minimised in effort: uploads are batch-processed with
automatic classification; the system tells the user what is missing;
verification supports single-fact, section, and reviewed-batch actions;
search and command access is available from the keyboard; defaults follow
the guided workflow; and export of an approved draft is a single gated
action.

---

# 4. References

```text
[1]  Parliament of the Democratic Socialist Republic of Sri Lanka,
     Registration of Title Act, No. 21 of 1998. Colombo, Sri Lanka:
     Government Publications Bureau, 1998.

[2]  LawLanka (Pvt) Ltd, "LawLanka — Sri Lanka's premier legal information
     portal." [Online]. Available: https://www.lawlanka.com.
     [Accessed: Jul. 23, 2026].

[3]  Harvey AI, "Harvey — Professional class AI for legal teams." [Online].
     Available: https://www.harvey.ai. [Accessed: Jul. 23, 2026].

[4]  Vercel Inc., "Next.js: Official documentation." [Online]. Available:
     https://nextjs.org/docs. [Accessed: Jul. 23, 2026].

[5]  Tiptap GmbH, "Tiptap: Headless editor framework — Official
     documentation." [Online]. Available: https://tiptap.dev/docs.
     [Accessed: Jul. 23, 2026].

[6]  S. Ramírez, "FastAPI: Official documentation." [Online]. Available:
     https://fastapi.tiangolo.com. [Accessed: Jul. 23, 2026].

[7]  The PostgreSQL Global Development Group, "PostgreSQL: Official
     documentation." [Online]. Available: https://www.postgresql.org/docs.
     [Accessed: Jul. 23, 2026].

[8]  S. Robertson and H. Zaragoza, "The probabilistic relevance framework:
     BM25 and beyond," Foundations and Trends in Information Retrieval,
     vol. 3, no. 4, pp. 333–389, 2009.

[9]  P. Lewis et al., "Retrieval-augmented generation for knowledge-
     intensive NLP tasks," in Advances in Neural Information Processing
     Systems (NeurIPS), Vancouver, Canada, 2020, pp. 9459–9474.

[10] Parliament of the Democratic Socialist Republic of Sri Lanka, Personal
     Data Protection Act, No. 9 of 2022. Colombo, Sri Lanka: Government
     Publications Bureau, 2022.

[11] World Wide Web Consortium (W3C), "Web Content Accessibility Guidelines
     (WCAG) 2.1," W3C Recommendation, Jun. 2018. [Online]. Available:
     https://www.w3.org/TR/WCAG21/. [Accessed: Jul. 23, 2026].

[12] Parliament of the Democratic Socialist Republic of Sri Lanka,
     Electronic Transactions Act, No. 19 of 2006. Colombo, Sri Lanka:
     Government Publications Bureau, 2006.
```
