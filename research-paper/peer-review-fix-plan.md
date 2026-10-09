# Proposed camera-ready fixes from the peer review

Status: proposal only. No manuscript edits or new experiments are part of this
document.

This plan reads the single review in [peer-reviews.md](peer-reviews.md) against
the current [manuscript](neurips_2026.tex). It uses the `rebuttal` skill's issue
and strategy stages to plan paper revisions. It is not a reply for OpenReview.
The reviewer rates the submission 6 (marginally above acceptance threshold)
with confidence 4, praises the complete-bundle metric and negative result, and
asks mainly for a narrower interpretation of evidence. The paper already
discloses that no attorney has approved the labels; preserve that honesty.

## Revision boundary

- Keep every reported score tied to **agent-produced proposed labels**. No
  attorney validation has been completed, so no wording should imply legal
  correctness or approved gold.
- Preserve the measured negative result. Limit it to this corpus, test split,
  explicit edge set and retrieval implementation. Do not claim that statutory
  structure in general is ineffective.
- Prefer replacements over added paragraphs: the main text currently ends on
  page 4, the workshop's short-paper limit. Recompile and check the page break
  after any accepted edit.
- Do not promise a legal-domain model, larger benchmark or public dataset by
  the camera-ready deadline. Describe these as future work unless completed
  and verified.

## Issue board

| ID | Review concern | Evidence in the submitted paper | Proposed response | Status |
| --- | --- | --- | --- | --- |
| R1-C1 | No attorney-validated indispensable labels; the benchmark table reports `lawyer approved 0`. | Abstract; Introduction; Corpus and benchmark; Limitations; Appendix B. | Keep the zero and pending protocol. Make the result and ranking explicitly conditional on proposed labels in the abstract, main result and conclusion. Say attorney review may change the labels and scores. | Cannot resolve empirically now; wording fix proposed. |
| R1-C2 | Only 40 test questions in 32 matters; intervals are wide. | Table 1 caption; Results; Limitations; Appendix F. | State the test size beside the headline result and avoid a claim of equivalence or broad generalization. Preserve the paired interval result. | Wording fix proposed. |
| R1-C3 | Mixed, case-law and missing-authority questions are excluded. | Corpus and benchmark; Limitations; Appendix B. | State the evaluated population as statute-only questions for which corpus text was available. Keep excluded questions visible in the funnel; do not imply the scored set covers conveyancing as a whole. | Wording fix proposed. |
| R1-C4 | Typed edges are heuristic and mostly explicit; only 2 of 114 misses were one-edge reachable. | Corpus; Ablations and errors; Limitations. | Say the reachability result diagnoses this graph and one-hop expansion. It does not test richer legal dependency graphs or learned relations. | Wording fix proposed. |
| R1-C5 | The generic MS MARCO reranker hurts MRR; stronger legal-domain retrievers and query expansion were not tested. | Retrieval systems; Main result; Conclusion. | Label this as a failure of the evaluated off-the-shelf reranker on this benchmark. Keep domain adaptation and alternatives in future work, with no performance prediction. | Wording fix proposed; new experiments deferred. |

The review's positive points need no defensive reply. Keep the all-or-nothing
metric, the indispensable/supporting/background distinction, the matched
baseline comparisons, the matter-level uncertainty and the negative result.

## Proposed manuscript edits, in priority order

These are candidate replacements. Check them against the final source and
rebuild before accepting them; none has been inserted into the manuscript.

### P0: Make the headline result conditional on proposed labels

1. **Abstract.** Replace the opening of the result sentence, "Structure does
   not help:", with wording such as: "Against the proposed labels, this
   explicit graph does not improve complete recall on the test split:". Keep
   the existing S4 and S7 values and paired-interval statement immediately
   after it. This retains the result while bounding its interpretation
   (R1-C1, R1-C2, R1-C4).
2. **Conclusion.** Qualify the first sentence with "On this 40-question test
   split, against proposed labels" and refer to "the tested Act-routing and
   typed-edge expansion". Use "did not demonstrate an improvement" rather
   than a general claim that structure cannot help (R1-C1, R1-C2, R1-C4).
3. **Limitations.** Add or substitute one sentence: "Attorney review may add,
   remove or relabel indispensable provisions, changing the reported recall
   values and possibly the system ranking." This is a risk statement, not a
   claim that a ranking change has occurred (R1-C1).

### P0: Correct the data-release status before finalizing

The abstract currently says the labels "are released as proposed gold". The
[dataset release plan](dataset-release-plan.md) says no Hugging Face repository
has been created or made public and all 50 benchmark labels await lawyer
validation. Replace "are released as proposed gold" with "are treated as
proposed reference labels" or another present-tense description of their
actual status. Appendix B also says review packets and empty approval forms
"ship with the data"; verify whether the final artifact is actually available
before retaining that sentence. Add a dataset URL or release claim only after
the release gates in the plan are met. This correction is independent of the
reviewer's criticism, but directly affects the credibility of R1-C1.

### P1: Sharpen what the experiment covers

1. **Corpus and benchmark or Limitations.** Use one compact scope sentence:
   "The scored benchmark covers statute-only questions with governing text in
   the frozen corpus; mixed, case-law and missing-authority questions remain
   outside this evaluation." The existing funnel counts and exclusions must
   stay intact (R1-C3).
2. **Ablations and errors.** Follow the 2-of-114 reachability observation with
   an interpretation limited to the tested graph: "This is a coverage limit
   of the extracted one-hop edge set, not a test of richer dependency
   representations." Avoid describing all legal structure as absent (R1-C4).
3. **Main result or Limitations.** State that the observed reranking loss is
   for the evaluated MS MARCO cross-encoder. The result does not establish how
   a legal-domain reranker would perform (R1-C5).

### Deferred, evidence-dependent work

- **Attorney validation (R1-C1):** The three-rater protocol is specified in
  Appendix B. It cannot be reported as completed until lawyers supply ratings,
  disagreements are adjudicated, and affected metrics are rerun.
- **Larger or broader test (R1-C2, R1-C3):** Adding questions or case law would
  create a new evaluation version, not retroactively strengthen this test.
- **New graph or retrieval models (R1-C4, R1-C5):** Any claim about learned
  edges, legal-domain rerankers, SPLADE or query expansion needs an actual
  controlled run on the frozen split.
- **Public dataset (R1-C1):** Follow the separate release plan's rights,
  privacy and provenance gates. A planned release is not a current artifact.

## Acceptance checks for the revision

- Every numerical result remains unchanged unless a documented rerun produces
  a replacement table and figures.
- The abstract, results, captions and conclusion consistently say which
  labels and question population were scored.
- The paper never presents agent agreement as attorney validation.
- The PDF uses the workshop final style, the complete main text stays within
  four pages, references and appendix remain separate, and citations resolve.
- Every new availability statement is checked against files or a live release.
