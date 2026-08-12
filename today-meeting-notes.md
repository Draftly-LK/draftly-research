# Draftly — supervisor meeting, 12 August 2026

Group 06. Prepared by Himath. Everything below is `status=unverified` until a
lawyer signs it off; the numbers are extraction yield, not legal correctness.

## In one minute

We built the statute index the case-law work was blocked on, and then found that
a section number alone is not enough — statutes change, so a citation has to be
resolved against the date of the judgment. Both of those are now measured rather
than assumed. The remaining blocker is that no free, official source carries the
text of the older Ordinances we still lack.

## 1. The statute index is built

Old court judgments cite provisions — "under section 247 of the Civil Procedure
Code". To use those citations we need a reliable list of which sections exist in
each statute. Ours was incomplete, and two copies of it disagreed with each
other by a factor of five on the most-cited statute.

Result of rebuilding it:

| | Before | Now |
| --- | ---: | ---: |
| Statutes indexed | 45 | 66 |
| Sections | 3,547 | 5,770 |

**Unreported Supreme Court and Court of Appeal judgments.** Since 2012 both
courts publish directly, and we hold 5,474. The difficulty is structural rather
than legal: there is no headnote, so the holding sits at the end of a long
judgment and must be found rather than looked up. That track needs a model with
a strict verbatim-quote grounding check, and it is Praveen's current work.

## 4. Corpus text — where we are blocked

- **Commencement dates for 1,464 statutes**, in a single request. This is what
  the temporal model needs to move from year precision to actual dates.
- **Section lists for 20 statutes**, which gave us a second opinion on the
  structural data. That cross-check immediately caught a real defect: for the
  Marriage Registration Ordinance one source returned **3** sections and the
  other **65**. With a single source we would not have known.

We also confirmed that five statutes which appear to have a PDF do not have
their own PDF — they point at 1980 Legislative Enactments *volumes*, one file
shared by four statutes, so extracting one means finding its boundaries inside a
480,000-word book.

## 5. Decision we need

For roughly 22 statutes we hold no text and no free source carries it. Options:
2. **Slice the statutes out of the 1980 volume PDFs we already own.** Free, but
   boundary detection inside a very large multi-statute book is error-prone.
3. **Use the republisher's text** under the written permission already obtained.
   Fast, but it is their edition rather than the Government Printer's, so it sits
   at priority 3 of our own source hierarchy and would need labelling as such.

Our source-priority rule (official PDF first, consolidators third, never as the
authority) points at option 1 or 2. We would like guidance on whether the
project's timeline justifies option 3 as an interim, clearly labelled.

## 6. Registration of Title Act — the point we could not explain last time

Sri Lanka runs two land-registration systems, and the difference decides what the
software has to do.

**Deeds registration** (Registration of Documents Ordinance No. 23 of 1927) —
what is registered is the *instrument*, not ownership. The register is an index
of documents and its legal effect is priority: an unregistered instrument is void
against a subsequent registered one. It does not prove the seller owns the land.
A notary must trace the chain of deeds backwards, check each link, and consider
prescription. Any gap stays the buyer's risk.

**Title registration** (Registration of Title Act No. 21 of 1998, the Bim Saviya
programme) — the State investigates once. Sections 10–33 cover initial
compilation: the area is declared by Gazette order, the Surveyor General produces
a cadastral map, claims are notified and investigated, disputes settled, and
title is registered against a surveyed parcel with a certificate of title issued.

**Why this decides our scope.** Because each form fixes exactly which particulars
are required, the form itself is a specification for what the system must extract
and check. Under the deeds system the hard work is reconstructing history; under
the RTA the history is already settled and the work is verifying the current
folio, parties, parcel and particulars. That is a far more tractable target,
which is why V0 is RTA-first and deliberately does not attempt historical title
tracking or ownership-chain reconstruction.

## 7. Tasks and owners

| Owner | Current work |
| --- | --- |
| Himath | Retrieval engine and platform architecture. Temporal statute model, evaluation gold set, authority-aware ranking, backend contracts. |
| Praveen | Case-law extraction and the dataset layer. Unreported-judgment run, the quote-rejection rate, unified citation graph. |
| Lahiru | Document intake and prescribed forms. Real model-backed extraction, RTA form support. |

| --- | --- | --- |
| Statutory retrieval | Requirements for registering a power of attorney | Correct statute, section and supporting passage |
| Applied reasoning | Determine ownership after a sequence of deaths and transfers | Conclusion, reasoning and evidence |
| Calculation or drafting | Compute stamp duty; draft a lease covenant | Deterministic calculation, or a lawyer-written rubric |

Target mix: 15 statutory retrieval, 15 applied scenarios, 5–10 calculations,
5–10 drafting.
