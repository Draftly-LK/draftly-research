"""Shared config for the LawLanka structural section-index sweep.

Executes the plan in `statue-plans.md`: take the *structure* of the statute book
(section numbers, marginal-note headings, inline `[n, Act of Year]` amendment
markers) from LawLanka. The consolidated body prose is LawLanka's editorial
product and is never taken -- official PDFs remain the text authority.

Loads .env for LAWLANKA_USER / LAWLANKA_PASS. Everything downstream imports
from here.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # scripts/lawlanka-section-index/ -> repo root
load_dotenv(dotenv_path=ROOT / ".env")

# --- credentials (never hardcode, never commit) ---
# Read under any of the spellings the .env has used, including the LAWLANKA_USERNMAE
# typo, so a key-name mismatch cannot look like a missing credential.
_USER_KEYS = ("LAWLANKA_USER", "LAWLANKA_USERNAME", "LAWLANKA_USERNMAE",
              "LAWLANKA_EMAIL")
_PASS_KEYS = ("LAWLANKA_PASS", "LAWLANKA_PASSWORD")


def _first_env(keys: tuple[str, ...]) -> str:
    for k in keys:
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return ""


LAWLANKA_USER = _first_env(_USER_KEYS)
LAWLANKA_PASS = _first_env(_PASS_KEYS)

# --- site ---
BASE = os.environ.get("LAWLANKA_BASE", "https://www.lawlanka.com/lal_v3")
LOGIN_URL = f"{BASE}/login"
# The page's checkLogin() rewrites the form action; POST straight to /login.
LOGIN_FIELDS = ("userMaster.emailAddress", "userMaster.password",
                "logInDirect", "userSessionFirstName")

# Endpoint templates, read off the site's own navigation on 2026-08-07 (the
# earlier guesses returned page chrome with no statute list). The consolidation,
# 1981-revised and 1956-revised indexes are all paginated by first letter, not by
# act code. Nothing else in the package hardcodes a URL.
URL_SHORT_TITLE = BASE + "/consShortTitleView?selectedAct={act_code}"
URL_AZ_INDEX = BASE + "/consolidation?menuValue=legislative&selectedLetter={letter}"
URL_ACTS_YEAR = BASE + "/actsYearWise?menuValue=acts&selectedYear={year}"
URL_REVISED_1981 = (BASE + "/revisedVersion1981?menuValue=legislative"
                           "&selectedLetter={letter}")
URL_REVISED_1956 = (BASE + "/revisedVersion1956?menuValue=legislative"
                           "&selectedLetter={letter}")

# Never fetched: returns the entire Act (712 KB) on every call, so 734 requests
# would buy what one index page already returns.
URL_BANNED = ("consSelectedSection",)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT_S = 60
DELAY_S = 1.0        # one request per second, sequential, single session
MAX_RETRIES = 3

# --- inputs ---
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"
TOPICS = ROOT / "data/legal-sources/manifests/topics.csv"
CHECKLIST = ROOT / "data/legal-sources/conveyancing-source-checklist.md"
SECTION_INDEX = ROOT / "data/legal-sources/derived/statute-section-index.json"

HEADNOTE_RUN = ROOT / "evaluation/runs/headnote-recovery-v1"
RULES_RECOVERED = HEADNOTE_RUN / "rules_recovered.csv"
STATUTE_LINKS = HEADNOTE_RUN / "structured/statute_links_v2.csv"

# --- outputs (gitignored: third-party extract, pending IP review) ---
OUT = ROOT / "evaluation/runs/lawlanka-section-index"
CACHE = OUT / "cache"                       # <sha1(url)>.html, one file per URL
SCOPE_DECISIONS = OUT / "scope-decisions.csv"
ALIASES = OUT / "aliases.csv"
FETCH_LOG = OUT / "fetch-log.csv"
SECTIONS_JSONL = OUT / "sections.jsonl"
ACTIONS_CSV = OUT / "actions.csv"
STATUTE_MAP = OUT / "statute-url-map.csv"   # in-scope statute -> LawLanka act code
CROSSCHECK = OUT / "crosscheck-report.md"

RETRIEVED_FROM = "lawlanka"

# --- gate knobs ---
MIN_CITATIONS = 3        # plan: candidates cited three or more times
TOP_STATUTES_REVISED = 8  # revisedVersion1981/1956 pulled for the top N only

for d in (OUT, CACHE):
    d.mkdir(parents=True, exist_ok=True)
