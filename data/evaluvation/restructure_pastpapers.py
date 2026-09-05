"""Rebuild the parsed past papers as atomic questions with explicit backgrounds.

The schema-2 files in parsed-pastpapers/questions/ are faithful to the OCR text
(validate_pastpapers.py proves every quote is verbatim and every source line is
claimed) but their STRUCTURE is uneven, because the extractor was asked for a
question tree and made a different call on each paper about where a scenario
ends and a question begins:

  * a scenario shared by every part of a question was sometimes stored as
    `fact_pattern`, sometimes folded into the first part's text, and sometimes
    kept only in the first part's `quote` while `text` started at the question;
  * a scenario belonging to one part only ("(A) By a Deed of Gift ... Your
    opinion is sought ...") was left inline in that part's text;
  * independent sub-questions ("1. What are the formal parts of a deed?",
    "3. Anura entered into a lease ...") sit as siblings with nothing saying
    that the third has its own facts and the first has none.

For gold authoring and retrieval that distinction matters: the retrieval query
should be the question plus whatever facts govern it, and nothing else. So this
script re-reads every node against its own verbatim quote and emits one record
per atomic question (a part with no items, or an item) with:

  shared_background   the question-level scenario that applies to every part
  group_background    the scenario printed on a part that holds items
  own_background      facts printed inside this node, ahead of its question
  prior_background    facts from earlier parts of the same matter
  question            the interrogative or task, with the facts stripped out
  matter_id           parts of one question that share a set of facts

Nothing here is re-extracted by a model. `question` and every background are
substrings of the schema-2 text or quote, both of which validate_pastpapers.py
has already checked against the OCR. The split points are found by sentence
cues and are heuristic, so every record carries `split_method` and a
`needs_review` list; records with a non-empty list are also written to
review.md for a human pass. Hand corrections go in overrides.json, keyed by
atomic_id, and are applied last so a re-run never loses them.

Reads   parsed-pastpapers/questions/paper-NN.questions.json  (schema 2, untouched)
        parsed-pastpapers/atomic/overrides.json               (optional)
Writes  parsed-pastpapers/atomic/paper-NN.atomic.json        (schema 3)
        parsed-pastpapers/atomic/atomic-questions.jsonl      (all papers, flat)
        parsed-pastpapers/atomic/review.md                    (flagged records)

Usage:
    uv run python data/evaluvation/restructure_pastpapers.py
    uv run python data/evaluvation/restructure_pastpapers.py --paper 16 --print
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUESTIONS_DIR = HERE / "parsed-pastpapers" / "questions"
OUT_DIR = HERE / "parsed-pastpapers" / "atomic"
OVERRIDES = OUT_DIR / "overrides.json"
SCHEMA_VERSION = 3

# Words that open a question or a task. A sentence starting with one of these
# is the question; everything before it in the same node is background.
CUES = (
    "What|Which|Who|Whom|Whose|When|Where|Why|How|Is|Are|Can|Could|Would|Will|"
    "Should|Shall|Does|Do|Did|Has|Have|Had|Advise|Advice|Explain|Discuss|State|"
    "Describe|Draft|Draw|Prepare|Calculate|Compute|Write|Set out|Name|List|Give|"
    "Identify|Comment|Your opinion|In your opinion|If|Indicate|Enumerate|Specify|"
    "Mention|Outline|Define|Distinguish|Examine|Consider|Compare|Under what|"
    "To whom|On what|In what|By whom|Briefly|Critically|As a|As the|You are|"
    "Assume|Assuming|Suppose|Justify|Analyse|Analyze|Evaluate|Illustrate|"
    "Elaborate|Summarise|Summarize|Cite|Quote|Refer|Show|Point out|Suggest|"
    "Determine|Ascertain|Decide|Answer|Please|Kindly|Would you|Do you|Must|"
    "Were|Was|Within|Your client|Your advice|(?:[A-Z]\\w+ )?seeks? your advice"
)
CUE_START = re.compile(rf"^(?:{CUES})\b")
TASK_START = re.compile(
    r"^(?:Draft|Draw|Prepare|Calculate|Compute|Write|Set out|Name|List|Specify|"
    r"Enumerate|Cite|Quote|Show|Illustrate|Indicate|Mention|Outline)\b"
)
# A question word buried mid-sentence because the OCR lost the full stop
# before it: "...obtain a loan of R$ 1,000,000/ What precautionary action..."
CUE_INLINE = re.compile(
    r"(?<=[^.?!]\s)(What|Which|Who|Whom|How|Why|When|Where|Is it|Can|Could|"
    r"Should|Does|Advise|Discuss|Explain)\b(?=[^.?!]*\?)"
)

LABEL = re.compile(r"^\(?(?:[0-9]{1,2}|[ivx]{1,4}|[IVX]{1,4}|[A-Ha-h])[.)\]:]?\s*[-.]?\s*", re.I)
MARKS_TAIL = re.compile(r"\s*\(\s*\d{1,3}(?:\.\d)?\s*marks?[^)]*\)?\.?\s*$", re.I)
NOISE = re.compile(r"\s*[-*¯_]{3,}\s*")

# Capitalised tokens that are legal vocabulary, not the names that tie one
# part's facts to another's.
COMMON_CAPS = set("""
Deed Deeds Notary Notaries Ordinance Act Law Code Section Sections Court Bank
Company Ltd Pvt Private Limited Lot Plan Registrar Registry Land Lands Title
Transfer Gift Lease Mortgage Bond Will Last Power Attorney Partition Schedule
Colombo Sri Lanka Rs Rupees No Nos Assessment Licensed Surveyor Public District
Divisional Secretary Condominium Declaration Management Corporation Apartment
Ownership Registration Documents Instruments Prevention Frauds Stamp Duty
Commissioner General Province Western Central Southern Northern Agreement
Indenture Codicil Testator Executor Donor Donee Lessor Lessee Vendor Purchaser
Mortgagor Mortgagee Attesting Witness Witnesses Client Principal Rule Rules
Certificate Building Plans Road Street Estate Acres Perches Roods Final
Decree Case Purchase Sale Property Properties House Unit Floor Board
Authority Urban Development Housing National State Crown Government Minister
Ministry Municipal Council Pradeshiya Sabha Grama Niladhari Survey
The A An In On At By For To Of And Or If Is Are Was Were He She His Her They
Their It Its This That These Those Which What Who Whom How When Where Why Can
Could Should Would Will Does Do Did Has Have Had Discuss Explain Advise State
Your You Our We I Mr Mrs Ms Dr Hon Sinhala Tamil English Japanese March April
May June July August September October November December January February
Month Year Day Million Thousand Hundred Fifty Forty Twenty Ten Two Three Four
Five Six Seven Eight Nine One Within Under Before After During However Also
""".split())
ANAPHORA = re.compile(
    r"^(the said|said|this|that|such|these|those|he|she|his|her|him|they|their|"
    r"them|the same|the above|thereafter|therein|thereof|the deed|the land|"
    r"the property|the notary|the bank|the company|in the above|in this case|"
    r"in such|on the above)\b",
    re.I,
)


def norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.?!])\s+(?=[A-Z\"'(])", text) if s.strip()]


def strip_label(text: str) -> tuple[str, bool]:
    stripped = LABEL.sub("", text, count=1)
    return stripped, stripped != text


def clean_quote(quote: str) -> str:
    q = norm(quote)
    q = NOISE.sub(" ", q)
    q = MARKS_TAIL.sub("", q)
    q = re.sub(r"\(attestation not (?:required|necessary)\)", "", q, flags=re.I)
    q = re.sub(r"\s*\(?\d{1,3}(?:\.\d)?\s*\.?marks?\)?\.?", "", q, flags=re.I)
    return norm(q)


def full_text(node: dict) -> tuple[str, bool, list[str]]:
    """The node's complete wording, with any lead-in the extractor left only in
    the quote put back. Returns (text, quote_started_with_label, flags)."""
    flags: list[str] = []
    text = norm(node.get("text"))
    quote = clean_quote(node.get("quote") or "")
    quote_body, had_label = strip_label(quote)
    if not had_label:
        # Stray single-token OCR lines in front ("M", "II", "i").
        quote_body = re.sub(r"^(?:[A-Za-z]{1,3}\s+)(?=[A-Z(])", "", quote_body)
    if not text:
        return quote_body, had_label, flags
    if text in quote_body:
        prefix = quote_body[: quote_body.index(text)].strip()
        if len(prefix) >= 20:
            flags.append("lead-in recovered from quote")
            return norm(prefix + " " + text), had_label, flags
        return text, had_label, flags
    # Text and quote disagree beyond whitespace (OCR drift the extractor
    # cleaned up). Prefer text, but check the quote for a longer lead-in.
    if len(quote_body) - len(text) >= 40:
        anchor = " ".join(text.split()[:5])
        idx = quote_body.find(anchor)
        if idx >= 20:
            flags.append("lead-in recovered from quote (approximate)")
            return norm(quote_body[:idx] + " " + text), had_label, flags
    return text, had_label, flags


def split_background(text: str) -> tuple[str, str, str]:
    """(background, question, method)."""
    sents = sentences(text)
    if len(sents) <= 1:
        m = CUE_INLINE.search(text)
        if m and m.start() >= 40 and re.search(r"[A-Z][a-z]+ [A-Z][a-z]+|\d{4}|Rs", text[: m.start()]):
            return norm(text[: m.start()]), norm(text[m.start():]), "inline-cue"
        return "", text, "none"
    idx = None
    for i, s in enumerate(sents):
        if CUE_START.match(s) or "?" in s:
            idx = i
            break
    if idx is None:
        return "", text, "no-cue"
    lead = sents[idx]
    if not CUE_START.match(lead):
        m = CUE_INLINE.search(lead)
        if m and m.start() >= 40:
            bg = " ".join(sents[:idx] + [lead[: m.start()]])
            q = " ".join([lead[m.start():]] + sents[idx + 1:])
            return norm(bg), norm(q), "sentence+inline-cue"
    if idx == 0:
        return "", text, "none"
    return norm(" ".join(sents[:idx])), norm(" ".join(sents[idx:])), "sentence-cue"


def entities(text: str) -> set[str]:
    out: set[str] = set()
    for m in re.finditer(r"\b([A-Z][a-z]{2,})(?:\s+(?:de\s+|De\s+)?([A-Z][a-z]{2,}))?\b", text or ""):
        first, second = m.group(1), m.group(2)
        if second and first not in COMMON_CAPS and second not in COMMON_CAPS:
            out.add(f"{first} {second}")
        if first not in COMMON_CAPS:
            out.add(first)
        if second and second not in COMMON_CAPS:
            out.add(second)
    for m in re.finditer(r"\bLot\s+['\"]?([A-Z]?\d*[A-Z]?\d*)['\"]?", text or ""):
        if m.group(1):
            out.add("Lot " + m.group(1))
    for m in re.finditer(r"\bNo\.?\s*(\d+[A-Z]?)", text or ""):
        out.add("No " + m.group(1))
    return out


ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}


def normalise_id(raw: str, parent: str | None = None) -> str:
    """Stable two-character id for atomic_id. The raw id is kept on the record.

    Papers number parts as (i), 1., (A) and items as a), 1., i); the OCR also
    mangles roman numerals ("!!" and "li" for "ii"). Roman and arabic both
    become zero-padded numbers; letters stay as upper-case letters; a dotted
    item id ("5.1" under part 5) drops the parent prefix.
    """
    value = str(raw).strip().strip("().")
    if parent is not None and value.startswith(f"{parent}."):
        value = value[len(parent) + 1:]
    if value.isdigit():
        return f"{int(value):02d}"
    roman = re.sub(r"[!|l1]", "i", value.lower())
    if roman in ROMAN:
        return f"{ROMAN[roman]:02d}"
    if re.fullmatch(r"[A-Za-z]", value):
        return value.upper()
    return value.upper()


def label_of(question_no: int, part_id: str | None, item_id: str | None) -> str:
    parts = [f"Q{question_no:02d}"]
    if part_id is not None:
        parts.append("P" + normalise_id(part_id))
    if item_id is not None:
        parts.append("I" + normalise_id(item_id, parent=str(part_id)))
    return "-".join(parts)


def question_kind(question: str, stem: str) -> str:
    """'question' | 'task' | 'topic'. A topic is a bare heading under a stem
    such as "Write short notes on the following"; the stem is the instruction."""
    if TASK_START.match(question):
        return "task"
    if "?" in question or CUE_START.match(question):
        return "question"
    if stem:
        return "topic"
    return "question"


def _lead_text(value) -> str:
    if isinstance(value, dict):
        return norm(value.get("text"))
    return norm(value)


def restructure_paper(paper: dict) -> dict:
    paper_no = paper["paper_no"]
    records: list[dict] = []
    for question in paper["questions"]:
        q_no = question["question_no"]
        stem = _lead_text(question.get("stem"))
        shared = _lead_text(question.get("fact_pattern"))
        shared_origin = "fact_pattern" if shared else None

        # First pass: full text + background/question split per node.
        prepared: list[dict] = []
        for part in question.get("parts") or []:
            items = part.get("items") or []
            p_text, p_labelled, p_flags = full_text(part)
            if items:
                g_bg, g_q, g_method = split_background(p_text) if p_text else ("", "", "none")
                if g_q and not g_bg and not g_q.rstrip().endswith("?") and not CUE_START.match(g_q):
                    g_bg, g_q = g_q, ""  # a bare scenario with no question of its own
                for item in items:
                    i_text, i_labelled, i_flags = full_text(item)
                    bg, q, method = split_background(i_text)
                    prepared.append(dict(
                        part=part, item=item, own_bg=bg, question=q, method=method,
                        group_bg=g_bg, group_lead=g_q, labelled=i_labelled,
                        flags=p_flags + i_flags + ([f"group split: {g_method}"] if g_bg and g_q else []),
                    ))
            else:
                bg, q, method = split_background(p_text)
                prepared.append(dict(part=part, item=None, own_bg=bg, question=q, method=method,
                                     group_bg="", group_lead="", labelled=p_labelled, flags=p_flags))

        # The extractor sometimes put the shared scenario in fact_pattern AND in
        # the first part's quote. Facts already covered by the shared background
        # are not that part's own facts.
        if shared:
            for p in prepared:
                for key in ("own_bg", "group_bg"):
                    value = p[key]
                    if value and (value in shared or shared in value):
                        p[key] = ""
                        p["flags"] = [f for f in p["flags"] if not f.startswith("lead-in recovered")]

        # Promote a first-part scenario to the question when the source printed
        # it before the part label (the label sits inside the quote, after the
        # facts) and the question has no fact_pattern of its own.
        if prepared and not shared and prepared[0]["own_bg"] and prepared[0]["item"] is None and len(prepared) > 1:
            first = prepared[0]
            quote = clean_quote(first["part"].get("quote") or "")
            _, starts_with_label = strip_label(quote)
            tail = quote[max(0, len(first["own_bg"]) - 5):] if len(quote) > len(first["own_bg"]) else ""
            label_inside = re.search(r"\s\(?(?:[ivx]{1,4}|[0-9]{1,2}|[a-hA-H])[.)]\s+(?=[A-Z])", tail)
            first_ents = entities(first["own_bg"])
            later_refer = sum(
                1 for p in prepared[1:]
                if (first_ents & entities(p["question"] + " " + p["own_bg"])) or ANAPHORA.match(p["question"])
            )
            if (not starts_with_label and label_inside) or (
                not starts_with_label and later_refer >= max(1, (len(prepared) - 1) // 2)
            ):
                shared = first["own_bg"]
                shared_origin = "promoted from first part"
                first["own_bg"] = ""
                first["flags"].append("scenario promoted to shared_background")

        # Matter grouping.
        matters: list[dict] = []
        for p in prepared:
            facts = " ".join(x for x in (p["group_bg"], p["own_bg"]) if x)
            ents = entities(facts)
            q_ents = entities(p["question"])
            chosen = None
            if shared and not facts:
                chosen = "shared"
            else:
                for m in reversed(matters):
                    overlap = (ents | q_ents) & m["ents"]
                    if facts and len(overlap) >= 2:
                        chosen = m
                        break
                    if not facts and (len(overlap) >= 1 or (ANAPHORA.match(p["question"]) and m is matters[-1])):
                        chosen = m
                        break
                if chosen is None and (facts or shared):
                    chosen = {"id": None, "ents": set(), "members": []}
                    matters.append(chosen)
            if chosen == "shared":
                p["matter"] = "shared"
            elif chosen is None:
                p["matter"] = None
            else:
                chosen["ents"] |= ents | (q_ents if facts else set())
                chosen["members"].append(p)
                p["matter"] = chosen
        for n, m in enumerate(matters, start=1):
            m["id"] = f"P{paper_no:02d}-{label_of(q_no, None, None)}-M{n:02d}"

        # Emit.
        for p in prepared:
            part, item = p["part"], p["item"]
            part_id, item_id = part.get("part_id"), (item or {}).get("item_id")
            node = item or part
            atomic_id = f"P{paper_no:02d}-" + label_of(q_no, part_id, item_id)
            part_uid = f"paper-{paper_no:02d}/q{q_no}/{part_id}" + (f"/{item_id}" if item_id is not None else "")
            prior: list[str] = []
            matter_id = None
            if p["matter"] == "shared":
                matter_id = f"P{paper_no:02d}-{label_of(q_no, None, None)}-M00"
            elif p["matter"]:
                matter_id = p["matter"]["id"]
                for other in p["matter"]["members"]:
                    if other is p:
                        break
                    facts = " ".join(x for x in (other["group_bg"], other["own_bg"]) if x)
                    if facts and facts not in prior and facts != p["group_bg"]:
                        prior.append(facts)
            flags = list(p["flags"])
            if p["method"] == "no-cue":
                flags.append("no question cue found; whole text kept as question")
            if p["method"] in ("inline-cue", "sentence+inline-cue"):
                flags.append("question word found mid-sentence; check split")
            kind = question_kind(p["question"], stem or p["group_lead"])
            if not p["question"]:
                flags.append("empty question")
            elif kind == "question" and "?" not in p["question"] and not CUE_START.match(p["question"]):
                flags.append("no question cue and no '?'; may be a scenario with the question lost")
            if p["own_bg"] and len(p["own_bg"]) < 30:
                flags.append("very short own_background")
            records.append({
                "atomic_id": atomic_id,
                "part_uid": part_uid,
                "paper_no": paper_no,
                "question_no": q_no,
                "part_id": part_id,
                "item_id": item_id,
                "matter_id": matter_id,
                "compulsory": bool(question.get("compulsory")),
                "stem": stem or None,
                "shared_background": shared or None,
                "shared_background_origin": shared_origin,
                "group_background": p["group_bg"] or None,
                "group_lead": p["group_lead"] or None,
                "prior_background": prior,
                "own_background": p["own_bg"] or None,
                "question": p["question"],
                "question_kind": kind,
                "marks": node.get("marks"),
                "part_marks": part.get("marks") if item is not None else None,
                "pdf_page": node.get("pdf_page"),
                "source_quote": node.get("quote"),
                "split_method": p["method"],
                "needs_review": flags,
            })
    return {
        "schema_version": SCHEMA_VERSION,
        "paper_no": paper_no,
        "session": paper.get("session"),
        "subject": paper.get("subject"),
        "code": paper.get("code"),
        "pdf_pages": paper.get("pdf_pages"),
        "derived_from": f"questions/paper-{paper_no:02d}.questions.json (schema 2)",
        "status": "unverified",
        "atomic_questions": records,
    }


OVERRIDABLE = {
    "shared_background", "group_background", "own_background", "prior_background",
    "question", "question_kind", "matter_id", "needs_review",
}


def apply_overrides(records: list[dict], overrides: dict) -> int:
    """Hand corrections, keyed by atomic_id. Only text/grouping fields may be
    overridden; identity, marks and source_quote always come from schema 2."""
    applied = 0
    for r in records:
        fix = overrides.get(r["atomic_id"])
        if not fix:
            continue
        bad = set(fix) - OVERRIDABLE - {"note"}
        if bad:
            raise SystemExit(f"{r['atomic_id']}: override touches non-overridable field(s) {sorted(bad)}")
        for key, value in fix.items():
            if key == "note":
                continue
            r[key] = value
        r["split_method"] = "override"
        r["override_note"] = fix.get("note")
        if "needs_review" not in fix:
            r["needs_review"] = []
        applied += 1
    return applied


def review_lines(records: list[dict]) -> list[str]:
    out = []
    for r in records:
        if not r["needs_review"]:
            continue
        out.append(f"## {r['atomic_id']} ({', '.join(r['needs_review'])})")
        out.append("")
        for key in ("shared_background", "group_background", "own_background"):
            if r[key]:
                out.append(f"- {key}: {r[key][:300].rstrip()}")
        out.append(f"- question: {r['question'][:300].rstrip()}")
        out.append("")
    return out[:-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paper", type=int)
    parser.add_argument("--print", action="store_true", dest="show")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.is_file() else {}
    paths = sorted(QUESTIONS_DIR.glob("paper-*.questions.json"))
    if args.paper:
        paths = [p for p in paths if p.name == f"paper-{args.paper:02d}.questions.json"]

    all_records: list[dict] = []
    applied = 0
    for path in paths:
        paper = json.loads(path.read_text(encoding="utf-8"))
        out = restructure_paper(paper)
        applied += apply_overrides(out["atomic_questions"], overrides)
        (OUT_DIR / f"paper-{paper['paper_no']:02d}.atomic.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        all_records.extend(out["atomic_questions"])
        if args.show:
            for r in out["atomic_questions"]:
                print(f"\n{r['atomic_id']}  matter={r['matter_id']}  marks={r['marks']}  [{r['split_method']}] {r['needs_review']}")
                if r["shared_background"]:
                    print(f"  shared : {r['shared_background'][:160]}")
                if r["group_background"]:
                    print(f"  group  : {r['group_background'][:160]}")
                if r["prior_background"]:
                    print(f"  prior  : {len(r['prior_background'])} earlier fact block(s)")
                if r["own_background"]:
                    print(f"  own    : {r['own_background'][:160]}")
                print(f"  Q      : {r['question'][:200]}")

    if not args.paper:
        with (OUT_DIR / "atomic-questions.jsonl").open("w", encoding="utf-8") as fh:
            for r in all_records:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        flagged = [r for r in all_records if r["needs_review"]]
        header = [
            "# Atomic question review queue",
            "",
            f"{len(all_records)} atomic questions across {len(paths)} papers; "
            f"{len(flagged)} carry a review flag. Generated by restructure_pastpapers.py. status=unverified.",
            "",
        ]
        body = "\n".join(header + review_lines(all_records)).rstrip() + "\n"
        (OUT_DIR / "review.md").write_text(body, encoding="utf-8")

    n = len(all_records)
    methods = Counter(r["split_method"] for r in all_records)
    with_shared = sum(1 for r in all_records if r["shared_background"])
    promoted = sum(1 for r in all_records if r["shared_background_origin"] == "promoted from first part")
    own = sum(1 for r in all_records if r["own_background"])
    grp = sum(1 for r in all_records if r["group_background"])
    matters = len({r["matter_id"] for r in all_records if r["matter_id"]})
    flagged = sum(1 for r in all_records if r["needs_review"])
    print(f"atomic questions : {n}")
    print(f"split methods    : {dict(methods)}")
    print(f"shared background: {with_shared} records ({promoted} via promotion)")
    print(f"group background : {grp}   own background: {own}   matters: {matters}")
    print(f"overrides applied: {applied}   flagged for review: {flagged}")
    print(f"wrote {OUT_DIR}")
    print("unverified: derived from OCR text; no lawyer has signed this off.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
