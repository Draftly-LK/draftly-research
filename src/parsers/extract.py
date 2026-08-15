"""Semantic field extraction from parsed LKSC judgments.

Turns a ``ParsedJudgment`` (evidence blocks) plus the page frame (title,
comments, footer) into a nested record: identity, report, dates, case
details, parties, bench, headnote, representation, judgment, authorities,
provenance and quality. Everything here is regex/heuristic extraction over
digitized print, so fields are best-effort: absent evidence yields null/empty
rather than a guess, and every extracted item that came from the body carries
the ``block_index`` it was found in.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from base import ParsedJudgment

# ---------------------------------------------------------------- frame ----

TITLE_RE = re.compile(
    r"^(?P<name>.+?)\s+-\s+(?:NLR|SLR)\s+-\s+.*?"
    r"\[(?P<nc_year>\d{4})\]\s+LKSC\s+(?P<nc_num>\d+);\s+"
    r"\((?P<rep_year>\d{4})\)\s+(?P<volume>\d+)\s+(?P<series>NLR|Sri\s?[Ll]R)\s+"
    r"(?P<page>\d+)\s+\((?P<date_raw>[^)]+)\)\s*$"
)
SOURCE_RE = re.compile(r"<!--make_database: source=(\S+)-->")
URL_RE = re.compile(r"URL:.*?(http://www\.commonlii\.org\S+?)<", re.S)
BATCH_RE = re.compile(r"/data/([^/]+)/")

# Multi-letter titles require their dots so a trailing capital of a name
# (e.g. the final A of "DE SILVA C. J.") cannot be absorbed into the title.
JUDGE_TITLES = r"S\.\s?P\.\s?J|A\.\s?C\.\s?J|C\.\s?J|A\.\s?J|P\.\s?J|CJ|J"
COURTS_RE = re.compile(
    r"\b(PRIVY COUNCIL|SUPREME COURT|COURT OF CRIMINAL APPEAL)\b", re.I
)

FRONT_MATTER_BLOCKS = 14  # caption/headnote conventionally sit in the first blocks


def parse_date(raw: str) -> str | None:
    raw = re.sub(r"\s+", " ", raw).strip().rstrip(".")
    for fmt in ("%d %B %Y", "%B %d, %Y", "%B %d %Y", "%d %b %Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def extract_frame(html: str, title: str, file: str) -> dict:
    match = TITLE_RE.match(title)
    frame: dict = {
        "case_name_raw": None,
        "neutral_citation": None,
        "series": None,
        "reported_year": None,
        "volume": None,
        "start_page": None,
        "decision_date": None,
        "decision_date_raw": None,
    }
    if match:
        frame.update(
            case_name_raw=match["name"],
            neutral_citation=f"[{match['nc_year']}] LKSC {match['nc_num']}",
            series="NLR" if match["series"] == "NLR" else "SLR",
            reported_year=int(match["rep_year"]),
            volume=int(match["volume"]),
            start_page=int(match["page"]),
            decision_date=parse_date(match["date_raw"]),
            decision_date_raw=match["date_raw"].strip(),
        )
    source = SOURCE_RE.search(html)
    url = URL_RE.search(html)
    frame["build_source"] = source.group(1) if source else None
    frame["source_batch"] = (
        BATCH_RE.search(source.group(1)).group(1)
        if source and BATCH_RE.search(source.group(1))
        else None
    )
    frame["source_url"] = url.group(1).strip() if url else None
    return frame


# ---------------------------------------------------------------- bench ----

PRESENT_RE = re.compile(r"\bPresent\s*:?\s*(?P<rest>.+)$", re.I)
NAME_WITH_TITLE_RE = re.compile(
    rf"(?P<name>[A-Z][A-Za-z.'\- ]*?)[\s,]+(?P<title>{JUDGE_TITLES})\.?(?=[\s,]|$)"
)
TITLE_ONLY_RE = re.compile(rf"^(?:{JUDGE_TITLES})\.?$")
NAME_ONLY_RE = re.compile(r"^[A-Z][A-Za-z.'\- ]+$")
NOT_A_NAME = {"SUPREME COURT", "PRIVY COUNCIL", "COURT OF CRIMINAL APPEAL", "PRESENT"}
# Particles that legitimately appear lowercase inside a judge's name; any other
# lowercase word means prose leaked in ("This is a judgment of Lawrie").
_NAME_PARTICLES = {"de", "van", "der", "den", "du", "of", "da", "le", "la", "el"}
# Counsel ranks are not judicial titles.
_COUNSEL_RANK_NAME = re.compile(r"^[KQCDSPA]\.?\s?[CGJ]\.?$", re.I)


def _plausible_judge_name(name: str) -> bool:
    if not 2 < len(name) <= 40 or _COUNSEL_RANK_NAME.match(name):
        return False
    if name.upper() in NOT_A_NAME:
        return False
    words = name.replace(".", " ").split()
    if len(words) > 6:
        return False
    return all(
        word.lower() in _NAME_PARTICLES or word[:1].isupper() or word[:1].isdigit()
        for word in words
    )


def _normalise_title(title: str) -> str:
    return re.sub(r"\s+", "", title).rstrip(".") + "."


def _split_judges(text: str) -> list[dict]:
    """Parse 'Gratiaen J. and Fernando A.J.' / 'SRIPAVAN, J. AND IMAM, J.'.

    Chunks are comma-separated; a title-only chunk ('J.') attaches to the
    preceding name chunk, since 'Fernando, J.' splits across the comma.
    """
    text = re.sub(r"\band\b", ",", text, flags=re.I)
    judges: list[dict] = []
    pending: str | None = None

    def emit(name: str, title: str) -> None:
        name = name.strip(" .,")
        if _plausible_judge_name(name):
            judges.append({"name": name, "title": _normalise_title(title)})

    leading_title = re.compile(rf"^({JUDGE_TITLES})\.?\s+(?P<rest>[A-Z].*)$")
    for chunk in text.split(","):
        chunk = chunk.strip(" .,—-")
        if not chunk:
            continue
        if TITLE_ONLY_RE.match(chunk + "."):
            if pending:
                emit(pending, chunk)
                pending = None
            continue
        # "WANASUNDERA, J. RANASINGHE" splits so the previous judge's title
        # leads the next chunk; hand it back before parsing the rest.
        lead = leading_title.match(chunk)
        if lead and pending:
            emit(pending, lead.group(1))
            pending = None
            chunk = lead["rest"].strip(" .,")
            if not chunk:
                continue
        # A chunk may hold several judges with no commas between them,
        # e.g. the SLR caption "J. A. N. DE SILVA C. J. SRIPAVAN".
        matches = list(NAME_WITH_TITLE_RE.finditer(chunk))
        for match in matches:
            emit(match["name"], match["title"])
        remainder = chunk[matches[-1].end():].strip(" .,") if matches else chunk
        pending = remainder if NAME_ONLY_RE.match(remainder) else None
    return judges


PEER_RE = re.compile(r"\b(?:Lord|Sir|Viscount|Baron(?:ess)?|Earl|Dame)\b")
CASE_NUMBER_CUT_RE = re.compile(
    r"\bS\.?\s?C\.?\s?(?:\([A-Z.]+\))?\s?(?:APPEAL|APPLICATION|LA|No|MINUTES|\d)",
    re.I,
)


def _split_peers(text: str) -> list[dict]:
    """Privy Council benches carry peerage styles, not 'J.' titles."""
    text = re.sub(r"\band\b", ",", text, flags=re.I)
    peers = []
    for chunk in text.split(","):
        chunk = chunk.strip(" .,—-")
        if PEER_RE.match(chunk) and len(chunk) < 60:
            peers.append({"name": chunk, "title": None})
    return peers


def extract_bench(paragraphs: list[str]) -> tuple[list[dict], str | None]:
    """Return (bench, deciding_court) from the front matter."""
    deciding_court = None
    front = paragraphs[:FRONT_MATTER_BLOCKS]
    for text in front:
        court = COURTS_RE.search(text)
        if court:
            deciding_court = court.group(1).title().replace("Of", "of")
            break

    for text in front:
        present = PRESENT_RE.search(text)
        if present:
            rest = present["rest"]
            # Cut anything after a case-number token leaking into the line.
            rest = CASE_NUMBER_CUT_RE.split(rest)[0]
            judges = _split_judges(rest)
            if judges:
                return judges, deciding_court
            peers = _split_peers(rest)
            if peers:
                return peers, deciding_court or "Privy Council"

    # SLR caption: judges listed after the court name, before the case
    # number -- sometimes in the same block, sometimes in the next ones.
    for index, text in enumerate(front):
        court = COURTS_RE.search(text)
        if not court:
            continue
        tail = text[court.end():]
        for extra in front[index + 1: index + 4]:
            if CASE_NUMBER_CUT_RE.search(tail):
                break
            tail += ", " + extra
        tail = CASE_NUMBER_CUT_RE.split(tail)[0]
        judges = _split_judges(tail)
        if judges:
            return judges, deciding_court
    return [], deciding_court


# -------------------------------------------------------------- parties ----

ROLE_WORDS = (
    "appellant", "respondent", "petitioner", "plaintiff", "defendant",
    "complainant", "accused", "applicant",
)


# "v.", "v", "V", "vs", "Vs." all appear as the versus token in case names.
PARTY_SPLIT_RE = re.compile(r"\s+(?:v|vs)\.?\s+", re.I)
AND_OTHERS_RE = re.compile(
    r"\s*[,-]?\s*\b(?:and|&)\s+(?:two|three|four|five|\d+\s+)?(?:others?|another)\b\.?"
    r"|\s*[,-]?\s*\bet\s+al\.?", re.I,
)
# Single-party matters ("In re X", "Re X") have an applicant, not two sides.
IN_RE_RE = re.compile(r"^(?:in\s+re|re)\b[\s:.]*", re.I)
_ROLE_PAIRS = {
    "appellant": "respondent",
    "petitioner": "respondent",
    "plaintiff": "defendant",
    "applicant": "respondent",
    "complainant": "accused",
}
# When the caption prints no role words, the proceeding implies them.
_PROCEEDING_ROLES = {
    "appeal": ("appellant", "respondent"),
    "privy-council appeal": ("appellant", "respondent"),
    "case stated": ("appellant", "respondent"),
    "application": ("petitioner", "respondent"),
    "fundamental-rights application": ("petitioner", "respondent"),
    "revision application": ("petitioner", "respondent"),
    "election petition": ("petitioner", "respondent"),
}


def extract_parties(
    case_name: str | None, paragraphs: list[str], proceeding_type: str | None
) -> list[dict]:
    if not case_name:
        return []
    front = " ".join(paragraphs[:FRONT_MATTER_BLOCKS]).lower()
    roles_present = [word for word in ROLE_WORDS if word in front]

    def roles() -> tuple[str | None, str | None]:
        for word in roles_present:
            if word in _ROLE_PAIRS:
                return word, _ROLE_PAIRS[word]
        return _PROCEEDING_ROLES.get(proceeding_type or "", (None, None))

    def party(raw: str, role: str | None) -> dict:
        name = AND_OTHERS_RE.sub("", raw).strip(" ,.-")
        return {
            "name": name,
            "role": role,
            "and_others": bool(AND_OTHERS_RE.search(raw)),
        }

    in_re = IN_RE_RE.match(case_name.strip())
    if in_re:
        return [party(case_name.strip()[in_re.end():], "applicant")]

    sides = PARTY_SPLIT_RE.split(case_name, maxsplit=1)
    if len(sides) == 2:
        left, right = roles()
        return [party(sides[0], left), party(sides[1], right)]
    return [party(case_name, roles()[0])]


# --------------------------------------------------------- case details ----

SC_NUMBER_RE = re.compile(
    r"\bS\.?\s?C\.?\s?(?:\([A-Za-z.]+\)\s?)?"
    r"(?:Appeal|Application|Appln|L\.?\s?A\.?|Spl|Minutes)?\s?"
    r"(?:\(?[A-Za-z.]+\)?\s?)?(?:No[.,]?s?\.?\s?)?[-–]?\s?"
    r"\d+[A-Za-z]?\s?(?:/|-|of)?\s?\d*",
    re.I,
)
# Old NLR captions carry both numbers in one line: "331-P. C Badulla, 1088."
OLD_NLR_NUMBER_RE = re.compile(
    r"^\d{1,4}\s?-\s?[A-Z][A-Za-z.,()'/ ]{2,60}\d[\d,./A-Za-z]*\.?$"
)
ELECTION_NUMBER_RE = re.compile(
    r"\b(?:Election Petition|Case)\s+No[.,]?\s?\d+(?:\s?of\s?\d{4})?", re.I
)
LOWER_COURT_PREFIXES = {
    "D.C.": "District Court",
    "C.A.": "Court of Appeal",
    "H.C.": "High Court",
    "M.C.": "Magistrate's Court",
    "C.R.": "Court of Requests",
    "P.C.": "Police Court",
    "L.T.": "Labour Tribunal",
    "LABOUR TRIBUNAL": "Labour Tribunal",
}
LOWER_COURT_RE = re.compile(
    r"\b(?P<prefix>D\.?\s?C\.?|C\.?\s?A\.?|H\.?\s?C\.?|M\.?\s?C\.?|C\.?\s?R\.?|"
    r"P\.?\s?C\.?|L\.?\s?T\.?|Labour Tribunal)\s?"
    r"(?P<body>(?:\([A-Za-z.]+\)\s?)?(?:No[.,]?s?\.?\s?)?[A-Za-z'.]*\s?,?\s?[\d][\d,./A-Za-z-]*)",
    re.I,
)

# Ordered most specific first; the generic appeal/application rules are last.
PROCEEDING_RULES = (
    (re.compile(r"fundamental rights|S\.?\s?C\.?\s?\(?F\.?R\.?\)?", re.I),
     "fundamental-rights application"),
    (re.compile(r"case stated", re.I), "case stated"),
    (re.compile(r"election petition", re.I), "election petition"),
    (re.compile(r"appeal.{0,40}privy council|privy council.{0,40}appeal", re.I),
     "privy-council appeal"),
    (re.compile(r"court of admiralty|\bin prize\b", re.I), "prize court cause"),
    (re.compile(r"trial at bar", re.I), "trial at bar"),
    (re.compile(r"crown case reserved", re.I), "crown case reserved"),
    (re.compile(r"contempt of court", re.I), "contempt proceeding"),
    (re.compile(r"S\.?\s?C\.?\s?\(?EXPULSION\)?", re.I), "expulsion determination"),
    (re.compile(
        r"S\.?\s?C\.?\s?REFERENCE|reference under Article\s?12[45]"
        r"|referred the following questions",
        re.I,
    ), "constitutional reference"),
    (re.compile(
        r"S\.?\s?C\.?\s?RULE NO|matter of a rule on a (?:proctor|attorney)"
        r"|rule to show cause|disciplinary rule",
        re.I,
    ), "disciplinary rule"),
    (re.compile(r"revision application|\bin revision\b", re.I), "revision application"),
    (re.compile(r"matter of the (?:last will|estate)|testamentary", re.I),
     "testamentary proceeding"),
    (re.compile(r"settlement inquiry|matter of an inquiry", re.I), "inquiry"),
    (re.compile(r"\bappeals?\b", re.I), "appeal"),
    (re.compile(r"\bapplication\b", re.I), "application"),
)

HEARING_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2})(?:ST|ND|RD|TH)?\s*,?\s*(\d{4})?",
    re.I,
)


def extract_case_details(paragraphs: list[str], decision_date: str | None) -> dict:
    # Case numbers and hearing dates come from the caption, which ends where
    # the headnote starts -- numbers quoted inside holdings belong to cited
    # cases. Proceeding type and originating court use the full front matter,
    # because NLR pages put "APPEAL from ..." after the headnote.
    front_full = paragraphs[:FRONT_MATTER_BLOCKS]
    caption = front_full
    for index, text in enumerate(front_full):
        if HELD_RE.match(text):
            caption = front_full[:index]
            break
    front_text = " ".join(front_full)

    case_numbers = []
    for text in caption:
        matches = list(SC_NUMBER_RE.finditer(text)) + list(
            ELECTION_NUMBER_RE.finditer(text)
        )
        for match in matches:
            token = re.sub(r"\s+", " ", match.group(0)).strip(" .,-/")
            if any(char.isdigit() for char in token) and token not in case_numbers:
                case_numbers.append(token)
        if len(text) < 100 and OLD_NLR_NUMBER_RE.match(text):
            token = text.strip(" .")
            if token not in case_numbers:
                case_numbers.append(token)

    # Appeals list the whole chain ("SC ... CA ... DC Colombo ..."); the
    # originating court is the court of first instance, not the first listed.
    FIRST_INSTANCE = {
        "District Court", "Magistrate's Court", "Court of Requests",
        "Police Court", "Labour Tribunal",
    }
    lower_numbers = []
    courts_seen: list[str] = []
    for text in caption:
        for match in LOWER_COURT_RE.finditer(text):
            prefix = re.sub(r"\s+", "", match["prefix"].upper())
            prefix = prefix if prefix == "LABOURTRIBUNAL" else prefix.rstrip(".") + "."
            prefix = "LABOUR TRIBUNAL" if prefix == "LABOURTRIBUNAL" else prefix
            court = LOWER_COURT_PREFIXES.get(prefix)
            if court is None:
                continue
            token = re.sub(r"\s+", " ", match.group(0)).strip(" .,-")
            if token not in lower_numbers:
                lower_numbers.append(token)
            courts_seen.append(court)
    originating_court = next(
        (court for court in courts_seen if court in FIRST_INSTANCE),
        courts_seen[0] if courts_seen else None,
    )

    proceeding_type = None
    for pattern, label in PROCEEDING_RULES:
        if pattern.search(front_text):
            proceeding_type = label
            break
    if proceeding_type is None and lower_numbers:
        # NLR captions often print only "D. C., Kandy, 7,816" -- a lower-court
        # number with no proceeding word still means this reached the SC on appeal.
        proceeding_type = "appeal"

    if originating_court is None:
        origin = re.search(
            r"from (?:an? (?:order|judgment|decree|conviction|sentence)s? of )?the "
            r"([A-Z][A-Za-z' ]+?(?:Court|Tribunal))",
            front_text,
        )
        if origin:
            originating_court = origin.group(1).strip()

    hearing_dates = []
    for text in caption:
        for month, day, year in HEARING_DATE_RE.findall(text):
            raw = f"{month.title()} {day}, {year}" if year else f"{month.title()} {day}"
            iso = parse_date(raw) if year else None
            if iso and decision_date and iso == decision_date:
                continue
            entry = iso or raw
            if entry not in hearing_dates:
                hearing_dates.append(entry)

    return {
        "proceeding_type": proceeding_type,
        "case_numbers": case_numbers,
        "originating_court": originating_court,
        "lower_court_case_numbers": lower_numbers,
        "hearing_dates": hearing_dates,
    }


# ------------------------------------------------------------- headnote ----

HELD_RE = re.compile(r"^Held(?P<qual>,?\s*(?:further|also))?\s*[,:.\-]?", re.I)
PER_JUDGE_RE = re.compile(rf"^Per\s+(?P<judge>[A-Z][A-Za-z.'\- ]+?(?:{JUDGE_TITLES}))", )
QUAERE_RE = re.compile(r"^Quaere\b", re.I)
NUMBERED_RE = re.compile(r"^\(?(?P<num>\d{1,2}|[ivx]{1,4})\)?[.)]\s+", re.I)
CASES_REFERRED_RE = re.compile(r"^Cases?\s+referred\s+to\b", re.I)
# Marks the start of the facts/procedural narrative, which follows the rule
# statement(s) in the headnote. Used to stop a "Held"-equivalent region from
# running on.
PROCEDURAL_OPEN_RE = re.compile(
    r"^THIS\s+(?:was|is)\b|^APPEAL\s+from\b|^APPLICATION\s+for\b", re.I
)
# A stronger facts-opener signal, valid ONLY for closing rule_zone_open (an
# unlabelled rule statement, no "Held" anywhere in the case -- see
# has_held_marker below). NOT safe to use against in_held: a real holding
# commonly opens by naming a party ("The petitioner's rights were
# infringed..."), so applying this to a case that DOES say "Held" would
# delete real holdings instead of ending a facts narrative. Anchored to the
# start of the block so it can't fire on a party word mid-sentence.
FACTS_PARTY_OPEN_RE = re.compile(
    r"^THE\s+(?:complaint|appellant|respondent|petitioner|defendant|accused|"
    r"plaintiff|applicant|deceased)\b",
    re.I,
)


# A date may precede the opinion heading in either order:
# 'December 5, 1958.' or '29th January, 1902.'
_DATE_PREFIX = (
    r"(?:(?:[A-Z][a-z]+ \d{1,2}(?:st|nd|rd|th)?\s?,?\s?\d{4}"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+\s?,?\s?\d{4})[.,]?\s*)?"
)
# The '?' and U+FFFD inside names absorb OCR artifacts ("COLIN?THOME', J.").
OPINION_HEADING_RE = re.compile(
    rf"^{_DATE_PREFIX}"
    rf"(?P<name>[A-Z][A-Za-z.'?�\- ]{{2,45}}?)[,.]?\s?(?P<title>{JUDGE_TITLES})"
    rf"\.?[\s.,:;—–-]*$"
)
# Privy Council style: '(Delivered by LORD PEARCE)-', '[Delivered by ...]'.
DELIVERED_RE = re.compile(
    rf"^{_DATE_PREFIX}[\[(]?\s*Delivered by\s+(?P<name>[A-Z][A-Za-z.'?\- ]+?)"
    rf"\s*[\])\-:.,]*$",
    re.I,
)
COURT_JUDGMENT_RE = re.compile(rf"^{_DATE_PREFIX}JUDGMENT OF (?:THE )?COURT\W*$", re.I)


def _heading_judge(text: str) -> str | None:
    """Judge named by an opinion heading block, or None."""
    if len(text) >= 80 or text.startswith("Per ") or "Present" in text:
        return None
    delivered = DELIVERED_RE.match(text)
    if delivered:
        return delivered["name"].strip(" ,.").title()
    if COURT_JUDGMENT_RE.match(text):
        return "The Court"
    match = OPINION_HEADING_RE.match(text)
    if match and "I agree" not in text:
        return (
            match["name"].strip(" ,.")
            + ", "
            + re.sub(r"\s+", "", match["title"]).rstrip(".")
            + "."
        )
    return None


def _is_catchword_block(block) -> bool:
    text = block.text
    if len(text) > 700 or " v. " in text:
        return False
    if COURTS_RE.search(text) or "Present" in text:
        return False
    segments = [part.strip() for part in text.split("-") if part.strip()]
    if block.was_italic and len(segments) >= 3:
        return True
    if len(segments) < 4:
        return False
    capital_led = sum(1 for part in segments if part[0].isupper() or part[0].isdigit())
    return capital_led / len(segments) >= 0.6


CUR_ADV_VULT_RE = re.compile(r"Cur\.?\s*adv\.?\s*vult", re.I)


def _headnote_anchor(paragraphs: list[str]) -> int:
    """Index of the last headnote marker (Held / Cases referred / Cur. adv.)."""
    anchor = -1
    for index, text in enumerate(paragraphs[: min(len(paragraphs), 45)]):
        if (
            HELD_RE.match(text)
            or CASES_REFERRED_RE.match(text)
            or CUR_ADV_VULT_RE.search(text)
        ):
            anchor = index
    return anchor


def _opinion_start(paragraphs: list[str]) -> int | None:
    """Index of the first opinion heading, e.g. 'December 5, 1958. FERNANDO, J.-'.

    SLR captions list judges one per block, and each looks like an opinion
    heading, so prefer the first heading AFTER the last headnote marker.
    """
    anchor = _headnote_anchor(paragraphs)
    first = None
    for index, text in enumerate(paragraphs):
        if index < 2:
            continue
        if _heading_judge(text):
            if first is None:
                first = index
            if index > anchor:
                return index
    return first


def headnote_end(paragraphs: list[str], opinion_start: int | None) -> int:
    """End of the headnote region.

    The opinion heading bounds it, but only when it actually follows the last
    headnote marker: SLR captions repeat judge names before the headnote, so a
    heading detected earlier would cut the region short and hide the
    'Cases referred to' list and numbered holdings that come after it.
    """
    anchor = _headnote_anchor(paragraphs)
    if opinion_start is not None and opinion_start > anchor:
        return opinion_start
    if anchor >= 0:
        # Cover the marker's own list/holdings without running into the opinion.
        return min(len(paragraphs), anchor + 15)
    return min(len(paragraphs), 40)


def extract_headnote(blocks, opinion_start: int | None) -> dict:
    # Long criminal headnotes can run past the caption window, so without a
    # detected opinion heading the region extends past the last marker.
    end = headnote_end([block.text for block in blocks], opinion_start)
    catchwords: list[str] = []
    holdings: list[dict] = []
    quaere: list[dict] = []
    per_judge: list[dict] = []
    facts: list[dict] = []
    in_held = False
    # True for the run of blocks right after the catchwords: some older
    # reports state the rule there without ever writing the word "Held". Only
    # engage this when the record has NO "Held" marker anywhere -- those are
    # exactly the cases where the old code guaranteed empty holdings, so there
    # is no correct existing behaviour to disturb. A record that DOES use
    # "Held" is trusted completely instead: its facts/issues paragraphs before
    # the marker must not be picked up as if they were rule statements.
    has_held_marker = any(HELD_RE.match(b.text) for b in blocks[:end])
    rule_zone_open = False
    # A generous last-resort backstop, not a precision tool -- real stopping
    # is now PROCEDURAL_OPEN_RE's job (including the "THE <party>" branch).
    # This only exists to bound the damage on some future, unanticipated
    # block shape that neither stop signal recognises; it must sit well above
    # any legitimate multi-part rule (the longest seen so far is ~2.3k chars).
    rule_zone_chars = 0

    for block in blocks[:end]:
        text = block.text
        if CASES_REFERRED_RE.match(text):
            in_held = False
            continue
        held = HELD_RE.match(text)
        if held:
            in_held = True
            rule_zone_open = False
            body = text[held.end():].strip()
            if body:  # a bare "Held" heading has its items in later blocks
                numbered = NUMBERED_RE.match(body)
                holdings.append({
                    "number": numbered["num"] if numbered else None,
                    "qualifier": (held["qual"] or "").strip(", ") or None,
                    "text": body,
                    "block_index": block.block_index,
                })
            continue
        if in_held and NUMBERED_RE.match(text):
            holdings.append({
                "number": NUMBERED_RE.match(text)["num"],
                "qualifier": None,
                "text": text,
                "block_index": block.block_index,
            })
            continue
        if QUAERE_RE.match(text):
            quaere.append({"text": text, "block_index": block.block_index})
            continue
        per = PER_JUDGE_RE.match(text)
        if per:
            per_judge.append({
                "judge": per["judge"].strip(" ,."),
                "text": text,
                "block_index": block.block_index,
            })
            continue
        # A counsel appearance or the facts narrative starting up ends the
        # "Held" region too. Without this, a missed opinion-heading detection
        # (headnote_end() falls back to a fixed block count) lets a single
        # holding swallow everything through to the end of the judgment.
        # COUNSEL_RE is written to scan a whole block for a match anywhere,
        # which is right for extract_counsel() but too loose here: ordinary
        # judgment prose ("...entered judgment for the plaintiff...") can
        # match it deep inside a long paragraph. A genuine counsel-appearance
        # block IS the counsel line, so require the match to start at or near
        # the front of the block.
        counsel_match = COUNSEL_RE.search(text)
        stop_marker = (
            (counsel_match is not None and counsel_match.start() < 40)
            or bool(PROCEDURAL_OPEN_RE.match(text))
        )
        if in_held and stop_marker:
            in_held = False
        # Broader than stop_marker -- only safe for rule_zone_open (see
        # FACTS_PARTY_OPEN_RE's docstring above).
        rule_zone_stop = stop_marker or bool(FACTS_PARTY_OPEN_RE.match(text))
        # Catchwords: early dash-separated topic blocks. Italics mark them in
        # clean conversions, but many files lost the markup, so a content
        # heuristic decides; multi-subject headnotes have several such blocks.
        if not holdings and _is_catchword_block(block):
            catchwords.extend(
                part.strip(" .")
                for part in re.split(r"\s*-\s*|-", text)
                if part.strip(" .")
            )
            rule_zone_open = not has_held_marker
            rule_zone_chars = 0
            continue
        if in_held:
            if holdings and len(holdings[-1]["text"]) < 1500:
                holdings[-1]["text"] += " " + text
                continue
            if not holdings:  # first item after a bare "Held" heading
                holdings.append({
                    "number": None,
                    "qualifier": None,
                    "text": text,
                    "block_index": block.block_index,
                })
                continue
            # Defensive cap: even with the stop markers above, don't let one
            # holding run away with the rest of the judgment if some other,
            # unanticipated block shape fails to end it. Fall through and let
            # this block be classified normally instead.
            in_held = False
        if rule_zone_open:
            if (
                not rule_zone_stop
                and not block.was_bold
                and len(text) > 80
                and rule_zone_chars < 6000
            ):
                holdings.append({
                    "number": None,
                    "qualifier": None,
                    "text": text,
                    "block_index": block.block_index,
                })
                rule_zone_chars += len(text)
                continue
            rule_zone_open = False
        if catchwords and not block.was_bold and len(text) > 80:
            facts.append({"text": text, "block_index": block.block_index})

    return {
        "catchwords": catchwords,
        "facts_summary": facts,
        "holdings": holdings,
        "quaere": quaere,
        "per_judge": per_judge,
    }


# List numbering may lack a space ("(1)Mutwakuda v. ...") and the "v." of the
# case name is often OCR'd as "us." / "vs.".
LIST_ITEM_RE = re.compile(r"^\(?(?P<num>\d{1,2}|[ivx]{1,4})[.)]\s*(?=\S)", re.I)
VERSUS_RE = re.compile(r"\s(?:v|vs|us|u)\.?\s", re.I)
# "In re Smith 5 NLR 12" and "Ex parte Jones" have no versus token, so accept a
# report citation or an SC-minutes reference as evidence of a case entry.
CASE_ENTRY_RE = re.compile(
    r"\(\d{4}\)|\[\d{4}\]|\bS\.?\s?C\.?\s?(?:Minutes|No)|\bin re\b|\bex parte\b"
    r"|\d\s?(?:NLR|N\.\s?L\.\s?R|Sri\s?LR|All\s?ER|A\.?\s?C)\b",
    re.I,
)


def _referred_items(text: str, block_index: int) -> list[dict]:
    """Split one block into case-list entries, whether one per block or many."""
    body = re.split(r":\s*-?", text, 1)[-1] if CASES_REFERRED_RE.match(text) else text
    # Several entries can share a block: "1. A v. B (1985) ... 2. C v. D ...".
    parts = re.split(r"(?:(?<=\.)|(?<=\d))\s+(?=\(?\d{1,2}[.)]\s*\S)", body)
    items = []
    for part in parts:
        part = LIST_ITEM_RE.sub("", part.strip()).strip(" ;.")
        if len(part) > 8 and (VERSUS_RE.search(part) or CASE_ENTRY_RE.search(part)):
            items.append({"text": part, "block_index": block_index})
    return items


def extract_cases_referred(blocks, opinion_start: int | None) -> list[dict]:
    end = headnote_end([block.text for block in blocks], opinion_start)
    referred: list[dict] = []
    active = False
    for block in blocks[:end]:
        if CASES_REFERRED_RE.match(block.text):
            active = True
            referred.extend(_referred_items(block.text, block.block_index))
            continue
        if active:
            items = _referred_items(block.text, block.block_index)
            # Counsel lines and "APPEAL from ..." follow the list; require the
            # block to look like an entry, not merely to contain a citation.
            if items and (
                LIST_ITEM_RE.match(block.text)
                or VERSUS_RE.search(block.text[:70])
                or re.match(r"^(?:in re|ex parte)\b", block.text, re.I)
            ):
                referred.extend(items)
            else:
                active = False
    return referred


# ------------------------------------------------------------- judgment ----

AGREE_RE = re.compile(
    rf"^(?P<judge>[A-Z][A-Za-z.'\- ]+?[,.]?\s?(?:{JUDGE_TITLES}))\s?[.,—-]*\s*I agree\.?$"
)
DISPOSITION_RE = re.compile(
    r"\b(appeals?|applications?|petitions?|actions?|cases?|rules?|convictions?|"
    r"orders?|judgments?|decrees?|complaint)\b[^.]{0,60}?"
    r"\b(allowed|dismissed|refused|discharged|set aside|affirmed|quashed|upheld|"
    r"varied|remitted|granted|acquitted|restored|accordingly)\b",
    re.I,
)
# Vocabulary of the reporter's one-line result ("Relief granted.", "Order
# made absolute.", "Objections overruled.", "Judgment for plaintiff.").
DISPOSITION_KEYWORDS = re.compile(
    r"\b(allowed|dismissed|refu[st]ed|discharged|(?:set|get|net)\s+a?side|"
    r"affirmed|qua-?shed|upheld|varied|remitted|granted|acquitted|restored|"
    r"over\s?ruled|rejected|absolute|sent\s+(?:back|to)|succeeds?|fails?|"
    r"accordingly|ordered|answered|maintainable|compensation|convicted|"
    r"judgment for|declared\s+(?:void|invalid|null)|determined|annulled|"
    r"amended|altered|vacated|reversed|enhanced|suspended|struck\s+(?:off|out)|"
    r"removed|adjourned|reported|referred|issued|directed|appointed|permitted|"
    r"found guilty|entertained|stated|to be\s+(?:listed|furnished)|"
    r"inconsistent|unnecessary|entered|made in favour)\b",
    re.I,
)
# "NIHILL J.-I agree. Application refused." puts the agree line and the
# reporter's result in one block, so strip rather than skip.
AGREE_INLINE_RE = re.compile(
    rf"[?\s]*[A-Z][A-Za-z.'?\- ]{{2,45}}?[,.]?\s?(?:{JUDGE_TITLES})\.?\s?[-—:.,]*\s*"
    rf"I agree\.?",
)
# Counsel's submission, not the court's order.
ARGUMENT_MARKERS = re.compile(
    r"\b(argued|submitted|contended|moves that|moved that|urged|on behalf of the|"
    r"counsel for|was of opinion)\b",
    re.I,
)
REPORTER_LINE_RE = re.compile(r"^[A-Z][^.]{2,120}\.$")
# Costs orders come in many idioms; match the trigger, then return the whole
# sentence it sits in (see _sentence_around) so amounts and payers survive.
COSTS_RE = re.compile(
    r"\bno\s+(?:order|award)\b.{0,45}?costs"
    r"|\b(?:there\s+will\s+be\s+)?no\s+costs\b"
    r"|\bwith\s*,?\s+costs\b"
    r"|\bwithout\s+costs\b"
    r"|\bentitled\b.{0,60}?costs"
    r"|\b(?:must|will|shall|is|are|do|to)\s+(?:personally\s+)?pay\b.{0,80}?costs"
    r"|\b(?:order|direct)\w*\b.{0,60}?pay\b.{0,60}?costs"
    r"|Rs\.?\s?[\d,/.]+\b.{0,30}?\bas\s+costs"
    r"|\bbear\b.{0,40}?costs"
    r"|\bcosts\b.{0,40}?(?:in the cause|abide|follow the event|reserved|taxed)"
    r"|\b(?:fix|award|grant|allow)\w*\b.{0,60}?costs",
    re.I,
)
# A recited lower-court order, not this court's: "...dismissing the application
# before it with costs is set aside".
RECITED_COSTS_RE = re.compile(
    r"costs\b.{0,30}?\bis\s+(?:set aside|varied|affirmed|quashed)", re.I
)
# Sentence splitting must not break on abbreviations or initials.
_ABBREV = re.compile(
    r"\b(?:Rs|No|Nos|s|ss|art|Art|vs|v|Ltd|Co|Cap|J|C\.J|A\.J|Mr|Mrs|Dr|St|"
    r"[A-Z])\.$"
)


def _sentence_around(text: str, start: int, end: int) -> str:
    """The full sentence containing text[start:end], abbreviation-aware."""
    boundaries = [0]
    for match in re.finditer(r"[.;]\s+", text):
        if not _ABBREV.search(text[: match.start() + 1]):
            boundaries.append(match.end())
    left = max((b for b in boundaries if b <= start), default=0)
    right = len(text)
    for match in re.finditer(r"[.;](?:\s+|$)", text):
        if match.start() >= end and not _ABBREV.search(text[: match.start() + 1]):
            right = match.start() + 1
            break
    return text[left:right].strip()
DISSENT_RE = re.compile(r"\bdissent\w*", re.I)


def extract_judgment(blocks, opinion_start: int | None) -> dict:
    paragraphs = [block.text for block in blocks]
    opinions = []
    start = opinion_start if opinion_start is not None else 0
    for index in range(start, len(blocks)):
        judge = _heading_judge(paragraphs[index])
        if judge:
            opinions.append({
                "judge": judge,
                "block_index": blocks[index].block_index,
            })

    agreements = []
    dissents = []
    for block in blocks[start:]:
        agree = AGREE_RE.match(block.text)
        if agree:
            agreements.append({
                "judge": agree["judge"].strip(" ,."),
                "text": block.text,
                "block_index": block.block_index,
            })
        elif DISSENT_RE.search(block.text) and len(block.text) < 200:
            dissents.append({"text": block.text, "block_index": block.block_index})

    disposition = None
    for block in reversed(blocks[-6:]):
        text = AGREE_INLINE_RE.sub("", block.text).strip(" -—.:")
        if not text or AGREE_RE.match(block.text) and not text:
            continue
        if CITATION_RE.search(text):  # trailing footnote block, not a result
            continue
        if len(text) <= 140 and DISPOSITION_KEYWORDS.search(text):
            disposition = text.strip(" .") + "."
            break
    if disposition is None:
        # Result phrased inside a closing paragraph: keep just its sentence.
        for block in reversed(blocks[-4:]):
            match = DISPOSITION_RE.search(block.text)
            if match:
                sentence = _sentence_around(block.text, match.start(), match.end())
                if len(sentence) <= 300 and not ARGUMENT_MARKERS.search(sentence):
                    disposition = sentence
                    break
    if disposition is None:
        # Positional fallback: the reporter's line is the last short,
        # capitalised, full-stop-terminated block that is not an agree line.
        for block in reversed(blocks[-3:]):
            text = AGREE_INLINE_RE.sub("", block.text).strip(" -—.:")
            if (
                text
                and len(text) <= 140
                and REPORTER_LINE_RE.match(text + ("" if text.endswith(".") else "."))
                and not CITATION_RE.search(text)
                and not _heading_judge(text)
                and not ARGUMENT_MARKERS.search(text)
            ):
                disposition = text.strip(" .") + "."
                break

    costs_order = None
    for block in reversed(blocks[-12:]):
        for match in COSTS_RE.finditer(block.text):
            sentence = _sentence_around(block.text, match.start(), match.end())
            if RECITED_COSTS_RE.search(sentence) or len(sentence) > 300:
                continue
            costs_order = sentence
            break
        if costs_order:
            break

    return {
        "opinion_author": opinions[0]["judge"] if opinions else None,
        "opinions": opinions,
        "agreements": agreements,
        "dissents": dissents,
        "disposition": disposition,
        "costs_order": costs_order,
    }


# -------------------------------------------------------- representation ----

# Ranks that may follow the counsel's name before "for the ...".
_COUNSEL_RANK = (
    r"Q\.?\s?[CG]\.?|K\.?\s?C\.?|P\.?C\.?|A\.?-?G\.?|S\.?-?G\.?|C\.?C\.?|"
    r"(?:Senior\s|Deputy\s)?(?:Crown|State) Counsel|D\.?S\.?G\.?|"
    r"(?:Deputy\s|Acting\s)?(?:Attorney|Solicitor)-General"
)
# Constrain the represented party to conventional role words so prose like
# "case stated for the opinion of the Supreme Court" cannot match.
_COUNSEL_ROLE = (
    r"[\w()'\- ]{0,40}?"
    r"(?:appellants?|respondents?|petitioners?|plaintiffs?|defendants?|accused|"
    r"applicants?|prisoners?|complainants?|assessees?|assessors?|employers?|"
    r"employees?|workmen|workman|unions?|intervenients?|claimants?|creditors?|"
    r"debtors?|insolvents?|objectors?|Crown|State|Republic|Attorney-General)"
    r"[\w()'\- ]{0,30}?"
)
COUNSEL_RE = re.compile(
    rf"(?P<names>[A-Z][A-Za-z.'\- ]{{1,60}}?"
    rf"(?:,\s?(?:{_COUNSEL_RANK}))?"
    rf"(?:,?\s?\(?with\s(?:him\s|her\s)?[^;()]{{2,120}}?\)?)?)"
    rf",?\s+for (?:the\s)?(?P<role>{_COUNSEL_ROLE})(?=[.;,:]|$)"
)
AMICUS_RE = re.compile(
    rf"(?P<names>[A-Z][A-Za-z.'\- ]{{1,60}}?(?:,\s?(?:{_COUNSEL_RANK}))?)"
    rf",?\s+(?:appears\s+|appearing\s+)?as amicus curiae",
)


def extract_counsel(blocks, opinion_start: int | None) -> list[dict]:
    end = opinion_start if opinion_start is not None else min(len(blocks), 20)
    counsel = []
    for block in blocks[:end]:
        if len(block.text) > 420:
            continue
        for match in COUNSEL_RE.finditer(block.text):
            counsel.append({
                "name": re.sub(r"\s+", " ", match["names"]).strip(" ,"),
                "represented_role": match["role"].strip().lower(),
                "block_index": block.block_index,
            })
        for match in AMICUS_RE.finditer(block.text):
            counsel.append({
                "name": re.sub(r"\s+", " ", match["names"]).strip(" ,"),
                "represented_role": "amicus curiae",
                "block_index": block.block_index,
            })
    return counsel


# ---------------------------------------------------------- authorities ----

# Longer alternatives first so e.g. "I.T.C." wins over "T.C.".
_REPORTERS = (
    r"Fundamental Rights? Decisions?|Times of Ceylon(?:\s+Law Reports)?|"
    r"N\.?\s?L\.?\s?R\.?|Sri\s?L\.?\s?R\.?|S\.?\s?L\.?\s?R\.?|C\.?\s?L\.?\s?W\.?|"
    r"S\.?\s?C\.?\s?C\.?|F\.?\s?R\.?\s?D\.?|App\.?\s?Cas\.?|All\s?E\.?\s?R\.?|"
    r"A\.?\s?E\.?\s?R\.?|W\.?\s?L\.?\s?R\.?|K\.?\s?B\.?(?:\s?D\.?)?|"
    r"Q\.?\s?B\.?(?:\s?D\.?)?|L\.?\s?J\.?\s?Ch\.?|"
    r"Ch(?:ancery)?\.?\s?D(?:iv(?:ision)?)?\.?,?|Ch\.?|"
    r"I\.?\s?T\.?\s?C\.?|T\.?\s?C\.?|T\.?\s?R\.?|H\.?\s?L\.?|A\.?\s?C\.?|"
    r"Cal\.?|Mad(?:ras)?\.?|Bom(?:bay)?\.?|L\.?\s?R\.?"
)
CITATION_RE = re.compile(
    rf"(?:[\[(]\s?\d{{4}}\s?[\])]\s?)?\d{{1,3}}\s?(?:{_REPORTERS})\s?,?\s?(?:at\s+p{{1,2}}\.?\s?)?\d+"
)
# Indian reports put the year next to the reporter: "AIR 1958 S.C. 538",
# "1952 A.I.R. Madras 605".
AIR_CITATION_RE = re.compile(
    r"\bA\.?\s?I\.?\s?R\.?,?\s?\d{4}\s?[A-Z][A-Za-z. ]{0,14}?\d+"
    r"|\b\d{4}\s?A\.?\s?I\.?\s?R\.?,?\s?[A-Z][A-Za-z. ]{0,14}?\d+"
)
CASE_NAME_RE = re.compile(
    r"([A-Z][A-Za-z.'\- ]{1,60}\sv\.?\s[A-Z][A-Za-z.'\- ]{1,60})"
)
TREATMENTS = (
    ("not followed", re.compile(r"\bnot follow", re.I)),
    ("overruled", re.compile(r"\boverrul", re.I)),
    ("distinguished", re.compile(r"\bdistinguish", re.I)),
    ("approved", re.compile(r"\bapprov", re.I)),
    ("applied", re.compile(r"\bappli(?:ed|es)\b", re.I)),
    ("followed", re.compile(r"\bfollow", re.I)),
)
# Title words may open with "(" and include lowercase connectors, so
# "Indian and Pakistani Residents (Citizenship) Act" survives whole.
LEGISLATION_RE = re.compile(
    r"(?P<title>(?:(?:[A-Z(][A-Za-z'()\-]*|and|of|for|the)\s+){0,9}"
    r"(?:Ordinance|Act|Code|Constitution|Order[- ]in[- ]Council|Regulations?|Rules))"
    r"(?:\s*[,(]?\s*(?P<number>No\.?\s?\d+\s?of\s?\d{4}|Cap\.?\s?\d+)\)?)?"
)
_TITLE_STOPWORDS = {"The", "This", "That", "Said", "A", "An", "and", "of", "for", "the"}


def _clean_legislation_title(title: str) -> str | None:
    words = title.split()
    # Drop unbalanced leading fragments ("Special Provisions) Act") and
    # leading articles/connectors.
    while words:
        joined = " ".join(words)
        if joined.count(")") > joined.count("("):
            words.pop(0)
        elif joined.count("(") > joined.count(")") and words[0].startswith("("):
            words[0] = words[0].lstrip("(")
            if not words[0]:
                words.pop(0)
        elif words[0] in _TITLE_STOPWORDS:
            words.pop(0)
        else:
            break
    if len(words) < 2:
        return None
    return " ".join(words)
PROVISION_RE = re.compile(
    r"\b(?P<kind>ss?|sections?|articles?|rules?|regulations?)\.?\s?"
    r"(?P<ref>\d+[A-Za-z]?(?:\s?\(\d+\))*(?:\s?\([a-z]\))*)",
    re.I,
)
PROVISION_KIND = {
    "s": "section", "ss": "section", "section": "section", "sections": "section",
    "article": "article", "articles": "article", "rule": "rule", "rules": "rule",
    "regulation": "regulation", "regulations": "regulation",
}


def _treatment_near(text: str, position: int) -> str:
    window = text[max(0, position - 120): position + 120]
    for label, pattern in TREATMENTS:
        if pattern.search(window):
            return label
    return "referred"


def extract_authorities(blocks) -> dict:
    cases: list[dict] = []
    legislation: list[dict] = []
    seen_cases: set[tuple] = set()
    seen_legislation: set[tuple] = set()

    for block in blocks:
        text = block.text
        citation_matches = list(CITATION_RE.finditer(text)) + list(
            AIR_CITATION_RE.finditer(text)
        )
        for match in citation_matches:
            citation = re.sub(r"\s+", " ", match.group(0)).strip()
            preceding = text[max(0, match.start() - 90): match.start()]
            name_match = None
            for name_match in CASE_NAME_RE.finditer(preceding):
                pass  # keep the closest preceding "A v. B"
            case_name = name_match.group(1).strip(" .,") if name_match else None
            key = (case_name, citation)
            if key in seen_cases:
                continue
            seen_cases.add(key)
            cases.append({
                "case_name": case_name,
                "citation": citation,
                "treatment": _treatment_near(text, match.start()),
                "block_index": block.block_index,
            })

        for match in LEGISLATION_RE.finditer(text):
            title = _clean_legislation_title(
                re.sub(r"\s+", " ", match["title"]).strip()
            )
            if title is None:
                continue
            number = re.sub(r"\s+", " ", match["number"]).strip() if match["number"] else None
            provisions = []
            window = text[match.end(): match.end() + 160]
            for prov in PROVISION_RE.finditer(window):
                kind = PROVISION_KIND.get(prov["kind"].lower().rstrip("."), "section")
                provisions.append({"provision_type": kind, "provision": prov["ref"].strip()})
            key = (title, number)
            if key in seen_legislation:
                continue
            seen_legislation.add(key)
            legislation.append({
                "title": title,
                "instrument_number": number,
                "provisions": provisions,
                "block_index": block.block_index,
            })
    return {"cases_cited": cases, "legislation": legislation}


# -------------------------------------------------------------- quality ----

def extract_quality(
    html: str, parsed: ParsedJudgment, decision_date: str | None, folder_year: int
) -> dict:
    decision_year = int(decision_date[:4]) if decision_date else None
    return {
        "has_page_missed": parsed.has_page_missed,
        "missing_page_locations": parsed.missing_page_locations,
        "has_encoding_errors": "�" in html or "�" in parsed.text,
        "has_malformed_tags": (
            html.count("</font>") > html.count("<font")
            or html.count("</span>") > html.count("<span")
        ),
        "date_conflict": (
            decision_year is not None and abs(decision_year - folder_year) > 1
        ),
    }


# ---------------------------------------------------------------- record ----

def build_record(path: Path, meta: dict, parsed: ParsedJudgment, bucket: str) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    frame = extract_frame(html, parsed.page_title, meta["file"])
    paragraphs = parsed.paragraphs

    bench, deciding_court = extract_bench(paragraphs)
    opinion_start = _opinion_start(paragraphs)
    details = extract_case_details(paragraphs, frame["decision_date"])
    fingerprint = meta.get("fingerprint", {})
    judgment = extract_judgment(parsed.blocks, opinion_start)

    # Cross-check: the opinion author should appear on the bench. A mismatch
    # flags a suspect extraction in one of the two fields.
    author = judgment["opinion_author"] or ""
    author_surname = re.sub(
        rf",?\s?(?:{JUDGE_TITLES})\.?$", "", author
    ).strip().split(" ")[-1].lower()
    def _on_bench(surname: str) -> bool:
        for judge in bench:
            name = judge["name"].lower()
            if surname in name:
                return True
            # Tolerate OCR spelling drift (Canekeratne vs Canakeratne).
            for word in name.replace(".", " ").split():
                if SequenceMatcher(None, surname, word).ratio() >= 0.8:
                    return True
        return False

    author_not_on_bench = bool(
        author and author != "The Court" and bench and not _on_bench(author_surname)
    )

    year, number = meta["file"].replace(".html", "").split("/")
    return {
        "identity": {
            "case_id": f"LKSC-{year}-{number}",
            "database": "LKSC",
            "database_court": "Supreme Court of Sri Lanka",
            "deciding_court": deciding_court or "Supreme Court",
            "case_name_raw": frame["case_name_raw"],
            "neutral_citation": frame["neutral_citation"],
        },
        "report": {
            "series": frame["series"] or meta.get("report_series"),
            "reported_year": frame["reported_year"],
            "volume": frame["volume"],
            "start_page": frame["start_page"],
            "printed_pages": parsed.page_numbers,
        },
        "dates": {
            "decision_date": frame["decision_date"],
            "decision_date_raw": frame["decision_date_raw"],
            "hearing_dates": details.pop("hearing_dates"),
        },
        "case_details": details,
        "parties": extract_parties(
            frame["case_name_raw"], paragraphs, details["proceeding_type"]
        ),
        "bench": bench,
        "headnote": {
            **extract_headnote(parsed.blocks, opinion_start),
            "cases_referred_to": extract_cases_referred(parsed.blocks, opinion_start),
        },
        "representation": {
            "counsel": extract_counsel(parsed.blocks, opinion_start),
            "cur_adv_vult": bool(fingerprint.get("has_cur_adv_vult", False)),
        },
        "judgment": judgment,
        "authorities": extract_authorities(parsed.blocks),
        "layout": {
            "category": meta.get("category"),
            "bucket": bucket,
            "confidence": meta.get("confidence"),
            "opinion_start_block": opinion_start,
        },
        "provenance": {
            "file": meta["file"],
            "source_url": frame["source_url"],
            "build_source": frame["build_source"],
            "source_batch": frame["source_batch"],
            "content_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        },
        "quality": {
            **extract_quality(html, parsed, frame["decision_date"], int(year)),
            "author_not_on_bench": author_not_on_bench,
        },
        "blocks": [block.to_dict() for block in parsed.blocks],
    }
