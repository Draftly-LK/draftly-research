from __future__ import annotations

import re
from dataclasses import dataclass

from .models import SectionNode


MAX_SECTION_NUMBER = 300
SECTION_START_RE = re.compile(r"^\s*(?P<num>\d{1,3}[A-Z]?)\.\s+(?P<body>.+?)\s*$")
HEADING_THEN_SECTION_RE = re.compile(
    r"^\s*(?P<head>[A-Z][A-Za-z0-9\s'\"().,/&;\[\]-]{2,140}?)\s+(?P<num>\d{1,3}[A-Z]?)\.\s*(?P<body>.*?)\s*$"
)
SECTION_ONLY_RE = re.compile(r"^\s*(?P<num>\d{1,3}[A-Z]?)\.\s*$")
SUBSECTION_PREFIX_RE = re.compile(
    r"^\(\s*[a-zivxlcdm]+\s*\)\s+[a-z]"
    r"|^\(\s*\d+\s*\)\s*[,;]"
    r"|^[a-z]\)"
)
NOISE_RE = re.compile(r"^(<!--.*-->|#+\s*.+|\d+|[IVXLCDM]+/\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class Boundary:
    line_index: int
    number: str
    heading: str


def parse_sections(
    *,
    source_id: str,
    doc_id: str,
    kind: str,
    title: str,
    act_number: str,
    year: str,
    topics: tuple[str, ...],
    public_source_url: str,
    source_sha256: str,
    text: str,
) -> list[SectionNode]:
    focused = focus_document_text(text, title)
    lines = [line.rstrip() for line in focused.splitlines()]
    boundaries = find_boundaries(lines)
    used: set[str] = set()
    nodes: list[SectionNode] = []

    for pos, boundary in enumerate(boundaries):
        section_id = f"{source_id}:s{boundary.number}"
        if section_id in used:
            continue
        end = boundaries[pos + 1].line_index if pos + 1 < len(boundaries) else len(lines)
        block = "\n".join(lines[boundary.line_index:end]).strip()
        block = normalize_text(block)
        if len(block) < 20:
            continue
        used.add(section_id)
        nodes.append(
            SectionNode(
                section_id=section_id,
                source_id=source_id,
                doc_id=doc_id,
                kind=kind,
                title=title,
                act_number=act_number,
                year=year,
                topics=topics,
                heading=boundary.heading or infer_heading(block),
                text=block,
                public_source_url=public_source_url,
                extraction_confidence="parsed",
                source_sha256=source_sha256,
            )
        )

    if len(nodes) >= 2:
        return apply_aliases(nodes, source_id=source_id, kind=kind, title=title)

    fallback_text = normalize_text(focused)
    return [
        SectionNode(
            section_id=f"{source_id}:doc",
            source_id=source_id,
            doc_id=doc_id,
            kind=kind,
            title=title,
            act_number=act_number,
            year=year,
            topics=topics,
            heading="Document fallback",
            text=fallback_text[:24000],
            public_source_url=public_source_url,
            extraction_confidence="document_fallback",
            source_sha256=source_sha256,
        )
    ]


def apply_aliases(nodes: list[SectionNode], *, source_id: str, kind: str, title: str) -> list[SectionNode]:
    by_id = {node.section_id: node for node in nodes}
    if kind == "amendment":
        for node in nodes:
            for target in amendment_target_sections(node.text):
                alias_id = f"{source_id}:s{target}"
                by_id[alias_id] = clone_node(node, section_id=alias_id, heading=f"Amendment of section {target}")

    for node in nodes:
        for target, heading, text in parenthetical_rule_aliases(node.text, title):
            alias_id = f"{source_id}:s{target}"
            existing = by_id.get(alias_id)
            if existing is None or alias_should_replace(existing.heading, heading):
                by_id[alias_id] = clone_node(node, section_id=alias_id, heading=heading, text=text)

    return list(by_id.values())


def amendment_target_sections(text: str) -> set[str]:
    targets = set()
    for match in re.finditer(r"\bSection\s+(?P<num>\d{1,3}[A-Z]?)\s+of\b", text, flags=re.IGNORECASE):
        window = text[match.start() : match.start() + 420]
        if re.search(r"\b(amended|repealed|substituted|replacement)\b", window, flags=re.IGNORECASE):
            targets.add(match.group("num"))
    for pattern in [
        r"\bReplacement of\s+section\s+(?P<num>\d{1,3}[A-Z]?)\b",
        r"\bAmendment\s+o[fr]\s+section\s+(?P<num>\d{1,3}[A-Z]?)\b",
    ]:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            targets.add(match.group("num"))
    return targets


def parenthetical_rule_aliases(text: str, title: str) -> list[tuple[str, str, str]]:
    if "notaries" not in title.lower():
        return []
    lines = text.splitlines()
    aliases: list[tuple[str, str, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^\s*(?P<head>[A-Z][A-Za-z\s]{3,80}?)\s*\((?P<num>\d{1,3})\)\s+(?P<body>.+)$", line)
        if not match:
            continue
        heading = clean_heading(match.group("head"))
        if "duplicates" not in heading.lower():
            continue
        end = min(len(lines), index + 35)
        block = "\n".join(lines[index:end])
        aliases.append((match.group("num"), heading, normalize_text(block)))
    return aliases


def alias_should_replace(existing_heading: str, new_heading: str) -> bool:
    if "duplicates" in new_heading.lower():
        return True
    if existing_heading.startswith("Amendment of section"):
        return False
    return False


def clone_node(node: SectionNode, *, section_id: str, heading: str, text: str | None = None) -> SectionNode:
    return SectionNode(
        section_id=section_id,
        source_id=node.source_id,
        doc_id=node.doc_id,
        kind=node.kind,
        title=node.title,
        act_number=node.act_number,
        year=node.year,
        topics=node.topics,
        heading=heading,
        text=text if text is not None else node.text,
        public_source_url=node.public_source_url,
        extraction_confidence="parsed_alias",
        source_sha256=node.source_sha256,
        metadata=node.metadata,
    )


def focus_document_text(text: str, title: str) -> str:
    if len(text) < 400_000:
        return text

    key = re.sub(r"\b(ordinance|act|law|code|statute)\b", "", title, flags=re.IGNORECASE).strip()
    key = re.sub(r"\s+", " ", key)
    if len(key) < 5:
        return text[:200_000]

    matches = [match.start() for match in re.finditer(re.escape(key), text, flags=re.IGNORECASE)]
    for start in matches:
        window = text[start : start + 1200]
        if re.search(r"\b(AN ORDINANCE|AN ACT|A LAW|CHAPTER)\b", window, re.IGNORECASE):
            return text[max(0, start - 1200) : start + 160_000]
    if matches:
        start = matches[-1]
        return text[max(0, start - 1200) : start + 160_000]
    return text[:200_000]


def find_boundaries(lines: list[str]) -> list[Boundary]:
    boundaries: list[Boundary] = []
    for index, line in enumerate(lines):
        candidate = detect_boundary(line, lines, index)
        if candidate:
            boundaries.append(candidate)
    return boundaries


def detect_boundary(line: str, lines: list[str], index: int) -> Boundary | None:
    stripped = line.strip()
    if not stripped or is_noise(stripped):
        return None

    match = HEADING_THEN_SECTION_RE.match(stripped)
    if match:
        number = match.group("num")
        body = match.group("body").strip()
        head = clean_heading(match.group("head"))
        if valid_section_number(number) and not looks_like_subsection(body):
            return Boundary(index, number, head)

    match = SECTION_START_RE.match(stripped)
    if match:
        number = match.group("num")
        body = match.group("body").strip()
        if valid_section_number(number) and not looks_like_subsection(body):
            return Boundary(index, number, nearby_heading(lines, index))

    match = SECTION_ONLY_RE.match(stripped)
    if match and valid_section_number(match.group("num")):
        return Boundary(index, match.group("num"), nearby_heading(lines, index))

    return None


def valid_section_number(value: str) -> bool:
    number_match = re.match(r"(\d{1,3})", value)
    return bool(number_match and 0 < int(number_match.group(1)) <= MAX_SECTION_NUMBER)


def looks_like_subsection(body: str) -> bool:
    return bool(SUBSECTION_PREFIX_RE.match(body.strip()))


def nearby_heading(lines: list[str], index: int) -> str:
    fragments: list[str] = []
    for line in reversed(lines[max(0, index - 4) : index]):
        value = clean_heading(line)
        if is_heading_fragment(value):
            fragments.append(value)
        elif fragments:
            break
    fragments.reverse()

    for line in lines[index + 1 : min(len(lines), index + 4)]:
        value = clean_heading(line)
        if is_heading_fragment(value):
            fragments.append(value)
        elif fragments:
            break
    return " ".join(fragments[:3]).strip()


def infer_heading(text: str) -> str:
    for line in text.splitlines()[:4]:
        value = clean_heading(line)
        if is_heading_fragment(value):
            return value[:140]
    return ""


def clean_heading(value: str) -> str:
    value = re.sub(r"^\s*#+\s*", "", value.strip())
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+\d{1,3}[A-Z]?\.\s*$", "", value)
    return value.strip(" .-")


def is_heading_fragment(value: str) -> bool:
    if not value or len(value) > 120:
        return False
    if is_noise(value):
        return False
    if re.search(r"\b(CHAPTER|Cap\.|AN ORDINANCE|AN ACT|A LAW|Ordinance Nos|Act Nos)\b", value, re.IGNORECASE):
        return False
    if re.search(r"\b(shall|may|must|where|when|unless|provided|thereof|hereby)\b", value, re.IGNORECASE):
        return False
    return bool(re.search(r"[A-Za-z]", value))


def is_noise(value: str) -> bool:
    return bool(NOISE_RE.match(value.strip()))


def normalize_text(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = value.replace("â€”", "-")
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"[ \t]+", " ", value)
    return value.strip()
