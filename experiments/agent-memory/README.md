# Agent-memory spike

Tests candidate memory systems for the per-matter agent session layer.
Background and the full paper review: `docs/memory-system-evaluation.md`.

One fixed scenario (`scenario.py`) is replayed against each system: ingest
three document summaries and a session note, then a lawyer corrects the
land extent. Four probes check whether the correction wins, whether the
old value survives with history, whether provenance is traceable, and what
the run costs.

## Candidates

### Graphiti (`run_graphiti.py`)

Uses the embedded Kuzu backend (no server) and Gemini for LLM, embeddings,
and reranking, so the only external dependency is `GEMINI_API_KEY` in the
repo `.env`.

```text
.venv\Scripts\pip install "graphiti-core[kuzu,google-genai]" python-dotenv
cd experiments\agent-memory
..\..\.venv\Scripts\python run_graphiti.py --dump
```

Delete `graphiti-kuzu-db/` between runs; the script refuses to reuse a
populated store so every replay is clean. The `--dump` output lists every
fact edge with `valid_at` / `invalid_at` / `expired_at`: pass criterion P2
is the old 2R 15P extent edge present with `invalid_at` set to the
correction time.

If Kuzu turns out unsupported by the installed graphiti-core version,
fall back to FalkorDB: start Docker Desktop, then
`docker run -p 6379:6379 falkordb/falkordb` and swap `KuzuDriver` for
`FalkorDriver` in the runner.

### MemMachine (`run_memmachine.py`)

MemMachine is client-server (FastAPI + Postgres/pgvector or SQLite, plus
Neo4j for the profile graph in full deployments). The runner targets the
lightest documented configuration. If the install demands Postgres or
Neo4j, record that under "infra weight" in the results rather than
fighting it: infra weight is one of the scored criteria.

## Scoring

| Criterion | Pass |
| --- | --- |
| P1 correction wins | Probe answers 1R 20P, not 2R 15P |
| P2 history survives | 2R 15P retrievable, marked invalid/superseded, with source |
| P3 provenance | Correction traceable to the lawyer event of 16 July |
| P4 resume | Last session's note and next step come back |
| Cost | Install pain, infra processes, latency, LLM calls per event |

Record results in `results.md`. Exit criteria are in the decision doc: if
Graphiti passes P1-P3 on embedded infra, adopt it for the episodic/notes
layer; if both candidates fail, build the ledger on SQLite using REMem's
append-only model plus an explicit `superseded_by` column.

Data note: scenario names, deeds, and plan numbers are invented. Do not
replace them with real matter data (`data/raw/` stays out of experiments).
