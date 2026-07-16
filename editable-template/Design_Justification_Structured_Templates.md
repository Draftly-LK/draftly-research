# Design Rationale: Structured-Data Templates with Lawyer Verification

*Draft subsection for the Methods or Design Rationale section of the report. Citation numbering is local to this subsection; renumber to match the main bibliography when merging.*

Draftly represents each conveyancing document not as an editable prose file but as structured data: a defined schema of typed fields is populated by extraction, rendered into a fixed template, edited field-by-field by the lawyer, and only then exported to a shareable document. This design was chosen over general-purpose document editors (for example, an embedded rich-text surface or an external service such as Google Docs) on the basis of four established findings.

**Structured capture yields more complete and accurate records than free-text authoring.** Across high-stakes documentation domains, controlled studies consistently find that structured, template-based capture outperforms free-text authoring on completeness and accuracy. In a controlled comparison of head and neck ultrasound reporting, structured reports achieved significantly higher completeness than free-text reports (94.4% versus a markedly lower free-text score), with a negligible time cost and higher rater-assessed quality [1]; the effect replicates across related studies, with structured reporting reaching completeness of roughly 95% or above against free-text scores in the 25–55% range [2]. Confining the lawyer's edits to typed slots in a fixed template lets Draftly inherit these completeness and consistency benefits. Free-form editing carries an additional risk directly relevant here — unconstrained text can silently alter or remove the underlying structured values during correction — which the typed-slot design structurally prevents.

**General-purpose generative editing is unsafe for legal documents, so outputs must be template-bound and verified.** Dahl et al. [3], in the first systematic study of legal hallucination, found that leading large language models produced incorrect information on specific, verifiable legal queries between 58% and 88% of the time, frequently failed to recognise their own errors, and often accepted a user's incorrect legal premises; the authors caution explicitly against unsupervised integration of such models into legal tasks. Draftly therefore does not free-generate legal content. It populates approved templates from lawyer-verified fields and returns retrieved, source-backed legal material rather than generated authority, keeping every output constrained and checkable.

**High-stakes AI must retain a competent human as the final authority.** Human oversight is treated as a requirement, not an enhancement. The EU AI Act makes human oversight a legal obligation for high-risk AI systems, requiring that a competent person be able to understand, monitor and override the system so as to prevent risks to health, safety and fundamental rights [4]. Legal scholarship similarly frames *meaningful* oversight — as distinct from a nominal "warm body" role — as the emerging standard of care for AI used in consequential decisions [5]. Draftly embodies this by keeping the lawyer as the party who verifies, edits, approves and exports every output; the system is assistive and never autonomous.

**Structured representation preserves provenance and enables traceability to source.** Representing each document as structured data preserves provenance — the record of where each value originated and how it was transformed — which is the established basis for data trustworthiness, auditability and error correction [6]. Because each field in Draftly is a discrete slot rather than a span of prose, it can carry a pointer back to the source page from which it was extracted, satisfying the platform's requirement that every fact remain traceable to source evidence; the same principle underlies the grounded legal-source retrieval evaluated elsewhere in this work [7]. Free-form document editing collapses these discrete, individually attributable values into undifferentiated text and discards that lineage.

**Privacy and data residency further favour a self-contained structured store.** The documents processed in this workflow contain personal data — owner and occupier names, addresses and financial particulars — which fall within the scope of Sri Lanka's Personal Data Protection Act, No. 9 of 2022, including its provisions restricting the transfer of personal data outside Sri Lanka [8]. While enterprise cloud services provide contractual data-protection commitments [9], routing entire client documents through an external collaborative-editing service places them under continuous third-party custody and forgoes the field-level control the structured approach retains. In Draftly, the template layer runs locally and transmits nothing to external services; any external processing is confined to, and evaluated within, the separate document-ingestion stage.

**A note on transferability of evidence.** Several of the strongest empirical results above (first point) originate in clinical informatics rather than law. They are relied upon for the general, domain-independent finding that structured capture outperforms free-text authoring on completeness and accuracy in high-stakes documentation, and that finding is then applied to legal conveyancing; no claim is made that the underlying studies concerned legal documents.

---

## References

[1] B. P. Ernst et al., "Structured reporting of head and neck ultrasound examinations," *BMC Medical Imaging*, vol. 19, art. 25, 2019. doi:10.1186/s12880-019-0325-5.

[2] B. P. Ernst et al., "The use of structured reporting of head and neck ultrasound ensures time-efficiency and report quality during residency," *European Archives of Oto-Rhino-Laryngology*, vol. 277, pp. 269–276, 2020. doi:10.1007/s00405-019-05679-z.

[3] M. Dahl, V. Magesh, M. Suzgun, and D. E. Ho, "Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models," *Journal of Legal Analysis*, vol. 16, no. 1, pp. 64–93, 2024. doi:10.1093/jla/laae003; arXiv:2401.01301.

[4] European Union, *Regulation (EU) 2024/1689 (Artificial Intelligence Act)*, Article 14 — Human oversight, 2024.

[5] "Redefining the Standard of Human Oversight for AI Negligence," *Harvard Journal of Law & Technology Digest*, 2026.

[6] W3C, "PROV-DM: The PROV Data Model," *W3C Recommendation*, 2013. https://www.w3.org/TR/prov-dm/

[7] "LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain," 2024. https://github.com/zeroentropy-ai/legalbenchrag  *(also listed in the main bibliography)*

[8] *Personal Data Protection Act, No. 9 of 2022*, Parliament of the Democratic Socialist Republic of Sri Lanka.

[9] Google Cloud, "Data Usage FAQ — Cloud Vision API" and "Document AI: security and compliance," Google Cloud Documentation.
