# Draftly: simple speaking script

Use this with the [reviewed PowerPoint](Draftly-Final-Academic-Presentation-Reviewed.pptx). The deck's speaker notes have the fuller explanations and evidence. This version gives you a short, natural way to present each slide. Pause on the charts and figures; do not rush through the numbers. Slide 19 is a demonstration cue, so rehearse it with the actual synthetic matter before presenting.

## Slide 01: Introduction

“Good morning. We are Group 06 from the University of Moratuwa. Our project is Draftly, a legal research and conveyancing matter workbench for Sri Lanka. We studied how to retrieve all the statutory provisions needed for a legal scenario, and we built a product that keeps document evidence and lawyer decisions together.”

## Slide 02: The two problems

“Here is a statutory example. A client wants to sell part of a parcel registered with First Class Title. Under the Registration of Title Act No. 21 of 1998, section 44 tells the notary to check the parties and the title. But section 47 requires the parcel to be subdivided and the new parcel registered before that part is transferred. Section 45 adds a step after attestation: forward the instrument and title certificate within seven working days. A search result with section 44 alone sounds useful, but misses those requirements. Our second problem is finding reliable facts in scanned matter documents.”

This is an illustrative transaction, not a scored benchmark question. Source: [Registration of Title Act No. 21 of 1998, ss. 44, 45(1)(a), and 47 (SRC011)](https://www.rgd.gov.lk/web/images/ActsPDF/title/TR-Act-english-1998-no-21.pdf). Section 47's condition is stated here for a parcel with First Class Title; the Act also names Second Class Title of Ownership.

## Slide 03: Practitioner input

“We had three in-person consultations with legal practitioners and experts. Anura Dhanaratna, a lawyer, notary, and Law College lecturer, helped us understand the conveyancing curriculum and supplied sample documents for document-reading trials. These discussions shaped three decisions: facts must point back to their source, legal requirements must be checked against the relevant law, and the lawyer must control the final decision. The consultations informed our design; they do not replace formal legal validation.”

## Slide 04: Statutory data

“This is the start of our legal retrieval research. We used the Law College course tables to select the initial Acts, then collected and parsed the source laws into sections. We also recorded links such as definitions, exceptions, cross-references, and amendments. The Hugging Face link here is a public index of Act metadata and source links. The parsed text used in our experiments is an internal research corpus.”

## Slide 05: Case-law data

“We also collected case law: 3,703 reported conveyancing judgments and 5,474 official-court judgment documents. We tested a process for pulling out a rule with a quotation from the judgment. On held-out cases, 74 out of 100 passed that quotation check, but a provisional model judge found only 58.1 percent of those accepted rules fully usable. So these rules are research candidates, not lawyer-approved statements.”

## Slide 06: Similar-case retrieval

“The case collection supports a separate similar-case retriever. It searches the text and the links between cases in parallel, then combines the results. Dense embeddings were available in the design but inactive in the recorded pilot. On 20 past-paper fact patterns, a model judge found an analogous case in 14 initial results. A later run on a different corpus snapshot reached 10 out of 20. These are exploratory proxy judgments, so we cannot claim lawyer-verified case relevance.”

## Slide 07: Question dataset

“For the statutory benchmark, we started from 16 Law College conveyancing examination papers. They yielded 667 atomic questions. From those, we selected 50 statute-only scored questions, with 40 questions in the test split. Agents proposed and checked the sections that each question needs, and software checked identifiers and quotations against the frozen corpus. Three-attorney validation is still pending. The provisional dataset is linked on Hugging Face.”

## Slide 08: What we measured

“Our main metric asks whether a system found every proposed indispensable section in its top 20 results. In this illustration, it found two of three sections. That gets a zero for complete-bundle recall, even though two results are useful. This is why ordinary top-result relevance alone is too weak for a multi-provision legal question. The reference bundles remain provisional until attorneys review them.”

## Slide 09: Seven research systems

“We compared seven retrieval configurations on the same frozen questions and corpus. They include lexical, dense, hybrid, reranked, hierarchical, and structure-aware approaches. Hierarchical retrieval routes to likely Acts before retrieving sections. Typed expansion follows explicit legal relationships. These were offline experiments. The hosted product currently uses a separate BM25 research index, which I will show later.”

## Slide 10: Research results

“The highest observed complete-bundle score was 0.375, from hierarchical retrieval. Hybrid had the highest average recall of individual indispensable sections. The leading systems were close enough that this study does not establish a clear winner. More importantly, none completed the 20 hardest test questions, which each needed at least four provisions. Only two of 114 missed sections were one explicit graph edge from a retrieved result. That points to a gap in the encoded relationships, not a simple one-hop expansion fix.”

## Slide 11: Research paper

“We reported the corpus, benchmark, seven-system evaluation, and the hard negative results in a paper accepted for presentation at the NeurIPS 2026 GlobalSouthAI workshop. The paper is careful about the provisional labels. It also does not claim that the offline best configuration is already deployed. Our teammate is working on embeddings and query rewriting for the product; that version will need its own evaluation.”

## Slide 12: Why RTA

“Now to the software workbench. We chose post-certificate transactions under the Registration of Title Act as our first scope. They give us a bounded route involving title certificates, survey or cadastral information, transaction evidence, and prescribed requirements. The older deeds-registration route can require handwritten records and historical title tracing. We discussed that challenge with our supervisor and deferred it, so we could test document review and legal checks within one clear workflow.”

## Slide 13: The matter workflow

“A matter begins with intake and documents. The system can propose candidate facts, but the lawyer checks them against the source before they become verified matter facts. Rules then support the checklist and findings. The lawyer can discuss the matter with the Draftly Matter Agent and open cited statutory research in a separate view. Direct research search from the agent is a future integration. Drafting, preflight, approval, and export remain separate steps with an audit trail.”

## Slide 14: Document-reading test

“Here is a redacted page from our document benchmark, with detected text regions. The benchmark inventory has four matters, 38 documents, and 282 pages. In one 26-page Vision pilot, every page returned text. That shows coverage, not that every word or field was correct. We also labelled 37 fields in four documents from one matter, but field-level accuracy was not scored. A detected box is only a candidate source region.”

## Slide 15: Processing design

“This figure shows the full document-processing design. It begins with upload, OCR, and quality checks; then it handles rotation, page classification, and grouping. Later stages would create derivatives and propose structured fields for lawyer review. The hosted workbench currently persists uploads and processing records, and it uses stub extraction candidates. The lawyer must verify a candidate before drafting can use it as a matter fact.”

## Slide 16: Hosted legal research

“In the hosted research workspace, a lawyer asks a question and the research service retrieves statutory sections from its BM25 index. The response carries Act and section citations, or says that authority is insufficient. This workspace is separate from the Matter Agent today. Embeddings and query rewriting are being developed, but they are not the solid deployed path shown here.”

## Slide 17: Matter Agent boundary

“The Matter Agent works inside an authorized matter session. It can read context through allowlisted server tools and suggest next actions. An action that changes the matter needs confirmation, and a model suggestion cannot directly become a verified legal fact. Legal questions to the agent currently abstain because its direct statute-search tool is not connected. The diagram is an earlier design reference; the cards on the right state the current control boundary.”

## Slide 18: Rules and gates

“The RTA rule pack holds versioned requirements, checklist items, checks, and form bindings. A matter records which version it used. If evidence is missing or conflicting, the lawyer sees a finding and can resolve it. An unresolved statutory blocker stops the relevant drafting path. An unapproved draft cannot be exported as approved, and form wording still needs professional sign-off.”

## Slide 19: Product demonstration

“I will use a synthetic RTA matter, with no client data. First, I open the matter and its document record. Then I show a candidate value and the source the lawyer must inspect before verification. Next, I show a checklist finding, a short matter conversation if available, and the separate cited-research view. Finally, I show the draft preflight or refusal gate and the activity history. The point is to show the review path and where the system stops.”

If a live step fails, switch to the rehearsed recording and say which step the recording shows. Do not describe a stub extraction result as measured field extraction.

## Slide 20: What we tested

“We tested five strands. The paper evaluated statutory retrieval on 40 test questions. The separate similar-case pilot used 20 fact patterns, and the case-law rule test checked quotation grounding. The document pilot measured whether OCR returned text on 26 pages, while field accuracy remains open. On the platform, 3,906 backend and 348 frontend tests passed; three browser refusal tests passed, but the wider browser run had failures. These results show useful progress and define the remaining validation work.”

## Slide 21: Team contributions

“The work crosses research and engineering, so these are the main contributions, not percentage shares. Himath led the statutory benchmark, worked on the High Court case-law strand, and drafted the research paper. Lahiru worked on case collection and retrieval, alongside OCR and extraction research. Praveen worked on BM25 search, templates and outputs, and the lawyer-facing interface. Integration and testing involved the team.”

Confirm this wording with the team before presenting, especially the case-law split.

## Slide 22: Close

“Draftly gives us a measured view of a difficult statutory retrieval task and a matter workflow where evidence and lawyer decisions remain inspectable. Our next validation steps are attorney review of the labels, document-field accuracy, form wording, and complete browser journeys. Thank you. We welcome your questions.”
