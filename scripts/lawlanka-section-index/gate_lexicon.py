"""Conveyancing relevance lexicon, extracted from notebook 05.

`STRONG_STATUTES`, `LEXICON`, and `gate()` are copied verbatim from
`notebooks/05_courts_judgment_extraction.ipynb` (Stage 2 -- conveyancing gate) so
the same decision rule can be reused outside a notebook. The notebook keeps its
own copy and still runs; this module is the importable form.

Decision rule (unchanged): conveyancing if `strong >= 1` or `lexicon >= 3`.
"""

from __future__ import annotations

import re

STRONG_STATUTES = [
    r"Partition Act", r"Partition Law",
    r"Prevention of Frauds Ordinance",
    r"Registration of Documents Ordinance",
    r"Notaries Ordinance",
    r"Land Development Ordinance",
    r"State Lands? (?:\(Recovery of Possession\) )?Ordinance",
    r"State Lands? Ordinance",
    r"Primary Courts.{0,3} Procedure Act",
    r"Prescription Ordinance",
    r"Trusts Ordinance",
    r"Land Acquisition Act",
    r"Registration of Title Act",
    r"Condominium (?:Property )?Act", r"Apartment Ownership",
]

LEXICON = [
    r"\bdeed\b", r"transfer deed", r"conveyance", r"\bpartition\b", r"prescriptive",
    r"prescription", r"servitude", r"\beasement\b", r"\bmortgage\b", r"notar(?:y|ial)",
    r"immovable propert", r"\bcorpus\b", r"\bco-?owner", r"land kachcheri",
    r"fideicommiss", r"\bdonation\b", r"deed of gift", r"\blease\b",
    r"prescriptive title", r"paper title", r"\bdispossess", r"quiet possession",
    r"\bstate land", r"\blot\s*\d", r"\bplan no", r"\b/[PL]\b", r"\d+/[PL]\b",
]


def gate(text: str, statute_refs: list[str]) -> dict:
    """Deterministic conveyancing verdict for a block of text."""
    joined = " ".join(statute_refs) + " " + text
    strong = sorted({re.search(p, joined, re.I).group(0)
                     for p in STRONG_STATUTES if re.search(p, joined, re.I)})
    lex = sorted({re.search(p, text, re.I).group(0).lower()
                  for p in LEXICON if re.search(p, text, re.I)})
    is_conv = len(strong) >= 1 or len(lex) >= 3
    return {"conveyancing": is_conv,
            "score": len(strong) * 3 + len(lex),
            "strong_statutes": strong, "lexicon_hits": lex}


# --- statute-name relevance, used by relevance_gate.py -----------------------
# The plan's own test: "does it touch land, title, deeds, succession,
# registration, tax on a conveyance, or civil procedure?" -- applied to a bare
# statute NAME, which carries far less text than a judgment, so the >=3 lexicon
# rule above would reject almost everything. These are name-level subject cues.
SUBJECT_CUES = [
    # land / title / conveyance
    r"\bland", r"\btitle", r"\bdeed", r"conveyanc", r"partition", r"prescription",
    r"prescriptive", r"servitude", r"easement", r"mortgage", r"notar",
    r"immovable", r"condominium", r"apartment", r"tenement", r"housing",
    r"\bestate", r"\bproperty", r"premises", r"\bhouse\b", r"\brent",
    r"landlord", r"tenant", r"\blease", r"paddy", r"agrarian", r"crown land",
    r"state land", r"survey", r"\bsurveyor", r"village", r"\bwaste land",
    r"settlement", r"\bacquisition", r"\bredemption", r"fragmentation",
    r"\bfideicommiss", r"\bencumbrance", r"\btenure", r"\bnindagama",
    r"\bsannas", r"\bboundar", r"\balienation", r"\bentail", r"pre-?emption",
    r"\bkachcheri", r"\bfolio", r"\bcaveat", r"\bvesting", r"\bescheat",
    r"quit rent", r"\bencroachment", r"\bgrants?\b", r"\bresumption",
    r"\breform", r"\bceiling", r"\bplanning", r"development authority",
    r"\bmunicipal", r"urban council", r"\bpradeshiya", r"village council",
    r"local authorit", r"\btemporalities", r"\bwa[qk]f", r"\bpartnership",
    r"\bcompan(?:y|ies)", r"powers? of attorney",
    # registration
    r"registration", r"\bregistrar", r"\bregistry",
    # succession / capacity
    r"inheritance", r"succession", r"\bwills?\b", r"testament", r"intestate",
    r"probate", r"administration", r"\btrust", r"\bminor", r"guardian",
    r"matrimonial", r"marriage", r"\bdivorce", r"\bage of majority",
    # tax on a conveyance
    r"\bstamp", r"\bduty\b", r"estate duty", r"\bnotarial fee",
    # civil procedure / courts
    r"civil procedure", r"\bcourts?\b", r"judicature", r"\bcivil law",
    r"\bevidence", r"\bprescription", r"\bfiscal", r"\bpartition",
    r"\bmediation", r"debt conciliation", r"money lending", r"\bpawn",
    r"\binterpretation", r"\bnotaries", r"\bpublic trustee", r"\bappeal",
    r"\bwrit", r"\bexecution", r"\binsolvency", r"\bbankrupt",
]

# Names that are legal *systems* / bodies of custom, not enactments. No download
# will ever satisfy them -- their content lives in case law and textbooks. The
# plan requires a distinct node type rather than treating them as statutes.
LEGAL_SYSTEMS = [
    # "kandyan law" is a body of custom; "Kandyan Marriage and Divorce Act" is an
    # enactment. Match the former exactly rather than any name starting "kandyan".
    r"^kandyan law$", r"^kandyan laws?\b", r"roman[- ]dutch", r"^muslim law$",
    r"^english law$", r"buddhist ecclesiastical", r"^thesawalamai$",
    r"^tesawalamai$", r"^tesavalamai$", r"^common law$", r"^customary law$",
    r"^hindu law$", r"^mohammedan law$", r"^civil law$", r"^canon law$",
    r"^natural law$", r"^roman law$", r"^dutch law$", r"^sinhalese law$",
]


# Subjects that trip a positive cue by coincidence but govern nothing about
# land, title, deeds, succession, or tax on a conveyance. Checked first.
NEGATIVE_CUES = [
    r"intellectual propert", r"industrial propert", r"births? and deaths?",
    r"provident fund", r"income tax", r"\bmotor\b", r"\bopium\b",
    r"\bpetroleum\b", r"\bexcise\b", r"\btobacco\b", r"\bliquor\b",
    r"\bfirearms?\b", r"\bpassports?\b", r"\bimmigration\b", r"\bquarantine\b",
]


def negative_hits(name: str) -> list[str]:
    """Non-conveyancing subjects present in a statute name."""
    return sorted({re.search(p, name, re.I).group(0).lower()
                   for p in NEGATIVE_CUES if re.search(p, name, re.I)})


def is_legal_system(name: str) -> str:
    """Return the matching legal-system pattern, or '' if the name is a statute."""
    low = name.strip().lower()
    for p in LEGAL_SYSTEMS:
        if re.search(p, low, re.I):
            return p
    return ""


def subject_hits(name: str) -> list[str]:
    """Subject cues present in a statute name."""
    return sorted({re.search(p, name, re.I).group(0).lower()
                   for p in SUBJECT_CUES if re.search(p, name, re.I)})
