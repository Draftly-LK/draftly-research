# HiREC-inspired statute retrieval

A port of **HiREC** (Hierarchical Retrieval with Evidence Curation, ACL 2025
Findings) to Sri Lankan statute retrieval, measured against the flat baselines in
`experiments/koblex-inspired-retrieval/`. Reference implementation:
`paper-implementations/LOFin-bench-HiREC/`.

Everything here is `status=unverified` experimental evidence. Nothing in `runs/`
is a legal answer, and none of it has been reviewed by a lawyer.

## Why

The flat baselines plateau at the same place. B0 (BM25) reaches recall@20 0.965
and B1 (LLM query generation + selection) reaches 0.922, and both put the
complete gold evidence in front of the model on only 18 of 20 questions.

The failures are structural, not lexical. Every one is "found the section, missed
its own children or siblings": q008's gold is s.51(a),(b) plus s.52(a)–(f),
q015's is s.13 plus its (a) and (b), q019's is s.188 plus s.189(a),(b). No amount
of query rewriting fixes that, which is why B1's rewriting made deep recall
worse rather than better.

HiREC's document → page → passage hierarchy maps onto act → section → provision,
and the corpus already carries all three levels. Expanding each BM25 hit to its
whole section subtree is the analog of HiREC's `--use_full_page`, and it is what
closes the gap.

## Results, 20-question smoke set

Retrieval ceiling, no LLM, free:

| run | seed K | complete evidence in pool | mean pool | max pool |
| --- | --- | --- | --- | --- |
| `smoke-r0-k5` | 5 | 0.80 | 23 | 99 |
| `smoke-r0-k10` | 10 | 0.90 | 52 | 116 |
| `smoke-r0-k20` | 20 | **1.00** | 91 | 179 |

Full pipeline, against the flat baselines on the same questions, corpus and
answering prompt:

| | B0 | B1 | B1 at matched pool | `smoke-h` (1 iter) | `smoke-full` (≤3 iter) |
| --- | --- | --- | --- | --- | --- |
| complete evidence available | 0.90 | 0.90 | 0.90 | **1.00** | **1.00** |
| evidence recall | — | 0.948 | 0.938 | **1.00** | **1.00** |
| complete-evidence accuracy | — | 0.85 | 0.85 | **1.00** | **1.00** |
| evidence precision | — | 0.990 | 0.978 | 0.865 | 0.911 |
| evidence F1 | — | 0.965 | 0.954 | 0.899 | 0.941 |
| citation F1 | — | 0.965 | 0.958 | 0.948 | 0.953 |
| exact-set accuracy | — | 0.85 | 0.85 | 0.70 | 0.75 |
| mean iterations | — | — | — | 1.0 | 1.2 |
| errors | 0 | 0 | 0 | 0 | 0 |

Three things to read out of that.

**The hierarchy solves the retrieval problem outright.** Complete-evidence
accuracy goes 0.85 → 1.00 and evidence recall reaches 1.00: every gold provision
was curated on every question. `smoke-b1-matched` is the control that rules out
the obvious alternative explanation — B1 given a candidate list the same size as
this pool scores exactly what it scored before (0.85 / 0.90), so the gain is the
section structure, not the extra candidates.

**It is paid for in precision.** The curator selects 2.55 provisions per question
against a gold mean of 2.2, so precision falls from 0.99 to 0.87–0.91 and F1
lands slightly *below* B1's. For a lawyer-in-the-loop product that is the right
trade — a missing provision is a wrong answer, an extra one is a moment's reading
— but it is a trade, not a free win.

**The iteration earns its keep, though not the way the paper suggests.** Two
questions ran the full budget, and at iterations 2 and 3 the curator selected
*fewer* provisions (1.5 vs 2.55) while recall stayed at 1.00. So the loop is not
finding missing evidence — the pool already had everything — it is tightening an
over-broad selection. Precision 0.865 → 0.911, exact-set 0.70 → 0.75, citation
exact match 0.80 → 0.85.

### The answerability finding

HiREC's loop is gated on an answerability check. The comparable koblex run shows
that check does not transfer: `evidence_complete` came back true on all 20
questions, giving a false-complete rate of 1.0 and an MCC of 0.0. That baseline
is recomputed into every `metrics.json` here under
`koblex_baseline_calibration`, so the finding is data rather than prose.

Deriving the flag from a forced coverage table instead of trusting the model's
boolean does change behaviour — it fires on 1–2 questions where the raw boolean
never fires, and those extra iterations are what produce the precision gain. The
coverage table is genuine analysis rather than narration: of the points it marked
`covered`, 95–96% named a gold provision.

But the calibration question itself becomes unanswerable here, and the metrics
say so out loud. Once the hierarchy puts complete evidence in the pool on 20 of
20 questions, a claim of "complete" is never wrong, so `false_complete_rate` has
no denominator and is reported as `null` with an explicit `degenerate` note.
Removing the retrieval ceiling removed the thing the answerability check was
there to catch. Measuring it properly needs questions whose evidence genuinely
is not in the corpus.

`iterations.gold_lost` is 0 everywhere, so HiREC's re-filter-don't-freeze policy
never cost a provision on this set and `--freeze-evidence` is not needed.

## Commands

```powershell
uv run python experiments/HiREC-inspired-retrieval/hirec_build_index.py
uv run pytest tests/test_hirec_smoke_pipeline.py -q

# free
uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py `
    --run-name smoke-r0-k20 --seed-top-k 20

# cost it before spending
uv run python experiments/HiREC-inspired-retrieval/run_hirec.py --dry-run

# paid
uv run python experiments/HiREC-inspired-retrieval/run_hirec.py --run-name smoke-h --max-iterations 1
uv run python experiments/HiREC-inspired-retrieval/run_hirec.py --run-name smoke-full --max-iterations 3

uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py `
    --run-name smoke-full --baseline-run smoke-b1
```

`OPENAI_API_KEY` in `.env`. Roughly 45 calls and 320k input tokens for the 20
questions at the observed 1.2 mean iterations; all runs here together cost well
under a dollar.

## Layout

| File | Role |
| --- | --- |
| `hirec_config.py` | Paths, per-stage effort, run provenance, the fidelity ledger |
| `hirec_index.py` | BM25 over provisions, plus act scoping and section-subtree lookup |
| `hirec_hierarchy.py` | Pooling policy: expansion, ordering, merging, rendering |
| `hirec_schemas.py` | Structured-output schemas and the derived signals |
| `hirec_llm.py` | The four stages, with one shared ID-guarded retry |
| `run_hierarchy_ceiling.py` | The free ceiling run |
| `run_hirec.py` | The loop |
| `hirec_evaluate.py` | Scoring. The only module that reads gold |

Every module is `hirec_`-prefixed. That is not cosmetic: the koblex directory
already defines `schemas.py` and `evaluate.py`, both experiments put their
directory on `sys.path`, and pytest collects both test files in one process, so
an unprefixed name would silently resolve to the wrong module. A test enforces
it.

The corpus (`statute.jsonl`), the questions and the gold file are read from
`experiments/koblex-inspired-retrieval/data/` rather than copied, which is what
keeps these numbers comparable to that experiment's. The index database is
private, because its schema carries `act_id`, `section_id` and `ordinal`.
`prompts/grounded_answer.md` is a byte-identical copy of the koblex one so the
answering stage is genuinely the same; a test compares their hashes.

## Fidelity

`run_config.json` records a `hirec_fidelity` ledger of what this port keeps and
where it departs, per run, so no number is read without knowing which flags were
on.

Kept: the act → section → provision hierarchy; one LLM inference doing filter,
answerability, missing-information and complementary question together; the
original question never mutated and always what the curator and the answering
stage see; the refined query driving retrieval only; accumulated evidence
re-filtered rather than frozen; the saturation hatch; and answering anyway on
budget exhaustion after one uncurated last-resort retrieval.

Departed, always: completeness derived from the coverage table with both values
recorded; the schema forcing analysis fields ahead of the boolean; curation at
effort `medium`; the answer as a separate stage; structured outputs with one
corrective retry rather than a hash-delimited blob; `max_iterations` 3 not 4;
`max_relevant_ids` 25 not 10 (gold sets reach 9 and pools reach 179, so 10 would
fire the hatch on nearly every question); a whole-section pool rather than 10
flat chunks; no query rewrite on the first iteration; and the tried-query list
withheld from the curator so no generated string can reach a prompt that judges
or cites evidence.

Behind off-by-default flags: `--negative-prior`, `--xref-precheck`,
`--freeze-evidence`, `--gate-on model`, `--act-selector llm`.

Bugs in the reference implementation deliberately not reproduced: the batch
runner's hardcoded 10-row dataset slice, and its evidence-replacement line
dedented out of its own loop so only the last question in a batch gets filtered.

## Known limitations

- 20 questions. One question moves any mean by 5 points, and the calibration
  confusion matrix is four cells with single-digit counts. Nothing here is
  significant; it is directional.
- The questions are `paper_id: synthetic-smoke-test`, authored alongside the
  corpus. They are not an independent benchmark.
- Because every question's evidence is in the corpus, the answerability check
  cannot be scored. Questions with genuinely absent evidence are what that needs.
- The act stage is `derived` by default and excluded no gold at any seed K
  (`gold_provisions_excluded_by_act_filter` is 0), so it is doing nothing
  measurable. `--act-selector llm` exists to test whether HiREC's document stage
  transfers to an 18-document corpus; that arm has not been run.
- Two schedule rate tables in the corpus are structured numeric data and are not
  flattened into provision text, so rate lookups cannot retrieve them.
