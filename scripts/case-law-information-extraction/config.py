"""Shared config for the case-law information-extraction pipeline.

Loads .env, defines model tiers, paths, and the NVIDIA NIM
endpoint. Everything downstream imports from here.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # scripts/case-law-information-extraction/ -> repo root
load_dotenv(dotenv_path=ROOT / ".env")

# --- NVIDIA NIM (OpenAI-compatible) ---
BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# Two tiers: cheap workhorse for the bulk, strong for escalation on hard cases.
MODEL_CHEAP = os.environ.get("DRAFTLY_MODEL_CHEAP", "meta/llama-3.1-8b-instruct")
MODEL_STRONG = os.environ.get("DRAFTLY_MODEL_STRONG", "meta/llama-3.3-70b-instruct")

# --- inputs ---
CASES = ROOT / "data/processed/cases.jsonl"
LINKS = ROOT / "data/processed/case_statute_section_links.csv"
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"
LIBMD = ROOT / "data/legal-sources/library-markdown"  # statute text for section checks

# --- outputs (live in this folder, per project decision) ---
OUT = Path(__file__).resolve().parent / "output"
CACHE = OUT / "cache"
RULES_CSV = OUT / "rules.csv"
META_CSV = OUT / "case_meta.csv"
REJECTS_CSV = OUT / "extract-rejects.csv"
USAGE_JSON = OUT / "usage.json"
RUN_LOG = OUT / "run.log"

# --- extraction knobs ---
CHARS_PER_TOKEN = 4          # rough
WINDOW_HEAD_CHARS = 2400     # ~600 tokens of facts/issue
WINDOW_TAIL_CHARS = 7200     # ~1800 tokens of reasoning/order
WINDOW_MAX_CHARS = 16000     # hard cap on the windowed extract sent to the model.
# Set from audit_window_recall.py: the selected middle is cue paragraphs only, so
# enlarging the budget from 12K->16K lifts at-risk ruling recall 88.0%->94.5% while
# staying ~4K tokens (well inside the 8B's focus range; 30K+ is where it dilutes).
# Full-text mode (--full-text): free-tier credits are per-request, not per-token,
# so on the hard tail we can send the whole judgment for the same 1 credit and let
# the model find the ruling itself. Capped well under the 70B's 128K context.
FULL_TEXT_MAX_CHARS = 110000  # ~30K tokens
DELAY_S = 0.4                # politeness between API calls
MAX_TOKENS_OUT = 700

for d in (OUT, CACHE):
    d.mkdir(parents=True, exist_ok=True)
