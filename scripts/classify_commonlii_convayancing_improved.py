"""Improved conveyancing gate for the CommonLII judgments (LKCA + LKSC).

This is a drop-in replacement for classify_commonlii_conveyancing.py. It keeps
the original deterministic scorer UNCHANGED and adds two signals that are
present in every row but were previously ignored:

  1. proceeding_type  -- a structured, per-case label from the parser.
       * Court types like election petition, fundamental-rights application,
         contempt, disciplinary rule, prize court cause are decisively OUT of
         scope. Measured: 576 such cases, 401 of which mention conveyancing
         vocab in the body and so could be wrongly pulled in by the old scorer.
       * 'testamentary proceeding' is decisively succession/wills -> IN scope
         (205 cases, 22 of them with no catchwords -- i.e. the weak group).

  2. has_encoding_errors / has_malformed_tags  -- parser damage flags.
       ~24% of cases have encoding errors and ~21% have malformed tags. Damaged
       text makes the regex silently miss real matches. When a verdict at a
       confident end (required / not-required) leaned on possibly-corrupted body
       text -- and was NOT decided by a clean catchword statute or a clean
       proceeding_type -- the case is routed to 'review' instead of trusted.

What is deliberately NOT changed: the statute / topic / out-of-scope vocab, the
weights, the caps, and the three-band thresholds. Everything the lawyer review
was built around still holds; these additions only sharpen the edges.

The run prints ORIGINAL vs IMPROVED band counts side by side so the effect is
visible, and writes the same outputs as before plus a few evidence columns.

Usage:
    uv run python scripts/classify_commonlii_conveyancing_improved.py
    uv run python scripts/classify_commonlii_conveyancing_improved.py --sample 40
    # custom locations (defaults assume the LKCA/ and LKSC/ split):
    uv run python scripts/classify_commonlii_conveyancing_improved.py \
        --sources data/commonlii/parsed/LKCA/judgments.csv \
                  data/commonlii/parsed/LKSC/judgments.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = [
    ROOT / "data" / "commonlii" / "parsed" / "LKCA" / "judgments.csv",
    ROOT / "data" / "commonlii" / "parsed" / "LKSC" / "judgments.csv",
]
OUT_DIR = ROOT / "evaluation" / "runs" / "conveyancing-gate-v2"

# ==========================================================================
# ORIGINAL SIGNALS  (unchanged)
# ==========================================================================

STRONG_STATUTES: dict[str, str] = {
    "prevention-of-frauds": r"Prevention of Frauds",
    "notaries-ordinance": r"Notaries Ordinance|Notaries Act",
    "registration-of-documents": r"Registration of Documents",
    "registration-of-title": r"Registration of Title Act",
    "partition-law": r"Partition (?:Act|Law|Ordinance)",
    "prescription-ordinance": r"Prescription Ordinance",
    "wills-ordinance": r"Wills Ordinance",
    "trusts-ordinance": r"Trusts Ordinance",
    "powers-of-attorney": r"Powers? of Attorney (?:Ordinance|Act)",
    "land-development": r"Land Development Ordinance",
    "state-lands": r"State Lands?(?: \(\w[^)]*\))? Ordinance|Crown Lands? Ordinance",
    "land-acquisition": r"Land Acquisition Act",
    "land-reform": r"Land Reform Law",
    "land-alienation-restrictions": r"Land \(Restrictions on Alienation\)",
    "apartment-ownership": r"Apartment Ownership|Condominium (?:Property )?(?:Act|Law)",
    "stamp-duty": r"Stamp (?:Duty|Ordinance|Act)",
    "matrimonial-rights": r"Matrimonial Rights and Inheritance",
    "kandyan-law": r"Kandyan (?:Law )?(?:Declaration|Succession|Marriage)",
    "thesawalamai": r"Thes+a?wal+amai|Tesawalamai",
    "muslim-succession": r"Muslim Intestate Succession",
    "buddhist-temporalities": r"Buddhist Temporalities",
    "fragmentation-control": r"Control of Fragmentation",
    "entails-and-fideicommissa": r"Entails and Fidei|Fidei-?Commissa",
    "land-settlement": r"Land Settlement Ordinance",
    "reconstructed-folios": r"Reconstructed Folios",
    "surveys": r"Surveyors Ordinance|Survey Act|Land Surveys Ordinance",
    "boundaries": r"Definition of Boundaries",
    "encroachments": r"State Lands Encroachments|Crown Lands Encroachments",
    "rent-act": r"Rent (?:Act|Restriction Act|Restriction Ordinance)",
    "gift-revocation": r"Deeds of Gift on the Ground of Gross Ingratitude",
}

TOPICS: dict[str, list[str]] = {
    "deeds-and-execution": [
        r"\bdeed\b", r"\bdeeds\b", r"conveyanc\w+", r"duly attested",
        r"notarial\w*", r"\bnotary\b", r"\bnotaries\b", r"attest(?:ed|ing|ation)\b",
        r"deed of transfer", r"instrument of transfer",
    ],
    "registration": [
        r"registration of (?:the )?deed", r"registered deed", r"prior registration",
        r"land registry", r"registrar of lands", r"\bfolio\b", r"\bencumbranc\w+",
    ],
    "title-and-prescription": [
        r"prescriptive title", r"paper title", r"adverse possession",
        r"\bprescription\b", r"\bprescribed title\b", r"ut singuli",
        r"undisturbed and uninterrupted possession", r"\bacquisitive prescription\b",
    ],
    "partition-and-co-ownership": [
        r"partition action", r"\bpartition\b", r"co-?owner\w*",
        r"undivided (?:share|interest|half|third)", r"\bpro indiviso\b",
    ],
    "succession-and-wills": [
        r"last will", r"testamentary", r"\bcodicil\b", r"letters of administration",
        r"\bprobate\b", r"\bintestate\b", r"\bexecutrix\b", r"\bexecutor\b",
        r"\bheirs?\b", r"\bdevolution of title\b", r"\bpedigree\b",
    ],
    "gift-and-fideicommissum": [
        r"deed of gift", r"\bdonation\b", r"\bdonor\b", r"\bdonee\b",
        r"fidei[\s-]?commiss\w+", r"\bfiduciary heir\b", r"gross ingratitude",
    ],
    "mortgage-and-security": [
        r"mortgage bond", r"\bmortgagor\b", r"\bmortgagee\b", r"hypothec\w+",
        r"secondary mortgage", r"\bbond no\b", r"\bhypothecary action\b",
    ],
    "lease-and-tenancy": [
        r"indenture of lease", r"\blessor\b", r"\blessee\b", r"\bsub-?lease\b",
        r"\btenancy\b", r"\bquiet enjoyment\b", r"\bground rent\b",
    ],
    "servitudes": [
        r"\bservitude\w*\b", r"\beasement\b", r"right of way", r"way of necessity",
        r"\bjus in re aliena\b",
    ],
    "state-land": [
        r"crown land", r"state land", r"\bpermit holder\b", r"land kachcheri",
        r"\bgrant under the\b.{0,30}Land Development", r"\bswarnabhoomi\b",
        r"\bjayabhoomi\b",
    ],
    "sale-and-agreements": [
        r"agreement to sell", r"contract of sale", r"\bvendor\b", r"\bpurchaser\b",
        r"sale of land", r"\bconditional transfer\b", r"\bright of re-?purchase\b",
    ],
    "trusts": [
        r"constructive trust", r"\btrustee\b", r"resulting trust", r"\bcestui que\b",
    ],
    "powers-of-attorney": [
        r"power of attorney", r"\battorney appointed\b", r"\bproxy holder\b",
    ],
    "condominium": [
        r"\bcondominium\b", r"common elements", r"\bapartment ownership\b",
    ],
    "stamp-duty": [
        r"stamp duty", r"insufficiently stamped", r"\bunstamped\b",
        r"\bstamp(?:ed)? in accordance\b",
    ],
    "temple-and-religious-property": [
        r"\bsangika\b", r"\bpudgalika\b", r"\bviharagam\b", r"\bnindagam\b",
        r"\bdevala\b", r"\btemporalities\b", r"\bdayaka\b",
    ],
    "immovable-property-general": [
        r"immovable propert\w+", r"\blot [A-Z0-9]", r"\bplan no\b",
        r"\bsurvey plan\b", r"\bboundaries of the land\b",
    ],
    "capacity-and-restrictions": [
        r"restriction on alienation", r"\bfragmentation\b", r"\bceiling on\b.{0,20}land",
        r"\bvesting order\b",
    ],
}

OUT_OF_SCOPE: dict[str, list[str]] = {
    "criminal": [
        r"penal code", r"\bindictment\b", r"\bthe accused\b", r"\bconvicted of\b",
        r"code of criminal procedure", r"\bmurder\b", r"\bculpable homicide\b",
        r"\bgrievous hurt\b", r"\bbailable\b",
    ],
    "revenue-and-tax": [
        r"income tax", r"\bcustoms ordinance\b", r"excise ordinance",
        r"\bassessable income\b", r"turnover tax",
    ],
    "labour": [
        r"industrial dispute", r"\bworkmen\b", r"\btermination of employment\b",
        r"wages board", r"\btrade union\b",
    ],
    "public-law": [
        r"fundamental rights", r"article 12[0-9]", r"\bwrit of certiorari\b",
        r"\bmandamus\b", r"election petition", r"\bbribery\b",
    ],
    "commercial-and-tort": [
        r"\bnegligence\b", r"\bdefamation\b", r"bills of exchange",
        r"\binsurance polic\w+", r"winding up", r"\bmotor traffic\b",
    ],
}

COMPILED_STRONG = {k: re.compile(v, re.I) for k, v in STRONG_STATUTES.items()}
COMPILED_TOPICS = {k: [re.compile(p, re.I) for p in v] for k, v in TOPICS.items()}
COMPILED_OUT = {k: [re.compile(p, re.I) for p in v] for k, v in OUT_OF_SCOPE.items()}

CORE_TOPICS = {
    "deeds-and-execution", "registration", "title-and-prescription",
    "partition-and-co-ownership", "gift-and-fideicommissum", "servitudes",
    "state-land", "condominium", "temple-and-religious-property",
    "capacity-and-restrictions",
}
SUPPORTING_STATUTES = {"rent-act", "stamp-duty", "land-acquisition"}

W_STRONG_CATCH = 6
W_STRONG_TEXT = 3
W_SUPPORTING = 2
W_CORE_TOPIC_CATCH = 4
W_SUPPORTING_TOPIC_CATCH = 2
W_OUT_OF_SCOPE = -2

CAP_STRONG_CATCH = 12
CAP_CORE_FREQUENCY = 12
CAP_SUPPORTING_TEXT = 4
CAP_OUT_OF_SCOPE = -6

TEXT_TOPIC_MIN = 4
REQUIRED_AT = 8
REVIEW_AT = 3
OPENING_CHARS = 2500

# ==========================================================================
# NEW SIGNALS
# ==========================================================================

# proceeding_type values that settle scope on their own. These are the parser's
# own structured classification of the case type, so they are cleaner than any
# body-text guess.
PROCEEDING_OUT = {
    "election petition",
    "fundamental-rights application",
    "contempt proceeding",
    "disciplinary rule",
    "prize court cause",
}
PROCEEDING_IN = {
    "testamentary proceeding",  # succession / wills -> conveyancing-adjacent, in scope
}

# A structured out-of-scope proceeding type is heavier than a stray body regex:
# it should sink a case that only looked conveyancing because it said "land" once.
W_PROCEEDING_OUT = -8
W_PROCEEDING_IN = 5


def _hits(patterns: list[re.Pattern[str]], field: str) -> list[str]:
    found = []
    for rx in patterns:
        m = rx.search(field)
        if m:
            found.append(m.group(0).lower().strip())
    return sorted(set(found))


def _count(patterns: list[re.Pattern[str]], field: str) -> int:
    return sum(len(rx.findall(field)) for rx in patterns)


def score_features(catchwords: str, text: str) -> dict:
    """Run the expensive regex work once and return everything the verdict needs.

    This is the ORIGINAL scorer, factored so both the original verdict and the
    improved verdict can be derived from a single pass (the regex over full
    judgment bodies is the slow part).
    """
    strong_catch = [k for k, rx in COMPILED_STRONG.items() if rx.search(catchwords)]
    strong_text = [
        k for k, rx in COMPILED_STRONG.items()
        if k not in strong_catch and rx.search(text)
    ]
    core_catch = [k for k in strong_catch if k not in SUPPORTING_STATUTES]
    core_text = [k for k in strong_text if k not in SUPPORTING_STATUTES]
    supporting_statutes = [
        k for k in strong_catch + strong_text if k in SUPPORTING_STATUTES
    ]

    topics_catch, topics_text, terms = [], [], []
    core_frequency = 0
    for topic, patterns in COMPILED_TOPICS.items():
        in_catch = _hits(patterns, catchwords)
        if in_catch:
            topics_catch.append(topic)
            terms.extend(in_catch)
            continue
        occurrences = _count(patterns, text)
        if occurrences >= TEXT_TOPIC_MIN:
            topics_text.append(topic)
            terms.extend(_hits(patterns, text)[:2])
            if topic in CORE_TOPICS:
                core_frequency += occurrences

    core_topics_catch = [t for t in topics_catch if t in CORE_TOPICS]
    core_topics_text = [t for t in topics_text if t in CORE_TOPICS]
    out_of_scope = [
        k for k, pats in COMPILED_OUT.items()
        if _hits(pats, catchwords or text[:OPENING_CHARS])
    ]

    base = (
        min(W_STRONG_CATCH * len(core_catch), CAP_STRONG_CATCH)
        + W_STRONG_TEXT * min(len(core_text), 2)
        + W_SUPPORTING * min(len(supporting_statutes), 2)
        + W_CORE_TOPIC_CATCH * len(core_topics_catch)
        + W_SUPPORTING_TOPIC_CATCH * len(set(topics_catch) - CORE_TOPICS)
        + min(core_frequency, CAP_CORE_FREQUENCY)
        + min(len(set(topics_text) - CORE_TOPICS), CAP_SUPPORTING_TEXT)
        + max(W_OUT_OF_SCOPE * len(out_of_scope), CAP_OUT_OF_SCOPE)
    )

    if core_catch:
        base_decisive = "catchword-statute"
    elif core_topics_catch:
        base_decisive = "catchword-topic"
    elif len(core_topics_text) >= 2:
        base_decisive = "body-core-topics"
    else:
        base_decisive = ""

    return {
        "base": base,
        "decisive": base_decisive,
        "strong_catch": strong_catch,
        "strong_text": strong_text,
        "core_catch": core_catch,
        "core_topics_catch": core_topics_catch,
        "topics_catch": topics_catch,
        "topics_text": topics_text,
        "out_of_scope": out_of_scope,
        "core_frequency": core_frequency,
        "terms": terms,
    }


def decide(f: dict, proceeding_type: str, damaged: bool, improved: bool) -> tuple[str, str]:
    """Turn features into a verdict. improved=False reproduces the original."""
    score = f["base"]
    decisive = f["decisive"]

    proc_out = improved and proceeding_type in PROCEEDING_OUT
    proc_in = improved and proceeding_type in PROCEEDING_IN
    if proc_out:
        score += W_PROCEEDING_OUT
    if proc_in:
        score += W_PROCEEDING_IN

    # A structured out-of-scope proceeding type cancels a body-only decisive
    # signal: a fundamental-rights case that happens to say "land" is still not
    # conveyancing. It never cancels a clean catchword signal.
    if proc_out and decisive in ("body-core-topics", ""):
        decisive = ""

    all_topics = set(f["topics_catch"]) | set(f["topics_text"])
    if decisive or score >= REQUIRED_AT:
        verdict = "required"
    elif score >= REVIEW_AT:
        verdict = "review"
    else:
        verdict = "not-required"

    if verdict == "required" and not decisive \
            and not (f["strong_catch"] + f["strong_text"]) and len(all_topics) < 2:
        verdict = "review"
    if verdict == "required" and score < REVIEW_AT:
        verdict = "review"

    # Parser damage is recorded as a flag and used to PRIORITISE the lawyer
    # review sample (fragile cases first), not to move bands. ~24% of the corpus
    # is flagged damaged, so rerouting all of it would swamp the review band and
    # make it useless. The one exception is the genuinely dangerous direction:
    # a case that scored right at the not-required threshold on damaged body text
    # may be a real conveyancing case whose matches were corrupted away -- only
    # those borderline damaged cases are lifted to review.
    routed_damaged = False
    if improved and damaged and verdict == "not-required" \
            and REVIEW_AT - 2 <= score < REVIEW_AT \
            and not f["core_catch"] and not f["core_topics_catch"]:
        verdict = "review"
        routed_damaged = True

    reason = decisive or ("score" if verdict != "not-required" else "")
    if proc_out:
        reason = (reason + "+proceeding-out").strip("+")
    if proc_in and not decisive:
        reason = (reason + "+proceeding-in").strip("+")
    if routed_damaged:
        reason = "damaged-routed-to-review"
    return verdict, reason


REVIEW_SAMPLE_PER_BAND = 40


def write_review_sample(rows: list[dict]) -> Path:
    """Even spread across the three bands for lawyer adjudication.

    Prioritises the fragile cases first (no catchwords, parser-damaged text),
    then fills the rest evenly -- so the lawyer's time lands on the calls most
    likely to be wrong.
    """
    picked = []
    for band in ("required", "review", "not-required"):
        band_rows = [r for r in rows if r["verdict"] == band]
        fragile = [r for r in band_rows if not r["has_catchwords"] or r["text_damaged"]]
        rest = [r for r in band_rows if r not in fragile]
        chosen = fragile[:REVIEW_SAMPLE_PER_BAND]
        if len(chosen) < REVIEW_SAMPLE_PER_BAND and rest:
            step = max(1, len(rest) // (REVIEW_SAMPLE_PER_BAND - len(chosen)))
            chosen.extend(rest[::step][:REVIEW_SAMPLE_PER_BAND - len(chosen)])
        picked.extend(chosen)

    out = OUT_DIR / "review-sample.csv"
    fields = [
        "case_id", "case_name", "reported_year", "proceeding_type", "verdict",
        "score", "decisive_signal", "text_damaged", "has_catchwords",
        "statutes", "topics", "evidence_terms", "lawyer_verdict", "lawyer_note",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in picked:
            w.writerow({**r, "lawyer_verdict": "", "lawyer_note": ""})
    return out


def load_sources(sources: list[Path]) -> pd.DataFrame:
    frames = []
    for src in sources:
        if not src.exists():
            print(f"missing source: {src}", file=sys.stderr)
            continue
        print(f"loading {src} ...", file=sys.stderr)
        frames.append(pd.read_csv(src, dtype=str).fillna(""))
    if not frames:
        raise SystemExit("no sources found")
    return pd.concat(frames, ignore_index=True)


def run(sample: int = 0, sources: list[str] | None = None) -> int:
    src_paths = [Path(s) for s in sources] if sources else DEFAULT_SOURCES
    df = load_sources(src_paths)
    total = len(df)
    print(f"classifying {total} judgment(s) ...", file=sys.stderr)

    rows = []
    orig_counts, imp_counts = Counter(), Counter()
    for i, r in enumerate(df.itertuples(index=False)):
        f = score_features(r.catchwords, r.text)
        damaged = (
            getattr(r, "has_encoding_errors", "") == "True"
            or getattr(r, "has_malformed_tags", "") == "True"
        )
        proc = getattr(r, "proceeding_type", "")

        orig_verdict, _ = decide(f, proc, damaged, improved=False)
        verdict, reason = decide(f, proc, damaged, improved=True)
        orig_counts[orig_verdict] += 1
        imp_counts[verdict] += 1

        rows.append({
            "case_id": r.case_id,
            "case_name": r.case_name,
            "neutral_citation": getattr(r, "neutral_citation", ""),
            "report_series": getattr(r, "report_series", ""),
            "reported_year": getattr(r, "reported_year", ""),
            "decision_date": getattr(r, "decision_date", ""),
            "deciding_court": getattr(r, "deciding_court", ""),
            "proceeding_type": proc,
            "verdict": verdict,
            "original_verdict": orig_verdict,
            "changed": "yes" if verdict != orig_verdict else "",
            "score": f["base"],
            "decisive_signal": reason,
            "text_damaged": damaged,
            "statutes": "; ".join(sorted(f["strong_catch"] + f["strong_text"])),
            "topics": "; ".join(sorted(set(f["topics_catch"] + f["topics_text"]))),
            "core_frequency": f["core_frequency"],
            "out_of_scope_signals": "; ".join(sorted(f["out_of_scope"])),
            "evidence_terms": "; ".join(sorted(set(f["terms"]))[:12]),
            "has_catchwords": bool(r.catchwords.strip()),
            "status": "unverified",
        })

        if (i + 1) % 500 == 0 or (i + 1) == total:
            pct = (i + 1) / total
            print(f"  {i+1}/{total} ({pct:.0%})", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "conveyancing_labels.csv"
    fields = list(rows[0].keys())
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # ---- ORIGINAL vs IMPROVED comparison -------------------------------------
    print(f"\njudgments classified: {total}  ->  {out}")
    print(f"\n{'band':<14}{'ORIGINAL':>20}{'IMPROVED':>20}")
    for band in ("required", "review", "not-required"):
        o, n = orig_counts[band], imp_counts[band]
        print(f"  {band:<12}{o:>7} ({o/total:>5.1%}){n:>10} ({n/total:>5.1%})")

    changed = sum(1 for r in rows if r["changed"])
    print(f"\ncases whose verdict changed: {changed} ({changed/total:.1%})")
    # break the changes down by direction
    moves = Counter((r["original_verdict"], r["verdict"]) for r in rows if r["changed"])
    print("what moved where (original -> improved):")
    for (a, b), n in moves.most_common():
        print(f"  {a:<13} -> {b:<13} {n:>5}")

    damaged_total = sum(1 for r in rows if r["text_damaged"])
    print(f"\nparser-damaged cases: {damaged_total} ({damaged_total/total:.1%})")

    topic_counts = Counter(
        t for r in rows if r["verdict"] == "required"
        for t in r["topics"].split("; ") if t
    )
    print("\ntopics inside the improved required band:")
    for topic, n in topic_counts.most_common():
        print(f"  {n:>5}  {topic}")

    no_catch = [r for r in rows if not r["has_catchwords"]]
    print(
        f"\ncases with no editor catchwords: {len(no_catch)} "
        f"({sum(r['verdict'] == 'required' for r in no_catch)} required, "
        f"{sum(r['verdict'] == 'review' for r in no_catch)} review)"
    )

    review_out = write_review_sample(rows)
    print(f"\nlawyer review sample: {review_out} "
          f"({REVIEW_SAMPLE_PER_BAND} per band, fragile cases first, "
          f"verdict column left blank)")

    if sample:
        for band in ("required", "review", "not-required"):
            print(f"\n--- {band} sample ---")
            picked = [r for r in rows if r["verdict"] == band]
            step = max(1, len(picked) // sample)
            for r in picked[::step][:sample]:
                print(
                    f"  [{r['score']:>3}] {r['case_id']:<14} "
                    f"{r['case_name'][:50]:<50} | {r['decisive_signal']:<24} "
                    f"| {r['topics'][:40]}"
                )
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", type=int, default=0, help="print N cases per band")
    ap.add_argument("--sources", nargs="+", default=None,
                    help="one or more judgments.csv paths (default: LKCA + LKSC)")
    raise SystemExit(run(**vars(ap.parse_args())))