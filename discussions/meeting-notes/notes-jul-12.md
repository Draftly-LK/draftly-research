# Meeting Notes — 12 July 2026

## About this document

A comprehensive synthesis of a mentoring discussion for the **Draftly** project,
reconstructed from six audio recordings made on 12 July 2026 (roughly 7:36 AM to
11:27 AM) and their Sinhala speech-to-text transcripts in
`discussions/transcripts/`.

- **Mentor / domain expert:** a senior Sri Lankan lawyer and notary who also
  lectures at Law College and has a commercial-law LL.M. (Australia). He designed
  a detailed conveyancing / notarial-practice curriculum (a ~23–24 page, 20-topic
  syllabus) and holds the source statutes, sample deeds, and worked examples.
- **Team:** the three Group 06 students building Draftly.

**Reliability note.** The transcripts are automatic Sinhala STT and are noisy;
some legal terms, numbers, and names came through garbled. Points below are
interpreted in good faith and marked *(uncertain)* where the source is unclear.
Verify numbers, section references, and dates against primary sources before
relying on them.

**Privacy note.** The mentor taught partly through a real client property chain
(a specific condominium matter with named parties and deed numbers). Personal
names, deed numbers, and addresses are **omitted** here and parties are referred
to by role. The concrete worked example lives in the source transcripts and in
`data/raw/`; do not copy that PII into committed or public files.

---

## 1. Strategic guidance (the big picture)

- **Build for the *current* legal system first; do not try to reform it.** He is
  emphatic: there are two very different jobs — (a) *help users operate the
  system that exists today*, and (b) *improve/redesign the system*. Start only
  with (a). Trying to "improve" entrenched government processes first is
  politically hard and kills projects ("you go to a department, a junior suggests
  a change, and they cut you down"). Get useful and popular first; propose
  reforms later.
- **Anchor the project to real professional need.** The goal is a tool notaries
  and lawyers actually use daily — encode an experienced notary's knowledge so
  that a junior clerk (even a fresh O/L-qualified school leaver) can do the work
  to the standard of a notary with ~10 years' experience.
- **Do the work alongside real life / real practice**, iterating with practising
  professionals rather than in isolation. He offered continued mentoring and
  domain validation.
- He has been thinking about and building materials for this since ~2010
  (free training groups, later interrupted by COVID and by his Law College work).

---

## 2. The three sources of law (framing for the whole system)

He grounds everything in the three sources of applicable law:

1. **Statutory law** — rules written in the statutes ("do it this way").
2. **Case law / common law** — judge-made law from decided cases.
3. **Law of equity** — the equity branch (English origin, chancery courts,
   ~1796 *(uncertain date)*). Equity ignores heavy technicalities and looks at
   fairness. Example doctrine he stressed: **unjust enrichment** as a fallback
   cause of action — e.g. you lent money and cannot prove it with a stamped
   document, but the other side has been *unjustly enriched*; that is a
   recognised cause of action worldwide and can carry a case where strict proof
   fails.

Teaching order for any professional skill: **philosophy → concepts → principles
→ rules → regulations.** Law College teaches only the *rules* layer, which is why
practitioners often lack the understanding above it. (He maps this to degree
levels: LL.B teaches principles, Master's teaches concepts, PhD teaches
philosophy.) For the *product*, though, the system only needs to deliver the
**rules** layer to users; the higher layers stay internal / are taught
separately.

---

## 3. Conveyancing vs Litigation — and why conveyancing first

- **Conveyancing** is comparatively mechanical and rule-driven — "basically like
  copy-and-paste." It is well-suited to a system and should be **built first**.
- **Litigation** is a large, genuinely creative area (drafting arguments, not
  copying) and is far more complicated. Handle it **later**, function by
  function.
- Decision for v1: **start with conveyancing.**

---

## 4. Conveyancing = the 6 functions of a notary

The core of the system. A notary's conveyancing work has **six functions, in
order**, and the rules for each are in the statutes (so they can be encoded):

1. **Examination of title** — check the title before anything is drafted.
2. **Drafting** of the deed.
3. **Execution** of the deed (design/handling of signing).
4. **Stamping** of the deed.
5. **Attestation** of the deed.
6. **Registration** of the deed.

**Scope decision for the build:** implement **four of the six now** — examination
of title, drafting, execution, attestation — and **defer registration** (the most
complicated). Stamping has relatively few rules. He wants the team to "type"
(tackle) these as: *Examination of Title*, *Drafting of Deeds*, *Execution of
Deeds*, *Attestation of Deeds* — and **not** *Registration of Deeds* yet.

### 4.1 Examination of title (detailed)

The most involved function. The mentor breaks it into ordered steps, and each
step, once entered, pulls in the relevant rules and keywords (which then drive
case-law lookup):

1. **Land search.** Go to the registry and read the records — every transaction
   on the property is recorded.
2. **Identify the current owner**, then trace **prior owners** — look back
   roughly **30 years**, across the relevant registration systems (he mentions
   needing to check across ~three systems).
3. **Encumbrances / income permissions** — are there mortgages, loans, charges?
   (He calls these relatively simple checks.)
4. **Local-authority documents** — Pradeshiya Sabha / Urban Council / Municipal
   Council documents; there is a set of tests here.
5. **Identification of the parties** — confirm who the parties are.

The output of doing all this is the examination-of-title result. The "steps"
model (step 1, 2, 3 …) is the retrieval pattern for the whole product: typing a
step surfaces the next set of rules, and the step's keywords are used to find the
applicable cases in the case-law corpus.

### 4.2 Drafting

- Mostly done by copying an existing deed of the same type and adapting it — swap
  in the correct grantor/grantee (transferor/transferee, vendor/purchaser),
  property schedule, etc. "Drafting is where the difficulty is" in conveyancing,
  but it is still largely derivative.
- Historic English drafts (from colonial-era notaries) run straight through; the
  English drafting style was inherited.

### 4.3 Execution (signing)

Rules include:

- The signing parties must attend together.
- Required presentation/attendance rules.
- Two witnesses required.
- Photographs of the parties/documents are required (a rule set of ~25 fairly
  simple rules) *(number uncertain)*.

### 4.4 Stamping

- Rules on what type/amount of stamp duty applies and how much to affix.
- Relatively small rule set.

### 4.5 Attestation

- A short certified summary of the whole transaction that the lawyer/notary
  certifies (the attestation). Relatively small rule set.

### 4.6 Registration (deferred, but explained)

**Four registration systems coexist in Sri Lanka** (a "mixed" landscape), and
there are ~five recurring title problems the systems address to varying degrees:

- **Deed registration (old system).** Bringing a deed does not give *conclusive*
  proof of absolute ownership. Weakness: **adverse possession** — if someone
  occupies the land ~10 years, the true buyer who paid can lose out; after the
  period the possessor can gain the land and the paying purchaser gets nothing.
  Beyond a point the court will not re-open questions.
- **Title registration (1998, "Bim Saviya").** Addresses the ~five core problems,
  but covers only about **10%** of the country.
- **Condominium property.** Solves roughly **half** of the five problems.
- **Special-area registration.** Solves roughly **25%**.

(All percentages *(uncertain)* — captured as he said them.) Net: Sri Lanka has a
mixed registration regime, which is why examination of title is hard.

---

## 5. The notary's real-world pain points (what the product should relieve)

- **Notaries get caught by fraud unknowingly** and can be prosecuted / disciplined
  — he has seen junior notaries in tears over it. The biggest fear is being
  penalised for a defect they didn't detect.
- **Due diligence is the shield.** If a notary has followed the proper checklist
  / due-diligence steps, they cannot be charged — the profession has effectively
  agreed this with the relevant department. So a system that guarantees the steps
  were followed directly removes the notary's liability risk.
- **Identity verification is now legally required.** A recent amendment requires
  the notary to check the parties' National Identity Cards and to state in the
  attestation ("notary's certificate") that identities were personally verified —
  because impersonation fraud has been rising. The system must capture NIC checks
  and produce that certification.
- **Notarial licence must be renewed annually** (typically March); without
  renewal the notary cannot practise the next year. The licence is sworn before
  the High Court; oaths/declarations are made before a judge. (He tied this to
  constitutional schedules — 4th/5th/7th schedules *(uncertain)* — for the forms
  of declaration, including language provisions.)
- **Jurisdiction (bala pradeshaya / territorial area).** Every notary has a
  territorial area. A Colombo-area notary can write a deed for land in Vavuniya,
  **but the Vavuniya party must come to the notary's Colombo area** — the notary
  cannot go to Vavuniya to execute it. Executing outside one's area is legally
  defective, and the first question a court asks about a deed is *where it was
  executed*. The system must respect notary jurisdiction rules.

---

## 6. Litigation (future scope — captured for later)

Although out of v1 scope, he explained the litigation workflow so it can be
built later:

- **IRAC method** for written submissions: **Issue → Rule → Application →
  Conclusion.** He stresses this method is not written down in any Sri Lankan
  textbook, yet it is how a problem should be solved: state the issue the court
  must decide, state the current law, apply the law to the facts, give the
  conclusion. He has a system built around IRAC that, if given to Sri Lankan
  lawyers, would push everyone to one consistent method and reduce errors.
- **Case flow / documents:** a case starts with a **plaint (පැමිණිල්ල)**; the
  other side files **objections**; the plaintiff files **counter-objections /
  replication**; both sides file **written submissions**; the judge then gives
  **judgment**. On appeal the parties' labels change (appellant/respondent) and a
  matter can pass through ~three stages/levels.
- **Petition (පෙත්සම) structure:** caption/heading (ශීර්ෂය), an averment that the
  court has **jurisdiction** to hear the matter, the parties, and it must be
  accompanied by an **affidavit (දිවුරුම් ප්‍රකාශය)** in which the client swears
  the facts. The case number is assigned only at registration (entry in the
  court books), not on the petition itself.
- **How the tool helps litigation:** the client writes the raw facts in plain
  language; the system converts that + the document set into a properly
  structured legal petition/affidavit/submission. A lawyer still reviews and
  completes it — the tool does most of the drafting, the lawyer finishes the last
  bit. He noted Gemini can already draft such letters but does **not** know the
  required local structure/format — encoding that structure is the value.
- Sri Lankan courts are slow (huge backlog — he cited on the order of ~1.1
  million pending cases *(uncertain)*); he has ~100 ideas for reducing delays,
  for later. He would also standardise the **plaint into a fixed format / boxes**
  (who is plaintiff, who is defendant, the issues, the evidence) so plaints stop
  being rejected for form defects.

---

## 7. The worked example (condominium title matter) — anonymized

He walked through a real matter end-to-end to show what the system must produce
(names, deed numbers, and addresses omitted; see `data/raw/`):

- The property is a **condominium parcel** (a floor-area unit, no land of its
  own), in a residential complex built by a **developer company**.
- The **pedigree / chain of title (පෙළපත් සටහන)** traces ownership through a
  chain: individual owners → the developer → the present owner. Individual lots
  (referred to as Lots B, C, D) were **acquired via several deeds and then
  amalgamated** into one holding by the developer.
- To create the condominium, an ordinary **survey plan is converted into a
  condominium survey plan** (via the Condominium/Apartment authority), and the
  building is built as a co-owned (සහාධිපත්‍ය) building under different
  regulations from an ordinary house. The owner then executes a **declaration
  deed** declaring it condominium (co-owned) property; ownership doesn't change,
  only the property's legal status.
- From the pedigree the notary produces the **title report (හිමිකම් වාර්තාව)** —
  narrated as: description of the deed(s) on one side, description of the land/lot
  on the other (who surveyed it, plan number, date, etc.). There is a standard
  order/format for writing a title report; the system should enforce one
  consistent standard (as taught at Law College) rather than each lawyer's own
  order.
- **Condominium section 9 *(uncertain)*** reportedly says absolute ownership
  arises on registration — but that sits awkwardly with how title flows from the
  ordinary registry; he flagged the inconsistency.

---

## 8. Documents, and the "everything must tally" rule

**Input evidence documents** for a matter: current deed, prior deeds (~30 years),
gift deeds, survey plan / condominium plan, land-registry (path-iru) extracts,
municipal/assessment documents (with the **assessment number, වරිපනම් අංකය**),
identity documents (NIC / passport), and existing title reports/pedigrees.

**Core checking rule:** the details must **tally across documents** — the deed's
schedule, the survey plan, and the municipal assessment record must all match
(same lot, same assessment number, same extent/boundaries). Cross-matching these
is central to examination of title and to red-flag detection.

**Output documents the system should generate** (for lawyer review):

- Pedigree / chain-of-title (පෙළපත් සටහන)
- Title report (හිමිකම් වාර්තාව)
- Abstract of Title Deed / **T-form / AT form** (ඔප්පු සාරාංශය) — note: the online
  AT form exists only for Colombo MC; other councils use a large paper "ඔප්පු
  සාරාංශය" sheet filled by hand.
- Certificate of ownership
- Assessor / municipal ownership-transfer letter
- The **deed schedule (උපලේඛනය)** and the new deed itself (e.g. Deed of Transfer,
  Transfer of Condominium Property)
- Missing-document checklist and red-flag / inconsistency report

He also noted: when a document (path-iru / deed) is unclear or partly illegible,
the system should flag the specific spot and ask the user to read/confirm it,
then continue — rather than silently guessing.

---

## 9. Data and sources the mentor will provide

- **His 20-topic syllabus + subtopics** (soft copies; ~23-page detailed syllabus
  he authored, plus the original 2-page Law College syllabus for comparison).
  This is the curriculum behind Draftly's `topics/` tree. He will email it; the
  team can extract the **keywords** per topic/subtopic to drive research.
- **~50–55 relevant statutes** for the notarial functions, which he holds as hard
  and soft copies and will share (also available online / LawNet).
- **Case law.** Total volume is very large (he cited figures on the order of
  100,000–500,000 cases *(uncertain)*), but only a handful actually apply to
  conveyancing deeds (~5 core ones). **Restrict to ~25,000 important cases** for
  study. Sources: LawNet (some paid), Lanka LawNet / free sources (no fee),
  paralegal websites. For each case, the **head note** is the key part to read /
  explain.
- **Registrar-General's handbook / regulations.** Officials have it but don't
  share it with lawyers; the process/regulations are otherwise hard to find (not
  in statutes or case law). Get it **officially through the university** (a formal
  request from the campus, not a private request) so the sources are used
  legally.
- **Sample deeds** — he wants ~50–60 deeds scanned; annotation may need more
  because of the variety of characters/handwriting. He has **16 condominium
  transfer deeds** and other samples (title reports, pedigrees, T-forms,
  assessor letters) as soft copies.
- **Field research:** send a small team to the Colombo Land Registry and the
  Registrar-General's office to research the process and its gaps; some helpful
  registrars are willing to explain. Talk to them in the field.

---

## 10. Product / scope decisions from this meeting

- **First deliverable:** a system/app "for notaries" that encodes the notarial
  knowledge so any user can work at an experienced notary's standard.
- **Build 4 of the 6 conveyancing functions now** (examination, drafting,
  execution, attestation); defer registration; stamping is light.
- **Two tracks, in order:** (1) help users operate the existing system — do this
  first and get popular; (2) improve the system — later, propose to government.
- **Input/output pairs for evaluation:** feed sample cases (deeds, plans, etc.)
  in and show the system produces the correct outputs; use his existing
  hand-prepared documents as ground truth. Demonstrate the system "working
  correctly" on real matters.
- **Checklist behaviour:** rather than a step-by-step checklist the user ticks,
  the system should accept the uploaded documents, then tell the user which items
  are **missing** ("these are missing, send them"). Once the missing items are
  supplied, it proceeds. (He explicitly did *not* want a heavy manual checklist —
  the system infers gaps.)

---

## 11. Curriculum: the 20 topics

He built the syllabus as **20 topics**, broken into subtopics, with a theory part
first and then a step-by-step applied part. The topics named/alluded to (matching
the project's existing `topics/` set) include: Introduction to Conveyancing;
Registration of Documents; Registration of Title; Condominium Property; Formation
of Deeds; Drafting/Instruments; Stamping of Deeds; Duties & Functions of a Notary;
Examination of Title; Special Laws; Temple/Devala/Nindagam properties; State
Lands; Power of Attorney; Last Wills; Trust Deeds; Local Authority/UDA
Regulations; Drafting of Deeds; Other Related Statutory Laws; Case Law on
Conveyancing; Criminal & Civil Liabilities of Notaries.

Teaching structure he proposes for the course (context, not v1 build): ~3 months
learning principles → applied steps → **internship** rotating through ~10
institutions (land registries, councils, Registrar-General's office) → tutorials.
For the *system*, only the applied rules/steps are exposed; principles/concepts
are taught separately.

---

## 12. Business / deployment thoughts (his framing)

- Run **one-day workshops per Law College batch** (he has done ~4 seminars /
  workshops, e.g. a 50-question discussion format, splitting a group into two for
  a small contest). Workshops double as advertising → funnel users into the
  program.
- Position it as a **consortium** with the university and Law College rather than
  a lone product; that brings recognition (his name, examiner status, etc.).
- **Keep the source code private** — do not open-source; there is a monetisation
  path. Give the university a "shape"/access under the consortium, but retain the
  code.
- Social value framing: most people can't afford good lawyers; a system that lets
  a low-knowledge lawyer/notary serve clients well reduces wasted money and time
  for the public, the profession, and the country.

---

## 13. Team's own technical notes (from the same recordings)

Captured because they shape the build; these are the students', not the mentor's:

- **Grounding / hallucination risk.** A team member relayed a warning that Gemini
  "lies creatively" — confidently fabricating in a way that's hard to distrust.
  The product therefore cannot rely on ungrounded generation; outputs must be
  grounded in and traceable to the real documents and statutes, or "the product
  fails." (This directly motivates the citation-first, retrieval-grounded design.)
- **Retrieval architecture.** Because there are only ~50 statutes, a plain RAG may
  not be enough; they discussed a **knowledge graph** or an **agent-memory / "R-mem"
  style** system, and agreed to **benchmark for efficiency first** before
  committing. (Consistent with the BookRAG tree/graph direction in `CONTEXT.md`.)
- **OCR / extraction.** Reading deeds is hard; consider Document AI custom OCR vs
  API cost (a large per-page cost was mentioned *(figure garbled)*); prefer
  format/layout-based reading where possible.
- **Dataset / annotation.** ~50 deeds is a starting point but the variety of
  handwriting/characters means more may be needed; prioritise getting the
  **workflow correct** over sheer volume. Build a dataset with lawyer-verified
  chain-of-title as ground truth.
- **IP / hosting.** Keep source private; give the university access as a
  shape/consortium; a finance/monetisation path was mentioned.

---

## 14. Action items / next steps

- **Mentor to send:** the detailed 20-topic syllabus (with subtopics/keywords),
  soft copies of the ~50–55 statutes, sample deeds (~50–60), the 16 condominium
  transfer deeds, sample title reports / pedigrees / T-forms / assessor letters,
  and pointers to free case-law sources.
- **Team to research (split the work):** one member on **examination of title /
  land search** case law; another on **drafting of deeds** case law; then
  **execution** and **attestation**. Use each step's keywords to find and read
  cases (focus on head notes). **Skip registration for now.**
- **Get the Registrar-General handbook officially via the university.**
- **Field visit** to the Colombo Land Registry and Registrar-General's office to
  document the real process and its gaps.
- **Build a small demo app** proving the flow on a real matter (documents in →
  pedigree / title report / T-form / assessor letter out), with grounded,
  reviewable output.
- **Benchmark** retrieval approaches (RAG vs knowledge graph vs agent-memory) for
  efficiency before committing.