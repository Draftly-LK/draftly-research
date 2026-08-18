"""Shared config for the LLM-based statute section-extraction pipeline.

Mirrors scripts/case-law-information-extraction/config.py's conventions
(NVIDIA NIM via the OpenAI-compatible endpoint, two model tiers, a per-source
cache for resumability) but sized for this task: finding exact verbatim
section boundaries across a whole Act, not extracting one ruling from a
judgment.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # scripts/statute-section-llm-extraction/ -> repo root
load_dotenv(dotenv_path=ROOT / ".env")

# --- NVIDIA NIM (OpenAI-compatible) ---
BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# Finding exact verbatim boundaries across a long, structurally dense legal
# text is a harder task than the case-law pipeline's single-quote extraction,
# so this defaults to a strong tier rather than starting cheap and escalating.
# NOT the shared DRAFTLY_MODEL_STRONG (meta/llama-3.3-70b-instruct, used by
# the case-law pipeline) -- live-tested at the start of this pipeline's build
# and found to reliably hit a 60s+ read timeout on this account/endpoint
# right now (models-list and other chat models responded in under a second;
# this one specifically didn't across repeated tries). nvidia/llama-3.3-nemotron-super-49b-v1
# tested reliably fast (<1s) and is NVIDIA's own instruction-tuned model in
# the same weight class -- used here instead so this pipeline isn't blocked
# on an endpoint issue outside this repo. Override with --model / this env
# var if that changes.
MODEL_STRONG = os.environ.get(
    "DRAFTLY_STATUTE_LLM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1"
)
MODEL_CHEAP = os.environ.get("DRAFTLY_MODEL_CHEAP", "meta/llama-3.1-8b-instruct")
DEFAULT_MODEL = MODEL_STRONG

# --- inputs ---
STATUTES_DIR = ROOT / "data/legal-sources/library/statutes"
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"
SANDBOX = STATUTES_DIR / "sandbox"  # extractor.py helpers reused for slicing/validation

# --- outputs ---
PARSED_DIR = STATUTES_DIR / "parsed"
OUT = Path(__file__).resolve().parent
CACHE = OUT / "cache"
USAGE_JSON = OUT / "usage.json"

# --- chunking knobs ---
CHARS_PER_TOKEN = 4  # rough
CHUNK_CHARS = 40000       # ~10K tokens of source text per LLM call
CHUNK_OVERLAP_CHARS = 2000
MAX_TOKENS_OUT = 4096      # a chunk can hold many {number, heading, anchor} entries
ANCHOR_MIN_WORDS = 6
ANCHOR_MAX_WORDS = 15
DELAY_S = 0.4

for d in (CACHE,):
    d.mkdir(parents=True, exist_ok=True)
