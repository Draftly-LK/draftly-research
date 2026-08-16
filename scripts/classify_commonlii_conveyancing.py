"""Split the parsed CommonLII judgments into what Draftly needs and what it does not.

Draftly's scope is conveyancing and notarial practice, so most of the 2,162
reported judgments in `data/commonlii/parsed/judgments.csv` are out of scope:
criminal appeals, revenue, labour, election and constitutional cases share the
corpus with the land and deeds cases we actually want.

The gate is deterministic and evidence-first. Two fields carry the signal:

- `catchwords` — the law-report editor's own subject line. When the editor names
  Prevention of Frauds or "prescriptive title", the case is about that, so a
  catchword hit counts for much more than a body-text hit.
- `text` — the judgment body, used as corroboration and as the only signal for
  the 276 cases whose catchwords are empty.

Output is three bands, not two. `required` and `not-required` are the confident
ends; `review` is the middle, held back for a lawyer rather than guessed at.
Every row records which topics fired and which terms matched, so a verdict can
be argued with.

Usage:
    uv run python scripts/classify_commonlii_conveyancing.py
    uv run python scripts/classify_commonlii_conveyancing.py --sample 40
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
SOURCE = ROOT / "data" / "commonlii" / "parsed" / "judgments.csv"
OUT_DIR = ROOT / "evaluation" / "runs" / "conveyancing-gate-v1"

# --------------------------------------------------------------------------
# Signals
# --------------------------------------------------------------------------

# Statutes from data/legal-sources/conveyancing-source-checklist.md. Naming one
# of these is decisive on its own: no criminal or revenue appeal turns on the
# Prevention of Frauds Ordinance.
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

# Subject vocabulary, grouped by the curriculum topic it serves. A single term
# here is weak — "lease" and "title" appear in commercial and criminal cases —
# so these count by distinct topic, not by raw frequency.
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
        # "corpus" is the partition-law word for the land being divided, and it
        # was tried here first. It is unusable: habeas corpus custody judgments
        # call the child "the corpus" throughout, so the term pulled in a run of
        # child-custody appeals. "Partition" carries those cases anyway.
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

# Subject matter Draftly does not draft for. These never veto a strong statute
# hit; they only break ties in the middle band, where a single stray "deed" or
# "purchaser" would otherwise pull a criminal or revenue appeal into scope.
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

# Which topics stand on their own. A judgment whose subject line says
# "Partition" or "Servitude" is a conveyancing judgment and needs no second
# signal. The supporting topics are the ambiguous ones: leases, sales, trusts
# and stamp duty all appear in commercial litigation that Draftly never drafts
# for, so they need corroboration.
CORE_TOPICS = {
    "deeds-and-execution",
    "registration",
    "title-and-prescription",
    "partition-and-co-ownership",
    "gift-and-fideicommissum",
    "servitudes",
    "state-land",
    "condominium",
    "temple-and-religious-property",
    "capacity-and-restrictions",
}

# Statutes whose subject overlaps conveyancing but whose case law is mostly
# something else. Rent control alone accounts for 153 judgments — landlord and
# tenant litigation, not lease drafting — so naming one corroborates, it does
# not decide.
SUPPORTING_STATUTES = {"rent-act", "stamp-duty", "land-acquisition"}

# Scoring weights. Catchwords are the editor's own subject line, so a hit there
# is worth several body-text hits. Body text is counted by occurrence, not by
# presence: a partition judgment says "partition" thirty times, while a criminal
# appeal that happens to mention a deed says it twice.
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

# A body-text topic only fires above this many occurrences. One stray mention is
# noise; four is what a case actually about the topic looks like.
TEXT_TOPIC_MIN = 4

REQUIRED_AT = 8
REVIEW_AT = 3

# Out-of-scope terms are read from the subject line when there is one. Without
# catchwords we read the opening of the judgment instead, because scanning a
# whole judgment for "negligence" or "the accused" flags almost everything.
OPENING_CHARS = 2500


def _hits(patterns: list[re.Pattern[str]], field: str) -> list[str]:
    found = []
    for rx in patterns:
        m = rx.search(field)
        if m:
            found.append(m.group(0).lower().strip())
    return sorted(set(found))


def _count(patterns: list[re.Pattern[str]], field: str) -> int:
    return sum(len(rx.findall(field)) for rx in patterns)


def classify(catchwords: str, text: str) -> dict:
    """Score one judgment and return the verdict with the evidence behind it."""
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

    score = (
        min(W_STRONG_CATCH * len(core_catch), CAP_STRONG_CATCH)
        + W_STRONG_TEXT * min(len(core_text), 2)
        + W_SUPPORTING * min(len(supporting_statutes), 2)
        + W_CORE_TOPIC_CATCH * len(core_topics_catch)
        + W_SUPPORTING_TOPIC_CATCH * len(set(topics_catch) - CORE_TOPICS)
        + min(core_frequency, CAP_CORE_FREQUENCY)
        + min(len(set(topics_text) - CORE_TOPICS), CAP_SUPPORTING_TEXT)
        + max(W_OUT_OF_SCOPE * len(out_of_scope), CAP_OUT_OF_SCOPE)
    )

    # Three signals settle a case on their own, whatever the arithmetic says: a
    # core conveyancing statute in the subject line, a core topic in the subject
    # line, or two core topics running through the body of the judgment.
    if core_catch:
        decisive = "catchword-statute"
    elif core_topics_catch:
        decisive = "catchword-topic"
    elif len(core_topics_text) >= 2:
        decisive = "body-core-topics"
    else:
        decisive = ""

    all_topics = set(topics_catch) | set(topics_text)
    if decisive or score >= REQUIRED_AT:
        verdict = "required"
    elif score >= REVIEW_AT:
        verdict = "review"
    else:
        verdict = "not-required"

    # One topic, found only in the body, with no statute behind it, is a word
    # that repeated — not a subject. "Co-owner" said five times in a partnership
    # dispute scores as well as a partition action here, so cap it at review.
    if verdict == "required" and not decisive and not strong_catch + strong_text \
            and len(all_topics) < 2:
        verdict = "review"

    # A decisive signal still has to clear the review floor. Where the subject
    # line names one conveyancing term and three out-of-scope ones, the term is
    # incidental and the case belongs in front of a lawyer, not in the corpus.
    if verdict == "required" and score < REVIEW_AT:
        verdict = "review"

    return {
        "verdict": verdict,
        "score": score,
        "decisive_signal": decisive or ("score" if verdict != "not-required" else ""),
        "statutes": "; ".join(sorted(strong_catch + strong_text)),
        "topics": "; ".join(sorted(set(topics_catch + topics_text))),
        "catchword_topics": "; ".join(sorted(topics_catch)),
        "core_frequency": core_frequency,
        "out_of_scope_signals": "; ".join(sorted(out_of_scope)),
        "evidence_terms": "; ".join(sorted(set(terms))[:12]),
        "has_catchwords": bool(catchwords.strip()),
    }


REVIEW_SAMPLE_PER_BAND = 40


def write_review_sample(rows: list[dict]) -> Path:
    """Spread a fixed sample across the three bands for lawyer adjudication.

    Nothing here is verified. The sample is what a lawyer needs to say whether
    the gate is keeping the right cases, so it takes an even spread through each
    band rather than the top scorers, which would only show the easy ones.
    """
    picked = []
    for band in ("required", "review", "not-required"):
        band_rows = [r for r in rows if r["verdict"] == band]
        step = max(1, len(band_rows) // REVIEW_SAMPLE_PER_BAND)
        picked.extend(band_rows[::step][:REVIEW_SAMPLE_PER_BAND])

    out = OUT_DIR / "review-sample.csv"
    fields = [
        "case_id", "case_name", "reported_year", "verdict", "score",
        "decisive_signal", "statutes", "topics", "evidence_terms",
        "lawyer_verdict", "lawyer_note",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in picked:
            w.writerow({**r, "lawyer_verdict": "", "lawyer_note": ""})
    return out


def run(sample: int = 0) -> int:
    if not SOURCE.exists():
        print(f"missing source: {SOURCE}", file=sys.stderr)
        return 1

    df = pd.read_csv(SOURCE, dtype=str).fillna("")
    rows = []
    for r in df.itertuples(index=False):
        verdict = classify(r.catchwords, r.text)
        rows.append({
            "case_id": r.case_id,
            "case_name": r.case_name,
            "neutral_citation": r.neutral_citation,
            "report_series": r.report_series,
            "reported_year": r.reported_year,
            "decision_date": r.decision_date,
            "deciding_court": r.deciding_court,
            **verdict,
            "status": "unverified",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "conveyancing_labels.csv"
    fields = list(rows[0].keys())
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    counts = Counter(r["verdict"] for r in rows)
    total = len(rows)
    print(f"judgments classified: {total}  ->  {out.relative_to(ROOT)}")
    for band in ("required", "review", "not-required"):
        n = counts[band]
        print(f"  {band:<13} {n:>5}  ({n / total:.1%})")

    topic_counts = Counter(
        t for r in rows if r["verdict"] == "required"
        for t in r["topics"].split("; ") if t
    )
    print("\ntopics inside the required band:")
    for topic, n in topic_counts.most_common():
        print(f"  {n:>5}  {topic}")

    no_catch = [r for r in rows if not r["has_catchwords"]]
    print(
        f"\ncases with no editor catchwords: {len(no_catch)} "
        f"({sum(r['verdict'] == 'required' for r in no_catch)} required, "
        f"{sum(r['verdict'] == 'review' for r in no_catch)} review)"
    )

    review_out = write_review_sample(rows)
    print(f"\nlawyer review sample: {review_out.relative_to(ROOT)} "
          f"({REVIEW_SAMPLE_PER_BAND} per band, verdict column left blank)")

    if sample:
        for band in ("required", "review", "not-required"):
            print(f"\n--- {band} sample ---")
            picked = [r for r in rows if r["verdict"] == band][:: max(1, counts[band] // sample)]
            for r in picked[:sample]:
                print(
                    f"  [{r['score']:>3}] {r['case_id']:<14} {r['case_name'][:58]:<58} "
                    f"| {r['topics'][:60]}"
                )
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", type=int, default=0, help="print N cases per band")
    raise SystemExit(run(**vars(ap.parse_args())))
