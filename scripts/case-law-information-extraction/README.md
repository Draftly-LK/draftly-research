# Case-Law Information Extraction

Extracts the **legal rule** (ratio) from each conveyancing judgment into a
structured, quote-grounded table for the retrieval engine. Implements P4 of
`retrieval-engine-plan.md` / the design in `case-law-extraction-plan.md`.

## What it produces (`output/`, gitignored — derived + copyrighted headnote text)

- `rules.csv` — one row per extracted rule: `rule_id, case_id, citation, court,
  year, statement, supporting_quote, statute_section, section_status, scope,
  confidence, method, status`. Every rule is `status=unverified`.
- `case_meta.csv` — one row per case: parties, disposition, court, year, reported.
- `extract-rejects.csv` — cases with no rule (abstained / no-headnote /
  quote-not-found / budget) with the reason.
- `cache/<case_id>.json` — per-case result (resumable; CSVs rebuild from here).
- `usage.json` — cumulative token usage per model (credit tracking).

## Two tracks (headnote-first)

- **Track A — reported cases (CommonLII):** deterministic `Held:`-block
  extraction, **no LLM, $0**. ~1,065 rules from the reported set. Cases without a
  clean `Held:` block fall through to Track B.
- **Track B — unreported / no-headnote:** bounded LLM extraction over a windowed
  extract; the model must return a `supporting_quote` that appears **verbatim**
  in the judgment or the rule is rejected. Full ~57-statute catalogue given as
  the allowed set, plus the statutes the case already cites (cross-task prior).

## Grounding gate (why a cheap model is safe)

`validate.py` rejects any rule whose `supporting_quote` is not a verbatim
substring of the judgment, and nulls any `statute_section` not in the registry /
not present in that statute's text. The validator — not the model — guards
correctness (see `case-law-extraction-plan.md` §"literature").

## Models (tiered, swappable)

OpenAI-compatible client → NVIDIA NIM by default (`NVIDIA_API_KEY` in `.env`):

- `MODEL_CHEAP` = `meta/llama-3.1-8b-instruct` — the workhorse.
- `MODEL_STRONG` = `meta/llama-3.3-70b-instruct` — escalation only, on
  `--escalate`, for low-confidence / quote-rejected cases.

Override via env (`DRAFTLY_MODEL_CHEAP`, `DRAFTLY_MODEL_STRONG`,
`NVIDIA_BASE_URL`) — point at local Ollama's `/v1` for a $0 offline run.

## Usage

```bash
# Track A — free, all reported cases
python scripts/case-law-information-extraction/extract_case_rules.py --track A --source commonlii

# Track B — sample the LLM path (credit-guarded)
python scripts/case-law-information-extraction/extract_case_rules.py \
    --track B --source official-courts --limit 25 --escalate --max-llm-calls 60

# Full run (all conveyancing cases), escalation on, generous credit cap
python scripts/case-law-information-extraction/extract_case_rules.py \
    --track all --escalate --max-llm-calls 6000
```

Flags: `--track {A,B,all}`, `--source {commonlii,official-courts,all}`,
`--limit N`, `--escalate`, `--normalize` (LLM-clean Track A headnotes),
`--model-cheap/-strong`, `--max-llm-calls N` (0 = unlimited), `--force`.

**Resumable:** re-running skips cached cases; CSVs are always rebuilt from the
full cache. **Idempotent.** **Credit-guarded** via `--max-llm-calls`.

## Files

- `config.py` — env, model tiers, paths, window sizes.
- `llm_client.py` — OpenAI-compatible call + JSON parse + retry/backoff + usage.
- `catalogue.py` — closed statute catalogue + `SRCxxx-sN` resolution/validation.
- `headnote.py` — Track A `Held:` block extraction.
- `windowing.py` — Track B focused extract (head + ruling-cue paras + tail).
- `validate.py` — verbatim-quote + section grounding gate.
- `extract_case_rules.py` — orchestrator.

## Status / next

Every rule is `unverified`. Promote to `verified` only after the
lawyer-verification sample signs off (extends `verification-sample.csv`), which
also yields per-method precision and a LoRA fine-tuning set if accuracy needs it.
