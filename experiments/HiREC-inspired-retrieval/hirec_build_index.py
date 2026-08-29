"""Build the BM25 (SQLite FTS5) index over the statute corpus, once.

Indexes the search_text field of every record in the shared statute corpus, plus
the act_id / section_id / ordinal columns and the act table that the hierarchy
needs. Every run command reuses the resulting database.

The corpus itself is read-only here and is shared with the koblex experiment;
this writes only into this experiment's own data directory.

Usage:
    uv run python experiments/HiREC-inspired-retrieval/hirec_build_index.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hirec_config as config  # noqa: E402
import hirec_index  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument("--corpus", type=Path, default=config.CORPUS_PATH)
    parser.add_argument("--db", type=Path, default=config.INDEX_DB_PATH)
    args = parser.parse_args()

    if not args.corpus.is_file():
        print(f"missing corpus {args.corpus}", file=sys.stderr)
        return 1

    count = hirec_index.build_index(args.corpus, args.db)

    with hirec_index.Bm25Index(args.db) as index:
        acts = index.acts()
    print(f"indexed {count} records from {args.corpus.name}")
    print(f"acts    : {len(acts)}")
    print(f"sections: {sum(a['section_count'] for a in acts)}")
    print(f"wrote {config.display_path(args.db)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
