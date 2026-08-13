# Agent memory systems: evaluation and decision

Date: 20 July 2026. Sources: 22 papers reviewed in full (PDFs at
`D:\projects\Logical\logical-context\papers\papers-pdf`), covering 16 memory
systems, 4 benchmarks, and 2 surveys. Purpose: pick the memory layer for
Draftly's per-matter agent memory (the "agent session layer" that lets the
assistant resume a matter across sessions).

## What we need

Each legal matter needs a persistent agent memory with these properties:

1. Self-hostable open source, Python. Client documents cannot leave our
   infrastructure.
2. Provenance. Every remembered fact traces to its source; nothing is
   silently overwritten.
3. Correction handling. When the lawyer corrects a fact, the old value is
   invalidated but preserved. This is the audit-trail requirement in
   memory form.
4. Two tiers. Verified matter facts (authority, can enter drafts) stay
   separate from agent working notes (suggestions only).
5. Light infrastructure preferred. SQLite-class beats a graph database
   cluster.
6. Per-matter keying and multi-session persistence.

## Decision

No system on the market satisfies all six. The decision is therefore a
spike, not an adoption:

1. Explore **Graphiti** (the open-source engine under Zep) first. It is the
   only system in the literature with native supersede-with-history: each
   fact edge carries four timestamps (valid, invalid, created, expired),
   contradictions set `t_invalid` on the old edge instead of deleting it,
   and every fact links back to its source episode. That is requirements 2
   and 3 already implemented. Cost: a graph database (Neo4j, or FalkorDB as
   the lighter option).
2. Explore **MemMachine** second. Apache-2.0 Python, namespaced by
   org/project/session (maps one-to-one onto per-matter isolation),
   append-only raw episodic store with sentence-to-episode provenance,
   partial SQLite support, and the best benchmark numbers of anything
   reviewed (LoCoMo 0.92, LongMemEval 93%). Its flaw: the derived profile
   tier updates to "most recent state" without an invalidation record, so
   history survives only in the raw episodes.
3. Whichever store wins, copy **REMem's data model** for the fact ledger:
   append-only facts with validity intervals and source links. REMem also
   posted the best refusal/abstention scores of any system tested, which
   matches our grounded-or-silent principle, but it ships no supersession
   semantics and no streaming ingestion, so it is a blueprint, not a
   dependency.

Independent of the store: the two-tier rule stays ours. The verified matter
record remains our own gated schema; the memory system only ever holds the
episodic/notes layer underneath it. Both surveys back this split (separate
memory modules with different write policies; human-gated writes to the
authoritative tier).

Mem0 is dropped from the earlier shortlist. Three independent papers
document its overwrite behaviour as a failure mode (details below).

## Why the benchmarks force this shape

The four benchmark papers converge on one lesson: overwrite-style memory
fails on corrections, and bolt-on memory fails without domain shaping.

- LongMemEval measured ChatGPT at 57.7% on memory tasks vs 91.8% for the
  same model reading the transcript offline, and names the cause: it
  "tended to overwrite crucial information as the chat continues". Its
  knowledge-update category is exactly our lawyer-corrects-a-fact case.
- StreamMemBench tests the correction lifecycle directly (does a user
  correction persist into later tasks?). Append-and-link designs (A-Mem,
  FUR 65.0) beat overwrite designs (Mem0, FUR 41.0, and its paper notes
  Mem0 "stores individual facts and overwrites them when new information
  conflicts"). MemOS applied corrections in-turn but almost never reused
  them later (FUR 4.0): retention is not behaviour.
- MemTrack put GPT-5 plus Mem0 or Zep on realistic multi-platform work
  (Linear, Slack, Git) and found no significant gain over no memory at
  all. Memory added via default APIs, unshaped by the domain, did nothing.
- Time-aware indexing is the documented fix for temporal questions
  (LongMemEval: +6.8 to +11.3% on temporal-subset recall), which supports
  Graphiti's and REMem's timestamp-everything designs.

The surveys agree from the theory side. CoALA ranks unrestricted memory
modification as the riskiest action class an agent has and recommends
separate modules with separate write permissions. The personalization
survey states the field's conflict rule plainly: retrieved facts outrank
agent-inferred content.

## The field, one line each

Systems, roughly strongest fit first:

| System | One-line verdict |
| --- | --- |
| Graphiti/Zep | Only native supersede-with-history (bi-temporal edges, source-linked); needs a graph DB. |
| MemMachine | Best benchmarks, per-project namespacing, append-only episodic ground truth; profile tier overwrites to latest. |
| REMem | Append-only facts with validity intervals and sources, best abstention; no supersession op, batch-only ingestion. |
| Hindsight | Four epistemic networks (world/experience/opinion/observation) with confidence trajectories; hard-fact correction unspecified, Postgres. |
| EMem | Non-lossy append-only event units, 94.4% on knowledge updates; supersession left to query-time reasoning, repo "to be released". |
| MIRIX | Six typed memory tiers on SQLite; updates are LLM overwrites, eight LLM agents per write. |
| MRAgent | Strong agentic graph retrieval with evidence citation; explicitly no update or forgetting mechanism. |
| MAGMA | Immutable temporal backbone, provenance-tagged context; no correction model, heaviest infra (four graphs + vector DB + worker). |
| HiMem | Immutable episodes under mutable notes; note UPDATE/DELETE is silent overwrite, and the paper itself warns against legal use without a human in the loop. |
| HiGMem | Cheap and precise retrieval with turn-level provenance; event fact sheets silently regenerated, weakest temporal scores. |
| O-Mem | Lightest footprint reviewed (~3MB/user); profile updates and cluster-merges destroy lineage. |
| Mem0 | Documented overwrite-on-conflict in three papers; the graph variant soft-invalidates but requires Neo4j. |
| Letta/MemGPT | The original working-vs-archival split; corrections are destructive string replaces decided by the LLM. |
| MemoryOS | Deletes by design (heat-based eviction, fixed-size FIFO queues); disqualifying for audit. |
| Cognee | Corpus-to-knowledge-graph construction, not session memory; updates are clear-and-rebuild. |
| MeMo | Memory stored in model weights: zero provenance, corrections require GPU retraining. |

Not memory systems: LongMemEval, StreamMemBench, MemTrack (benchmarks) and
SuperMemory-VQA (an egocentric video QA dataset, unrelated to the
commercial Supermemory product). CoALA and the personalization survey are
covered above.

## The spike

One fixed scenario replayed against Graphiti and MemMachine, scored on
four questions. Scaffold at `experiments/agent-memory/`.

Scenario (mirrors a real matter session):

1. Create a matter memory space.
2. Ingest three document summaries (deed of transfer, survey plan, prior
   deed) with distinct facts, including land extent "2 roods 15 perches"
   from the survey plan.
3. Write session notes ("chain of title verified back to 1998; extent
   conflict suspected").
4. Correct a fact: the lawyer determines the extent is "1 rood 20 perches"
   per a newer survey.
5. Close the session, reopen, and probe: "what is the extent of the land,
   and where does that answer come from?" plus "what were we working on?"

Scoring:

1. Correction wins: the answer gives the corrected extent, not the
   original.
2. History survives: the original value is still retrievable with its
   source, marked superseded or equivalent.
3. Provenance: the answer can be traced to the correcting event.
4. Cost: integration effort, infra weight, latency, and per-event LLM
   calls.

Exit criteria: if Graphiti passes 1 to 3 and FalkorDB keeps the infra
tolerable, adopt it for the notes/episodic layer. If both fail or the
integration fights us, build the ledger ourselves on SQLite using REMem's
model plus an explicit `superseded_by` column, which is a small schema, not
a research project.

## References

All PDFs in `D:\projects\Logical\logical-context\papers\papers-pdf`. Key
identifiers: Zep/Graphiti arXiv:2501.13956; MemMachine arXiv:2604.04853;
REMem arXiv:2602.13530 (ICLR 2026); Hindsight arXiv:2512.12818; EMem
arXiv:2511.17208; MIRIX arXiv:2507.07957; Mem0 arXiv:2504.19413;
MemGPT arXiv:2310.08560; MemoryOS arXiv:2506.06326; LongMemEval (ICLR
2025); StreamMemBench arXiv:2606.14571; MemTrack arXiv:2510.01353; CoALA
(TMLR 2024); personalization survey (ACM TOIS, May 2026).
