from __future__ import annotations

import argparse
import json

from .embeddings import build_embeddings, embedding_status
from .graph import graph_stats
from .index import build_index
from .models import CaseQuery
from .search import find_similar


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m draftly.case_retrieval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build or refresh the conveyancing case index.")
    build_parser.add_argument("--force", action="store_true", help="Rebuild even if the corpus fingerprint matches.")
    build_parser.add_argument("--with-embeddings", action="store_true", help="Also build the dense embedding cache.")

    search_parser = subparsers.add_parser("search", help="Find similar conveyancing cases for a fact pattern.")
    search_parser.add_argument("query", help="Free-text fact pattern.")
    search_parser.add_argument("--limit", type=int, default=8)

    subparsers.add_parser("status", help="Report index and embedding/graph availability.")

    args = parser.parse_args()
    if args.command == "build":
        stats = build_index(force=args.force)
        print(json.dumps(stats.to_dict(), indent=2))
        if args.with_embeddings:
            count = build_embeddings(force=args.force)
            print(json.dumps({"cases_embedded": count}, indent=2))
    elif args.command == "search":
        result = find_similar(CaseQuery(text=args.query, limit=args.limit))
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    elif args.command == "status":
        print(
            json.dumps(
                {
                    "index": build_index(force=False).to_dict(),
                    "embeddings": embedding_status(),
                    "graph": graph_stats(),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
