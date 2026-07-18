from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EXAM_HEADING_RE = re.compile(
    r"^##\s+.*?\bExamination\b\s*(?:[-\N{EN DASH}\N{EM DASH}]\s*)?"
    r"(?P<session>[A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?P<year>(?:19|20)\d{2})\s*$",
    re.IGNORECASE | re.MULTILINE,
)
QUESTION_HEADING_RE = re.compile(
    r"^##\s+Question\s+(?P<number>\d+)\s*$", re.IGNORECASE | re.MULTILINE
)
SUBQUESTION_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<number>\d+)[.)]\s+", re.MULTILINE)
MARKS_RE = re.compile(r"\s*\*\*\(\s*(?P<marks>\d+)\s+marks?\s*\)\*\*\s*$", re.IGNORECASE)
TOTAL_RE = re.compile(r"^\s*\*\*Total\s*:", re.IGNORECASE | re.MULTILINE)
MARKDOWN_RE = re.compile(r"[*_`>#]+")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class Subquestion:
    number: int
    text: str
    marks: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceHint:
    """An advisory source suggestion, not a retrieval filter or authority claim."""

    source_id: str
    title: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class QuestionAnalysis:
    text: str
    subquestions: tuple[Subquestion, ...]
    subqueries: tuple[str, ...]
    source_hints: tuple[SourceHint, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "subquestions": [item.to_dict() for item in self.subquestions],
            "subqueries": list(self.subqueries),
            "source_hints": [item.to_dict() for item in self.source_hints],
        }


@dataclass(frozen=True)
class ExamQuestionBlock:
    year: int
    session: str
    question_number: int
    text: str
    subquestions: tuple[Subquestion, ...]

    @property
    def number(self) -> int:
        return self.question_number

    @property
    def full_text(self) -> str:
        return self.text

    @property
    def question_id(self) -> str:
        session_slug = re.sub(r"[^a-z0-9]+", "-", self.session.lower()).strip("-")
        return f"{self.year}-{session_slug}-q{self.question_number:02d}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "year": self.year,
            "session": self.session,
            "question_number": self.question_number,
            "text": self.text,
            "subquestions": [item.to_dict() for item in self.subquestions],
        }


@dataclass(frozen=True)
class _TopicRule:
    name: str
    patterns: tuple[str, ...]
    sources: tuple[tuple[str, str], ...]


_TOPIC_RULES = (
    _TopicRule(
        "notarial practice and attestation",
        (
            r"\bnotaries ordinance\b",
            r"\bnotar(?:y|ies)\b.{0,60}\b(?:attest|licen[cs]|practis|title search|interest)\b",
            r"\b(?:attest|licen[cs]|practis)\w*\b.{0,60}\bnotar(?:y|ies)\b",
            r"\bprotocol\b",
        ),
        (
            ("SRC014", "Notaries Ordinance"),
            ("SRC015", "Notaries (Amendment) Act No. 31 of 2022"),
            ("SRC016", "Notaries (Amendment) Act No. 6 of 2024"),
        ),
    ),
    _TopicRule(
        "registration of documents and caveats",
        (
            r"\bregistration of documents\b",
            r"\b(?:register|registered|registration)\w*\b.{0,50}\b(?:deed|instrument)\b",
            r"\b(?:deed|instrument)\b.{0,50}\b(?:register|registered|registration)\w*\b",
            r"\bland registr(?:y|ar)\b",
            r"\bcaveat(?:or)?\b",
            r"\bpresent (?:an )?instrument\b",
        ),
        (
            ("SRC005", "Registration of Documents Ordinance"),
            ("SRC009", "Registration of Documents (Amendment) Act No. 32 of 2022"),
        ),
    ),
    _TopicRule(
        "registration of title",
        (r"\bregistration of title\b", r"\btitle settlement\b", r"\bcadastral\b", r"\bbimsaviya\b"),
        (("SRC011", "Registration of Title Act No. 21 of 1998"),),
    ),
    _TopicRule(
        "apartment ownership and condominium management",
        (r"\bapartment ownership\b", r"\bcondominium\b", r"\bmanagement corporation\b", r"\bsinking fund\b"),
        (
            ("SRC012", "Apartment Ownership Law No. 11 of 1973"),
            ("SRC013", "Apartment Ownership (Special Provisions) Act No. 23 of 2018"),
        ),
    ),
    _TopicRule(
        "wills and testamentary estates",
        (r"\blast will\b", r"\bwills? ordinance\b", r"\bexecutor(?:'s)?\b", r"\badministrator(?:'s)?\b", r"\btestator\b"),
        (
            ("SRC024", "Wills Ordinance"),
            ("SRC026", "Wills (Amendment) Act No. 29 of 2022"),
            ("SRC030", "Civil Procedure Code"),
        ),
    ),
    _TopicRule(
        "powers of attorney and remote execution",
        (r"\bpower of attorney\b", r"\bsign .* abroad\b", r"\bin (?:her|his|their) absence\b"),
        (
            ("SRC017", "Powers of Attorney Ordinance"),
            ("SRC019", "Powers of Attorney (Amendment) Act No. 28 of 2022"),
            ("SRC020", "Powers of Attorney (Amendment) Act No. 3 of 2024"),
        ),
    ),
    _TopicRule(
        "formalities for land transactions and deeds",
        (
            r"\bprevention of frauds\b",
            r"\bformal parts? of a deed\b",
            r"\bdraft(?:ing)? .*\bdeed\b",
            r"\b(?:makes?|validity of)\b.{0,30}\bdeed\b",
            r"\bdeed\b.{0,30}\bvalid\b",
        ),
        (
            ("SRC001", "Prevention of Frauds Ordinance"),
            ("SRC002", "Prevention of Frauds (Amendment) Act No. 30 of 2022"),
            ("SRC003", "Prevention of Frauds (Amendment) Act No. 4 of 2024"),
        ),
    ),
    _TopicRule(
        "stamp duty",
        (r"\bstamp duty\b", r"\bstamp-duty\b", r"\bmode of payment\b"),
        (
            ("SRC034", "Stamp Duty Act No. 43 of 1982"),
            ("SRC035", "Western Province Financial Statute No. 6 of 1990"),
            ("SRC068", "Stamp Duty (Special Provisions) Act No. 12 of 2006"),
            ("SRC069", "Stamp Duty (Special Provisions) (Amendment) Act No. 10 of 2008"),
        ),
    ),
    _TopicRule(
        "state land grants and succession",
        (r"\bland development ordinance\b", r"\bdivisional secretary\b", r"\bappoint a successor\b", r"\bthird schedule\b"),
        (("SRC050", "Land Development Ordinance"),),
    ),
    _TopicRule(
        "foreign ownership restrictions",
        (r"\brestrictions? on alienation\b", r"\bforeign(?:er| citizen| company)?\b", r"\bnon-citizen\b"),
        (
            ("SRC021", "Land (Restrictions on Alienation) Act No. 38 of 2014"),
            ("SRC022", "Land (Restrictions on Alienation) (Amendment) Act No. 21 of 2018"),
        ),
    ),
    _TopicRule(
        "intestate inheritance",
        (r"\bintestate\b", r"\bdevolution of title\b", r"\bpedigree\b", r"\bshares? presently owned\b", r"\bheirs?\b"),
        (("SRC004", "Matrimonial Rights and Inheritance Ordinance No. 15 of 1876"),),
    ),
    _TopicRule(
        "partition",
        (r"\bpartition (?:law|case|deed|plan)\b", r"\bdeed of partition\b"),
        (("SRC027", "Partition Law No. 21 of 1977"),),
    ),
    _TopicRule(
        "prescription",
        (r"\bprescriptive rights?\b", r"\bprescription ordinance\b", r"\badverse possession\b"),
        (("SRC071", "Prescription Ordinance"),),
    ),
)

_CORPUS_GAP_RULES = (
    (
        re.compile(r"\b(?:coastal zone|coast conservation|coastal resource)\b", re.IGNORECASE),
        "The corpus does not contain the coastal-zone enactment and approval rules needed for this part.",
    ),
    (
        re.compile(
            r"\b(?:pedigree|devolution of title|shares? presently owned|calculate .*?shares?|intestate shares?)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "The inheritance source has interleaved two-column OCR in key share provisions; a verified transcription is required before calculating ownership shares.",
    ),
    (
        re.compile(
            r"\bstamp duty\b.*\b(?:galle|southern province)\b|"
            r"\b(?:galle|southern province)\b.*\bstamp duty\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "The corpus does not contain a verified Southern Province stamp-duty rate and payment source.",
    ),
    (
        re.compile(
            r"\bstamp duty\b.*\b(?:anuradhapura|north central province)\b|"
            r"\b(?:anuradhapura|north central province)\b.*\bstamp duty\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "The corpus does not contain a verified North Central Province stamp-duty rate and payment source.",
    ),
    (
        re.compile(
            r"\b(?:draft|draw up)\b.{0,80}\b(?:clause|covenant|schedule|deed)\b|\bdrafting rules\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "The corpus has statutes but no lawyer-verified deed template or drafting-model source for this part.",
    ),
)


def parse_question_file(path: str | Path) -> list[ExamQuestionBlock]:
    """Parse Markdown exam papers into deterministic question blocks."""

    source_path = Path(path)
    document = source_path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    exams = list(EXAM_HEADING_RE.finditer(document))
    questions = list(QUESTION_HEADING_RE.finditer(document))
    if not questions:
        return []

    blocks: list[ExamQuestionBlock] = []
    exam_index = -1
    for index, question_match in enumerate(questions):
        while exam_index + 1 < len(exams) and exams[exam_index + 1].start() < question_match.start():
            exam_index += 1
        if exam_index < 0:
            raise ValueError(f"Question heading before examination metadata in {source_path}")

        candidate_ends = [questions[index + 1].start() if index + 1 < len(questions) else len(document)]
        if exam_index + 1 < len(exams):
            candidate_ends.append(exams[exam_index + 1].start())
        end = min(candidate_ends)
        body = _trim_block(document[question_match.end() : end])
        exam = exams[exam_index]
        blocks.append(
            ExamQuestionBlock(
                year=int(exam.group("year")),
                session=WHITESPACE_RE.sub(" ", exam.group("session")).strip(),
                question_number=int(question_match.group("number")),
                text=body,
                subquestions=extract_subquestions(body),
            )
        )
    return blocks


def extract_subquestions(text: str) -> tuple[Subquestion, ...]:
    """Extract top-level numbered parts while retaining multiline content."""

    matches = [match for match in SUBQUESTION_RE.finditer(text) if not match.group("indent")]
    if not matches:
        return ()

    total_match = TOTAL_RE.search(text)
    content_end = total_match.start() if total_match else len(text)
    result: list[Subquestion] = []
    for index, match in enumerate(matches):
        if match.start() >= content_end:
            break
        end = matches[index + 1].start() if index + 1 < len(matches) else content_end
        raw_text = text[match.end() : end].strip()
        mark_match = MARKS_RE.search(raw_text)
        marks = int(mark_match.group("marks")) if mark_match else None
        if mark_match:
            raw_text = raw_text[: mark_match.start()].rstrip()
        result.append(
            Subquestion(
                number=int(match.group("number")),
                text=_trim_block(raw_text),
                marks=marks,
            )
        )
    return tuple(result)


def analyze_question(text: str) -> QuestionAnalysis:
    """Create a deterministic, advisory retrieval plan for an exam question."""

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    subquestions = extract_subquestions(normalized_text)
    context = _question_context(normalized_text)
    query_parts = subquestions or (Subquestion(number=1, text=normalized_text),)

    subqueries: list[str] = []
    for part in query_parts:
        query = _plain_text(part.text)
        if context and context.lower() not in query.lower():
            query = f"{query} Context: {context}"
        if query and query not in subqueries:
            subqueries.append(query)

    hint_text = " ".join(part.text for part in query_parts)
    lowered = _plain_text(hint_text).lower()
    hints: list[SourceHint] = []
    seen_sources: set[str] = set()
    for rule in _TOPIC_RULES:
        if not any(re.search(pattern, lowered, re.IGNORECASE) for pattern in rule.patterns):
            continue
        for source_id, title in rule.sources:
            if source_id in seen_sources:
                continue
            seen_sources.add(source_id)
            hints.append(SourceHint(source_id=source_id, title=title, reason=f"Matched {rule.name}."))

    return QuestionAnalysis(
        text=normalized_text,
        subquestions=subquestions,
        subqueries=tuple(subqueries),
        source_hints=tuple(hints),
    )


def known_corpus_gaps(text: str) -> tuple[str, ...]:
    """Return inventory-backed limitations without inferring substantive law."""

    return tuple(message for pattern, message in _CORPUS_GAP_RULES if pattern.search(text))


def is_supported_domain_question(text: str) -> bool:
    legal_terms = re.compile(
        r"\b(?:act|amendment|apartment|attest|caveat|condominium|deed|executor|gift|heir|"
        r"inheritance|instrument|land|lease|law|mortgage|notar|ordinance|partition|power of attorney|"
        r"prescription|property|registr|stamp duty|statute|succession|testator|title|transfer|will)\w*\b",
        re.IGNORECASE,
    )
    return bool(legal_terms.search(text))


def _question_context(text: str) -> str:
    first = next((match for match in SUBQUESTION_RE.finditer(text) if not match.group("indent")), None)
    if not first:
        return ""
    context = _plain_text(text[: first.start()])
    return context[:600].rstrip()


def _plain_text(text: str) -> str:
    without_marks = MARKS_RE.sub("", text.strip())
    without_total = TOTAL_RE.split(without_marks, maxsplit=1)[0]
    return WHITESPACE_RE.sub(" ", MARKDOWN_RE.sub("", without_total)).strip(" -")


def _trim_block(text: str) -> str:
    value = text.strip()
    value = re.sub(r"(?:\n\s*---\s*)+$", "", value).rstrip()
    return value


QuestionBlock = ExamQuestionBlock
QueryPlan = QuestionAnalysis


__all__ = [
    "ExamQuestionBlock",
    "QuestionBlock",
    "QuestionAnalysis",
    "QueryPlan",
    "SourceHint",
    "Subquestion",
    "analyze_question",
    "extract_subquestions",
    "is_supported_domain_question",
    "known_corpus_gaps",
    "parse_question_file",
]
