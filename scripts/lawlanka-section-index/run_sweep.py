"""Phase 1 -- the LawLanka structural sweep.

Builds the fetch plan, then walks it at one request per second through the cached
fetcher. Roughly 100 requests total.

The fetch list is *not* just the acquisition candidates. 810 of the 1,957
pinpoint case-to-section links fail because the section is missing from our
index, and 525 of those are in statutes we already hold -- 452 in the Civil
Procedure Code alone. Fetching only the new statutes would leave the headline
number untouched. So the plan covers both:

  * held statutes whose section index has gaps (grade `gap-in-index` or
    `statute-not-indexed` in the recovered links);
  * the in-scope acquisition candidates from the relevance gate.

Modes:
    --plan-only   write statute-url-map.csv and the request budget, no network
    --dry-run     log in, fetch one index page, parse it, print what came back
    (default)     the full sweep

Nothing runs until the pre-flight passes: credentials in .env, and the operator
confirming the written permission is on file and the single seat is free.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as C
import fetch as F
import parse_index as P
from relevance_gate import load_registry, normalise, title_tokens

STATUTES_DIR = C.OUT / "statutes"
AZ_MAP = C.OUT / "az-index.csv"
OVERRIDES = Path(__file__).resolve().parent / "act-code-overrides.csv"
LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

# A marginal note is typeset as a multi-line block in the left column. The
# extraction behind the canonical index took one line of it, so `s.4` of the
# Civil Procedure Code reads `is made special` instead of `Where no provision is
# made special directions to be given by Court of Appeal.` A heading opening
# lowercase, or on a connective, is a fragment rather than a heading.
TRUNCATED_HEADING = re.compile(r"^(?:[a-z]|and\b|or\b|to be\b|is\b|of\b|in\b|the\b)")


def looks_truncated(heading: str) -> bool:
    heading = (heading or "").strip()
    return bool(heading) and bool(TRUNCATED_HEADING.match(heading))


# --- the fetch plan ----------------------------------------------------------
def build_plan() -> list[dict]:
    """Every statute whose structure we need, with why we need it."""
    registry = {r["source_id"]: r for r in load_registry()}
    links = pd.read_csv(C.STATUTE_LINKS, dtype=str).fillna("")
    pin = links[links["section"].str.strip() != ""]

    targets: dict[str, dict] = {}

    # 1. held statutes with an incomplete section index
    for grade, why in (("gap-in-index", "sections missing from our index"),
                       ("statute-not-indexed", "no section index at all")):
        sub = pin[pin["grade"] == grade]
        for sid, n in sub["source_id"].value_counts().items():
            if not sid or sid not in registry:
                continue
            t = targets.setdefault(sid, {
                "source_id": sid, "statute_name": registry[sid]["official_title"],
                "held": "yes", "failing_links": 0, "reasons": []})
            t["failing_links"] += int(n)
            t["reasons"].append(f"{n} links: {why}")

    # 2. held statutes already in the canonical index but never swept.
    #    The first pass targeted statutes with *failing links*, which left 35
    #    held statutes untouched -- and they carry most of the remaining
    #    truncated headings, including 33 of 75 in the Registration of Title
    #    Act, the core V0 statute. One request each.
    if C.SECTION_INDEX.exists():
        derived = json.loads(C.SECTION_INDEX.read_text(encoding="utf-8"))
        for sid, entries in derived.items():
            if sid in targets or sid not in registry:
                continue
            # The canonical index carries five placeholder rows that are not
            # enactments at all -- gazette bundles, an institution source pack,
            # a Registrar General's guide -- each with zero sections. A
            # consolidation of statutes has nothing to say about them.
            if registry[sid].get("source_type") not in ("statute", "amendment"):
                continue
            trunc = sum(1 for e in entries if looks_truncated(e.get("heading", "")))
            targets[sid] = {
                "source_id": sid,
                "statute_name": registry[sid]["official_title"],
                "held": "yes",
                "failing_links": 0,
                "reasons": [f"heading repair: {trunc}/{len(entries)} truncated"],
            }

    # 3. in-scope acquisition candidates from the relevance gate
    if not C.SCOPE_DECISIONS.exists():
        raise SystemExit("run relevance_gate.py first -- scope-decisions.csv is missing")
    dec = pd.read_csv(C.SCOPE_DECISIONS, dtype=str).fillna("")
    for _, r in dec[dec["decision"] == "in-scope"].iterrows():
        key = "NEW:" + r["candidate_name"]
        targets[key] = {
            "source_id": "", "statute_name": r["candidate_name"], "held": "no",
            "failing_links": 0,
            "reasons": [f"in-scope acquisition candidate, cited {r['citations']} times"],
        }

    plan = sorted(targets.values(),
                  key=lambda t: (-t["failing_links"], t["statute_name"]))
    for t in plan:
        t["reason"] = "; ".join(t["reasons"])
        del t["reasons"]
    return plan


def load_overrides() -> dict[str, str]:
    """Hand-confirmed statute name -> act code, for titles the automatic match
    cannot settle. Kept in a file so the decision is auditable and survives a
    re-run, rather than being edited into the generated map.

    A row with an empty `act_code` is a confirmed *absence* -- a repealed
    statute, or a provincial one, that a consolidation of in-force national law
    does not carry. Those are returned too, so the sweep stops asking the
    operator to fill in something already established as unavailable.
    """
    if not OVERRIDES.exists():
        return {}
    df = pd.read_csv(OVERRIDES, dtype=str).fillna("")
    return {r["statute_name"].strip().lower(): r["act_code"].strip()
            for _, r in df.iterrows()}


def resolve_act_codes(plan: list[dict], az: list[dict]) -> None:
    """Attach a LawLanka act code to each target by title match.

    Ambiguous or missing matches are left blank with `needs_confirmation=yes`
    rather than guessed -- a wrong act code silently indexes the wrong statute.
    """
    by_sig: dict[frozenset, list[dict]] = {}
    for e in az:
        sig = frozenset(title_tokens(normalise(e["statute_name"])))
        if sig:
            by_sig.setdefault(sig, []).append(e)

    overrides = load_overrides()
    for t in plan:
        key = t["statute_name"].strip().lower()
        if key in overrides:
            ov = overrides[key]
            t["act_code"] = ov
            t["lawlanka_name"] = next(
                (e["statute_name"] for e in az if e["act_code"] == ov), "") if ov else ""
            t["needs_confirmation"] = (
                "confirmed-by-hand" if ov else "confirmed-unavailable")
            continue
        sig = frozenset(title_tokens(normalise(t["statute_name"])))
        hits = by_sig.get(sig, [])
        if not hits:
            # fall back to a unique superset match ("Rent Restriction Act" ->
            # "Rent Restriction Act, No. 29 of 1948")
            supersets = [e for k, v in by_sig.items() if sig and sig < k for e in v]
            hits = supersets if len({e["act_code"] for e in supersets}) == 1 else []
        codes = {e["act_code"] for e in hits if e["act_code"]}
        if len(codes) == 1:
            t["act_code"] = codes.pop()
            t["lawlanka_name"] = hits[0]["statute_name"]
            t["needs_confirmation"] = "no"
        else:
            t["act_code"] = ""
            t["lawlanka_name"] = "; ".join(sorted(
                {e["statute_name"] for e in hits})[:3])
            t["needs_confirmation"] = "yes"


def write_plan(plan: list[dict]) -> None:
    cols = ["source_id", "statute_name", "held", "failing_links", "act_code",
            "lawlanka_name", "needs_confirmation", "reason"]
    with C.STATUTE_MAP.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for t in plan:
            w.writerow({c: t.get(c, "") for c in cols})


def budget(plan: list[dict], *, az_cached: int = 0) -> dict:
    n_short = sum(1 for t in plan if t.get("act_code"))
    return {
        "A-Z consolidation index": len(LETTERS) - az_cached,
        "consShortTitleView per statute": n_short,
        "revisedVersion 1981 + 1956 (by letter)": 2 * C.TOP_STATUTES_REVISED,
        "total": (len(LETTERS) - az_cached) + n_short
                 + 2 * C.TOP_STATUTES_REVISED,
    }


# --- fetch steps -------------------------------------------------------------
def fetch_az(fetcher: F.Fetcher) -> list[dict]:
    """The A-Z consolidation index: statute name -> act code, 1,774 entries."""
    out: list[dict] = []
    for letter in LETTERS:
        url = C.URL_AZ_INDEX.format(letter=letter)
        try:
            page = fetcher.get(url, note=f"az:{letter}")
        except Exception as e:  # noqa: BLE001 - record and continue
            print(f"    {letter}: FAILED {type(e).__name__}: {e}")
            continue
        entries = P.parse_consolidation_index(page.html)
        for e in entries:
            e["letter"] = letter
            e["source_url"] = url
        out.extend(entries)
        print(f"    {letter}: {len(entries)} statutes"
              + ("  (cached)" if page.from_cache else ""))
    seen, dedup = set(), []
    for e in out:
        k = (e["statute_name"].lower(), e["act_code"])
        if k not in seen:
            seen.add(k)
            dedup.append(e)
    if dedup:
        with AZ_MAP.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["letter", "statute_name",
                                              "act_code", "href", "source_url"])
            w.writeheader()
            w.writerows(dedup)
    return dedup


def fetch_statute(fetcher: F.Fetcher, target: dict) -> dict | None:
    """One `consShortTitleView` page -> parsed sections + provenance."""
    url = C.URL_SHORT_TITLE.format(act_code=target["act_code"])
    page = fetcher.get(url, note=f"short-title:{target['statute_name'][:40]}")
    sections = P.parse_section_index(page.html)
    record = {
        **page.provenance,
        "source_id": target.get("source_id", ""),
        "statute_name": target["statute_name"],
        "act_code": target["act_code"],
        "amending_instruments": P.parse_amending_instruments(page.html),
        "sections": sections,
        "summary": P.summarise(sections),
        "status": "unverified",
    }
    STATUTES_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", target["statute_name"].lower()).strip("-")
    name = f"{target['source_id'] or 'NEW'}-{slug}.json"[:120]
    (STATUTES_DIR / name).write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def fetch_revised(fetcher: F.Fetcher, plan: list[dict]) -> None:
    """Temporal anchors for the most-cited statutes (Phase 3 input).

    Both revised-version indexes are paginated by first letter, not by act code,
    so the letters covering the top statutes are fetched rather than one page per
    statute -- same coverage, fewer requests.
    """
    top = [t for t in plan if t.get("act_code")][:C.TOP_STATUTES_REVISED]
    letters = sorted({t["statute_name"].strip()[:1].upper() for t in top
                      if t["statute_name"].strip()[:1].isalpha()})
    print(f"    letters covering the top {len(top)} statutes: {' '.join(letters)}")
    for letter in letters:
        for label, tmpl in (("1981", C.URL_REVISED_1981),
                            ("1956", C.URL_REVISED_1956)):
            url = tmpl.format(letter=letter)
            try:
                page = fetcher.get(url, note=f"revised{label}:{letter}")
                n = len(P.parse_consolidation_index(page.html))
                print(f"    {letter} {label}: {n} entries"
                      + ("  (cached)" if page.from_cache else ""))
            except Exception as e:  # noqa: BLE001
                print(f"    {letter} {label}: FAILED {type(e).__name__}")


def top_amending_years(records: list[dict], n: int = 10) -> list[str]:
    """The years that the amendment markers cite most often."""
    from collections import Counter
    c: Counter[str] = Counter()
    for rec in records:
        for s in rec.get("sections", []):
            for m in s.get("markers", []):
                y = re.search(r"\b(1[89]\d{2}|20\d{2})\b", m["amending_act"])
                if y:
                    c[y.group(1)] += 1
    return [y for y, _ in c.most_common(n)]


def fetch_acts_year(fetcher: F.Fetcher, years: list[str]) -> None:
    for y in years:
        url = C.URL_ACTS_YEAR.format(year=y)
        try:
            page = fetcher.get(url, note=f"acts-year:{y}")
            print(f"    {y}: {len(page.html)} bytes"
                  + ("  (cached)" if page.from_cache else ""))
        except Exception as e:  # noqa: BLE001
            print(f"    {y}: FAILED {type(e).__name__}")


# --- main --------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan-only", action="store_true",
                    help="write the fetch plan and budget, make no requests")
    ap.add_argument("--dry-run", action="store_true",
                    help="log in and fetch a single index page to verify the "
                         "endpoint and the parser against the live site")
    ap.add_argument("--dry-run-act-code", default="",
                    help="act code for the dry run (default: whatever the A-Z "
                         "index resolves for the Civil Procedure Code)")
    ap.add_argument("--i-have-written-permission", action="store_true",
                    help="confirm the written permission is attached to the "
                         "corpus IP review file and the single seat is free")
    args = ap.parse_args()

    print("Phase 1 -- LawLanka structural sweep")
    plan = build_plan()
    held = [t for t in plan if t["held"] == "yes"]
    new = [t for t in plan if t["held"] == "no"]
    fixable = sum(t["failing_links"] for t in plan)
    print(f"  {len(plan)} statutes to index: {len(held)} already held with index "
          f"gaps ({fixable} failing links), {len(new)} acquisition candidates")

    az: list[dict] = []
    if AZ_MAP.exists():
        az = pd.read_csv(AZ_MAP, dtype=str).fillna("").to_dict("records")
        print(f"  A-Z index: {len(az)} statute names cached")
    if az:
        resolve_act_codes(plan, az)
    write_plan(plan)
    print(f"  wrote {C.STATUTE_MAP.relative_to(C.ROOT)}")

    b = budget(plan, az_cached=len(LETTERS) if az else 0)
    print("\n  request budget:")
    for k, v in b.items():
        print(f"    {k:<38} {v:>4}")

    if args.plan_only:
        unresolved = [t for t in plan if t.get("needs_confirmation") == "yes"]
        if az and unresolved:
            print(f"\n  {len(unresolved)} statutes have no unambiguous act code; "
                  f"fill act_code in {C.STATUTE_MAP.name} by hand before the sweep")
        return 0

    # --- gates -----------------------------------------------------------------
    blockers = F.preflight()
    if not args.i_have_written_permission:
        blockers.append(
            "written permission not confirmed -- attach it to the corpus IP "
            "review file, then pass --i-have-written-permission")
    if blockers:
        print("\n  BLOCKED, no requests made:")
        for b_ in blockers:
            print(f"    - {b_}")
        print("\n  statue-plans.md, 'Before running': permission in writing is a "
              "release gate, and the password must be rotated before the "
              "credentials go into .env.")
        return 2

    fetcher = F.Fetcher()
    try:
        if args.dry_run:
            code = args.dry_run_act_code
            if not code:
                cpc = next((t for t in plan if t.get("source_id") == "SRC030"), None)
                code = (cpc or {}).get("act_code", "")
            if not code:
                print("  no act code for the dry run: fetch the A-Z index first, "
                      "or pass --dry-run-act-code")
                return 2
            print(f"\n  dry run: consShortTitleView act_code={code}")
            rec = fetch_statute(fetcher, {"source_id": "SRC030", "act_code": code,
                                          "statute_name": "Civil Procedure Code"})
            s = rec["summary"]
            print(f"    sections            : {s['n_sections']} "
                  f"({s['n_distinct']} distinct, highest s.{s['highest_section']})")
            print(f"    headings present    : {s['with_heading']} "
                  f"(missing {s['headings_missing']})")
            print(f"    amendment markers   : {s['n_amendment_markers']} across "
                  f"{s['sections_with_markers']} sections")
            print(f"    header instruments  : {len(rec['amending_instruments'])}")
            for sec in rec["sections"][:5]:
                print(f"      s.{sec['section']:<5} {sec['heading'][:70]}")
            print(f"\n  {fetcher.summary()}")
            print("  expected from statue-plans.md: 797 sections, 734 distinct, "
                  "up to s.840, headings complete")
            return 0

        print("\n  A-Z consolidation index")
        az = fetch_az(fetcher) or az
        resolve_act_codes(plan, az)
        write_plan(plan)

        ready = [t for t in plan if t.get("act_code")]
        skipped = [t for t in plan if not t.get("act_code")]
        print(f"\n  consShortTitleView: {len(ready)} statutes "
              f"({len(skipped)} skipped, no unambiguous act code)")
        records = []
        done: dict[str, str] = {}
        for t in ready:
            # Two cited names can be one enactment ("rent restriction act" and
            # "rent restriction ordinance"). Index it once and record the second
            # name as an alias rather than storing the sections twice.
            if t["act_code"] in done:
                t["needs_confirmation"] = f"duplicate-of:{done[t['act_code']]}"
                print(f"    {t['statute_name'][:44]:<46} same act as "
                      f"{done[t['act_code']]!r}, skipped")
                continue
            try:
                rec = fetch_statute(fetcher, t)
                records.append(rec)
                done[t["act_code"]] = t["statute_name"]
                s = rec["summary"]
                print(f"    {t['statute_name'][:44]:<46} "
                      f"{s['n_sections']:>4} sections, "
                      f"{s['n_amendment_markers']:>3} markers")
            except Exception as e:  # noqa: BLE001
                print(f"    {t['statute_name'][:44]:<46} FAILED "
                      f"{type(e).__name__}: {e}")
        write_plan(plan)

        # actsYearWise is not fetched. It ignores a year in the query string --
        # every year returned a byte-identical page on 2026-08-07 -- so the 10
        # requests the plan budgeted for it bought nothing. The amending Acts are
        # recovered from the inline markers instead (see actions.csv).
        years = top_amending_years(records)
        print(f"\n  amending years from the markers (no requests): "
              f"{', '.join(years)}")

        print("\n  revised versions (temporal anchors)")
        fetch_revised(fetcher, plan)

        print(f"\n  {fetcher.summary()}")
        if skipped:
            print(f"\n  NOT FETCHED ({len(skipped)}) -- act code unresolved, "
                  f"fill by hand in {C.STATUTE_MAP.name}:")
            for t in skipped:
                print(f"    {t['statute_name']}")
        print("\n  next: python scripts/lawlanka-section-index/build_outputs.py")
        return 0

    except F.SessionConflict as e:
        print(f"\n  STOPPED: {e}")
        return 3
    except F.NotLoggedIn as e:
        print(f"\n  STOPPED: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
