"""Build the BM25 (SQLite FTS5) index over the statute corpus, once.

Indexes the search_text field of every record in data/statute.jsonl. Both run
commands reuse the resulting database, so the index is built once for all
20 questions.

Usage:
    uv run python experiments/koblex-inspired-retrieval/build_index.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import smoke_config as config  # noqa: E402
import corpus_index  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--corpus", type=Path, default=config.CORPUS_PATH)
    parser.add_argument("--db", type=Path, default=config.INDEX_DB_PATH)
    args = parser.parse_args()

    if not args.corpus.is_file():
        print(f"missing corpus {args.corpus}", file=sys.stderr)
        return 1

    count = corpus_index.build_index(args.corpus, args.db)
    print(f"indexed {count} records from {args.corpus.name}")
    print(f"wrote {config.display_path(args.db)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
