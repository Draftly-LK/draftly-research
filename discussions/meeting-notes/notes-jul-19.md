# Meeting Notes — 19 July 2026

## About this document

A comprehensive synthesis of a mentoring discussion for the **Draftly** project,
reconstructed from two audio recordings made on 19 July 2026 (9:41 AM and
11:16 AM sessions) and their Sinhala speech-to-text transcripts in
`discussions/transcripts/` (Chirp-2, average confidence 0.815 and 0.794).

- **Mentor / domain expert:** the senior Sri Lankan lawyer and notary from the
  12 July sessions — Law College lecturer, set seven notary exam papers, runs a
  legal-education YouTube/TV presence (Siyatha, Rupavahini/Nugasewana).
- **Team:** the Group 06 students (all three at the morning session; two at the
  later session). A junior law student the mentor knows is being added for
  case-law work.

**Reliability note.** The transcripts are automatic Sinhala STT and noisy; the
final third of the 11:16 recording is largely unrecoverable (STT loops/noise).
Points below are interpreted in good faith and marked *(uncertain)* where the
source is unclear. Verify statute sections, dates, and figures against primary
sources before relying on them.

**Privacy note.** Client anecdotes, party names, and phone numbers from the
recordings are omitted or reduced to roles. Do not copy PII from the source
transcripts into committed or public files.

---

## 1. The headline decision — the first app is "notary functions under the RTA"

The product scope was narrowed decisively:

- An app covering the **whole notarial profession cannot be built in four
  months** (mentor's opening position).
- Sri Lanka has **four land-registration regimes**, adopted as the team's
  working vocabulary: **RDO** (Registration of Documents Ordinance 1927 — the
  pattiru/folio system), **RTA** (Registration of Title Act No. 21 of 1998 —
  Bim Saviya title registration), **Apartment Ownership Law** (condominium
  registration), and **Special Area registration** (an 1800s statute — "1878"
  *(uncertain which enactment)*). Drafting differs completely under each.
- **Decision: build for the RTA / Bim Saviya system first**, starting at the
  post-certificate stage (transactions on registered title). Initial
  compilation is background knowledge only.
- Why RTA won:
  - **No pattiru OCR problem** — handwritten folios are the hardest thing for a
    machine to read; RTA documents are machine-readable.
  - **~90% of lawyers don't know the RTA** — a genuine market gap and service.
  - It is the **simplest, most self-contained** system ("lawyers only find it
    hard because they've never read it").
  - It is **the future**: the mentor expects the whole country under title
    registration in **10–15 years**.
  - It is **~90% statute law**, so registries and officials follow statute, not
    case law — a statutory-knowledge app can satisfy **90–95% of notaries'
    needs**.
- A team member believes the RTA-scoped build needs **under three months**;
  the mentor's broader-version guess was 6–12 months. Not reconciled.

## 2. Why land law is hard (context the app must encode)

- The two core land problems: **identifying the land** (boundaries) and
  **determining ownership**. Historical survey coverage was partial until
  modern GPS mapping; written boundary descriptions could not be reliably
  located, so boundary disputes flourished.
- The 1927 deeds-registration system **does not cure defects**: forged deeds
  can be registered, undivided shares multiply, and both core problems
  survived. England moved to title registration around 1921; Sri Lanka got the
  RTA in 1998 with Australian (Torrens-style) aid.
- Other categories the team must know of: **LRC lands** (1973 land reform,
  holdings over 50 acres), **LDO grants**, and **Nindagam / Devalagam /
  Viharagam** lands under separate regimes.

## 3. The RTA in depth (content walkthrough)

- **Two halves of the Act:** (1) **initial compilation** — the state procedure
  up to the first title certificate; (2) **subsequent transactions** — where
  notary work and Draftly begin.
- Initial compilation: Minister gazettes an area (e.g., a municipal-council
  limit) → Commissioner of Title Settlement asks the **Surveyor-General** for a
  **cadastral map** (zones/sheets, whole-area) → claims are called by gazette →
  claimants' pattiru are checked at the registry → titles determined
  **first-class / second-class** (s.14 *(uncertain)*) → final gazette →
  schedule transmitted to the **Title Registrar**; **entry in the register is
  the registration** and confers ownership. State lands must also be brought
  in. Old folio books are formally **closed with a seal** on conversion.
- **Section 15 correction (doctrinal point):** undivided co-owned land **does**
  receive a title certificate, with a **manager appointed** — field advice to
  "divide first and come back" is wrong. Disputes can go to a conciliation
  board or court.
- **Key ownership effects:** entries are **conclusive evidence** and confer
  **absolute ownership** (ss.32–33); a first-class title effectively cannot be
  challenged in court; a defrauded innocent owner is **compensated from a
  state insurance fund routed through the Central Bank**; **prescription does
  not apply** to title-registered land (eliminating the squatter/10-year
  possession problem and ~17-year land cases); **undivided shares cannot be
  written** (killing partition litigation — e.g., 20 perches must be formally
  subdivided into two lots with two certificates; a 6-perch lot that cannot be
  split three ways becomes a condominium instead).
- **Transactions (s.38 onward):** every dealing uses **prescribed forms in the
  gazettes** (transfer, gift, lease, notary's attestation shown). **Three
  gazettes** hold the formats and rules — one is 69 pages, "nobody reads it";
  it contains counter-practice details (two copies tendered, one to the folio,
  which forms to sign where). The mentor will supply the gazettes.
- **Subdivision:** application + private surveyor → Surveyor-General
  certification → registry issues two certificates. **Succession:** ownership
  passes to heirs, partition actions cannot be filed; second-class title can be
  upgraded (after 10 years *(uncertain)*).
- **Drafting sequence rule:** a transfer draft must go for **stamp-duty
  valuation first**, and the assessed value is inserted into the deed before
  execution — the app must encode this ordering.

## 4. What the app should do (functional spec)

- **Reject the exam-question paradigm.** The mentor critiqued the current
  prototype: it answers like Law College exam questions (testing rule
  knowledge). Practitioners need **step-by-step workflow guidance**: "Step 1,
  Step 2, Step 3 — when the steps are done the job is done," serving both the
  new lawyer (zero knowledge) and the experienced one.
- **Function flows:** clickable transaction types — sale, mortgage, lease,
  gift, transfer, attestation ("six functions" *(uncertain count)*) — each
  opening its step list, applicable rules, and prescribed forms.
- **Deed generation:** given the particulars, produce **the deed itself plus
  the steps**; identify errors in a user's draft.
- **Voice + Sinhala:** dictate deed particulars by voice; answers deliverable
  by voice ("the client sits opposite; the lawyer turns the screen"); read and
  listen modes; **Sinhala content is required**, with a UI language selector.
  Landing page = the four registration systems (only RTA active initially).
- **FAQ layers:** per module, a *Frequently Asked Questions* and a *Frequently
  Wrong/Mistaken Questions* bank (~100–300 questions; roughly 100 per topic),
  plus **cautionary notes** under each function sourced from case law
  (including obiter dicta).
- **Reminders/notifications:** anchored on the Registration Rules — e.g., the
  notary's **monthly list must reach the registry before the 15th** of the
  following month (s.27 *(uncertain)*); since the app holds the deed data it
  can **auto-generate the monthly list** and remind the notary. The mentor
  called this feature alone worth the subscription.
- **Evaluation:** maintain a **gold set of correct questions and answers** and
  score the system by closeness to expected answers; print model outputs on
  paper for the mentor to mark up (his preferred review loop).

## 5. Content-construction method (the exam-paper technique)

- Model the knowledge base on the mentor's exam papers (he set seven; his are
  organised one-question-per-topic). Extract points from papers without
  adopting exam logic. Example expected answer: RTA **ss.32–33** for
  conclusive evidence/absolute ownership; registrar's **5–6 grounds** for
  refusing a deed registration.
- **Workflow:** one member drafts the **question set** per function (starting
  with examination of title: land search → extracts → encumbrances → recommend
  title; also "how to identify executing parties and witnesses") → the mentor
  answers and fills gaps (**next week**) → the team feeds his answers to the
  AI to see if anything can be added → the surplus becomes sub-questions or
  FAQ items ("together we produce a perfect answer").
- **The "55 rules" (Rules of Notaries)** must all be folded in; the mentor has
  the material **split into ~20 topics** already. Possibly a separate
  module/app ("Rules of Notary"), since it stems from the Notaries Ordinance
  rather than the RTA.
- **Notaries Ordinance vs gazette controversy:** authorities claim the
  Ordinance no longer applies to RTA work and point to a gazette; the mentor's
  firm position is that **a gazette cannot override an Ordinance**. The app
  must state the correct current position plainly (no confusing "it used to be
  X" histories). The Prevention of Frauds Ordinance also continues to apply
  *(uncertain)*.
- Old case-law principles become Q&A items. Worked example: a deed signed by
  all four (transferor, transferee, two witnesses + notary) at one time but
  bearing the wrong date **is valid** — under **s.2 Prevention of Frauds
  Ordinance** the date is immaterial; simultaneous execution is what matters.
  Answers must be **substantiated with the judgments**.

## 6. Case law strategy

- Case law is **out of core scope for the RTA module** (statute-dominated),
  but is the source for cautionary notes, FAQ items, and validity questions.
- Sourcing: AI tools surface almost nothing pre-2005; **NLR (pre-1998) lives
  only in books**. Plan: **download NLR/SLR from CommonLII** (coverage from
  ~1900; SLR to ~2005/2012 *(both figures mentioned)*), consider the
  subscription, and supplement with the **mentor's SLR soft copies** (offered).
- Method: judgments carry **headnotes with the holding** — extract the rule
  per case into a **database the AI queries when answering** (the team noted
  ~**2,200 rules already extracted**, earliest ~1900/1903 — this matches the
  existing Draftly rule-extraction pipeline). Caveat: modern headnotes state
  rules less crisply than older reports.
- Statute-timeline problem flagged: old cases attach to old statutes
  (1880s–1930s), so case→current-statute mapping needs design; mitigated by
  the RTA scope.
- **A dedicated person is assigned to case law** — the junior law student the
  mentor is introducing (he was expected that morning; contact number was
  dictated but the digits are unreliable in the transcript).

## 7. Business, funding, and positioning

- **Government funding declined in principle:** a contact (met via an event)
  offered a Ministry of Digital Economy-linked fund through the university.
  The mentor pushed back hard: taking it makes the product a **government
  project** (IP/copyright to the state, no commercialisation, years of
  approvals). Preferred institutional channel: **BASL** (Bar Association),
  possibly with a membership/commission arrangement *(uncertain)*.
- **Strategy: "get a foothold first"** — once popular, data and momentum
  compound and the position is defensible.
- **Pricing/economics anchors:** even at **Rs 5,000** the app is cheap for a
  notary; testamentary practice economics (typical fee ~Rs 5 lakhs; ≥500
  matters over a 30-year practice; mastery cuts paper time to ~3 hours; the
  app to ~half an hour) show the value story. Marketing must be planned
  deliberately; the mentor's media reach (YouTube — a Deed of Gift video with
  ~24,000 views; 10–15 Siyatha programs; ~4 Rupavahini appearances) is a
  channel; his publicity has brought real matters (one worth ~Rs 5 lakhs).
- A business should be **50/50 service and profit** (mentor's philosophy).
- Later products: the other three registration systems; litigation modules
  built on the mentor's **25-question-per-action template** (his programme
  surveyed ~100 case types and selected the ~25 most common — testamentary,
  partition, land, divorce, etc.); a standardised **plaint-drafting** tool
  (could save ~2 years per case) is possible later, potentially
  government-facing. The mentor separately holds **~100 reform points** on
  eliminating court delays — a distinct track, not this product.

## 8. Materials, people, and logistics

- **Handed over / promised by the mentor:** a stack of his papers at the
  meeting (to be scanned into questions); his master notes file (scanning
  already begun); the **three RTA gazettes/formats**; his **recorded class
  videos including Bim Saviya** (via his clerk); his **SLR soft copies**; a
  **lawyer contact's number** ("tonight") to be briefed on the project from
  the beginning; question-set review **next week**.
- **App naming method:** pick a **working name now, finalise at the end**
  (film-title approach); generate 10–15 candidates; concept: "all the answers
  are in here — basic functions of a notary under Registration of Title"; no
  fancy English; logo/branding deferred.
- **Team process:** stop ad-hoc building — hold **one full planning meeting,
  then split the work three ways** and build in parallel; two workstreams run
  simultaneously (content/question bank and the system build); UI structure
  plan to be discussed **tonight**; a UI already exists but lacks a structured
  plan; landing-page video to be **AI-generated as a ~1-second loop** (member
  has ~100,000 credits at ~100 credits per generated second; font rendering a
  known risk).
- **Team composition:** proceed with the current members ("they have the
  knowledge"); one discussed candidate is "not keen", another lacks dev
  skills; the junior student joins for case law.
- **Tooling chatter:** document/text extraction experiments live in the
  meeting (Claude, Gemini, ChatGPT, WhatsApp Web, Google-Translate photo OCR);
  GCP free credits (~$1,000) fund the pipeline; a second account idea floated,
  unverified. A stray English fragment suggests the team must still "complete
  part of the data science component" for the university even though the
  product framing is app-first *(uncertain)*.

## 9. Decisions (consolidated)

1. First app = **notary functions under the RTA 1998 (Bim Saviya)**, post-certificate transactions.
2. Step-by-step practitioner guidance replaces the exam-question paradigm.
3. Content built as a **question bank per function**, mentor-answered, AI-augmented, with FAQ + frequently-wrong-questions + cautionary case-law notes.
4. All **55 Rules of Notaries** included (mentor's 20-topic split); possibly its own module.
5. Case law: secondary layer; **CommonLII download + mentor's SLR soft copies + headnote rule database** queried at answer time; dedicated case-law person.
6. **Gold Q&A evaluation set** + printed mentor review loop.
7. **Sinhala + voice** required; four-system landing; deed generation with stamp-duty-first sequencing; monthly-list auto-generation + reminders.
8. **Decline government funding**; BASL as the institutional channel; working name now, final name later.
9. Full planning meeting → three-way work split; UI plan tonight; AI-generated landing video.
10. Doctrine: undivided co-owned land **does** get a certificate with an s.15 manager.

## 10. Action items

- **Content lead:** build the question set (examination of title first); scan the mentor's papers into questions.
- **Mentor:** review/fill question-set gaps next week; hand over gazettes, notes, 20-topic rules material, recorded classes, SLR soft copies; send the lawyer contact tonight.
- **Data/engineering:** verify CommonLII bulk download feasibility (+ subscription); build the judgment/headnote rule database for retrieval; extend the prototype from Topic-3 statutes to the RTA set + three gazettes.
- **Product:** 10–15 name candidates; UI structure plan (tonight); 1-second AI landing video; language selector; four-section landing.
- **Team:** gold Q&A set; voice dictation; Sinhala delivery; notification/monthly-list feature; plan marketing/pricing; loop in the junior student for case law; full planning meeting then split.

## 11. Open questions

- Exact timeline (mentor 6–12 months vs member <3 months for the RTA scope).
- Whether the mentor's notes can be shared before the structure is typed up (contradictory statements).
- CommonLII bulk-download feasibility and subscription decision.
- Rules-of-Notary as separate app vs module.
- The Notaries Ordinance vs gazette dispute — the app states the mentor's position; authorities may disagree.
- How many RTA cases actually exist (assumed few; to verify).
- Which 1878 enactment the "Special Area" system refers to; the s.27 monthly-list citation; the "six functions" list — all garbled in the STT and needing confirmation with the mentor.
- Roughly the last 20 minutes of the 11:16 recording are unrecoverable noise; anything said there is lost — worth asking the team if key decisions were made late in that session.
