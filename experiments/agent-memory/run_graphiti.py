"""Graphiti spike: replay the correction scenario, inspect supersession.

Backend: Kuzu (embedded graph DB, no server) so the run tests Graphiti at
its lightest. LLM + embeddings + reranker: Gemini via GEMINI_API_KEY.

Run:  python run_graphiti.py            (ingest + probe)
      python run_graphiti.py --dump     (also dump every edge with its
                                         valid_at/invalid_at timestamps —
                                         the supersession evidence)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from scenario import EVENTS, MATTER_ID, PROBES

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
LLM_MODEL = os.environ.get("SPIKE_GEMINI_MODEL", "gemini-3.5-flash")
DB_PATH = str(Path(__file__).parent / "graphiti-kuzu-db")


async def main(dump: bool) -> None:
    from graphiti_core import Graphiti
    from graphiti_core.driver.kuzu_driver import KuzuDriver
    from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.llm_client.gemini_client import GeminiClient
    from graphiti_core.nodes import EpisodeType

    try:
        from graphiti_core.cross_encoder.gemini_reranker_client import (
            GeminiRerankerClient,
        )
        reranker = GeminiRerankerClient(config=LLMConfig(api_key=GEMINI_KEY))
    except ImportError:
        reranker = None  # fall back to Graphiti's default reranker

    graphiti = Graphiti(
        graph_driver=KuzuDriver(db=DB_PATH),
        llm_client=GeminiClient(
            config=LLMConfig(api_key=GEMINI_KEY, model=LLM_MODEL)
        ),
        embedder=GeminiEmbedder(
            config=GeminiEmbedderConfig(api_key=GEMINI_KEY)
        ),
        cross_encoder=reranker,
    )
    await graphiti.build_indices_and_constraints()

    print(f"== Ingesting {len(EVENTS)} events into group {MATTER_ID}")
    for name, body, source_desc, ref_time in EVENTS:
        print(f"   + {name}")
        await graphiti.add_episode(
            name=name,
            episode_body=body,
            source=EpisodeType.text,
            source_description=source_desc,
            reference_time=ref_time,
            group_id=MATTER_ID,
        )

    print("\n== Probes (session closed and reopened: fresh searches)")
    for probe_id, question, expected in PROBES:
        results = await graphiti.search(
            query=question, group_ids=[MATTER_ID], num_results=8
        )
        print(f"\n-- {probe_id}: {question}")
        print(f"   expected: {expected}")
        for r in results:
            flag = " [INVALIDATED]" if getattr(r, "invalid_at", None) else ""
            print(f"   fact: {r.fact}{flag}")
            print(f"         valid_at={getattr(r, 'valid_at', None)} "
                  f"invalid_at={getattr(r, 'invalid_at', None)}")

    if dump:
        print("\n== Full edge dump (supersession evidence)")
        rows, _, _ = await graphiti.driver.execute_query(
            "MATCH (a)-[r:RELATES_TO]->(b) "
            "RETURN r.fact AS fact, r.valid_at AS valid_at, "
            "r.invalid_at AS invalid_at, r.created_at AS created_at, "
            "r.expired_at AS expired_at"
        )
        for row in rows:
            print(f"   {row}")

    await graphiti.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", action="store_true")
    args = parser.parse_args()
    if Path(DB_PATH).exists():
        sys.exit(
            f"DB already exists at {DB_PATH} — delete it for a clean replay."
        )
    asyncio.run(main(args.dump))
