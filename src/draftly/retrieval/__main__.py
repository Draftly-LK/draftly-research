from __future__ import annotations

import argparse
import json

from .evaluation import run_evaluation
from .index import build_index
from .models import StatuteQuery
from .search import search


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m draftly.retrieval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build or refresh the statutes-only BM25 index.")
    build_parser.add_argument("--force", action="store_true", help="Rebuild even if the corpus fingerprint matches.")

    search_parser = subparsers.add_parser("search", help="Search statutes and amendments.")
    search_parser.add_argument("query", help="Question or legal lookup query.")
    search_parser.add_argument("--topic", dest="topic_slug", help="Hard filter to a curriculum topic slug.")
    search_parser.add_argument("--kind", choices=["statute", "amendment"], action="append", help="Filter by document type.")
    search_parser.add_argument("--source-id", help="Filter to one source ID, e.g. SRC001.")
    search_parser.add_argument("--limit", type=int, default=8)

    subparsers.add_parser("evaluate", help="Run development retrieval evaluation.")

    args = parser.parse_args()
    if args.command == "build":
        print(json.dumps(build_index(force=args.force).to_dict(), indent=2))
    elif args.command == "search":
        hits = search(
            StatuteQuery(
                text=args.query,
                topic_slug=args.topic_slug,
                kinds=tuple(args.kind) if args.kind else None,
                source_id=args.source_id,
                limit=args.limit,
            )
        )
        print(json.dumps([hit.to_dict(include_text=False) for hit in hits], indent=2))
    elif args.command == "evaluate":
        print(json.dumps(run_evaluation(), indent=2))


if __name__ == "__main__":
    main()

