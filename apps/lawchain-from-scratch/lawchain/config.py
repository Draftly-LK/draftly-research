from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

EXPECTED_STATUTE_COUNT = 24

# Escape hatch: source_id -> exact JSON filename, for a folder whose
# candidate files can't be disambiguated by the registry/edition-kind rules
# in extraction.select_statute_files(). Empty today; documented in the plan
# as the last resort before extraction raises.
STATUTE_FILE_OVERRIDES: dict[str, str] = {}

DENSE_EMBEDDING_MODEL = os.getenv("LAWCHAIN_EMBEDDING_MODEL", "intfloat/e5-base-v2")
GEMINI_MODEL = os.getenv("LAWCHAIN_GEMINI_MODEL", "gemini-3.5-flash")

DISABLE_DENSE = os.getenv("LAWCHAIN_DISABLE_DENSE") == "1"
DISABLE_GRAPH = os.getenv("LAWCHAIN_DISABLE_GRAPH") == "1"

MAX_EXPANSION_ROUNDS = 2
SUFFICIENCY_SCORE_THRESHOLD = 0.02
SUFFICIENCY_MIN_HITS = 5

RRF_K = 60
LLM_JUDGE_CANDIDATE_POOL = 20

PAGERANK_ALPHA = 0.5
GRAPH_TOP_N = 10

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
