# Draftly final-product demonstration runbook

This is a **planned** two-and-a-half-minute sequence for slide 18, using a prepared **synthetic** RTA matter. It is not a record that the sequence has already been rehearsed on the hosted site. Choose live or recorded playback after checking the assessment room and team preference. Prepare a recording and labelled screenshots of the same verified path as a fallback. Do not use real client documents.

| Time | Screen/action | Point for assessors to observe |
| --- | --- | --- |
| 0:00–0:20 | Open an existing synthetic RTA matter and refresh or navigate back to it. | Matter details persist through the API rather than being a static slide. |
| 0:20–0:45 | Open its documents and a processing/candidate view. | Source file and candidate are separate records; hosted extraction is a stub. |
| 0:45–1:10 | Open a candidate's evidence and show the review/correction action. | A machine suggestion needs human verification before it becomes a fact. |
| 1:10–1:35 | Open checklist/checks and one finding. | Governed checks turn missing or conflicting evidence into a review task. |
| 1:35–1:55 | Open legal research and one returned passage, or the insufficient-authority state. | Research is cited or abstains; the hosted index is BM25. |
| 1:55–2:20 | Open the draft/preflight path and show an unresolved value or refusal. | The system records a gate and does not claim a registration-ready instrument. |
| 2:20–2:30 | Return to the matter/activity view and close. | Evidence, findings, and decisions remain in one matter history. |

## Before the assessment

1. Confirm a prepared synthetic matter, account access, stable network, and the exact screens that work in the hosted build. Do not improvise with a real client matter.
2. Rehearse the six transitions above and record the actual working path. If a screen is unavailable, remove that step and replace it with a labelled capture of a verified build, rather than narrating an unobserved capability.
3. Check that the candidate shown is visibly marked as a stub or synthetic example. Do not imply OCR field accuracy from the demo.
4. Check that the selected research response really shows a source passage or a clear insufficient-authority response. Do not promise a particular answer in advance.
5. Check the draft/preflight refusal in the current build. An approved or registration-ready export is not the target of this demonstration.
6. Keep the backup recording local and show the same status captions as the live route: **synthetic**, **stub extraction**, and **hosted BM25**.

## Narration cue

“This is one synthetic RTA matter. The uploaded document and the extracted candidate remain distinct. A person verifies the fact; the rule pack then raises findings for review. Legal research shows its source or says authority is insufficient. The drafting gate retains unresolved values and prevents an approved output when prerequisites are missing.”

The current-system basis is `final-submission/current-platform-system.md`, with test and limitation evidence in `final-submission/final-report.tex`, §§4–5. The exact click path must be checked on the build used for the assessment.
