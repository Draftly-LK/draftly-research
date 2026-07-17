# Case-Law Information Extraction — Implementation Plan

Full plan for extracting structured information (the **rule**, the parties, the
statute links, the disposition) from the 5,121 conveyancing judgments into
`data/processed/rules.csv` + `case_meta.csv`, for the retrieval engine.

This is **P4** of `retrieval-engine-plan.md`, made concrete: schema, prompts,
script architecture, model choice, cost.

## 0. What we're extracting, and the grounded reality

Per-case target (one `rules.csv` row per extracted rule; a case may yield 0–3):

```text
rule_id            draftly-rule-<case_id>-<n>
case_id            commonlii-LKCA-1985-12
citation           (1985) 1 Sri LR 45   |  72 NLR 289
court              LKSC | LKCA
year               1985
statement          the legal rule/holding, one sentence, neutral
supporting_quote   verbatim span from the judgment that states it
statute_section    SRC001-s2  (nullable; the section the rule construes)
topics             05;09        (from the case's topic tags)
scope              ratio | obiter | fact-specific
confidence         high | medium | low
method             headnote | llm-extract
status             unverified
```

Plus `case_meta.csv` (one row/case): parties, disposition
(allowed/dismissed/remitted), judges, catchwords, is_reported, slr_citation.

**Grounded corpus facts (measured 2026-07-17):**

- 5,121 conveyancing judgments: **3,703 reported** (CommonLII, NLR/SLR) +
  **1,418 unreported** (courts, 2012+).
- Sizes: reported median ~12k chars (~3k tokens), p90 30k; unreported median
  ~18k chars (~4.5k tokens), p90 46k.
- **64% of reported judgments contain a `Held`/`HELD` marker** → the holding is
  locatable by rule, not just by LLM. This is the single most important fact for
  cost: most reported cases don't need the model to *find* the rule, only to
  *clean* it.

## 1. Two-track strategy (headnote-first)

### Track A — reported cases (3,703): deterministic-first, LLM-clean

The reporter already wrote the rule (the headnote / `Held` block). So:

1. **Deterministic extraction** — regex-locate the `Held:` block (and the
   catchword line above the judgment). For the 64% with a clean marker, this
   *is* the rule text, verbatim → `supporting_quote`. `method=headnote`,
   `confidence=high`, no LLM call.
2. **LLM only to normalize** — the headnote is dense legalese; one cheap call
   turns it into a clean one-sentence `statement` and tags `scope`, *constrained
   to the extracted quote* (it may not add facts). If the quote is present, this
   is a tiny, low-risk call — or skip it and keep the raw headnote as statement
   for v1.

### Track B — unreported cases (1,418): bounded LLM extraction

No headnote. The model reads a **windowed extract** (not the whole judgment —
cost + focus) and returns a quote-backed rule or abstains:

1. **Deterministic windowing** — most SL judgments put the ruling near the end
   ("I hold…", "The appeal is allowed…", "In my view…"). Send: the first ~600
   tokens (facts/issue framing) + the last ~1,800 tokens (reasoning/order) +
   any paragraphs containing ruling cues. Caps input at ~2.5k tokens regardless
   of a 46k-char outlier.
2. **Bounded extraction** — model returns JSON: `statement`, `supporting_quote`,
   `statute_section` (from the closed catalogue), `scope`, `confidence`, or
   `{"rule": null}` to abstain.
3. **Validation** (non-negotiable): `supporting_quote` must appear **verbatim**
   in the judgment text (substring check after whitespace-normalization) — else
   the row is rejected → `status=quote_not_found`, never stored as a rule. Any
   `statute_section` must resolve against the registry + section must exist.

## 2. The prompts

### Prompt A — normalize a reported headnote (Track A, optional)

System:

```text
You are a legal editor for a Sri Lankan conveyancing case database. You are given
the verbatim HEADNOTE / HELD passage of a decided case. Restate the legal rule it
contains as ONE neutral sentence. Do not add facts, parties, or reasoning not in
the passage. If the passage states more than one distinct rule, return up to 3.
Output JSON only.
```

User:

```text
CITATION: {citation}
COURT: {court}
HEADNOTE:
\"\"\"{headnote_text}\"\"\"

Return JSON:
{"rules": [{"statement": "<one sentence>", "scope": "ratio|obiter|fact-specific"}]}
```

### Prompt B — extract a rule from an unreported judgment (Track B)

System:

```text
You are extracting the legal RULE (ratio decidendi) from a Sri Lankan
conveyancing judgment, for a citation database. Rules:
- Return ONLY a rule that is directly supported by a verbatim span you copy from
  the text into "supporting_quote". The quote MUST be copied exactly.
- The "statement" is your one-sentence neutral paraphrase of that quote's rule.
- If the judgment establishes no general conveyancing rule (purely fact-specific,
  procedural, or you are unsure), return {"rule": null}. Abstaining is correct
  and expected for many cases.
- "statute_section": ONLY if the rule construes a specific statute, choose from
  the CANDIDATE STATUTES list by its source_id; else null. Never invent one.
- Do not use knowledge outside the provided text. Do not cite other cases.
Output JSON only, no prose.
```

User:

```text
CITATION: {citation}   COURT: {court}   YEAR: {year}
CANDIDATE STATUTES (choose statute_section only from these):
{catalogue}          # ~57 lines: "SRC001  Prevention of Frauds Ordinance No.7 of 1840"
STATUTES THIS CASE ALREADY CITES (deterministic links, high prior):
{linked_sections}    # e.g. "SRC001-s2, SRC027-s48"  — from case_statute_section_links.csv

JUDGMENT EXTRACT:
\"\"\"{windowed_text}\"\"\"

Return JSON:
{"rule": {"statement": "...", "supporting_quote": "<verbatim span>",
          "statute_section": "SRCxxx-sN | null", "scope": "ratio|obiter|fact-specific",
          "confidence": "high|medium|low"}}
   OR
{"rule": null}
```

The `linked_sections` line is IL-PCSR's cross-task injection (+4.3 F1 in the
paper): we already know which sections this case cites, so we hand the model the
prior instead of making it guess.

## 3. Model choice + cost (this is the practical question)

The task is **short-context, structured classification/paraphrase with strict
JSON** — the easiest thing an LLM does. You do **not** need a frontier model; you
need one that (a) follows a JSON schema reliably and (b) is cheap. The validation
layer catches its mistakes, so raw IQ matters little.

### Recommended: **NVIDIA NIM, `meta/llama-3.1-8b-instruct`** (or `qwen2.5-7b-instruct`)

- OpenAI-compatible endpoint (`https://integrate.api.nvidia.com/v1`), free
  developer credits, one API key in `.env`. Swappable to anything OpenAI-shaped.
- 8B-class handles closed-set extraction fine; validation is the safety net.

### Cost math (grounded in the measured sizes)

| Track | Cases | Input tokens/case | Calls | Notes |
| --- | --- | --- | --- | --- |
| A (reported) | 3,703 | ~600 (just the headnote) | ≤3,703, or **0** if v1 keeps raw headnote | 64% need no *finding* |
| B (unreported) | 1,418 | ~2,500 (windowed) | 1,418 | the real LLM work |

Total ≈ **1,418 × ~2.5k in + ~0.3k out ≈ 3.5M input + 0.4M output tokens**
(+ optionally 3,703 × 0.6k ≈ 2.2M for Track A normalization).

- **NVIDIA free tier:** effectively **$0** — this volume fits in dev credits;
  re-runs are cached so cost doesn't repeat.
- **If paid, at ~$0.05–0.20 / 1M tokens (8B class):** roughly **$0.30–$1.50
  total.** Even a mid-tier model (~$0.60/1M) is **~$3–4**.
- **Fully local (Ollama, qwen2.5-7b) = $0**, just slower (~1,418 calls at a few
  sec each ≈ under an hour). Good fallback / privacy default.

**Verdict:** NVIDIA 8B free tier as default; Ollama local as the zero-cost/
offline fallback; both behind the same OpenAI-compatible client so the choice is
one env var. Don't pay for GPT-4-class here — wasted money on a task the
validator polices.

### Tier the spend (optional refinement)

Run 8B on everything; route only the **`low`-confidence or quote-rejected**
Track-B cases (likely a few hundred) to a stronger model. Keeps 95% on the cheap
model, spends real money only where it's earned.

## 4. Script architecture

```text
scripts/extract_case_rules.py        # orchestrator, resumable, cached
  ├─ llm_client.py (new)             # OpenAI-compatible; base_url+model+key from .env
  ├─ headnote.py (new)               # Track A: regex Held/catchword extraction
  ├─ windowing.py (new)              # Track B: build the ~2.5k-token extract
  └─ validate.py (new)               # quote-in-text + section-in-registry checks
outputs → data/processed/rules.csv, case_meta.csv, extract-cache/<case_id>.json,
          extract-rejects.csv (quote_not_found / invalid_section / abstained)
```

Design rules (match the repo's conventions):

- **Resumable + cached.** One JSON per case in `extract-cache/`; re-runs skip
  cached cases. A crash/rate-limit never loses work (same pattern as the
  harvesters).
- **Idempotent.** Re-running rebuilds `rules.csv` from the cache deterministically.
- **Batched + rate-limited.** Small concurrency (e.g. 4), polite backoff on 429.
- **`--limit N` / `--track A|B` / `--model <id>`** flags for cheap iteration on a
  sample before the full run.
- **Everything `status=unverified`.** Nothing becomes retrieval authority until
  the lawyer-verification sample signs off (extends the existing
  `verification-sample.csv` gate).
- **Grounding hard-stop:** a rule whose `supporting_quote` isn't found verbatim
  is never written to `rules.csv` — it goes to `extract-rejects.csv`. This is the
  line that keeps the model honest.

## 5. Validation + quality gate

1. **Quote check** — normalize whitespace, assert `supporting_quote` is a
   substring of the judgment. Reject otherwise. (Catches fabrication directly.)
2. **Section check** — `statute_section` resolves in `source-registry.csv` and
   the section number exists in that statute's text. Else null it, keep the rule.
3. **Sample for lawyer** — extend `verification-sample.csv` with ~30 rules
   (balanced reported/unreported, high/low confidence) → lawyer marks
   correct/incorrect → gives us **per-method, per-confidence precision** before
   any rule is trusted.
4. **Auto-metrics without a lawyer:** abstain rate, quote-rejection rate,
   %rules with a resolved section, rules-per-case distribution — sanity signals
   run every batch.

## 6. Build order

| Step | Deliverable |
| --- | --- |
| 1 | `headnote.py` + Track A on 3,703 reported → rules.csv (deterministic, $0). Measure: how many clean `Held` blocks. |
| 2 | `llm_client.py` + `validate.py` + `windowing.py`; run Track B on `--limit 50` → eyeball quality + JSON reliability |
| 3 | Tune the window + prompt on the 50; then full Track B (1,418) on NVIDIA free tier |
| 4 | Build `case_meta.csv` (parties/disposition) in the same pass (one prompt, extra fields) |
| 5 | Lawyer-verification sample → precision per method → promote verified rules |
| 6 | Wire `rules.csv` into the retrieval engine (Q1 doctrinal + Q7 authority panel) |

## 7. Honest risks

- **LLM misreads the ratio** (calls obiter the ratio, or over-generalizes). Quote-
  backing bounds it (the claim is anchored to real text), the lawyer sample
  measures it, but recall of *correct* rules on unreported cases will be
  imperfect — report it as a measured number, don't claim solved.
- **64% headnote coverage** means ~36% of reported cases also need the windowed
  LLM path — folded into Track B automatically (no clean `Held` → treat as
  unreported).
- **Scope label (ratio vs obiter)** is genuinely hard even for lawyers; treat it
  as advisory metadata, not a filter, until verified.
- **Copyright:** SLR headnotes are Council-of-Law-Reporting copyright — fine to
  use internally, don't republish. For a public artifact, store our own
  paraphrased `statement` + citation, not the verbatim headnote.
