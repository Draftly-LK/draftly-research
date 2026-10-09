# Draftly presentation: testing evidence map

This document supplies the evidence behind slide 20. The slide is a brief
summary; this file gives the presenter and PPT builder the test scope, result,
and limit for each project stream. The September platform test report and the
final research report were produced at different points, so their experiments
are identified separately.

## What to show on slide 20

| Track | Test performed | Recorded outcome | Boundary to state |
| --- | --- | --- | --- |
| Statutory retrieval | Seven systems on 40 held-out questions grouped into 32 matters; complete-indispensable recall at 20 | Highest observed C@20: hierarchical 0.375; hybrid 0.344 | Provision labels were agent-proposed and await attorney review; leading paired intervals include zero. |
| Similar-case retrieval | Separate case index; 20 Law College fact-pattern queries graded for an analogous returned case | Original snapshot 14/20 proxy-correct; later corpus rebaseline 10/20 | LLM judgements, no lawyer-verified relevant-case set; the dense channel was inactive in these runs. |
| Case-law rule extraction | 100 held-out cases checked by a quote-grounding gate and a provisional usability judge | 74/100 passed grounding; 58.1% of accepted rules rated fully usable | Usability was judged by an LLM proxy, below the 90% target; no lawyer sign-off. |
| Document reading | Four-matter inventory of 38 documents and 282 pages; one 26-page Vision text pass; 37 labelled fields across four documents in one matter | Text returned on 26/26 pilot pages | Coverage and OCR confidence are not field accuracy; the field-extraction variants were not scored. |
| Platform software | Real-PostgreSQL backend tests, frontend unit/component tests, and one browser refusal journey | 3,906 backend passed; 348 frontend passed; three browser refusal tests passed; 15 defects found and fixed | Wider browser run: four passed, nine failed, two skipped. Lawyer acceptance and full authenticated journeys remain open. |

The first row is the **accepted-paper evaluation**. Its 40-question split is
different from the earlier 10-question, 462-question and four-question
development runs listed in the combined test report. Do not put those scores
in the same comparison chart.

## Platform test detail

The 19 September 2026 completion report collected 3,922 backend tests:
3,906 passed, zero failed, ten were expected failures, one was skipped, and
five live-service tests were excluded. Backend line coverage was 85.4% and
branch coverage 63.9%. All 348 frontend unit and component tests passed.
Frontend logic-layer line coverage was 93.3%, while whole-frontend line
coverage was 27.0%. Coverage is a code-execution measure, not proof of legal
correctness.

The test programme covered domain policies, repositories and migrations on
real PostgreSQL, authentication and organisation isolation, API contracts,
concurrency, audit-chain integrity, privacy at rest, outbox delivery, quota
accounting, frontend logic and components, and a browser refusal journey.
Seven named safety rules were traced to passing tests. Fifteen defects were
found and fixed, including two critical defects; twelve appeared only with
real PostgreSQL behaviour.

Three Playwright tests passed for one refusal journey. A separate 20
September single-worker run of the wider browser suite recorded four passed,
nine failed and two skipped. Full authenticated approval, export, tenancy and
error-recovery journeys were not completed. Registration-ready export stayed
blocked because form wording lacked legal verification.

## Other research tests in the combined report

These development studies were run, but they are not the main accepted-paper
comparison:

| Study | Recorded test | Interpretation |
| --- | --- | --- |
| Earlier statute baselines | BM25 on 10 questions; an LSR variant on 462 questions; LawChain reproduction and BM25 comparison on four questions | Different question sets and provisional labels; unsuitable for a direct pooled ranking with the final 40-question paper test. |
| Similar-case variants | Variants v1–v8 on the same 20 fact patterns, judged for appropriateness by independent LLM subagents | A separate feature comparison tried verified-only graph edges, lexical IDF, fan-out weights, and catchword links; results varied and did not establish a stable improvement over the original snapshot. |
| Headnote rule recovery | Rule-based extractor with a bounded LLM fallback | Outputs remained unverified; the later held-out quote-grounding and proxy-usability results above give the more useful summary. |
| OCR field-extraction harness | Six planned variants and a deterministic synthetic fixture | Paid Gemini routes failed authentication and the open-source candidate was skipped pending a licence decision. No real field-accuracy score resulted. |

## Presenter boundaries

- The hosted research service currently uses BM25. The seven-system paper
  scores are offline research results.
- The case-law retriever is a separate research package. Its 20-query pilot
  exercised lexical and graph channels, not its optional dense channel; the
  LLM-graded score is not a lawyer-approved retrieval accuracy measure.
- A detected OCR region or returned text does not prove a correct parcel
  number, title fact, or legally sufficient document.
- Passing software tests support the specified behaviour under those tests.
  They do not constitute attorney validation of labels, answers, or form
  wording.
- Do not describe practitioner consultations as a completed lawyer acceptance
  test. They informed scope and requirements.

## Source documents

- [Final academic report](../final-report.tex), especially §§5.2–5.4 and
  Tables 3–4.
- [Combined project test report](../../../draftly-platform/docs/review/test-report-combined.md),
  especially §§6–9.
- [Similar-case retrieval architecture and test results](../../scripts/similar-case-retrieval/RESULTS.md)
  and its [initial](../../evaluation/runs/similar-case-retrieval-v1/metrics.json)
  and [rebaseline](../../evaluation/runs/similar-case-retrieval-v1-rebaseline/metrics.json)
  run records.
- [Platform test completion report](../../../draftly-platform/docs/review/testing-report.md),
  especially §§2–7.
- [OCR benchmark inventory](../../ocr-benchmark/README.md) and
  [Vision pilot metrics](../../ocr-benchmark/reports/vision-corpus-metrics.json).
- [Current platform status](../current-platform-system.md) for deployed
  component boundaries.
