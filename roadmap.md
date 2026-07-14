# Draftly Team Roadmap

Three workstreams, one shared contract. The trick to working in parallel: agree
the **case record schema** first, then each person builds their side against it.

## Where we are

Inputs are collected: ~67 conveyancing statutes (extracted to Markdown), 20
curriculum topics, and a large case-law corpus — 3,703 conveyancing judgments, a
9,539-case index (NLR/SLR era, 1872–2010), and 33 public-domain volumes.
Retrieval will be **rule-based and grounded** (deterministic lookups with
citations, not similarity search). No product demo yet — that's the target.

## The team

| Member | Workstream | Owns |
| --- | --- | --- |
| Lahiru | **OCR & Extraction** | Reading scanned deeds/plans/receipts → structured fields |
| Himath | **Data & Legal Corpus** | The statute + case-law knowledge base, datasets, ground truth |
| Praveen | **Templates & Outputs** | Every output doc (path-iru, AT form, title report, …) as a re-generatable template |

## Workstream A — OCR & Extraction

**Goal:** turn a scanned document bundle (Sinhala/English deeds, survey plans,
municipal receipts, path-iru/registry extracts, NIC) into text and structured
fields that populate `case_record.json`.

Next targets:

1. **OCR pipeline** — take the sample scans and produce clean per-page text
   (compare Document AI vs docling vs the current fallback; pick what handles
   Sinhala + English + old print best). Deliver text for the demo-case documents.
2. **Field extraction** — pull the key fields per document type (deed: no/date/
   parties/notary/plan/lot/extent/boundaries/registry ref; plan: plan no/
   surveyor/lots/extent; receipt: assessment no/owner). Start rule/regex + layout,
   output the schema JSON, and measure accuracy against Himath's verified record.

### Candidate engines (research → benchmark → pick)

Our documents are the hard case: **scanned, mixed Sinhala + English, often old
print / legacy fonts.** Don't guess an engine — benchmark a shortlist on our own
pages (CER + field accuracy on the demo case), using the method in the
Sinhala/Tamil OCR paper below.

**Commercial (managed, cloud):**

| Engine | Notes for us |
| --- | --- |
| **Google Document AI** | Best on *historical* Sinhala in the zero-shot benchmark; layout-aware JSON |
| **Google Cloud Vision API** | Supports Sinhala; simpler OCR, good baseline |
| **AWS Textract** | Strong on forms/tables (English); Sinhala support limited — verify |
| **Azure AI Document Intelligence** | Layout + key-value extraction |
| **ABBYY** | 150+ languages, on-prem option |

**Open-source (self-host — preferred for privacy, see below):**

| Model | Notes for us |
| --- | --- |
| **Tesseract** | Has Sinhala (`sin`); fine-tunable on legacy fonts (a paper cut CER 7.61%→4.74% on Sri Lankan gov docs) |
| **Surya** (Datalab) | Top small model (~650M); OCR + layout + tables + reading order; multi-script |
| **PaddleOCR / PaddleOCR-VL**, **EasyOCR**, **docTR** | Traditional/hybrid pipelines |
| **VLM OCR (2025–26):** olmOCR-2-7B, DeepSeek-OCR, dots.ocr, GOT-OCR 2.0, Qwen2.5-VL, Granite-Docling, Nanonets-OCR2 | End-to-end image → Markdown; need a ~16 GB GPU |
| **Sinhala-specific:** TrOCR-Sinhala-finetuned (HF `eshangj`), Subasa OCR, Theekshana Sinhala OCR | Purpose-built starting points |

**Privacy note (drives engine choice):** client deeds carry real
names/NICs/addresses. Sending them to a cloud OCR API is a data-exposure
decision — this favours **self-hosted open-source** for real matters, keeping
cloud engines for public/anonymized docs or as an accuracy ceiling to compare
against.

### Key papers & resources (start reading here)

- **Zero-shot OCR Accuracy of Low-Resourced Languages: Sinhala & Tamil** —
  arXiv:2507.18264. Compares Cloud Vision, Document AI, Surya, Tesseract, Subasa,
  EasyOCR. **Use its benchmark method.**
- **Cross-Temporal Sinhala OCR: Page-Level Adaptation** — arXiv:2606.29378.
  Fine-tuning Tesseract on legacy fonts for old government documents (our exact
  problem).
- **SinhaLegal: benchmark corpus for IE in Sinhala legislative texts** —
  arXiv:2603.04854. Legal-domain Sinhala; OCR/layout challenges.
- **Sri Lanka Document Datasets (law/news/policy, Si/Ta/En)** — arXiv:2510.04124.
- **Deciphering the Underserved: LLM OCR for Low-Resource Scripts** —
  arXiv:2412.16119.
- **olmOCR-bench** — open-source OCR leaderboard for comparing VLM models.

(arXiv IDs are from web search — verify each before citing formally.)

**Approach:** (1) deep-research pass to confirm the shortlist and read the papers;
(2) benchmark 3–4 engines on our demo-case pages; (3) pick a self-hostable
open-source default, with a cloud engine (Document AI/Vision) as the accuracy
ceiling and the fallback for the hardest historical Sinhala.

Needs from others: sample documents + the verified record (Himath); the field
list each output needs (Praveen).

## Workstream B — Data & Legal Corpus (Himath)

**Goal:** turn the raw statute + case-law corpus into a **traversable, queryable,
rule-based knowledge base** — plus the datasets to build and evaluate retrieval on
it — so every check and draft can cite real law.

Next targets (in order):

1. **Retrieval research — pick the engine.** Survey the current methods for
   retrieval over a *static, closed* legal corpus and decide with evidence:
   - rule-based / keyword lookup (deterministic, grounded),
   - classic RAG (embeddings + vector store),
   - graph retrieval (HippoRAG / GraphRAG),
   - hierarchical / tree (RAPTOR / BookRAG).
   Current lean (to confirm or revise): **rule-based engine over a BookRAG-shaped
   index** — keep the tree/graph *structure*, drop the LLM/embedding machinery.
   Output: a short decision note + the chosen design. (Bibliography already
   gathered in the plan file; do a focused deep-research pass to finalize.)

2. **Prepare the datasets (so we can actually retrieve + measure).**
   - **Corpus dataset:** normalize the statutes + 3,703 cases into clean records
     with metadata (`source_id`, `section`, `topics`, `citation`) — the thing
     retrieval runs over.
   - **Retrieval eval set:** ~30–50 realistic conveyancing questions/steps paired
     with the *expected* statute sections + cases (gold answers), so retrieval
     quality is measurable (recall@k, etc.).
   - **Ground-truth case record:** the verified/anonymized `case_record.json` for
     the demo case (chain-of-title ground truth) + the annotation schema the OCR
     side (A) is scored against.

3. **Make the whole corpus traversable.** Build the navigable index: topic →
   subtopic → statute section (heading anchors + node frontmatter) and the
   case ↔ statute graph (regex citation links). Do one topic end-to-end first
   (`09-examination-of-title`), then scale to all 20. Result: from any
   topic/keyword/section you can walk to the governing sections and the cases
   that cite them.

4. **Stand up the retrieval engine.** Implement the chosen (rule-based) engine
   over the traversable corpus: topic router (keyword tables) → sections + cases
   → grounded answer with citations and in-force caveat. Wire it to the
   `legal-source-lookup` skill and the POC's "Relevant Law & Authority" panel.

Needs from others: OCR output to validate extraction against the verified record
(A); the template field lists so the record captures what generation needs (C).

Feeds others: the traversable corpus + engine powers C's authority citations and
the POC's authority panel; the eval set + case record measure A's extraction.

## Workstream C — Templates & Output Documents

**Goal:** every document the system produces, defined as a parameterized template
so it can be regenerated from a verified record — path-iru, Abstract of Title
Deed (AT form), title report, pedigree, certificate of ownership, assessor letter,
deed schedule, and the transfer deed.

Next targets:

1. **Catalog + collect** one clean real example of each output document (DOCX),
   with notes on when/why each is used. This defines the output set.
2. **Parameterize each template** — separate the fixed boilerplate from the
   `{slots}`, and list the fields each template needs. Generation then = fill
   slots from `case_record.json`. Keep it deterministic (no LLM in the core fill).

### Input documents we expect (the bundle that comes in)

What a matter typically arrives with — Praveen needs these to know what source
facts feed the templates, and Lahiru needs them as the OCR input set:

- **Current deed** — the operative deed being acted on.
- **Prior deeds** — the ~30-year chain (transfers, gift deeds, exchanges).
- **Survey plan / condominium plan** — lots, extents, boundaries, surveyor.
- **Land registry (path-iru / පත් ඉරු) folio extract** — registrations,
  encumbrances, prior refs.
- **Assessment register extract + municipal rates receipts** (වරිපනම්) —
  assessment number, owner, address.
- **Identity documents** — NIC / passport (verified, not stored in public form).
- **Existing title report / pedigree**, if the client already has one.
- **Declaration deed** — when a property was converted to condominium.
- **Court documents**, where relevant — e.g. probate / letters of administration
  for an executor's or administrator's conveyance.

### Output documents we produce (the full catalog)

**A. Title-analysis outputs (the examination result):**

- Pedigree / chain-of-title (පෙළපත් සටහන)
- Title report (හිමිකම් වාර්තාව)
- Abstract of Title Deed / AT form / T-form (ඔප්පු සාරාංශය)
- Certificate of ownership
- Assessor / municipal ownership-transfer letter
- Missing-document checklist
- Red-flag / inconsistency report

**B. Draftable deeds & instruments (generated from the verified record):**

- Deed of Transfer
- Transfer of a Condominium Property
- Deed of Gift
- Deed of Exchange
- Deed of Partition
- Deed of Declaration (e.g. condominium)
- Deed of Rectification
- Mortgage Bond
- Indenture of Lease
- Agreement to Sell
- Special Power of Attorney
- Executor's / Administrator's Conveyance
- Last Will and Testament, Codicil
- **Deed schedule (උපලේඛනය)** — the property-description block reused across all
  of the above; build this template first, it is shared.

**POC priority:** Praveen doesn't build all of these at once. For the first demo,
target group A (title report, pedigree, AT form, assessor letter) plus **one**
group-B deed (Deed of Transfer) and the shared deed schedule. The rest are the
same pattern repeated, added later.

---

## Principle to hold

Grounded and deterministic first. Every extracted fact, every check, every
generated line should trace to a source document or a statute/case citation —
templates and rules before any model that could "creatively" fill a gap.
