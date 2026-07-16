# Draftly — Project Pitch

**Draftly reads a client's stack of prior deeds, reconstructs and checks the
chain of title, and produces lawyer-reviewable draft documents — it automates the
*examination* work, not just the final typing.**

A lawyer-in-the-loop platform for **title examination and conveyancing document
drafting in Sri Lanka**. ML + Software Engineering, end to end, demoable.

## The problem

In Sri Lanka, preparing a property deed is still mostly manual — and the hard
part isn't typing the deed. Before anything can be drafted, a lawyer or notary
has to:

- read a stack of prior deeds, survey plans, and assessment records,
- work out who owned the land and how it changed hands over ~30 years,
- catch missing documents, name mismatches, extent/lot/plan discrepancies, and
  undischarged mortgages.

This is slow, error-prone, and depends on scarce expertise. A junior clerk can't
safely do it; a general-purpose chatbot can't be trusted with it.

## The idea

Give the system a client's document bundle. It extracts the facts, links them
across documents, rebuilds the **chain of title (pedigree)**, flags what's
missing or inconsistent, and generates the standard outputs a notary produces —
each one grounded in the source documents and open to lawyer correction.

Outputs: title report, pedigree, Abstract of Title Deed (AT form), certificate
of ownership, assessor letter, deed schedule, missing-document checklist, and a
red-flag report.

## Why this isn't just template-filling

This is the first question anyone asks, so it's worth answering head-on.

The template is only the **last** step. The real work happens before it:

```text
Documents → Extraction → Linking → Chain-of-title graph → Consistency checks → Lawyer verification → Drafts
```

The system reads unstructured, historical, code-mixed (Sinhala/English) deeds,
turns them into a **structured, verified title record**, checks that record, and
generates many documents from it. That's what makes it measurable as an ML
project — not "did a PDF come out," but did we extract, link, and reason
correctly.

## What we build first (scope)

Conveyancing work has six notarial functions: examination of title, drafting,
execution, stamping, attestation, registration. We build the first four and defer
registration (the most complex). This keeps v1 focused and shippable.

## Why it's a real ML + SE project

**Data Science:** OCR for scanned Sinhala/English deeds, document classification,
named-entity and relation extraction, entity resolution across name variants,
cross-document linking, chain-of-title reconstruction, inconsistency detection,
and grounded generation with clause-level provenance.

**Measurable:** classification accuracy, key-field extraction accuracy, NER F1,
chain-of-title reconstruction accuracy, defect-detection precision/recall,
lawyer-rated draft correctness, and time saved vs. manual work.

**Software Engineering:** a web platform — matter dashboard, document upload and
processing pipeline, extracted-fact review UI, evidence/provenance viewer,
pedigree viewer, red-flag dashboard, lawyer review/edit workspace, version
history, audit trail, and DOCX/PDF export.

## What we've built so far

Real, in-hand progress — not just a plan:

- **Statutory corpus assembled.** ~85 Sri Lankan conveyancing sources (statutes,
  amendments, gazettes, regulations) collected, extracted to text, and organized
  into the **20 curriculum topics** — with a source registry and topic→statute
  rule tables, cross-checked by an automated integrity audit.
- **Case-law corpus assembled.** ~**5,100 conveyancing judgments + 33 historical
  law-report volumes**, spanning **1839–2026**, gathered from free/official
  primary sources: the Internet Archive (public-domain volumes), CommonLII
  (reported New Law Reports / Sri Lanka Law Reports, pre-2012), and the official
  Supreme Court + Court of Appeal sites (post-2012 judgments). Filtered to the
  conveyancing subset. As far as we can tell, no comparable open Sri Lankan
  conveyancing case-law dataset exists.
- **A reproducible data pipeline.** Scripts + a Jupyter notebook that turn the raw
  law into a structured, queryable dataset — a **case↔statute citation graph**
  and topic→statute→case tables.
- **Retrieval approach chosen and justified.** Rule-based and **citation-grounded**
  over a structured index — deliberately *not* plain vector similarity, because in
  law a loose or wrong match is a real error. Every answer traces to a cited
  section or case.
- **Domain validation.** Mentored by a practising senior notary and Law College
  lecturer; the six-function workflow and curriculum are validated against real
  practice. A real (anonymized) property matter is set aside as evaluation ground
  truth.
- **Team.** Three parallel workstreams — OCR/extraction, legal-data corpus,
  output-document templates — around one shared verified-record contract.

## What's new

Existing Sri Lankan legal platforms (LawLanka, AI PAZZ, Paralegal.lk) do legal
*search* and legislation retrieval. We haven't found an end-to-end system that
reads a client's own prior-deed bundle and **reconstructs the chain of title**.
The project aligns with the legal-NLP direction of Dr. Nisansa's SigmaLaw work,
but aims at practical drafting and workflow automation rather than search,
sentiment, or case analytics.

## One design rule: grounding

Every fact and citation must trace back to a real source document or statute
section. A general model that "creatively" fills gaps is worse than useless here
— a wrong owner or a repealed section is a real legal risk. Provenance over
fluency, always.

## Demo story

Upload a few source documents (prior deed, current/gift deed, survey plan,
assessment record) → the system classifies them, extracts the key fields, shows
each fact with its source, builds the pedigree, flags a missing document, and
generates a draft title report + AT form + assessor letter → the lawyer reviews
and exports. That single flow shows the ML and the SE working together.

## Where we are, and what's next

**Now:** normalizing the whole corpus (statutes + case law) into one clean,
processed store for the retrieval engine, and OCR-ing a small scanned backlog
with open-source OCR. The statutory + case-law data and the citation graph are
already in place.

**Next:**

1. Rule-based lookup engine — question/step → the governing statute sections +
   the cases that cite them, with citations and in-force caveats.
2. The document pipeline — OCR + field extraction on a real (anonymized) matter,
   measured against our ground-truth record.
3. The Streamlit demo — documents in → pedigree / title report / AT form /
   assessor letter out, each grounded and lawyer-reviewable.

**What we'd show at the symposium:** that single end-to-end flow on a real matter,
plus the measurable metrics (extraction accuracy, chain-of-title reconstruction,
defect detection, time saved).
