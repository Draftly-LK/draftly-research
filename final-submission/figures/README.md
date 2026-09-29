# Final report figure assets

This folder collects project-created PNGs that may be useful for the final
report. The source files remain in their original locations. Names here describe
content and origin; they do not assign final figure numbers.

## Editable current-system diagrams

Each new system diagram has a raw Mermaid `.mmd` source and a matching Markdown
`.md` preview. The PNG is the verified render. Solid paths show the documented
hosted system; dashed paths mark designed or planned components.

| Diagram | Mermaid preview | Report use |
| --- | --- | --- |
| Hosted deployment | [hosted-system.md](hosted-system.md) | Detailed source; [hosted-report.md](hosted-report.md) is the condensed report variant. |
| Document processing | [document-processing.md](document-processing.md) | Detailed source; [document-processing-report.md](document-processing-report.md) is the condensed report variant. |
| Matter workflow | [matter-workflow.md](matter-workflow.md) | Current lawyer-controlled process model. |
| Workbench use cases | [workbench-use-cases.md](workbench-use-cases.md) | Current actor and action model. |
| Matter domain | [matter-domain.md](matter-domain.md) | Conceptual classes. |
| Core data model | [core-data-model.md](core-data-model.md) | Conceptual entity relationships. |

The live VPS uses PostgreSQL 18 and a source-file volume. MinIO is a planned
object-storage service, and Laya is an evaluation candidate for classifying
OCR text. Neither is represented as a live service.

## Platform and system diagrams

| File | Source | Status |
| --- | --- | --- |
| `platform-document-processing-v1-pipeline.png` | `proj-docs/project Management/document-processing-v1-pipeline.png` | Historical design reference with Google Cloud Storage and Neon labels; superseded in the report by `document-processing-current-target.png`. |
| `platform-matter-agent-service-architecture.png` | `proj-docs/project Management/matter-agent-service-architecture.png` | Design reference. Check service and storage status before publication. |
| `srs-system-context.png` | `proj-docs/SRS/diagrams/draftly_system_context.png` | SRS context diagram; review against final scope. |
| `report-fig-01-use-cases.png` | Draft report, Fig. 1 | Existing report diagram. |
| `report-fig-02-deployment-draft.png` | Draft report, Fig. 2 | Revise: it describes hybrid retrieval and provider integrations as deployed. |
| `report-fig-03-domain-classes.png` | Draft report, Fig. 3 | Existing report diagram; verify against current schema. |
| `report-fig-04-rta-transfer-activity.png` | Draft report, Fig. 4 | Existing report diagram; check human approval boundary. |
| `report-fig-05-core-er.png` | Draft report, Fig. 5 | Existing report diagram; verify table and association counts. |
| `report-fig-14-grounded-research-sequence.png` | Draft report, Fig. 14 | Existing report diagram; verify against deployed service. |
| `deployment-demo.png` | `deployment-demo.dot` in this folder | Report deployment figure with self-hosted PostgreSQL, current VPS file storage, and planned MinIO. |
| `document-processing-current-target.png` | `document-processing-current-target.dot` in this folder | Report processing figure with hosted stub path and marked design candidates. |
| `ui-prototype-fact-review.png` | `draftly-platform/docs/review/` baseline capture, 22 July 2026 | Cropped synthetic-data fact-review prototype used in the final report. It is not a current live capture. |
| `ui-prototype-checks.png` | `draftly-platform/docs/review/` baseline capture, 22 July 2026 | Cropped synthetic-data checks prototype used in the final report. It is not a current live capture. |

## Retrieval research and evaluation

| File | Source | Status |
| --- | --- | --- |
| `research-architecture-preview.png` | `research-paper/figures/architecture-preview.png` | Preview; a vector source also exists in the research folder. |
| `research-benchmark-construction-preview.png` | `research-paper/figures/benchmark-construction-preview.png` | Preview; a vector source also exists in the research folder. |
| `research-corpus-retrieval-preview.png` | `research-paper/figures/corpus-retrieval-preview.png` | Earlier preview of the corpus and retrieval diagram. |
| `research-corpus-retrieval-figure.png` | `research-paper/figures/corpus-retrieval-figure.png` | Full PNG variant. |
| `research-corpus-retrieval-paperbanana.png` | `research-paper/figures/corpus-retrieval-paperbanana.png` | Paperbanana variant. |
| `report-fig-06-corpus-retrieval.png` | Draft report, Fig. 6 | Black-and-white report variant. |
| `report-fig-13-recall-by-bundle-size.png` | Draft report, Fig. 13 | Existing test-split chart; labels are provisional pending lawyer review. |
| `benchmark-main-test-complete-at-k.png` | `data/evaluvation/statutory-qa-v1/experiments/figures/main-test/complete_at_k.png` | Main test run; proposed gold labels. |
| `benchmark-main-test-ablations.png` | `data/evaluvation/statutory-qa-v1/experiments/figures/main-test/ablations.png` | Main test run; proposed gold labels. |
| `benchmark-gold-sunburst.png` | `data/evaluvation/statutory-qa-v1/experiments/figures/gold-sunburst-main.png` | Benchmark distribution; proposed gold labels. |

## Historical progress and brand

| File | Source | Status |
| --- | --- | --- |
| `progress-aug-corpus.png` | `progress-figures/fig-1-corpus-progress.png` | August snapshot. |
| `progress-aug-coverage-gap.png` | `progress-figures/fig-2-coverage-gap.png` | August snapshot. |
| `progress-aug-retrieval-comparison.png` | `progress-figures/fig-3-retrieval-b0-vs-b1.png` | August snapshot. |
| `progress-aug-selection-by-hops.png` | `progress-figures/fig-4-selection-by-hops.png` | August snapshot. |
| `brand-draftly-logo-blue.png` | `assets/draftly-logo/logo-tw-blue.png` | Brand asset for cover or appendix. |

## Missing final assets

The draft report's Fig. 7 and Fig. 8 use the same 1-by-1-pixel placeholder.
Its Fig. 9 through Fig. 12 contain labelled screenshot placeholders, not
captured application screens. These were excluded. The final LaTeX report
renders two pseudocode figures directly and uses the two dated synthetic
prototype captures listed above.
