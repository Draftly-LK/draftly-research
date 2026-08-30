# Task: build an evaluation dataset for the statute retrieval engine

**Owner:** Praveen
**Requested by:** Himath
**Status of everything produced here:** `status=unverified` until a lawyer signs it off. Nothing in this task produces legal advice.

## The goal

Turn the 589 parsed Law College past-paper question parts into an evaluation
dataset the retrieval engine can be scored against: a `questions.jsonl` and a
matching `gold.jsonl` where every question is tagged with the exact statutory
provisions that answer it.

Today the engine is measured on 20 synthetic questions written alongside the
corpus. That is enough to prove the pipeline runs and nothing more. One question
moves any average by five points, and because the questions were written to fit
the corpus, every one of them is answerable from it — which makes some of the
metrics meaningless (see [What this unblocks](#what-this-unblocks)). Real exam
questions fix both problems.

**You are not writing legal answers.** You are identifying which provisions of
which Acts a question turns on. If you find yourself drafting an opinion, you
have gone too far.

## What this unblocks

Two things, and the second is the one people miss.

1. **Real Recall and MRR numbers.** 20 synthetic questions cannot support a
   claim about how well the engine works. A few hundred real ones can.

2. **A working answerability metric.** The engine is supposed to say "I do not
   have the evidence to answer this" instead of guessing. Right now it cannot be
   scored on that, because all 20 existing questions have complete evidence in
   the corpus — a claim of "I have everything" is never wrong when everything is
   always there. The measurement is degenerate and reports `null`.

   Questions whose evidence is genuinely **absent** from the corpus are what fix
   it. That is bucket B below, and it is the most valuable output of this task,
   not the leftover pile. It doubles as a ranked backlog telling Lahiru and you
   which statutes to canonicalise next.

## What already exists — do not rebuild these

| Thing | Where |
| --- | --- |
| Parsed past papers, 16 papers / 144 questions / 589 parts | `data/evaluvation/parsed-pastpapers/` |
| Pre-sorted authoring worksheet, one row per part | `data/evaluvation/pastpaper-triage/worksheet.csv` |
| Triage summary | `data/evaluvation/pastpaper-triage/triage-summary.json` |
| Triage / build tool | `experiments/HiREC-inspired-retrieval/pastpaper_triage.py` |
| Dataset self-check | `experiments/HiREC-inspired-retrieval/validate_dataset.py` |
| Free (no-API) retrieval run | `experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py` |
| Scoring | `experiments/HiREC-inspired-retrieval/hirec_evaluate.py` |

The corpus you are tagging against is 21 Acts, 971 sections, 6,211 provisions,
at `experiments/koblex-inspired-retrieval/data/statute.jsonl`.

## The deliverable

1. `data/evaluvation/pastpaper-triage/worksheet.csv` — every row reviewed, with
   `bucket`, `verified_by` and `verified_date` filled in.
2. `pastpaper_questions.jsonl` and `pastpaper_gold.jsonl`, generated from it.
3. `validate_dataset.py` exits 0 against them.
4. A short results note: counts per bucket, Recall@k and MRR from a free run,
   and the ten worst retrieval failures with your reading of why.

## The three buckets

This is the whole judgement call. The worksheet already carries a
`suggested_bucket` from a keyword scan — **it is a suggestion and it is wrong
often enough that you must confirm every row.** Put your decision in the
`bucket` column. Leave `suggested_bucket` alone; the disagreement between the
two columns is itself useful.

Current suggestions across 589 parts: **A 66, B 90, C 433**.

### A — retrievable (`A-retrievable`)

The question turns on a rule in one of the 21 Acts in the corpus.
**Fill in `gold_provisions`.** Set `corpus_coverage` to `complete`.

> `paper-01/q1/iv` — "Explain the rules set out in sections 22 to 26 of
> Matrimonial Rights and Inheritance Ordinance No. 15 of 1876."

That one hands you the answer. Most will not.

### B — evidence absent (`B-evidence-absent`)

The question turns on a statute the corpus does not hold.
**Leave `gold_provisions` empty.** Set `corpus_coverage` to `absent`. Record the
statute it needs in `notes` — that is the ingestion backlog.

> `paper-01/q3/ii` — "Does Herath require approval from the Divisional Secretary
> to Mortgage the said land?" — needs the Land Development Ordinance, which is
> not in the corpus.

The statutes most often needed and missing: Registration of Documents Ordinance
(33 parts), Notaries Ordinance (23), Prevention of Frauds Ordinance (9),
Partition Act (7), Mortgage Act (4), Land Development Ordinance (3).

### C — not a retrieval question (`C-not-retrieval`)

Drafting, pedigree drawing, or pure arithmetic. No statutory rule to find.
**Excluded from the dataset.** Say why in `notes`.

> `paper-01/q1/i` — "Draw up the pedigree showing the devolution of title…"

### The override case — read this one

> `paper-01/q1/ii` — "What are the shares presently owned by each heir in the
> property?"

Suggested **C**, because it names no statute. It is really **A**: the shares
follow the intestacy rules in the Matrimonial Rights and Inheritance Ordinance,
which the corpus has. A question that names no Act can still be a statute
question. Override it and note why.

## How to write a gold provision ID

A `node_id` is the corpus's address for one provision. It is not a citation —
it is an exact string that must match the corpus character for character.

```text
15-1876/section-22                      a whole section
17-2002/section-13/paragraph-a          a paragraph within a section
7-2007/section-73/proviso-1             a proviso
21-1998/section-60/subsection-1         a subsection
```

The prefix is the `act_id`, `<number>-<year>`:

| act_id | Act | act_id | Act |
| --- | --- | --- | --- |
| `1-1911` | Jaffna Matrimonial Rights and Inheritance Ord. | `21-1844` | Wills Ordinance |
| `2-1958` | Tea and Rubber Estates (Control of Fragmentation) Act | `21-1931` | State Land (Claims) Ordinance |
| `7-2007` | Companies Act | `21-1998` | Registration of Title Act |
| `10-1931` | Muslim Intestate Succession Ordinance | `23-1917` | Kandyan Succession Ordinance |
| `11-1973` | Apartment Ownership Law | `30-1968` | Nindagama Lands Act |
| `15-1876` | Matrimonial Rights and Inheritance Ordinance | `35-1947` | Registration of Old Deeds and Instruments Ord. |
| `17-1852` | Deeds and Documents (Execution before Public Officers) Ord. | `37-1954` | National Housing Act |
| `17-2002` | Survey Act | `38-2014` | Land (Restrictions on Alienation) Act |
| `18-1945` | Land Registers (Reconstructed Folios) Ordinance | `41-1978` | Urban Development Authority Act |
| `19-1931` | Buddhist Temporalities Ordinance | `43-1979` | Land Grants (Special Provisions) Act |
| | | `59-1947` | Thesawalamai Pre-emption Ordinance |

Rules:

- **Copy the ID, never type it.** Find the provision in `statute.jsonl` and copy
  its `node_id`. A typo becomes a silent wrong answer that makes the engine look
  worse than it is. `validate_dataset.py` catches IDs that do not exist; it
  cannot catch an ID that exists but is the wrong one.
- **Separate multiple IDs with a semicolon** in the worksheet:
  `15-1876/section-22; 15-1876/section-23`.
- **Tag the provision that carries the rule, not its neighbours.** If the rule is
  in `section-13/paragraph-a`, tag the paragraph. If the operative words are
  spread across a section and its paragraphs, tag each part that carries some of
  the rule.
- **Do not pad.** An honest three-provision answer beats a nine-provision one
  that hedges. Precision is measured too.
- **If you are unsure, mark the row `notes: UNSURE` and move on.** Flagged rows
  get reviewed together. Guessing is worse than flagging.

## Procedure

Work in batches of one paper. Do not do all 16 and then ask for review.

```powershell
# 1. Read the worksheet. One row per part, 589 rows, pre-sorted.
#    data/evaluvation/pastpaper-triage/worksheet.csv

# 2. Fill in one paper's rows: bucket, gold_provisions, citations,
#    question_type, n_hops, corpus_coverage, notes, verified_by, verified_date

# 3. Build the dataset from the rows you have confirmed so far
uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py build

# 4. Self-check. This must exit 0 before you ask anyone to look.
uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py `
    --questions data/evaluvation/pastpaper-triage/pastpaper_questions.jsonl `
    --gold data/evaluvation/pastpaper-triage/pastpaper_gold.jsonl

# 5. Free retrieval run. No API calls, costs nothing, run it as often as you like.
uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py `
    --questions data/evaluvation/pastpaper-triage/pastpaper_questions.jsonl `
    --run-name pastpaper-r0-k20 --seed-top-k 20

# 6. Score it
uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py `
    --run-name pastpaper-r0-k20 `
    --gold data/evaluvation/pastpaper-triage/pastpaper_gold.jsonl
```

Steps 5 and 6 are free and make no API calls. **Do not run `run_hirec.py`
without asking first** — that one spends money.

Field values:

| Field | Allowed |
| --- | --- |
| `bucket` | `A-retrievable`, `B-evidence-absent`, `C-not-retrieval` |
| `question_type` | `recall`, `application`, `calculation` |
| `corpus_coverage` | `complete`, `partial`, `absent` |
| `n_hops` | Integer ≥ 1. How many separate provisions must be combined. |

## Definition of done, per paper

- Every row of that paper has `bucket`, `verified_by`, `verified_date`.
- Every bucket A row has at least one `gold_provisions` ID and a `citations` entry.
- Every bucket B row has an empty `gold_provisions` and names the missing statute in `notes`.
- Every bucket C row has a reason in `notes`.
- `validate_dataset.py` exits 0.
- Rows you were unsure about are marked `UNSURE`, not guessed.

## Do not touch

These have automated guards; breaking them fails the test suite and silently
invalidates comparisons against earlier runs.

- `experiments/koblex-inspired-retrieval/data/statute.jsonl` — generated. To add
  a statute, use the canonicalisation pipeline, not a hand edit.
- Anything in `experiments/HiREC-inspired-retrieval/prompts/`. Changing a prompt
  makes every previous run incomparable.
- The 20-question smoke set and its gold. Your work is a new dataset alongside
  it, not a replacement.
- Do not put gold answers into any file the engine reads at run time. The
  separation between what the engine sees and what it is scored against is
  enforced by tests.

## What to report back

Per batch, one short message:

- Paper number, rows reviewed, bucket counts.
- How often you overrode `suggested_bucket`, and the pattern if there is one.
- Rows marked `UNSURE` and why.
- Once a few papers are in: Recall@20, Recall@50, MRR and complete-evidence
  from step 6, plus the worst ten failures with your reading of each — the
  question, the gold, what the engine retrieved instead.

## Known gaps — mine to fix, not yours

- **Scoring a bucket B question will currently crash.** `hirec_evaluate.py`
  divides by the number of gold provisions, which is zero for an
  evidence-absent question. Until that is fixed, run steps 5 and 6 over bucket A
  rows only. Tell me when you have bucket B rows ready and I will fix it.
- Latency and cost are recorded per run in `usage.jsonl` and
  `usage_summary.json`, but only for paid runs. The free run has neither, by
  definition.
- The cost figure is derived from a hand-entered price table that is not
  verified against the provider's current list. Token counts are measured and
  trustworthy; the money number is not. Do not quote it externally.

## Questions

Ask early rather than guessing on 50 rows. The expensive mistake is a
consistently wrong convention applied across a whole paper — that is why the
first batch is one paper and not sixteen.
