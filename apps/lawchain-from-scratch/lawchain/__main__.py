from __future__ import annotations

import argparse
import json

from . import engine
from .compare import run_comparison
from .extraction import select_statute_files


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m lawchain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--force", action="store_true")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=5)

    subparsers.add_parser("evaluate")
    subparsers.add_parser("sources")

    args = parser.parse_args()

    if args.command == "build":
        stats = engine.build(force=args.force)
        print(json.dumps(vars(stats), indent=2))
    elif args.command == "search":
        hits = engine.retrieve(args.query, limit=args.limit)
        print(json.dumps([hit.to_dict() for hit in hits], indent=2))
    elif args.command == "evaluate":
        result = run_comparison()
        print(json.dumps(result, indent=2))
    elif args.command == "sources":
        resolved = select_statute_files()
        print(json.dumps({source_id: str(path) for source_id, path in sorted(resolved.items())}, indent=2))


if __name__ == "__main__":
    main()
