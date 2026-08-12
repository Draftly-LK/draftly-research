"""Phase 0 -- the relevance gate over statute names cited in the case corpus.

`statue-plans.md` requires a per-candidate decision, written to a CSV so the
scope is auditable rather than remembered:

    is it a statute at all?              -> no  : legal system, separate node type
    is it a fragment of a held statute?  -> yes : aliases.csv, do not acquire
    does it touch land, title, deeds,
    succession, registration, tax on a
    conveyance, or civil procedure?      -> yes : IN SCOPE
    otherwise                            -> OUT, record the reason

Inputs: the 3,521 recovered headnotes (`rules_recovered.csv`) and the resolved /
unresolved statute links (`structured/statute_links_v2.csv`).
Outputs: `scope-decisions.csv`, `aliases.csv`.

Deterministic: no network, no model. Re-running produces identical CSVs.

Usage:
    python scripts/lawlanka-section-index/relevance_gate.py
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as C
import gate_lexicon as G

# --- statute-name extraction -------------------------------------------------
# A statute name is a run of Capitalised/quoted words ending in one of the
# enactment nouns. Headnotes are OCR'd, so tolerate stray punctuation inside the
# run but stop at sentence boundaries.
ENACTMENT_NOUN = r"(?:Act|Ordinance|Law|Code|Statute|Proclamation|Regulations?)"
NAME_WORD = r"(?:[A-Z][A-Za-z'\-]*|of|the|and|for|to|in|on|No\.|\([A-Za-z' \-]+\))"
STATUTE_NAME = re.compile(
    r"\b(" + NAME_WORD + r"(?:\s+" + NAME_WORD + r"){0,7}?\s+" + ENACTMENT_NOUN + r")\b"
)

# Words that cannot begin a real statute title -- their presence at the head means
# the regex started mid-name (the plan's "regex artifacts" bucket).
ARTIFACT_HEADS = {
    "amendment", "special", "general", "further", "certain", "other", "said",
    "aforesaid", "new", "old", "principal", "relevant", "above", "same",
    "consolidated", "amending", "repealed", "present", "former", "later",
    "and", "or", "the", "of", "to", "in", "on", "for", "by", "under", "this",
    "that", "such", "any", "no", "not", "as", "at", "an", "a", "provisions",
}

# Bare enactment nouns with no distinguishing name.
BARE = {"act", "ordinance", "law", "code", "statute", "acts", "ordinances",
        "laws", "codes", "regulations", "regulation", "proclamation"}

STOP_TITLE_WORDS = {"of", "the", "and", "for", "to", "in", "on", "no", "act",
                    "ordinance", "law", "code", "statute", "regulations",
                    "regulation", "proclamation", "amendment", "consolidated"}

# Leading tokens that are never part of a statute title. Single and double
# letters come from headnote catchword numbering ("(p) Kandyan law", "l.").
JUNK_LEAD = {"of", "the", "and", "in", "on", "to", "for", "under", "by", "a",
             "an", "said", "this", "that", "such", "any", "per", "vide", "see",
             "cf", "re", "at", "as", "with", "from", "into", "upon",
             # structural pointers into a statute -- never the start of a title
             "schedule", "schedules", "part", "chapter", "appendix", "table",
             "proviso", "paragraph", "clause", "item", "rule", "rules"}

# Headnote catchwords name an abstraction and then the statute it is asked about
# ("Applicability of Rent Act", "Validity - Civil Procedure Code"). The
# abstraction is the topic, not part of the title, so it is trimmed when it is
# followed by a linking preposition.
CATCHWORD_LEAD = {
    "validity", "invalidity", "admissibility", "inadmissibility",
    "applicability", "permissibility", "concurrence", "construction",
    "effect", "scope", "meaning", "proof", "breach", "waiver", "want",
    "absence", "failure", "compliance", "non-compliance", "operation",
    "presumption", "burden", "sufficiency", "necessity", "nature", "extent",
}

# Ordinary legal prose that happens to end in an enactment noun. These are not
# statute names and must not become acquisition candidates.
PROSE_NAMES = [
    r"^(?:court|courts|rule|rules|question|questions|point|points|matter|matters"
    r"|error|errors|operation|force|principle|principles|body|process|breach"
    r"|choice|conflict|maxim|maxims|provision|provisions|letter|spirit|eye"
    r"|majesty|state|province|due course|course)\s+of\s+(?:the\s+)?law$",
    r"^(?:ceylon|sri lanka|sri lankan|local|general|written|unwritten|personal"
    r"|substantive|procedural|adjective|statute|statutory|case|positive"
    r"|municipal|international|domestic|foreign|ordinary|land|property|criminal"
    r"|penal|public|private|modern|ancient|existing|applicable|governing"
    r"|prevailing|colonial|indian|our|his|her|their|its|the)\s+law$",
    r"^law$", r"^laws$", r"^act$", r"^acts$", r"^code$", r"^ordinance$",
]

# Spelling variants seen across 150 years of reports, folded so the registry
# match can find them. Left side is what the reports write.
SPELLING = [
    (r"\bthesa+valamai\b", "tesawalamai"), (r"\bthesawalamai\b", "tesawalamai"),
    (r"\btesavalamai\b", "tesawalamai"), (r"\bthesawalame\b", "tesawalamai"),
    (r"\bkandian\b", "kandyan"), (r"\bkandyian\b", "kandyan"),
    (r"\bmahomedan\b", "muslim"), (r"\bmohammedan\b", "muslim"),
    (r"\bmuhammadan\b", "muslim"), (r"\bmoorish\b", "muslim"),
    (r"\bcrown lands?\b", "state lands"),
    # keep the compound intact so the dash trim below does not reduce
    # "roman-dutch law" to "dutch law"
    (r"\broman[- ]dutch\b", "roman dutch"),
]


def normalise(name: str) -> str:
    """Lowercase, collapse whitespace, drop trailing punctuation, fold spelling."""
    n = re.sub(r"\s+", " ", name).strip()
    n = n.replace("’", "'")
    # OCR'd reports mix hyphen, en dash, em dash and minus as the catchword
    # separator. Fold them all to '-' so one rule can strip the prefix.
    n = re.sub(r"[‐-―−]", "-", n)
    n = n.strip(" .,;:-").lower()
    for pat, rep in SPELLING:
        n = re.sub(pat, rep, n)
    return n


def extract_names(text: str) -> list[str]:
    if not text:
        return []
    return [normalise(m.group(1)) for m in STATUTE_NAME.finditer(text)]


def is_prose(name: str) -> bool:
    return any(re.match(p, name) for p in PROSE_NAMES)


# --- canonicalisation --------------------------------------------------------
# Headnote catchwords glue the topic to the statute name with a dash
# ("Validity-Civil Procedure Code, s. 247") and the prose glues a preposition to
# the front ("of the Courts Ordinance"). Both produce a distinct spelling of a
# name we already have, splitting its citation count. Fold them together before
# deciding scope -- otherwise the same statute is counted three times and each
# copy falls below the >=3 threshold.
def _trim_lead(name: str) -> str:
    toks = name.split()
    if (len(toks) > 2 and toks[0] in CATCHWORD_LEAD
            and toks[1] in {"of", "under", "in", "to"}):
        toks = toks[1:]
    i = 0
    while i < len(toks) - 1 and (toks[i] in JUNK_LEAD or len(toks[i]) <= 2):
        i += 1
    return " ".join(toks[i:])


def _trim_hyphen(name: str, known: set[str]) -> str:
    """Drop a catchword prefix glued on with a dash, but only if the tail is a
    name we have independently seen -- so 'roman-dutch law' is left alone."""
    toks = name.split()
    if "-" not in toks[0]:
        return name
    tail_head = toks[0].rsplit("-", 1)[1]
    if not tail_head:
        return name
    tail = " ".join([tail_head] + toks[1:])
    return tail if tail in known else name


def _reduce(name: str, known: set[str]) -> str:
    """Strip prefix junk until nothing more comes off.

    Both trims have to run repeatedly: 'in Court-Civil Procedure Code' needs the
    preposition gone before the dashed catchword is even at the front, and the
    intermediate form is not itself a spelling we saw.
    """
    cur, prev = name, ""
    for _ in range(6):
        if cur == prev:
            break
        prev = cur
        cur = _trim_hyphen(cur, known)
        trimmed = _trim_lead(cur)
        if trimmed != cur and len(trimmed.split()) >= 2 and trimmed not in BARE:
            cur = trimmed
        elif trimmed != cur and trimmed in known:
            cur = trimmed
    return cur


def canonicalise(counts: Counter[str]) -> dict[str, str]:
    """Map every extracted spelling to the name it should be counted under."""
    known = set(counts)
    direct = {name: _reduce(name, known) for name in known}
    # resolve chains to a fixed point
    out: dict[str, str] = {}
    for name in known:
        seen, cur = {name}, direct[name]
        while cur in direct and direct[cur] != cur and direct[cur] not in seen:
            seen.add(cur)
            cur = direct[cur]
        out[name] = cur

    # Fold spellings that differ only in plural, apostrophe or word order
    # ("court ordinance" / "courts ordinance"; "business names registration
    # ordinance" / "registration of business names ordinance"). The enactment
    # noun stays in the signature -- "partition act" and "partition ordinance"
    # are different instruments in the same lineage, not one name.
    groups: defaultdict[tuple, list[str]] = defaultdict(list)
    for base in set(out.values()):
        sig = (frozenset(title_tokens(base)), _fold(base.split()[-1]))
        groups[sig].append(base)
    elect: dict[str, str] = {}
    for sig, members in groups.items():
        if len(members) == 1:
            continue
        # the most-cited spelling wins; ties go to the longest (most complete)
        winner = max(members, key=lambda m: (
            sum(counts[r] for r in known if out[r] == m), len(m)))
        for m in members:
            elect[m] = winner
    if elect:
        out = {raw: elect.get(base, base) for raw, base in out.items()}
    return out


def is_artifact(name: str) -> str:
    """Return a reason if the name is a regex artifact, else ''."""
    words = name.split()
    if not words:
        return "empty"
    if name in BARE or len(words) < 2:
        return "bare enactment noun, no distinguishing name"
    if words[0] in ARTIFACT_HEADS:
        return f"begins with '{words[0]}' -- regex started mid-name"
    if ")" in name and "(" not in name:
        return "unmatched ')' -- truncated parenthetical"
    return ""


# --- registry / alias matching ----------------------------------------------
def _fold(word: str) -> str:
    """Fold a singular/plural pair to one key ('trusts' == 'trust')."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def title_tokens(title: str) -> set[str]:
    """Distinguishing words of a title, plural-folded, stop-words removed."""
    t = title.lower()
    for pat, rep in SPELLING:
        t = re.sub(pat, rep, t)
    return {_fold(w.replace("'", "")) for w in re.findall(r"[a-z']+", t)
            if w not in STOP_TITLE_WORDS} - {""}


def load_registry() -> list[dict]:
    reg = pd.read_csv(C.REGISTRY, dtype=str, encoding="utf-8-sig").fillna("")
    reg.columns = [c.strip().strip('"') for c in reg.columns]
    rows = []
    for _, r in reg.iterrows():
        title = r["official_title"].strip()
        rows.append({
            "source_id": r["source_id"].strip(),
            "official_title": title,
            "norm": normalise(title),
            "tokens": title_tokens(title),
            "source_type": r.get("source_type", "").strip(),
        })
    return rows


def match_registry(name: str, registry: list[dict]) -> tuple[str, str]:
    """Match a cited name to a held statute.

    Returns (source_id, match_kind) where match_kind is 'exact', 'fragment', or ''.
    A fragment is a name whose distinguishing words are all present in exactly one
    registry title -- e.g. 'frauds ordinance' -> Prevention of Frauds Ordinance.
    """
    norm = name
    cand_tokens = title_tokens(name)

    # exact / near-exact: same distinguishing token set
    exact = [r for r in registry if r["norm"] == norm or r["tokens"] == cand_tokens]
    if exact:
        return exact[0]["source_id"], "exact"
    if not cand_tokens:
        return "", ""

    # fragment: every distinguishing word of the candidate appears in the title.
    # The enactment noun need not agree -- the reports routinely write "Partition
    # Ordinance" for the Partition Law and "Mortgage Ordinance" for the Mortgage
    # Act, so requiring the noun to match would send real fragments to
    # acquisition as if they were statutes we do not hold.
    subs = [r for r in registry if cand_tokens < r["tokens"]]
    if len(subs) == 1:
        return subs[0]["source_id"], "fragment"
    if len(subs) > 1:
        # Prefer the principal statute over its own amendments, then the shortest
        # title (least assumed context). A citation to "frauds ordinance" means
        # the Prevention of Frauds Ordinance, not one of its amending Acts.
        subs.sort(key=lambda r: (r["source_type"] != "statute", len(r["tokens"])))
        principal = [r for r in subs if r["source_type"] == "statute"]
        if len(principal) == 1:
            return principal[0]["source_id"], "fragment"
        pool = principal or subs
        if len(pool) == 1 or len(pool[0]["tokens"]) < len(pool[1]["tokens"]):
            return pool[0]["source_id"], "fragment"
        return "", "ambiguous"

    # Near miss: shares most of a held title's distinguishing words but is not a
    # clean subset -- an OCR variant ("matrimonial bights") or a fuller official
    # title than the registry records ("... Succession and Wakfs Ordinance").
    # Never auto-acquired; a human decides whether it is an alias.
    for r in registry:
        shared = cand_tokens & r["tokens"]
        if len(shared) >= 2 and len(shared) >= len(r["tokens"]) - 1:
            return r["source_id"], "near-miss"
    return "", ""


# --- topic keywords ---------------------------------------------------------
def load_topic_keywords() -> list[str]:
    t = pd.read_csv(C.TOPICS, dtype=str).fillna("")
    kws: set[str] = set()
    for cell in t["keywords"]:
        for k in cell.split(";"):
            k = k.strip().lower()
            if len(k) > 3:
                kws.add(k)
    return sorted(kws)


def topic_hits(name: str, keywords: list[str]) -> list[str]:
    low = name.lower()
    return [k for k in keywords if k in low]


# --- main -------------------------------------------------------------------
def main() -> int:
    print("Phase 0 -- relevance gate")
    print(f"  registry : {C.REGISTRY.relative_to(C.ROOT)}")
    print(f"  headnotes: {C.RULES_RECOVERED.relative_to(C.ROOT)}")

    for p in (C.REGISTRY, C.TOPICS, C.RULES_RECOVERED, C.STATUTE_LINKS):
        if not p.exists():
            print(f"MISSING INPUT: {p}")
            return 1

    registry = load_registry()
    keywords = load_topic_keywords()
    print(f"  {len(registry)} registry rows, {len(keywords)} topic keywords")

    # 1. candidate extraction
    rules = pd.read_csv(C.RULES_RECOVERED, dtype=str).fillna("")
    counts: Counter[str] = Counter()
    cases: defaultdict[str, set[str]] = defaultdict(set)
    for _, r in rules.iterrows():
        blob = f"{r['catchwords']} {r['rule']}"
        for nm in extract_names(blob):
            counts[nm] += 1
            cases[nm].add(r["case_id"])

    links = pd.read_csv(C.STATUTE_LINKS, dtype=str).fillna("")
    for _, r in links.iterrows():
        nm = normalise(r["statute"])
        if nm and not r["source_id"].strip():
            counts[nm] += 1
            cases[nm].add(r["case_id"])

    print(f"  {len(counts)} raw spellings extracted "
          f"({sum(counts.values())} mentions)")

    # 1b. fold prose-glued and catchword-glued spellings into one name
    canon = canonicalise(counts)
    counts_raw = dict(counts)
    folded: Counter[str] = Counter()
    fcases: defaultdict[str, set[str]] = defaultdict(set)
    variants: defaultdict[str, set[str]] = defaultdict(set)
    for raw, n in counts.items():
        key = canon[raw]
        folded[key] += n
        fcases[key] |= cases[raw]
        if raw != key:
            variants[key].add(raw)
    counts, cases = folded, fcases
    print(f"  {len(counts)} distinct names after folding variants")

    candidates = [(n, c) for n, c in counts.items() if c >= C.MIN_CITATIONS]
    candidates.sort(key=lambda t: (-t[1], t[0]))
    print(f"  {len(candidates)} cited >= {C.MIN_CITATIONS} times -> the gate set")

    # 2. classify
    decisions, aliases = [], []
    tally: Counter[str] = Counter()
    for name, n in candidates:
        sys_pat = G.is_legal_system(name)
        art = is_artifact(name)
        sid, kind = match_registry(name, registry)
        subj = G.subject_hits(name)
        neg = G.negative_hits(name)
        tops = topic_hits(name, keywords)

        if is_prose(name):
            decision, reason = "artifact", (
                "ordinary legal prose ending in an enactment noun, not a title")
        elif sys_pat:
            decision, reason = "legal-system", (
                "body of custom / legal system, not an enactment -- needs its own "
                "graph node type; no acquisition possible")
        elif kind in ("exact", "fragment"):
            if kind == "exact":
                decision, reason = "already-held", f"in catalogue as {sid}"
            else:
                decision, reason = "alias", (
                    f"name fragment of {sid}; resolve via aliases.csv")
            aliases.append({"alias": name, "source_id": sid,
                            "alias_type": "short-title" if kind == "exact" else "fragment",
                            "citations": n})
            # Also map the spellings that folded into this name, so a lookup of
            # the raw citation string as the reports write it resolves too.
            for v in sorted(variants[name]):
                aliases.append({"alias": v, "source_id": sid,
                                "alias_type": "variant", "citations": counts_raw[v]})
        elif kind == "near-miss":
            decision, reason = "review", (
                f"nearly matches {sid} -- OCR variant or a fuller official title "
                f"than the registry records; alias or acquisition, human decides")
        elif art:
            decision, reason = "artifact", art
        elif kind == "ambiguous":
            decision, reason = "review", (
                "fragment matches more than one held statute equally -- needs a "
                "human decision before it can become an alias")
        elif neg:
            decision, reason = "out", (
                "non-conveyancing subject: " + ", ".join(neg)
                + (f" (positive cue '{subj[0]}' is coincidental)" if subj else ""))
        elif subj:
            decision = "in-scope"
            bits = ["subject cues: " + ", ".join(subj[:4])]
            if tops:
                bits.append("topic keywords: " + ", ".join(tops[:3]))
            reason = "; ".join(bits)
        elif tops:
            # A topic keyword alone is too weak -- topics.csv carries generic
            # single words ("dispute") that hit unrelated statutes.
            decision, reason = "review", (
                "topic keyword only, no subject cue: " + ", ".join(tops[:3]))
        elif n >= 10 and re.search(r"\bamendment\b|special provisions|\)", name):
            # Frequently cited and shaped like a truncated title -- worth a look
            # rather than a silent rejection.
            decision, reason = "review", (
                f"no subject cue, but cited {n} times and the name looks "
                f"truncated -- confirm what statute this is")
        else:
            decision, reason = "out", (
                "no land/title/deed/succession/registration/conveyance-tax/"
                "civil-procedure subject cue in the name")

        tally[decision] += 1
        decisions.append({
            "candidate_name": name,
            "citations": n,
            "distinct_cases": len(cases[name]),
            "decision": decision,
            "reason": reason,
            "matched_source_id": sid,
            "subject_cues": "; ".join(subj),
            "negative_cues": "; ".join(neg),
            "topic_keywords": "; ".join(tops),
            "folded_variants": "; ".join(sorted(variants[name])),
        })

    # 3. write
    C.OUT.mkdir(parents=True, exist_ok=True)
    with C.SCOPE_DECISIONS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(decisions[0].keys()))
        w.writeheader()
        w.writerows(decisions)

    aliases.sort(key=lambda a: (a["source_id"], a["alias"]))
    with C.ALIASES.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["alias", "source_id", "alias_type", "citations"])
        w.writeheader()
        w.writerows(aliases)

    print("\n  decisions:")
    for d, k in tally.most_common():
        print(f"    {d:<14} {k:>4}")
    resolved = sum(a["citations"] for a in aliases)
    print(f"\n  aliases.csv: {len(aliases)} rows resolving {resolved} citations "
          f"with no acquisition")
    print(f"  wrote {C.SCOPE_DECISIONS.relative_to(C.ROOT)}")
    print(f"  wrote {C.ALIASES.relative_to(C.ROOT)}")

    in_scope = [d for d in decisions if d["decision"] == "in-scope"]
    print(f"\n  IN SCOPE ({len(in_scope)}) -- the Phase 1 fetch list:")
    for d in in_scope:
        print(f"    {d['citations']:>4}  {d['candidate_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
