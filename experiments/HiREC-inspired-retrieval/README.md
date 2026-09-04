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

## The pipeline

```text
background + question
   │
   ├─ act selection ──────────── 21 Acts → ≤3.  Default "derived": free, no LLM call
   │
   ├─ BM25 seed ──────────────── top-20 provisions, scoped to those Acts
   │
   ├─ SECTION EXPANSION ──────── each hit → its whole section subtree = the "pool"
   │                             (~90 provisions, grouped by section, ranked)
   │
   ├─ CURATION ──── ONE LLM call: which provisions are needed
   │                            + is anything missing
   │                            + what to search for next
   │       │
   │       ├─ complete? ──── yes ──→ answer
   │       └─ no ──→ rewrite the gap as a query, re-retrieve, merge, curate again
   │                 (max 3 iterations)
   │
   └─ ANSWER ─────────────────── from curated provisions only, citing node_ids
```

Section expansion is the step that matters, and it is deterministic and free.
Everything above and below it is bounded LLM work over what that step produced.

Two properties of the diagram are enforced in code rather than by convention.
The refined query written by the curation stage feeds only the next retrieval —
`curate_evidence()` and `answer()` have no parameter it could arrive through, so
a generated string cannot reach a prompt that judges or cites evidence. And the
answering stage sees the original question every time; the loop never mutates it.

## Results, 20-question smoke set

**Read the corpus version before comparing anything.** The statute corpus grew
from 18 Acts / 5,342 provisions to 21 Acts / 6,211 provisions on 2026-08-26,
when the National Housing Act, Urban Development Authority Act and Buddhist
Temporalities Ordinance were ingested. Numbers taken either side of that are not
comparable: re-running the same command on the larger corpus cost about 5 points
of evidence precision, because there is more competing text to pull in.

Retrieval ceiling, no LLM, free. Current corpus (21 Acts):

| run | seed K | complete evidence in pool | mean pool | max pool |
| --- | --- | --- | --- | --- |
| `smoke-r0-k5` | 5 | 0.80 | 25 | 99 |
| `smoke-r0-k10` | 10 | 0.90 | 50 | 116 |
| `smoke-r0-k20` | 20 | **1.00** | 90 | 181 |
| `smoke-r0-k30` | 30 | **1.00** | 123 | 219 |

K=20 is the operating point: the first value where complete evidence is
available for every question. K=30 buys nothing and starts truncating pools.

Full pipeline. All four `smoke-*` columns are on the current corpus; the three
baselines are **not**, and are marked accordingly:

| | B0 † | B1 † | B1 matched † | `smoke-h` | `smoke-act-llm` | `smoke-full` | `smoke-final` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| act selector | — | — | — | derived | llm | derived | llm |
| max iterations | — | 1 | 1 | 1 | 1 | 3 | 3 |
| complete evidence available | 0.90 | 0.90 | 0.90 | **1.00** | **1.00** | **1.00** | **1.00** |
| evidence recall | — | 0.948 | 0.938 | **1.00** | **1.00** | **1.00** | **1.00** |
| complete-evidence accuracy | — | 0.85 | 0.85 | **1.00** | **1.00** | **1.00** | **1.00** |
| evidence precision | — | 0.990 | 0.978 | 0.817 | 0.890 | 0.838 | 0.825 |
| evidence F1 | — | 0.965 | 0.954 | 0.852 | 0.915 | 0.870 | 0.861 |
| citation F1 | — | 0.965 | 0.958 | 0.903 | 0.919 | 0.966 | 0.923 |
| exact-set accuracy | — | 0.85 | 0.85 | 0.65 | 0.75 | 0.65 | 0.65 |
| act precision | — | — | — | 0.558 | 0.858 | 0.558 | 0.867 |
| mean acts selected | — | — | — | 2.15 | 1.35 | 2.15 | 1.30 |
| gold lost to act filter | — | — | — | 0 | 0 | 0 | 0 |
| gold lost to re-filtering | — | — | — | 0 | 0 | 0 | 0 |
| mean iterations | — | — | — | 1.0 | 1.0 | 1.2 | 1.2 |
| cost (USD) | 0 | ~0.05 | ~0.06 | 0.114 | 0.130 | 0.129 | 0.154 |
| latency per question | — | — | — | 14.2s | 19.0s | 15.5s | 17.1s |
| errors | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

† measured on the 18-Act corpus. Not comparable to the unmarked columns.

### What is established, and what is not

**Established.** Complete evidence available and evidence recall are **1.00 in
every configuration**. That is the result: the section-expanded pool always
contains every gold provision, and the curator always selects all of them. The
retrieval half is deterministic and reproduces exactly across runs — identical
pool recall@20 for the two `derived` runs (0.925) and for the two `llm` runs
(0.942). Errors are zero throughout, and `gold_lost` to re-filtering is zero, so
HiREC's re-filter-don't-freeze policy never costs a provision here and
`--freeze-evidence` is unnecessary.

**Not established: any precision or F1 difference between these four
configurations.** Evidence precision spans 0.817–0.890 across them, and the
configuration combining the two apparent improvements (`smoke-final`: LLM acts
*and* 3 iterations) lands in the middle, worse than either component alone. The
iteration effect even changes sign depending on the act selector — with
`derived` it helps precision (0.817 → 0.838), with `llm` it hurts
(0.890 → 0.825). Two "improvements" that do not compose, and whose direction
flips, is what noise looks like.

At 20 questions one question moves any mean by 5 points, which is most of the
observed 7-point spread. There are no repeat runs of any configuration, so the
run-to-run variance is unmeasured and cannot be separated from the config
effect. **Do not quote a best configuration from this table.** Establishing one
needs either repeated runs per config or the larger past-paper question set.

The LLM act selector is worth keeping in the running for a reason that does not
depend on the noisy metrics: it selects 1.3 Acts against `derived`'s 2.15,
loses no gold at any seed K, and picks the single correct Act on 14 of 20
questions where `derived` drags in irrelevant ones on 13 of 20 — Tea and Rubber
Estates for a title-registration question, National Housing for a Companies Act
one. Whether that tidiness converts into better answers is the open question.

One side effect worth knowing: act scoping concentrates all 20 BM25 seeds inside
fewer Acts, so they spread across more distinct sections there and the *maximum*
pool grows (204 against 181) even though the mean shrinks. Two questions
truncate under `llm`. `max_pool_records` is closer to binding than it was.

Three things to read out of that.

**The hierarchy solves the retrieval problem outright.** Complete-evidence
accuracy goes 0.85 → 1.00 and evidence recall reaches 1.00: every gold provision
was curated on every question. `smoke-b1-matched` is the control that rules out
the obvious alternative explanation — B1 given a candidate list the same size as
this pool scores exactly what it scored before (0.85 / 0.90), so the gain is the
section structure, not the extra candidates.

**It is paid for in precision.** The curator selects more provisions than the
gold mean of 2.2, so precision falls from B1's 0.99 to 0.82–0.89 and F1 lands
*below* B1's. For a lawyer-in-the-loop product that is the right trade — a
missing provision is a wrong answer, an extra one is a moment's reading — but it
is a trade, not a free win, and precision is where the remaining work is.

**The iteration does something, but not what the paper intends.** Two questions
run the full budget, and at iterations 2 and 3 the curator selects *fewer*
provisions (1.5 against 2.5) while recall stays at 1.00. It is not finding
missing evidence — the pool already had everything — it is narrowing an
over-broad selection. Both questions exhaust the budget rather than converging,
so the loop never satisfies its own completeness gate on them. Whether the
narrowing is a real gain is exactly what the variance problem above leaves
unresolved.

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

Scoring now supports absent-evidence questions, so the negative class can be
added as soon as it exists. A question with `corpus_coverage: absent` carries no
gold provisions; it is excluded from every rank-aware and set-valued metric
(where an empty gold set has no defined value rather than a value of zero), and
scored instead in the `absent_evidence` block on the only thing that matters
there — did the pipeline abstain, or answer anyway and cite provisions that do
not govern the question. In the calibration block such a question counts as
never complete, which it must: an empty gold set is a subset of everything, so
left to the ordinary subset test it would score as "the evidence was complete"
on every run and silently inflate the very metric it exists to fix.

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
