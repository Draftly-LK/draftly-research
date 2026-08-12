# What to say — supervisor meeting, 12 August 2026

Speaking script. `today-meeting-notes.md` has the full detail and the tables if
anyone wants to dig in. Numbers to remember: **810 to 94**, **397**, **95%**,
**3 versus 65**.

---

## 4. The blocker and the ask

Allow about one minute for this section. This is the main point to raise with
the supervisors.

> There's one thing I'm stuck on and would like guidance.
>
> We have the section numbering for 66 statutes but the actual text for only 39.
> The missing ones are mostly old Ordinances — Insolvency 1853, Service Tenures
> 1870, Marriage Registration 1908.
>
> I went looking for them. The government document site serves a blank
> placeholder page. LawNet returns an empty body. Parliament's site has recent
> Acts but not nineteenth-century Ordinances. There's one private site that
> republishes them — but it paywalls each article part-way through, and it
> doesn't mark where it stopped.
>
> That last bit is why I didn't use it. If a page is cut, a section that's
> missing looks exactly like a section that doesn't exist. For legal work that's
> worse than having nothing, so I stored it flagged as incomplete and kept it out
> of the corpus.
>
> So the question is how we get that text. Three options.
>
> One, buy the official Government Printer volumes — correct, but slow and it
> costs money.
>
> Two, we already own the 1980 Legislative Enactments as volume PDFs. We could
> cut the individual statutes out of those. It's free, but each volume is about
> 480,000 words with many statutes inside, so finding the boundaries reliably is
> fiddly.
>
> Three, use the republisher's text under the permission we already have. Fast,
> but it's their edition rather than the government's, so under our own source
> hierarchy it sits at the bottom tier and would have to be labelled as such.
>
> Our own rule says official sources first, so that points at one or two. But if
> the timeline matters more, I'd want your view on whether three is acceptable as
> a clearly-labelled interim.

---

## 5. Say this before they ask it

> Two weaknesses I want to flag rather than have you find.
>
> First, **nothing has been scored yet.** The 95% is extraction yield — how much
> we got out — not accuracy. We have no gold-standard question set, so there's no
> relevance or legal-correctness number anywhere in the project. Building that set
> is the next priority, because until it exists we can't measure or tune
> anything.
>
> Second, **the platform side is behind.** The backend design and the
> architecture document are done, and the interface prototype covers the main
> screens, but the step that connects the engine to the interface hasn't started
> and it's on the critical path.

---

## 6. How we plan to fix the evaluation gap

*(Say this straight after the "nothing has been scored" admission — it turns a
weakness into a plan.)*

> On evaluation, we've found a source we think is strong. The Law College
> Conveyancing examination papers, including 2025 and 2026. They cover exactly
> our scope — examination of title, chain of ownership and intestate succession,
> deeds and leases and mortgages, notarial duties, powers of attorney, apartment
> ownership, land registration, rights of way, stamp duty, and drafting clauses.
>
> We won't use the scanned questions as they are. The OCR has errors, some pages
> are rotated, one question often contains several independent subquestions,
> questions repeat across years, and there are no model answers or marking
> schemes in the paper. Stamp duty rates also depend on the year, so an answer
> can be right for one paper and wrong for another.
>
> So we'd build a cleaned, human-verified benchmark from it — 30 to 50
> subquestions, in three categories.

### If they want the categories

> Statutory retrieval — "what's required to register a power of attorney" —
> scored on whether we return the right statute, section and supporting passage.
> Applied reasoning — work out who owns what after a sequence of deaths and
> transfers — scored on conclusion, reasoning and evidence. And
> calculation or drafting — compute stamp duty, or draft a lease covenant —
> where calculation is deterministic and drafting needs a lawyer-written rubric,
> because you can't score a drafted clause by string matching.
>
> One methodological point: we'd keep each examination year together rather than
> splitting randomly, because near-duplicate questions recur across years and a
> random split would leak the answer between development and test.

**Then say the limit — this is the important bit:**

> I want to be clear about what that benchmark does *not* cover. It tests legal
> knowledge and retrieval. It does not test document extraction, cross-document
> consistency checking, chain-of-title construction, or title-report generation
> — which are the actual core of Draftly. Those need a separate evaluation built
> on real or synthetic deed bundles. So this is a secondary evaluation set, not
> the main one.

---

## If the RTA comes up

*(This is the one you couldn't explain last time. Keep it to the contrast — that's
the part that matters.)*

> Sri Lanka has two land registration systems running in parallel.
>
> The older one is **deeds registration**, under the Registration of Documents
> Ordinance of 1927. What gets registered is the *document*, not the ownership.
> The register is an index of instruments, and its legal effect is priority — an
> unregistered deed loses to a later registered one. It doesn't prove the seller
> owns anything. So the notary has to trace the chain of deeds backwards, check
> every link, and any gap is the buyer's risk.
>
> The newer one is **title registration**, under the Registration of Title Act,
> No. 21 of 1998 — that's the Bim Saviya programme. There the State does the
> investigation once: the area is declared by Gazette, the Surveyor General makes
> a cadastral map, claims are notified and investigated, disputes are settled, and
> then title is registered against a surveyed parcel with a certificate issued.
> After that, the register *is* the title.
>
> And this is why we chose RTA-first. Each transaction type has a prescribed form
> — Form 8 for transfer, Form 9 for gift, Form 11 for mortgage — set out in the
> regulations, most recently the 2022 Gazette. Because the form fixes exactly
> which particulars are required, **the form is effectively a specification for
> what our system has to extract and check.** Under the deeds system the hard part
> is reconstructing history; under the RTA the history is already settled and the
> work is verifying the current folio, the parties, the parcel, and the
> particulars. That's a much more tractable target.

---

## Likely questions

### "How do you know the structural data is right?"

> We got the same statutes from two independent sources and compared. Fourteen of
> twenty agreed exactly. And the comparison caught a real error — for the
> Marriage Registration Ordinance one source returned 3 sections and the other
> returned 65. The first one was wrong. With a single source we'd never have
> known.

### "Is any of this verified?"

> No. Everything is marked unverified. Lawyer sign-off on the review samples is
> the gate before any rule or statute link is treated as authority, and we have a
> pre-registered precision criterion that has to be met before we run the full
> extraction.

### "What's next?"

> The evaluation gold set, because nothing can be measured until it exists.
> Then authority-aware ranking — Supreme Court binding, Court of Appeal binding
> on the courts below, High Court persuasive. We believe that's absent from the
> published legal-RAG literature, so it's our most novel component, and right now
> it's a design note rather than a result.

### "Why is the platform behind?"

> We front-loaded the corpus and engine work because the extraction had a long
> lead time. The contracts step is the next thing and it unblocks the rest of the
> platform.

---

## Don't say

- Don't say "95% accurate". Say "95% extraction yield" or "recovered from 95%".
- Don't say the temporal problem is solved. It's measured.
- Don't name the paid database in a way that sounds like the corpus depends on
  it — it doesn't; 80% of the index survives without it.
