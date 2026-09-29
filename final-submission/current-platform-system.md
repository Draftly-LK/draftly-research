# Draftly platform: current implemented system

Status snapshot: 29 September 2026. This account is based on the sibling
`draftly-platform` repository at commit `a116a59`, its deployed-system record,
and its September test report. It describes the software and deployment that
exist today. The final project report can draw on it, but should recheck the
snapshot against a later platform commit before submission.

## Purpose and user workflow

Draftly is a Sri Lankan notarial and conveyancing workbench. Its first workflow
centres on land matters under the Registration of Title Act (RTA). A lawyer
creates a matter, answers intake questions, gathers title evidence, reviews
machine-proposed facts, completes a governed checklist, runs deterministic
checks, prepares prescribed forms, and records approval and later registration
events. The system keeps the lawyer responsible for factual and legal decisions.

The intended path through the implemented services is:

```text
Matter intake -> document upload -> candidate extraction -> lawyer verification
              -> checklist and checks -> form draft -> lawyer approval -> export
              -> attestation and registration record
```

These steps do not all form a completed production path yet. In the live demo,
document extraction is stubbed. The form catalogue's legal wording has not been
verified for registration-ready export, so the backend refuses that final
output. The hosted app uses API-backed, persistent matter and document records.
Its current operating policy limits it to synthetic data; it is not yet
approved for real client files.

## Software architecture

The application consists of a Next.js 15 frontend (React 19 and TypeScript), a
Python 3.12 FastAPI backend, and PostgreSQL with Alembic migrations. The backend
is a modular monolith. Its API routers handle HTTP and authorization;
application services coordinate operations; domain modules hold rules; ports
describe dependencies; and adapters connect to PostgreSQL or external
providers. `backend/src/bootstrap.py` chooses adapters and mounts the module
routers under `/api/v1`. Background work uses an outbox and worker process.

The frontend has both API-backed screens and an offline demo store. Setting
`NEXT_PUBLIC_API_BASE_URL` connects the app to the backend. The production
build sets it, so fixture matters and documents are not shown in the deployed
app. With no API URL, the offline demo uses fixed synthetic fixtures. This
distinction matters when interpreting screenshots and browser tests.

Clerk provides sign-in for the deployed app. The backend checks bearer tokens
and enforces user-scoped access. Local and CI environments can select a stub
identity adapter; the backend refuses that adapter in other environments.
Capability checks, matter ownership, version headers, signed pagination
cursors, and audit events are part of the API design. The current deployment
uses a single account scope for most data: backend repository queries filter
on `user_id` and hide another user's matter by returning 404.

## Implemented product areas

| Area | Current implementation |
| --- | --- |
| Account and billing | Sign-in provisioning, profile and role APIs, seeded plans, a first-sign-in trial, feature entitlements, usage quotas, checkout and payment webhook handling. The deployed server enforces plan limits. |
| Matter intake | Matter creation and listing, classification, intake answers, subtype selection, eligibility routing, and compilation of a versioned checklist. |
| Document handling | Immutable source-file upload, source versions, document inbox, processing runs, boundary and classification review, page artifacts, candidate-field correction and approval. A separate processing endpoint returns candidate data only. |
| Verified facts | Extracted facts, evidence references, review decisions, and fact versions. Machine proposals do not become confirmed facts without review. |
| Workflow and checks | Checklist items and satisfaction links; deterministic cross-document checks and legal issues. Unresolved statutory blockers stop the relevant workflow, and statutory blockers cannot be waived. |
| Drafting and approval | Form generation from rule-pack templates, evidence-linked field bindings, field decisions, preflight, stale-form marking, lawyer approval records, export records, and registration events. Unresolved values render as explicit tokens. |
| Legal research and library | A read-only legal-source catalogue, search and conversation endpoints, asynchronous research jobs, and grounded answer composition when the provider is configured and approved. |
| Matter assistant | Per-matter sessions and messages, queued turns, job events, an allowlisted tool executor, and confirmation of proposed actions. Its availability and model depend on deployment settings. |
| Party records | Party profiles, identity evidence, beneficial owners, customer due diligence, screening, duplicate probes, merges, and matter-party links. Sensitive identifiers have field encryption and blind-index support. |
| Practice operations | Obligations and due dates, notification preferences and delivery, attestations, protocol records, registration submission and acknowledgement, register entries, and monthly return periods. |

The RTA rule pack is code-defined and versioned. It contains taxonomy,
questions, document classes, checklist requirements, checks, forms, and source
metadata. A matter's compiled checklist is pinned to the rule-pack version it
used. The existence of a form definition or API route does not mean its legal
copy has received professional sign-off.

The interface includes home, matter lists and intake, matter overview,
documents and processing review, facts, checks, workflow, drafts, approval,
exports, activity, legal research, library, assistant, billing, profile, and
settings screens. It uses `next-intl` for English and Sinhala interface text.
Sinhala interface support is separate from OCR support for Sinhala source
documents. The draft editor uses Tiptap. Some screens and journeys are still
more complete in the offline demo than in API-backed browser testing.

## Evidence, decisions, and safety boundaries

Original uploaded evidence is treated as immutable; a new version supersedes
an earlier file rather than changing its bytes. Extraction output is a
candidate. A lawyer can approve or correct a candidate, producing a verified
fact version with an evidence link and review decision. Forms bind to a
specific fact version, so a later correction can make a form stale. The system
does not silently replace an approved value with a new machine prediction.

Checks evaluate the verified matter record against the RTA rule pack and
produce findings for review. The backend enforces important refusals:
unverified machine values cannot fill approved legal fields, open statutory
blockers stop draft progression, and an unapproved form cannot be exported as
approved. Export is a separate event from registration. Material mutations
append an audit event in the same database transaction; the audit chain is
hash-linked per user.

The legal research path retrieves statute passages and can send a typed
question with retrieved text to Gemini to compose a grounded response. It is
an aid to review, not a source of legal authority on its own. If retrieval
returns no usable passage or the retrieval container is unavailable, the
service abstains with insufficient authority. The deployed index currently
uses BM25-style lexical retrieval. The richer hybrid retrieval described in
research designs is not the deployed index.

## Live deployment

The platform's deployment record describes one Ubuntu VPS serving the landing
page, Next.js application, FastAPI API, outbox worker, internal retrieval
service, Caddy reverse proxy, and PostgreSQL. The public landing page is
`draftly.adlahiru.com`; the application and API share
`app.draftly.adlahiru.com`. The retrieval service and database are internal to
the Docker network. Clerk handles sign-in. The database was moved from Neon to
PostgreSQL on this VPS on 21 September 2026. Source files currently use a VPS
volume. The team plans to add MinIO object storage; the checked platform code
has no MinIO storage adapter yet. Nightly backups are configured on the same
server.

Changes reach the server through feature-branch pull requests to `main`, then
a promotion pull request to `prod`. A push to `prod` runs GitHub Actions checks,
builds images, applies migrations, checks health, and can roll back a failed
deployment. The deployment record is a configuration account, not proof that
every external provider or user journey is production approved.

The live backend runs with `ENVIRONMENT=local` to permit demo adapters and
synthetic data. `EXTRACTION_PROVIDER=stub` means uploaded documents are not
processed by a live OCR provider there. Research questions and retrieved
statute text may be sent to Gemini under the recorded provider approval, but
that approval does not turn on real document extraction. Real evidence storage,
provider terms, retention, and the production matter-access adapter still need
decisions before accepting client documents.

## Verification and remaining limits

The platform has pytest tests for domain policies, API security, repositories,
services, migrations, workers, and PostgreSQL integration. The frontend uses
Vitest for logic and components and Playwright for browser journeys. CI runs
these checks along with type checking, linting, builds, and deployment-config
validation. The September 2026 test completion report records fifteen defects
found and fixed in its cycle. It also says sign-off is incomplete.

The most material limits recorded by the platform are:

1. The live document pipeline uses a stub. The research repository does not
   yet establish a lawyer-validated field-accuracy result for live extraction.
2. None of the current form templates is marked capable of registration-ready
   export. Legal wording verification belongs to the legal team. The test
   report verifies the refusal path rather than an approved-export success.
3. The deployed retrieval index is lexical only. Retrieval evaluation in the
   research repository uses provisional, unverified labels, so its scores do
   not establish legal reliability.
4. Clerk-backed browser journeys for approval, export, tenancy, and error
   recovery were not completed in the September test cycle. Several operational
   jobs and reminder paths are recorded as known gaps.
5. The live database, app, worker, and retrieval service share one VPS. The
   backups are on that same server, so an off-server copy remains an operational
   need.

This snapshot supports a claim that Draftly has an implemented, deployed
lawyer-controlled platform and tested safety refusals. It does not support a
claim that it already processes real client title bundles into legally ready
forms without further provider, legal, and end-to-end validation.

## Related systems and literature

This review was checked on 29 September 2026. It covers systems that overlap
with Draftly's property-document workflow, legal drafting, or source-grounded
research, followed by research on the component tasks. Product descriptions
come from their vendors and establish advertised capabilities, not measured
performance. Paper results concern their own datasets and jurisdictions; they
cannot be transferred to Sri Lankan title documents without new evaluation.

### Comparable products

| System | What its source describes | Relationship to Draftly |
| --- | --- | --- |
| [Orbital Copilot](https://www.orbital.tech/blog/ai-drafts-for-title-survey) | The closest workflow comparison. Its title and survey review uses source documents and a review checklist to produce editable issue lists, objection letters, and title and survey memoranda, with source links and version history. | Both connect property evidence, issue review, and drafting. Orbital's published workflow addresses commercial real-estate title and survey work; Draftly's implemented rule pack and forms address Sri Lankan RTA notarial matters. Orbital's product account is a vendor claim. |
| [Clio Draft](https://help.clio.com/hc/en-us/articles/24317070863899-Clio-Draft-Draft-and-Manage-Documents) | Populates court forms and Word templates from client and matter data, then presents a final review step. | It is a strong comparison for template-driven drafting and matter-data reuse. Draftly adds a specific evidence-to-verified-fact and RTA-check path before form binding. Clio's documentation does not establish a comparable Sri Lankan title-verification workflow. |
| [Harvey](https://help.harvey.ai/articles/getting-started-with-harvey) | Offers an assistant, knowledge sources, document analysis, drafting, and configured multi-step workflows for legal teams. | It shows the broader legal-assistant pattern, while Draftly concentrates its current rules on a defined land-registration workflow. Harvey's documentation does not establish Draftly's RTA-specific checks or forms. |
| [Lanka Law](https://lankalaw.net/our-services/) | Provides Sri Lankan case-law and legislation search and AI-assisted legal research. | It is a local comparison for authority discovery. Draftly also stores a matter's uploaded evidence, reviewed facts, checklist, form bindings, and approval events. The comparison is about published scope, not an independent feature audit. |

Orbital is the important challenge to any broad novelty claim: a property-law
product already links document review, issue spotting, and editable drafting.
Draftly's narrower contribution lies in encoding an RTA matter workflow,
versioned facts and rule packs, and lawyer-controlled form gates for Sri Lankan
notarial work. That contribution still requires lawyer validation and a
measured end-to-end evaluation. Clio Draft demonstrates that reusable forms and
matter-data population are established product features, so template filling
alone is not a defensible research contribution.

### Research on component tasks

| Work and publication status | Method and finding | Relevance and limit |
| --- | --- | --- |
| [CUAD](https://www.atticusprojectai.org/cuad/), Hendrycks et al., 2021, NeurIPS Datasets and Benchmarks | Expert-supervised labels identify 41 clause types across 510 commercial contracts. | Shows the value of legally supervised extraction labels. Its corporate contracts and clause taxonomy do not validate OCR or title particulars in Sri Lankan deeds. |
| [ContractNLI](https://aclanthology.org/2021.findings-emnlp.164/), Koreeda and Manning, 2021, Findings of EMNLP | Tests whether a contract entails, contradicts, or does not mention a hypothesis, with evidence spans; reports 607 annotated contracts and difficult exception language. | Supports evidence-linked review and explicit conflict or absence states. It studies contracts, not cross-document cadastral or registry checks. |
| [LegalBench-RAG](https://arxiv.org/abs/2408.10343), Pipitone and Alami, 2024, arXiv preprint | Evaluates retrieval of minimal relevant legal passages rather than only whole documents or large chunks; its dataset has 6,858 query-answer pairs. | Supports passage-level citations and a separate retrieval evaluation. Its legal corpus and questions do not test whether Draftly retrieves every applicable Sri Lankan provision. A local PDF is in `papers/qa-agent/2408.10343-legalbench-rag.pdf`. |
| [CLERC](https://aclanthology.org/2025.findings-naacl.441/), Hou et al., 2025, Findings of NAACL | Couples case retrieval with citation-grounded analysis generation and finds that strong generation can coexist with hallucination and weak retrieval. | Relevant to Draftly's legal-research component and its abstention policy. The benchmark uses US case law and does not assess notarial drafting. A local prepublication PDF is in `papers/qa-agent/2406.17186-clerc-case-retrieval-generation.pdf`. |
| [LawFlow](https://openreview.net/pdf?id=MsgdEkcLRz), Das et al., 2025, COLM | Records iterative legal work in business-formation scenarios rather than isolated question-answer pairs; its study finds a preference for AI support over autonomous completion of complex work. | Supports measuring the whole lawyer workflow and retaining review gates. Its participants and transaction type differ from Sri Lankan conveyancing. |
| [SinhaLegal](https://arxiv.org/abs/2603.04854), Lasandi and Jayatilleke, 2026, arXiv preprint | Builds a Sinhala legislative-text corpus from 1,206 Acts and Bills using OCR followed by extensive manual cleaning. | Establishes relevant local-language data work and the need to check OCR output. It is a legislative corpus, not a test of mixed-script client deeds or Draftly's extractor. A local PDF is in `papers/ocr/2603.04854-sinhalegal-a-benchmark-corpus-for-information-extractio.pdf`. |
| [Large Legal Fictions](https://arxiv.org/abs/2401.01301), Dahl et al., 2024, arXiv preprint | Finds frequent unsupported answers to verifiable US case-law questions and difficulty correcting false user premises. | Motivates source checks, abstention, and human verification. Its figures are for the studied models and US cases, so they are not a Draftly error rate. |

The studies divide the problem into extraction, evidence identification,
retrieval, and professional workflow. CUAD and ContractNLI provide supervised
examples of identifying what a document actually says. LegalBench-RAG and
CLERC show why retrieving the right authority needs its own evaluation, before
judging a generated answer. LawFlow shifts the unit of analysis to the full
sequence of legal decisions. SinhaLegal provides a Sinhala legal-text resource,
but its manual cleaning also warns against treating raw OCR as authoritative.

The gap relevant to Draftly is an evaluated path from a mixed property-document
bundle to verified RTA particulars, check outcomes, and a lawyer-approved
instrument, with source and decision provenance at each step. The reviewed
papers do not evaluate that complete task. The product comparison also does
not establish that no other system does it: this is a targeted review, not an
exhaustive market survey. A credible next evaluation would have lawyers label
document fields and required authorities, then measure exact identifier
accuracy, evidence-span correctness, check errors, time spent reviewing, and
whether an unsafe draft or export is refused. The live Draftly demo cannot yet
claim those end-to-end outcomes.

## Source map

All paths below are in the sibling `draftly-platform` repository:

- `backend/src/bootstrap.py` and `backend/src/modules/`: mounted APIs and
  implementation structure.
- `backend/ARCHITECTURE.md` and `backend/contracts/rta-rule-pack.v1.json`:
  module boundaries and rule-pack contract. The architecture guide's old
  count of implemented modules predates newer party, billing, research,
  assistant, and practice-operation code; use the routers for current scope.
- `frontend/src/app/`, `frontend/src/components/`, and `frontend/src/lib/api/`:
  routes, screens, and API clients.
- `deploy/PRODUCTION.md` and `deploy/docker-compose.vps.yml`: live deployment
  shape, settings, and declared limitations.
- `docs/review/testing-report.md`: September testing evidence and known gaps.
- `docs/draftly-rta-matter-workflow-v1.md`: product workflow and legal design;
  it is a specification, so its proposed features are not all implemented.
