#!/usr/bin/env bash
# Spawn Codex GPT-5.5(high) judge workers over pending packs, PARALLEL at a time.
# Resumable: a pack with an existing part-N.jsonl is skipped. Run from this dir.
#   bash launch_judges.sh [max_packs]
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
JUDGE="$DIR/output/judge"
PARALLEL=4
MAX="${1:-999}"
launched=0

for pack in "$JUDGE"/pack-*.json; do
  n=$(basename "$pack" | sed 's/pack-\(.*\)\.json/\1/')
  part="$JUDGE/part-$n.jsonl"
  [ -s "$part" ] && continue
  [ "$launched" -ge "$MAX" ] && break
  while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do sleep 15; done
  echo "[launch] pack-$n"
  codex exec -m gpt-5.5 -c model_reasoning_effort=high --sandbox workspace-write -C "$DIR/../.." - >"$JUDGE/worker-$n.log" 2>&1 <<EOF &
You are a strict Sri Lankan legal auditor. Judge every rule in the file
scripts/case-law-information-extraction/output/judge/pack-$n.json (JSON array).

For EACH rule object: read the judgment text at its "text_path" (repo-relative).
Judge six booleans STRICTLY, leaning false when uncertain:
- statement_correct: the statement accurately reflects what THIS court decided.
- quote_supports: the supporting_quote genuinely supports the statement — false
  if the quote is counsel's submission, a quotation of another case, a lower
  court's reproduced judgment, or merely topically related.
- is_ratio: ratio decidendi/holding, not obiter, not a "semble", not argument.
- qualifications_ok: no material condition/exception the court stated is dropped.
- statute_correct: if statute_section is non-empty it is the provision actually
  construed for this rule; true when empty (nothing claimed).
- usable: overall safe to show a lawyer as this case's rule (essentially all of
  the above).
Write EXACTLY one output file:
scripts/case-law-information-extraction/output/judge/part-$n.jsonl
— one JSON object per line: {"rule_id": "...", "statement_correct": bool,
"quote_supports": bool, "is_ratio": bool, "qualifications_ok": bool,
"statute_correct": bool, "usable": bool, "reason": "one sentence"}.
Every rule_id from the pack must appear exactly once. Do not modify any other
file. Reply with one line: judged N rules, M usable.
EOF
  launched=$((launched+1))
done
wait
echo "[done] launched=$launched"
