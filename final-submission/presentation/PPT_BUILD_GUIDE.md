# Draftly final academic presentation: slide copy and speaker notes

This is the **single slide plan and content source for the PPT build**. It combines the former slide outline with the detailed copy and speaker notes. Build exactly 22 slides, in this order, using the slide IDs, projected words, image choices, presenter notes, transitions, evidence, and timing below. The academic audience is assessing a final data science and engineering project, including understanding, analysis, innovation, tool choices, presentation, product demonstration, and completeness of team tasks. Do not substitute generic legal-tech claims for the evidence in this guide.

The working slot is **20 minutes**. Planned slide time is **19:15**, including **2:30** for the product demonstration, leaving 45 seconds for handovers and pauses. If the official slot differs, retime the notes before building. The speaker allocation is not fixed here; the team can assign blocks without changing slide order.

The talk has **two labelled sections** after the opening: **Part I — Legal information retrieval (slides 04–11)**, then **Part II — Software engineering and the product (slides 12–20)**. Slide 21 credits the team's work, and slide 22 closes both sections. Show a small running section label on each section slide; make the label prominent on slides 04 and 12 without adding separate divider slides. The two problems on slide 02 appear in that order: legal IR first, document-bound information second.

## Build contract

- **Canvas:** 16:9, professional academic presentation. Use the `$guizang-ppt-skill` Swiss Style B, International Klein Blue preset, or an equivalent restrained academic layout if exporting to editable PPTX. Use one type family, consistent grid, large readable headings, and no stock courtroom imagery, gradients, emoji, or decorative icons.
- **Logo on all 22 slides:** use the existing transparent typewriter mark, cropped for slide use: [`assets/draftly-logo-blue-transparent.png`](assets/draftly-logo-blue-transparent.png) on white/light slides and [`assets/draftly-logo-white-transparent.png`](assets/draftly-logo-white-transparent.png) on dark-blue slides. Cover and closing: prominent. Slides 02–21: one consistent small size in the upper-right corner, with clear margin from titles and figures. Preserve the alpha channel; there must be no white rectangular logo background. Use the same visible mark size for both variants.
- **Slide text:** the “On-slide copy” is the exact audience copy. Keep no more than its listed lines; do not project presenter notes. Figure source/status footers may be added in small but readable type. Titles are claims, not section names.
- **Status language:** visually distinguish **hosted/implemented**, **offline research**, **earlier design**, and **planned validation**. Never depict the offline hybrid result as the hosted search engine, or the OCR design as live extraction.
- **Evidence:** use fitted, legible versions of the supplied figures. Redraw a complicated figure only by simplifying its actual content and preserving its status caption. The real OCR page on slide 14 is redacted; no identifying text is visible. Synthetic demo data must be labelled.
- **Presenter notes:** put the prose below into the deck's notes area verbatim or lightly edit for each speaker's voice. The final sentence of each note cues the next slide. Do not put the notes on screen.
- **Demonstration:** slide 19 must show a rehearsed synthetic matter path. The live/recorded choice remains open; [`DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md) gives timings and fallback behavior. Capture actual screens before treating any step as demonstrable.
- **Source of truth:** [`final-report.tex`](../final-report.tex) for final claims and results, [`current-platform-system.md`](../current-platform-system.md) for deployed status, and [`figures/README.md`](../figures/README.md) for image provenance. The older mid-evaluation deck supplies practitioner framing, not current counts. The supplied Google Slides draft was inaccessible to the available tools, so none of its text was copied.

## Image manifest for the PPT builder

All paths are relative to this guide. Keep evidence figures uncropped unless the treatment says otherwise. Do not use `report-fig-02-deployment-draft.png`; the figure inventory says it misstates deployed retrieval/provider status.

| Slide | Asset | Treatment and required caption |
| --- | --- | --- |
| Every slide | [`transparent blue`](assets/draftly-logo-blue-transparent.png) / [`transparent white`](assets/draftly-logo-white-transparent.png) | Persistent Draftly logo. Blue on light slides, white on dark slides; prominent on 01 and 20, small upper-right on all others. Do not flatten transparency onto a box. |
| 03 | [`Anura Dhanaratna`](assets/consultations/anura-dhanaratna.jpeg) | Lead practitioner portrait. His curriculum signs the name **Anura Dhanaratna**; the supplied filename spells it differently. Credit him as lawyer, notary, and Sri Lanka Law College conveyancing lecturer. |
| 03 | [`Priyal Wijayaweera`](assets/consultations/priyal-wijayaweera.jpeg), [`Ishan Rathnapala`](assets/consultations/ishan-rathnapala.jpeg), [`fourth portrait`](assets/consultations/stakeholder-portrait-04.jpeg) | Use as a small **additional stakeholder conversations** portrait row. Individual names, roles, and meeting attribution require confirmation before visible captions are added. The filenames are not evidence of professional role or consultation count. |
| 04 | [`statutory corpus crop`](assets/research-statutory-corpus-crop.png) | Corpus half of the existing research figure, enlarged to show Act, section, and typed-edge structure. The parsed Act text is an internal research corpus. |
| 04 and 07 | [`official Hugging Face mark`](assets/hugging-face-logo.png) | Small release badge beside a **specific public resource**: the Act source-link index on 04 and the provisional QA benchmark on 07. Do not imply that the full parsed Act or case-law text is on Hugging Face. Source: [Hugging Face brand assets](https://huggingface.co/brand). |
| 06 | `assets/case-retrieval-pipeline.png` (team to supply) | Main image. Show BM25, statute/topic/catchword graph, optional dense channel, fusion, and corroboration/abstention. Label as a separate research retriever and mark dense inactive in the recorded pilot. |
| 07 | [`QA benchmark-construction figure`](../figures/research-benchmark-construction-preview.png) | Fit across the slide at text width; the dashed three-attorney stage is **planned**, not completed. |
| 09 | [`retrieval-system crop`](assets/research-retrieval-system-crop.png) | Enlarged retrieval/evaluation half of the existing paper figure, fitted by height in the left two-thirds of the slide. Cover the figure's “Gold Indispensable Bundle” label with a small **proposed reference labels; lawyer validation pending** annotation. Offline research system, not the deployed index. |
| 10 | [`retrieval-c20-results-slide.png`](retrieval-c20-results-slide.png) | Primary result chart; fit without trimming labels. Pair with compact hard-question and one-hop-edge callouts. Offline benchmark, provisional labels. An editable [`SVG`](retrieval-c20-results-slide.svg) is available. |
| 11 | [`accepted paper title and authors`](assets/accepted-paper-title-authors.png) | Crop rendered from [`neurips_2026.pdf`](../../research-paper/neurips_2026.pdf). Show the full title and author line; caption **accepted, NeurIPS 2026 GlobalSouthAI workshop**, not the main conference. |
| 13 | [`../figures/matter-workflow.png`](../figures/matter-workflow.png) | Fit within slide; conceptual lawyer-controlled workflow. |
| 14 | [`real OCR region overlay, redacted`](assets/redacted-real-ocr-boxed-page.png) | Main image beside the evaluation counts. Actual benchmark page with text blurred and region outlines retained; detection boxes are not field-accuracy evidence. |
| 15 | [`complete processing sequence`](assets/document-processing-research-pipeline-crop.png) | Main image across the slide. All nine process stages and human review are visible; obsolete storage lanes are cropped away. Label as a research design reference. |
| 15 | [`current intake boundary`](../figures/document-processing-current-target.png) | Source for the small hosted-status strip. The live extraction provider is a stub. |
| 16 | [`../figures/deployment-demo.png`](../figures/deployment-demo.png) | Small **hosted topology** inset behind the main shipped-retrieval path. Solid path is documented BM25; embeddings and query rewriting remain a dashed in-progress callout. |
| 17 | [`../figures/platform-matter-agent-service-architecture.png`](../figures/platform-matter-agent-service-architecture.png) | User-specified **earlier design reference**. Crop to turn loop, allowlisted tool executor, decision band, and outputs. Exclude old Neon/GCS lanes and reserved research-tool box. Do not use old provider labels as deployment proof. |
| 18 | [`../figures/report-fig-04-rta-transfer-activity.png`](../figures/report-fig-04-rta-transfer-activity.png) | Optional small process reference; show the gate sequence more simply if this figure is too dense. Caption “designed RTA process.” |
| 19 | Actual hosted-app capture or recording, to be made after rehearsal | Synthetic matter only. Do not replace it with July prototype screenshots while calling it “live.” |

## Slide 01 — `draftly-cover` — Draftly makes conveyancing decisions traceable

**Time:** 0:20. **Visual:** large Draftly logo, project title, restrained university identification.

### On-slide copy

> **Draftly**  
> Grounded legal retrieval and a lawyer-controlled conveyancing matter workflow for Sri Lanka  
> Group 06 · Department of Computer Science and Engineering · University of Moratuwa  
> Dhanapalage Himath Nimpura Dhanapala · Lahiru Dilshan · B. K. Praveen De Silva  
> Supervisor: Dr. Nisansa de Silva

**Speaker notes:** “Draftly is our final data science and engineering project. We built a statutory retrieval study and a matter workbench for Sri Lankan conveyancing. Both are grounded in evidence and keep legal decisions with the lawyer. We begin with the task practitioners face.”

**Evidence:** Final report title page and abstract.

## Slide 02 — `matter-before-form` — A conveyancing matter has two information bottlenecks

**Time:** 0:40. **Visual:** two equal, numbered columns. Left: a scenario question pointing to several statutory sections, with one visibly missing. Right: document bundle/PDF icon. Use simple shapes, not an invented deed or benchmark question. Keep the Draftly logo in its standard upper-right position.

### On-slide copy

> **01 · Legal information retrieval**  
> A scenario needs a *complete set* of provisions; search can miss one.  
> **02 · Matter documents**  
> Key facts are buried in PDFs and scans. Lawyers must read and reconcile them.  
> **Draftly links measured legal search to source-linked document review.**

**Speaker notes:** “Draftly addresses two related problems. Here is a statutory illustration: a client wants to sell part of a parcel registered with First Class Title. Under the Registration of Title Act No. 21 of 1998, section 44 tells the notary to check the parties' identity and capacity, and the land and title. Section 47 also requires subdivision and registration of the new parcel before that part is transferred. Section 45(1)(a) then requires the attestor to forward the attested instrument and title certificate to the relevant Registrar of Title within seven working days. A search result containing only section 44 sounds useful but misses a prerequisite and a later filing step. Our paper measures this kind of multi-provision completeness. The second problem is that matter facts are buried in PDFs and scans; a lawyer must inspect and reconcile them. We show the retrieval research first, then the workbench.”

**Evidence:** [Registration of Title Act No. 21 of 1998, ss. 44, 45(1)(a), and 47](https://www.rgd.gov.lk/web/images/ActsPDF/title/TR-Act-english-1998-no-21.pdf) (SRC011, illustrative fact pattern, not a scored benchmark question); final report §§1.1–1.2 and §2; accepted research paper introduction; mid-evaluation slides 4–6.

## Slide 03 — `practitioner-constraints` — Practitioners shaped the corpus and the matter workflow

**Time:** 0:40. **Visual:** use Anura Dhanaratna's supplied portrait at left, with three concise evidence-to-design rows at right. Add the three other supplied portraits as a small row labelled “Additional stakeholder conversations,” without individual captions until their names, roles, and meeting attribution are confirmed. A separate “3 in-person consultations” label records the meeting count, not the number of people pictured. Do not show any sample client document or identifying field.

### On-slide copy

> **Three in-person practitioner consultations**  
> **Anura Dhanaratna:** lawyer, notary, Law College conveyancing lecturer  
> **Notarial curriculum →** topic map and statutory corpus coverage  
> **Sample matter documents →** document-reading trials  
> **Practitioner feedback →** evidence review and lawyer decision gates

**Speaker notes:** “We held three in-person discussions with legal practitioners and experts. One was with Anura Dhanaratna, a lawyer and notary who teaches conveyancing at Sri Lanka Law College. His detailed notarial-practice curriculum helped us organize the conveyancing topic map and identify statutory coverage; we obtained the actual Acts from legal source collections. He also supplied sample matter documents that we used in document-reading trials. Those trials informed page handling and multilingual OCR design, but field-level extraction accuracy has not been established. The discussions gave us concrete workflow constraints: link proposed facts to their source, check the law that applied on the relevant date, and keep consequential decisions with the lawyer. This is stakeholder grounding of the problem and design, while legal labels and final instruments still need professional validation. We begin the research section with the data these sources helped us assemble.”

**Evidence:** Final report §§1.2, 3.4, 5.4; mid-evaluation slides 7–8; `proj-docs/project Management/Proposed Curriculum Conveyancing Course.md`; July mentor notes; user confirmation that supplied matter documents were used in document-processing trials. The 16 Law College examination papers used for benchmark questions are a separate source from this curriculum.

## Slide 04 — `statutory-corpus` — Law College course tables guided statutory corpus selection

**Time:** 0:55. **Visual:** **PART I · LEGAL INFORMATION RETRIEVAL** label; show a vertically tightened version of the [statutory-corpus crop](assets/research-statutory-corpus-crop.png) beside a numeric strip so the graph is readable. Add the [Hugging Face mark](assets/hugging-face-logo.png) only beside the [public Act source-link index](https://huggingface.co/datasets/lanka-legal-nlp/draftly-sri-lanka-act-sources). The full parsed Act text is an internal research corpus.

### On-slide copy

> **52 principal enactments + 60 amending Acts**  
> **4,557 sections · 17,854 provisions · 6,346 typed edges**  
> Law College course tables guided principal-Act selection  
> Public release: Act source-link index; parsed corpus used internally

**Speaker notes:** “The practitioner curriculum gave us the notarial and conveyancing topic map. Principal enactments named in the Law College course tables became the starting set; we collected their amendments and parsed source PDFs into a frozen section index. Six edge types record definitions, exceptions, qualifications, procedural requirements, cross-references, and amendments. The section is the retrieval unit. The Hugging Face resource here is an Act metadata and source-link index, while the full parsed text used in the experiments remains internal. Alongside statutes, we assembled case law for legal research.”

**Evidence:** Accepted paper §2 and Appendix A; final report §3.4; [public Act source index](https://huggingface.co/datasets/lanka-legal-nlp/draftly-sri-lanka-act-sources); `research-paper/dataset-release-plan.md`.

## Slide 05 — `case-law-corpus` — The case-law collection adds judgments, with provisional rule extraction

**Time:** 0:55. **Visual:** two data columns: **reported NLR/SLR** and **official Supreme Court/Court of Appeal**. Show source counts and a small rule-extraction gate. Use no private judgment page or invented excerpt. Keep the Part I label.

### On-slide copy

> **3,703** reported conveyancing judgments  
> **5,474** official Supreme Court / Court of Appeal judgment documents  
> **3,521 / 3,703** reported cases yielded verbatim headnote rules  

**Speaker notes:** “The case-law work complements statutory retrieval. We collected 3,703 reported conveyancing judgments from NLR and SLR and 5,474 official Supreme Court and Court of Appeal judgment documents. A deterministic headnote reader recovered a verbatim rule in 3,521 reported cases. For harder cases, a bounded model-assisted path required a quotation present in the judgment. On a held-out set, 74 of 100 outputs passed that quote gate; a provisional model judge rated 58.1 percent of accepted outputs fully usable, below our threshold. No extracted rule is lawyer approved, and case-law ranking was outside the scored statutory benchmark. The next slide shows the separate retriever built over these cases.”

**Evidence:** Final report §§3.4 and 5.4; dataset inventory. Reported and official-court counts describe distinct collections.

## Slide 06 — `case-retrieval` — A separate retriever finds analogous conveyancing cases

**Time:** 0:50. **Visual:** the current PPTX uses an editable flow with **BM25 text** and **case graph** as parallel branches from the case index. A third grey branch marks dense embeddings as optional and inactive in the recorded pilot. Branches converge at rank fusion and corroboration, then return cited cases or no-similar-case. A team-supplied pipeline image can replace the native diagram after review. The bottom strip labels 14/20 and 10/20 as proxy results on **different corpus snapshots**, not as a before-and-after intervention. Keep the Part I label and Draftly logo upper-right. Do not depict facet-weighted reranking or generated party-stance explanations as implemented in Draftly.

### On-slide copy

> **Case index:** 5,121 conveyancing-flagged cases from 9,177 collected cases  
> **Search:** BM25 + case-to-case statute/topic/catchword graph; dense optional  
> **Output:** ranked case citations or an explicit no-similar-case state  
> **20-query proxy pilot:** 14/20 on the initial corpus snapshot; 10/20 after rebaseline

**Speaker notes:** “Alongside the statutory corpus, we assembled 3,703 reported conveyancing judgments and 5,474 official-court judgment documents. A separate case retriever indexes 5,121 cases flagged as conveyancing-related. Given a fact pattern, it searches judgment text and extracted rule statements lexically, expands through cases sharing statute or topic links, and fuses the ranked lists. The code also supports a dense channel, but no embedding key was available in the recorded evaluation, so those results reflect lexical plus graph retrieval only. A case needs lexical or graph corroboration to be returned. Twenty past-paper fact patterns were judged by LLM proxies: 14 of 20 initial results were judged to contain an analogous case, but a later corpus rebaseline fell to 10 of 20. This is exploratory evidence without lawyer-verified relevance labels. The case service is separate from the paper's statutory retriever and from the hosted BM25 research path.”

**Image brief for the team:** Use one left-to-right flow with three visibly separate evidence channels. Show the dense path as optional and annotate that it was inactive in the reported pilot. The graph links cases via shared statutory references, curriculum topics, and catchwords; a citation edge is evidence for ranking, not a legal holding. Add the corroboration gate before the result and a branch for no-similar-case. Leave all labels editable in the PPT. Confirm the user's intended “IL Parser” reference before naming it. The [section-weighted hybrid case-retrieval paper](https://arxiv.org/abs/2606.03138) is one possible related source, but Draftly's tested pipeline does **not** implement its facet-weighted reranker.

**Evidence:** `scripts/similar-case-retrieval/RESULTS.md` architecture and proxy evaluation; `evaluation/runs/similar-case-retrieval-v1/metrics.json` and `similar-case-retrieval-v1-rebaseline/metrics.json`; `src/draftly/case_retrieval/` implementation; final report §§3.4, 5.4 for corpus counts. Case retrieval was outside the accepted paper's scored statutory benchmark.

## Slide 07 — `qa-benchmark` — Law College scenarios became a provisional statutory QA benchmark

**Time:** 0:55. **Visual:** place three large phase labels above the [QA benchmark-construction figure](../figures/research-benchmark-construction-preview.png): question selection, proposed provision labels, and human review pending. Keep the figure across the text width but let the large labels carry the stage names at projector distance. Put the [official Hugging Face mark](assets/hugging-face-logo.png) and [versioned dataset link](https://huggingface.co/datasets/lanka-legal-nlp/draftly-statutory-retrieval/tree/v1.0-paper-provisional) in a small release badge.

### On-slide copy

> **16** conveyancing examination papers → **667** atomic questions  
> **50** scored questions in **40** matters; **40** test questions in **32** matters  
> Proposed indispensable sections with verbatim statutory provenance  
> Public benchmark on Hugging Face · attorney adjudication pending

**Speaker notes:** “These questions came from sixteen Law College conveyancing examination papers, a different input from Anura Dhanaratna’s notarial curriculum. The papers yielded 667 atomic questions. Scenario selection and matter grouping produced fifty statute-only scored questions in forty matters; forty questions in thirty-two matters formed the test split. One agent proposed the indispensable provisions and evidence-linked answers, and an independent agent checked them. A deterministic validator confirmed identifiers and quotations in the frozen corpus. It could not decide legal indispensability. The three-attorney stage shown at right remains planned. The provisional benchmark is public on Hugging Face. We need a metric that reflects whether all proposed sections were found.”

**Evidence:** Accepted paper §2 and Fig. 1; final report §§3.4 and 5.4; [versioned provisional dataset](https://huggingface.co/datasets/lanka-legal-nlp/draftly-statutory-retrieval/tree/v1.0-paper-provisional).

## Slide 08 — `complete-bundle-metric` — Retrieval succeeds only when it finds every proposed indispensable section

**Time:** 0:40. **Visual:** large illustrative three-section bundle: the top-20 list contains two sections and misses one, so C@20 = 0. Label the example **illustrative** and the reference bundle **agent-proposed**. Keep the Part I label.

### On-slide copy

> Question → proposed indispensable section set  
> **C@20 = 1 only if every proposed section is in the top 20**  
> One missing proposed provision makes the bundle incomplete

**Speaker notes:** “A system can rank a plausible section first and still omit a definition, exception, or procedural requirement. Complete-indispensable recall at twenty gives full credit only if every proposed indispensable section appears in the first twenty results. This picture explains the metric; it is not an actual benchmark case. Because the labels have not been attorney adjudicated, the score uses provisional reference sets. We used the same frozen data and metric to compare seven retrieval configurations.”

**Evidence:** Accepted paper §3; final report §5.4. The drawn bundle is illustrative.

## Slide 09 — `retrieval-systems` — Seven offline retrieval systems used the same benchmark

**Time:** 0:55. **Visual:** show the enlarged upper retrieval-method portion of the [retrieval-system crop](assets/research-retrieval-system-crop.png) in the left two-thirds; omit its small evaluation panel, which slide 10 covers. Put three large method-family labels at right. Mark the figure **offline research**, distinct from hosted BM25; the reference labels are proposed and await attorney validation.

### On-slide copy

> Lexical: BM25 and field-weighted BM25  
> Semantic/fusion: dense, hybrid, hybrid + reranker  
> Structure-aware: hierarchical, hierarchical + typed expansion  
> **Seven matched configurations · one frozen test split**

**Speaker notes:** “The diagram shows where methods diverge after receiving the same scenario question. BM25 favors exact terminology; dense search uses semantic section windows; hybrid fuses rankings; a reranker is a separate variant. Hierarchical retrieval first routes to likely Acts, then retrieves sections. Typed expansion follows explicit legal relationships and applies a temporal filter. All seven were offline configurations scored on the same frozen questions and corpus. The live platform has a BM25 index, not seven selectable modes. The next slide shows which approaches recovered complete bundles.”

**Evidence:** Accepted paper §3 and retrieval-system figure; final report §3.4.

## Slide 10 — `retrieval-results` — Complete recall peaked at 0.375, while hard bundles remained unsolved

**Time:** 1:00. **Visual:** fit [the C@20 result chart](retrieval-c20-results-slide.png) on the left, with two compact callouts on the right: **0/20** hard questions completed and **2/114** misses one edge away. Keep chart labels legible. Footer: **offline · provisional labels · 40 test questions / 32 matters**.

### On-slide copy

> **C@20:** BM25 0.281 · hybrid 0.344 · hierarchical 0.375 · typed expansion 0.312  
> **0 / 20** questions needing ≥4 provisions completed  
> **2 / 114** missed provisions one explicit edge from a retrieved seed  
> No clear winner among the leading systems

**Speaker notes:** “Hierarchical retrieval recorded the highest observed complete-bundle score, 0.375, while hybrid had the highest average indispensable recall. The paired intervals among leading systems include zero, so point estimates do not establish a certain winner. None of the twenty test questions needing four or more provisions was completed by any system. Of 114 indispensable sections missed by the structure-aware retriever, only two were one explicit edge from a retrieved seed. The graph holds useful explicit relationships, but most scenario dependencies were not encoded as reachable edges. These are offline results against provisional labels. The accepted paper packages this dataset, method, and negative result.”

**Evidence:** Accepted paper §4 and main table; final report Table 4, Fig. 13, §5.4; [editable result chart](retrieval-c20-results-slide.svg).

## Slide 11 — `accepted-research-paper` — The accepted paper reports the complete-bundle retrieval result

**Time:** 0:45. **Visual:** display the [paper title and author crop](assets/accepted-paper-title-authors.png) large enough to read. Caption **Accepted for presentation · NeurIPS 2026 GlobalSouthAI workshop**. At right, three short contribution lines. Use the actual [camera-ready PDF](../../research-paper/neurips_2026.pdf) as the source, not a generic paper mock-up. Keep the Part I label.

### On-slide copy

> **Does Statutory Structure Help?**  
> Statutory corpus · provisional scenario QA benchmark · seven-system evaluation  
> **Finding:** typed-edge expansion did not demonstrate a complete-recall gain over hybrid retrieval  
> **Next:** attorney labels and evaluation of the new retrieval integration

**Speaker notes:** “This paper is accepted for presentation at the NeurIPS 2026 GlobalSouthAI workshop. It contributes the structured Sri Lankan statutory corpus, a scenario QA benchmark with proposed indispensable sections, and a matched seven-system retrieval evaluation. The tested typed-edge expansion did not demonstrate a gain over strong hybrid retrieval. The paper also reports the hard multi-provision failure and limited one-hop reachability of missed sections. Labels need attorney validation before we can claim legal gold. Our hosted search is currently BM25; a teammate is developing embedding-enabled retrieval with query rewriting, which the paper did not evaluate. That integration must be scored on the same complete-bundle question. We now move to the software workbench that uses legal research and document evidence in a lawyer-owned matter.”

**Evidence:** [Accepted paper PDF](../../research-paper/neurips_2026.pdf), title page, abstract, §§2–5; final report §§1.3 and 5.4; documented hosted deployment and user-reported upgrade workstream.

## Slide 12 — `rta-scope` — Post-certificate RTA gives the first workflow a bounded scope

**Time:** 0:50. **Visual:** **PART II · SOFTWARE ENGINEERING** section label over a clear scope boundary. Inside: **post-certificate RTA matter** with simple, synthetic icons for a title certificate, cadastral/survey plan, and transaction documents, leading to evidence review and prescribed-form checks. Outside, muted: **legacy handwritten pattiru/folio OCR**, AT-form extraction, historical title reconstruction, and initial title settlement. The outside lane is future work, not a claim that such records never appear in the wider RTA process. Keep the Draftly logo upper-right; use no private deed or plan image.

### On-slide copy

> **First scope:** post-certificate Registration of Title Act (RTA) transactions  
> Title certificate + cadastral/survey plan + transaction evidence  
> Structured requirements and prescribed forms support reviewable checks  
> **Deferred:** handwritten pattiru/folio OCR and historical title reconstruction

**Speaker notes:** “Part two is the software engineering workbench. We chose post-certificate transactions under the Registration of Title Act No. 21 of 1998 after practitioner discussions. In this first lane, the lawyer can work from a title certificate, cadastral or survey plan information, and the relevant transaction documents, following defined requirements and prescribed forms. That gave us a bounded workflow in which to test source-linked document review and checks. The older deeds-registration path brings handwritten pattiru or folio records and historical title tracing; making Sinhala handwriting recognition reliable would have become a separate research project. After discussion with our supervisor, we deferred that OCR problem, AT-form extraction, and initial title settlement to later work. This does not mean every RTA input is clean or machine-readable: scans still need lawyer verification. The next slide shows how the selected matter moves through the workbench.”

**Evidence:** Registration of Title Act No. 21 of 1998, ss. 4 and 10 (SRC011: parcel and cadastral-map basis); final report §§1.1 and 1.3; July 19 mentor notes on the post-certificate RTA and pattiru boundary; `proj-docs/project Management/v0-implementation.md` exclusions; mid-evaluation slides 20–21. The supervisor discussion is reported by the team and has not been separately documented in the cited project files.

## Slide 13 — `matter-route` — One matter connects intake, review, checks, and audit

**Time:** 0:40. **Visual:** an editable three-lane PowerPoint redraw of the [matter workflow source](../figures/matter-workflow.mmd). Show matter and evidence, lawyer review, and draft and record. The earlier raster was too soft to read at presentation size. After checks, show the **Matter Agent conversation** and then **cited research in a separate view**. Highlight lawyer verification, finding resolution, and draft review; retain the feedback note below the lanes.

### On-slide copy

> Matter + source documents → candidate facts → lawyer verification  
> Checklist + checks → matter-agent conversation → separate cited research → draft + preflight  
> Lawyer decision → approval/export record + audit

**Speaker notes:** “The matter is the unit of work. A user opens and classifies it, uploads documents, and sees candidate facts linked to evidence. A lawyer verifies or corrects those candidates before checks or form bindings. The versioned rule pack supplies requirements. The lawyer can discuss matter state with the Draftly Matter Agent and separately inspect cited legal research; direct agent-to-research calling remains planned. Draft, preflight, approval, and export are distinct records. The hosted demonstration later shows which screens and gates are connected today. First, look closely at the fact boundary.”

**Evidence:** Final report §3.2 and Fig. 4; current-platform-system workflow.

## Slide 14 — `document-ocr-evaluation` — OCR detects text regions, but field accuracy remains unscored

**Time:** 0:55. **Visual:** make the [redacted real OCR page with detected boxes](assets/redacted-real-ocr-boxed-page.png) the main image on the left. On the right, use three clean number cards for the benchmark inventory, Vision pilot, and labelled subset. Caption the image **real benchmark page; text redacted; OCR regions shown**. Keep the Draftly logo upper-right.

### On-slide copy

> **Benchmark inventory:** 4 matters · 38 documents · 282 pages  
> **Vision pilot:** text returned on 26/26 pages in one matter  
> **Labelled subset:** 37 fields · 4 documents · 1 matter  
> **Field-level accuracy:** not yet scored

**Speaker notes:** “We tested document reading on a collection of four matters, 38 documents, and 282 pages. That is the available inventory, not a claim that every engine processed every page. This actual title-document page shows the OCR regions found in one benchmark run; the source text has been redacted for the presentation. In a 26-page Vision pilot, text was returned on every page. That measures coverage, not correctness. One matter also has 37 labelled fields across four documents, but the extraction comparison was not scored after credential and availability failures. A detected box is evidence of a text region, not a verified title fact. The next slide shows how such evidence would travel through the full document-processing design.”

**Evidence:** `ocr-benchmark/README.md` inventory and labelled-field scope; `ocr-benchmark/reports/vision-corpus-metrics.json` pilot coverage; `ocr-benchmark/reports/metrics.json` unscored variants; real page crop from `ocr-benchmark/renders/overlays/vision/vision-003-title-certificate-parcel-p1.png`, redacted by `build_redacted_ocr_overlay.py`.

## Slide 15 — `document-processing-pipeline` — The full processing design ends at lawyer review

**Time:** 0:50. **Visual:** put three large macro-stage labels above a tightened crop of the [complete nine-stage process image](assets/document-processing-research-pipeline-crop.png): **capture**, **organize pages**, **propose and verify**. The crop preserves upload, Cloud Vision OCR, quality check, rotation, page classification, split/group, derivatives, structured extraction, and human review while removing the lower dashed storage lanes. Caption it **research pipeline design; later extraction stages are not the hosted implementation**. Put a status strip below the image: **hosted now: upload → processing record/stub candidates → lawyer review**. Keep the Draftly logo upper-right. Do not put the test counts or boxed page on this slide.

### On-slide copy

> **Research pipeline:** document → OCR and quality checks → grouping → proposed fields → lawyer review  
> **Hosted boundary:** source and processing run persist; extraction currently yields stub candidates  
> **Review rule:** a detected value becomes a verified fact only after lawyer approval or correction

**Speaker notes:** “Here is the complete document-processing sequence we designed from the OCR trials. It starts with upload, OCR and quality checks, then handles orientation before classifying and grouping pages. The later stages create derivatives and propose structured fields for human review. The diagram is a research design reference, and its original storage lanes were removed because they no longer match the VPS. In the hosted workbench, the source file and processing run persist, but extraction currently supplies stub candidates. A lawyer must verify or correct a candidate before it becomes a versioned fact for drafting. So the pipeline image shows the full intended flow and its review gate, while the status strip names what is running today. Next is the separate statutory research service.”

**Optional PaperBanana brief:** Redraw the supplied nine-stage sequence as one legible 16:9 academic figure. Preserve all stages and the uncertain-page branch. Use editable labels, a distinct human-review endpoint, and a separate hosted-status strip. Omit obsolete storage providers and do not depict classification or structured field extraction as live hosted services.

**Evidence:** [Original nine-stage figure](../figures/platform-document-processing-v1-pipeline.png); [current intake boundary](../figures/document-processing-current-target.png); final report §§3.1–3.4, 5.4; current-platform-system document-processing status.

## Slide 16 — `shipped-retrieval` — The shipped research service returns cited statutory passages

**Time:** 0:55. **Visual:** make the retrieval path the main diagram: **lawyer's research question → Next.js research view → FastAPI research API → internal retrieval service / BM25 section index → cited passages → grounded response or insufficient-authority state**. Use a readable lower-right card for the present boundary: legal research remains in a separate workspace and the Matter Agent does not call it today. A grey note marks **embeddings + query rewriting in progress**; it must not join the solid shipped path. Keep the Draftly logo at upper right. This is the one software-section slide about the retrieval system that is actually shipped, separate from the seven offline paper systems on slide 09.

### On-slide copy

> **Hosted research path:** question → API → internal BM25 index  
> **Output:** ranked statutory passages with Act and section citations  
> Grounded response **or** insufficient authority  
> **Next version in progress:** embeddings + query rewriting

**Speaker notes:** “The hosted research workspace takes a lawyer's question through the workbench and API to an internal retrieval container. That container currently ranks statutory sections with BM25; it is not the paper's offline hybrid or hierarchical system. Retrieved passages retain Act and section citations. The research API can use those passages to compose a grounded response, and it abstains with insufficient authority when no usable passage is returned. This path is separate from the Draftly Matter Agent today: the agent's direct legal-research tool is not connected. A teammate is building embedding-enabled retrieval and query rewriting, but we should update the solid diagram only after the deployed configuration and a smoke test confirm it. The assistant has a similar authority boundary.”

**Image brief for Hugging Face generation:** Create a restrained 16:9 academic systems illustration on white, in navy and muted blue. Show five left-to-right modules as simple flat shapes: a research question interface, an API service, a searchable statute-section index, ranked source passages, and a lawyer review screen. Use thin directional arrows and generous space for editable labels. Add one separate pale-grey dashed module below the index for a future enhancement. **No embedded text, numbers, logos, legal seals, people, 3D effects, or invented document content.** The PPT builder must overlay the exact labels from the visual description above as editable text; keep the future module dashed and visibly marked “in progress.” If the generated image cannot keep the flow clear, use native PPT shapes instead.

**Presenter accuracy note:** The checked deployment record has `RETRIEVAL_WITH_EMBEDDINGS=0`. Do not put dense, hybrid, hierarchical retrieval, or query rewriting in the solid hosted path without a newer deployment record and smoke-test evidence. The paper's enriched scenarios are an offline fact-enrichment analysis, not evidence of a deployed query-rewriting service.

**Evidence:** `draftly-platform/deploy/PRODUCTION.md` retrieval configuration; `final-submission/current-platform-system.md` research and live-deployment sections; final report §3.2. The [deployment figure](../figures/deployment-demo.png) shows the current VPS context.

## Slide 17 — `agent-boundary` — The assistant can propose actions; the server and lawyer control them

**Time:** 0:50. **Visual:** cropped [`matter-agent architecture`](../figures/platform-matter-agent-service-architecture.png), clearly captioned **earlier design reference**. Show turn loop, tool executor, decision band, and outputs; omit obsolete persistence lanes.

### On-slide copy

> Matter-scoped session  
> Allowlisted, typed server tools  
> Consequential action → explicit confirmation  
> Legal question to agent → abstention today  
> Cited statute research → separate workspace today

**Speaker notes:** “The Draftly Matter Agent is organized around a matter session, not unrestricted access to the database. It can read authorized matter context through allowlisted tools, while consequential proposed actions require confirmation. A model suggestion cannot directly write a verified legal fact. The agent's direct statute-search tool is still to be connected; legal questions abstain there today. The separate research workspace returns cited statutory material or an insufficient-authority response. This image is a design reference, so its older storage and provider labels do not describe the current VPS. The rule pack carries the same control into drafting.”

**Evidence:** Current-platform-system implemented assistant and safety sections; named design figure.

## Slide 18 — `rules-and-gates` — The rule pack can stop an unsafe drafting path

**Time:** 0:45. **Visual:** four-step gate diagram. Optional source reference [`RTA activity figure`](../figures/report-fig-04-rta-transfer-activity.png), labelled designed process.

### On-slide copy

> Versioned RTA rule pack → checklist and deterministic findings  
> Unresolved statutory blocker → **stop**  
> Verified facts → form bindings → preflight → lawyer approval

**Speaker notes:** “The RTA rule pack is versioned content, not a free-form prompt. It records transaction types, required documents, checklist items, checks, forms, and each requirement's source class. A matter's checklist is pinned to the rule-pack version used. Findings send the lawyer back to missing or conflicting evidence; they are not a determination of title. Unresolved statutory blockers stop relevant progression, and an unapproved form cannot be exported as approved. Legal wording still needs professional sign-off, so no registration-ready export is claimed. We can now demonstrate these gates in a synthetic matter.”

**Evidence:** Final report §§3.1, 4; current-platform-system rule-pack and refusal controls.

## Slide 19 — `product-demo` — Inspect a synthetic RTA matter from evidence to refusal gate

**Time:** 2:30. **Visual:** the current PPTX is a route card for switching to the live synthetic-matter demonstration, with the exact seven stops and hosted-status label. If a rehearsed capture or recording is ready, replace the route card with that verified build image while keeping the agenda compact. Do not use July prototype screenshots while calling them live.

### On-slide copy

> **Demo route:** matter → documents → candidate review → checks → matter-agent chat → cited research → draft/preflight  
> Synthetic matter · hosted extraction stub · BM25 search

**Speaker notes:** “This is a synthetic RTA matter, so no client information is being shown. Open the matter and its persisted document record. At the candidate view, show the source and the separate lawyer-review action; hosted extraction supplies a stub candidate here. Open a checklist finding. If the matter chat is available, show a short conversation about matter state. Then move to the separate research workspace for a cited statute passage or insufficient-authority state; do not imply the agent called research. End at draft preflight with an unresolved value or refusal, not an approved instrument. Return to activity history. If a live screen fails, switch to the recorded path and state what the capture shows.”

**Cue sheet:** 0:00 matter; 0:20 document; 0:45 candidate evidence; 1:10 checks; 1:30 matter chat if available; 1:45 separate research view; 2:00 draft/preflight; 2:20 activity. See [`DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md).

**Evidence:** Final report §§4–5; current-platform-system implemented areas and limits. Capture and rehearse the exact route before delivery.

## Slide 20 — `testing-rundown` — Five test tracks show what Draftly has measured

**Time:** 1:15. **Visual:** five compact horizontal rows with **test**, **result**, and a small **limit** label: statutory retrieval, similar-case retrieval, case-law rules, document reading, and platform software. Use neutral status colours; do not render every row as a success badge. A short footer carries the wider browser result. Keep the standard Draftly logo upper-right. The detailed evidence map is [`TESTING_EVIDENCE.md`](TESTING_EVIDENCE.md).

### On-slide copy

> **Statutory IR:** C@20 0.375 on 40 test questions · provisional labels  
> **Similar cases:** 14/20 initial, 10/20 rebaseline · proxy judged; dense inactive  
> **Case-law rules:** 74/100 quote-grounded · 58.1% proxy usable  
> **Document reading:** 26/26 pilot pages returned text · fields unscored  
> **Platform:** 3,906 backend + 348 frontend passed · 3 browser refusals in one journey  
> **Wider browser run:** 4 passed · 9 failed · 2 skipped

**Speaker notes:** “Five tracks test different parts of the project. The accepted-paper statutory study compared seven systems on 40 questions, with a highest observed complete-bundle score of 0.375 on provisional labels. The separate similar-case retriever was tried on 20 past-paper fact patterns: an LLM judged 14 initial results correct, but only 10 after a corpus rebaseline; the dense channel was inactive. In held-out case-law rule extraction, 74 of 100 cases passed quote grounding and 58.1 percent of accepted rules were judged fully usable by a provisional model judge. The Vision pilot returned text on 26 of 26 pages, while field accuracy remains unscored. Platform tests recorded 3,906 backend passes, 348 frontend passes, three browser refusal passes, and 15 fixed defects. The wider browser run had nine failures. None of the legal relevance or field results is lawyer-validated. The [testing evidence map](TESTING_EVIDENCE.md) holds the methods and gates.”

**Evidence:** [Testing evidence map](TESTING_EVIDENCE.md); final report §§5.2–5.4 and Tables 3–4; `draftly-platform/docs/review/test-report-combined.md` §§6–9; `draftly-platform/docs/review/testing-report.md` §§2–7; OCR benchmark pilot metrics.

## Slide 21 — `team-contributions` — Three contributors connected research and the product

**Time:** 0:45. **Visual:** three contributor columns with equal visual weight. Put each name above two or three concrete outputs; use a thin bottom band for shared integration and review. Keep the Draftly logo in the upper-right at the standard size. Do not use percentage shares or imply the columns represent equal quantities of work.

### On-slide copy

> **Himath Dhanapala**  
> Statutory corpus and benchmark lead · retrieval evaluation · High Court case-law work · research-paper first draft  
> **Lahiru Dilshan**  
> Case-law collection and retrieval · OCR and document-extraction research  
> **Praveen De Silva**  
> BM25 search work · templates and output flow · lawyer-facing review interface  
> **Shared:** integration, testing, and final project review

**Speaker notes:** “These contributions overlap, so the slide names the main outputs each person drove. Himath led the statutory corpus and benchmarking, worked on the High Court case-law strand, and produced the first draft of the research paper. Lahiru worked on case-law collection and retrieval alongside the OCR and extraction research. Praveen worked on BM25 search and the templates, output flow, and lawyer-facing interface. Integration and testing drew on the team. We are showing the actual research and engineering strands rather than assigning artificial percentage shares.”

**Build note:** Himath's statutory benchmarking, High Court case-law work, and paper-drafting role; Lahiru's case-law role; and Praveen's BM25 role are from the presenter's September 30 account. The older OCR and template/interface assignments are documented in `.agents/context/CONTEXT.md`. The linked contribution spreadsheet required Google sign-in during this edit, so verify this wording against it and resolve Praveen's unfinished “common law” item before the final deck. Do not display this build note on the audience slide.

**Evidence:** [Team contribution spreadsheet](https://docs.google.com/spreadsheets/d/1nXDMcQasJwarbH1gzFlEUETFjycg34KPZjTLUrVtIaM/edit?usp=sharing) (access pending); presenter's September 30 contribution account; documented team workstreams in `.agents/context/CONTEXT.md`.

## Slide 22 — `takeaway` — A measured retrieval study and a reviewable matter workflow

**Time:** 0:25. **Visual:** one short closing statement and a large transparent Draftly logo. No repeated contributor columns.

### On-slide copy

> **Measured retrieval. Versioned evidence. Lawyer-owned decisions.**  
> Next: attorney labels · document-field evaluation · form review · complete browser journeys

**Speaker notes:** “Draftly measured a hard statutory retrieval problem and built a matter workflow that keeps evidence and lawyer decisions inspectable. The next validation steps are attorney adjudication, document-field accuracy, form wording, and complete browser journeys. Thank you; we welcome questions.”

**Evidence:** Final report conclusion; [testing evidence map](TESTING_EVIDENCE.md).

## Final QA for the PPT skill

1. Count **22 slides** and **22 instances of the Draftly logo**. Check that the transparent blue mark is visible on light slides, the transparent white mark on dark slides, and neither has a rectangular background. Inspect the mark at presentation size, especially on slides with large figures.
2. Sum the times to **19:15**. Keep slide 19's demonstration at **2:30** and preserve the remaining 0:45 of slot margin. Rehearse closely: this is a tight 20-minute plan.
3. Compare every number with `final-report.tex`: 52 + 60 Acts, 4,557 sections, 6,346 edges, 50 benchmark questions, 40 test questions/32 matters, C@20 values, 0/20 hard questions, 2/114 graph reachability, and September test counts.
4. Label older design figures, July synthetic prototype images, offline research charts, hosted components, and planned validation distinctly. Keep the supplied document-processing and matter-agent figures in the deck with the cropping/status treatment above.
5. Check that slide 19 shows only synthetic material and that its recording or screenshots come from a verified build. Do not imply a successful approved export, live OCR field accuracy, or hosted hybrid retrieval.
6. Put this guide's notes into presenter notes, not onto the slide canvas. Check transitions and speaker handoffs after the team confirms presenters and allocation.
7. Visually preview every slide at projector size; fit all evidence figures without cutting axes, labels, status legends, or source captions. Run the chosen PPT skill's slide/notes validators before delivery.
