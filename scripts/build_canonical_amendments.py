"""Build canonical trees for the amending Acts, from their own HTML.

The amending Act is a separate statute with its own sections, and LankaLaw
publishes many of them with the same semantic markup as the consolidated
statutes. `build_canonical_statutes.py` only walks the statutes folder, so those
pages were fetched and then never parsed.

An amending Act differs from a principal one in what the output has to say about
it. It amends something, so the document records what it amends rather than what
amended it, and `amendments` is meaningless here. Its operative sections are the
instructions that produced the consolidated text, which is what makes them worth
holding: `operation` on an amendment event is `unknown` everywhere in the corpus
precisely because nobody has read these.

    uv run python scripts/build_canonical_amendments.py
    uv run python scripts/build_canonical_amendments.py --number 45 --year 1982 --show
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_canonical_statutes import (  # noqa: E402
    LONG_TITLE,
    parse,
    quality_flags,
    read_csv,
    source_location,
    text_of,
)

HTML_DIR = REPO_ROOT / "data/legal-sources/library/amendments/html"
REPORT = REPO_ROOT / "data/processed/lankalaw-amendment-downloads.csv"
OUT_DIR = REPO_ROOT / "data/processed/canonical-amendments"

# What an amending section does, and to what. The heading usually states it
# outright ("Insertion of new section 7A in the principal enactment"); the
# operative words are the fallback ("is hereby repealed", "substituted therefor").
OPERATIONS = (
    ("insert", re.compile(r"(?:insertion|inserted?)", re.IGNORECASE)),
    ("repeal_and_substitute", re.compile(r"repealed[^.]{0,80}substitut", re.IGNORECASE)),
    ("substitute", re.compile(r"(?:substitution|substituted?|replacement|replaced)", re.IGNORECASE)),
    ("repeal", re.compile(r"(?:repeal|repealed)", re.IGNORECASE)),
    ("amend", re.compile(r"(?:amendment|amended)", re.IGNORECASE)),
)
TARGET_SECTIONS = re.compile(
    r"sections?\s+(\d{1,3}[A-Z]{0,2}(?:\s*(?:,|and|to)\s*\d{1,3}[A-Z]{0,2})*)", re.IGNORECASE
)
SECTION_TOKEN = re.compile(r"\d{1,3}[A-Z]{0,2}")
PRINCIPAL = re.compile(r"principal\s+enactment", re.IGNORECASE)

# An amending section says so in a set formula. Matching a loose verb anywhere in
# the section made the short-title section an amendment (because it cites the
# "(Amendment) Act") and made a transitional saving one too. The heading form and
# the operative formula are both accepted; nothing else is.
AMENDING_HEADING = re.compile(
    r"^\s*(?:amendment|insertion|repeal|substitution|replacement|addition)\s+of\b", re.IGNORECASE
)
AMENDING_FORMULA = re.compile(
    r"(?:is|are)\s+hereby\s+(?:amended|inserted|repealed|substituted|added)"
    r"|shall\s+have\s+effect\s+as\s+section"
    r"|there\s+shall\s+be\s+substituted",
    re.IGNORECASE,
)
SHORT_TITLE = re.compile(r"^\s*short\s+title", re.IGNORECASE)
# "shall have effect as section 12A and section 12B of that enactment"
INSERTED_AS = re.compile(
    r"(?:have\s+effect\s+as|inserted\s+as)\s+((?:section\s+\d{1,3}[A-Z]{0,2}"
    r"(?:\s*(?:,|and)\s*(?:section\s+)?\d{1,3}[A-Z]{0,2})*))",
    re.IGNORECASE,
)
# The opening of an inserted provision inside the amending section's prose:
# "12A (1) There shall be established ..." or a bare "12B."
INSERTED_OPEN = re.compile(r"^(\d{1,3}[A-Z]{1,2})\s*\.?\s*(?:\(\s*(\d{1,3}[A-Z]?)\s*\)\s*)?(.*)$",
                           re.DOTALL)


def subtree_text(node: dict) -> str:
    """A node's own text plus every descendant's, for reading an instruction."""
    parts = [node.get("heading", ""), node.get("text", "")]
    for child in node.get("children", []):
        parts.append(subtree_text(child))
    return " ".join(p for p in parts if p)


def join_split_labels(nodes: list[dict]) -> list[dict]:
    """Rejoin a provision the source split across two blocks under one label.

    "by the substitution in paragraph-" / "(b) of that subsection for the words"
    is one paragraph (b) broken over two cells, and came back as two (b) nodes.
    """
    joined: list[dict] = []
    for node in nodes:
        previous = joined[-1] if joined else None
        if (
            previous
            and previous.get("type") == node.get("type")
            and previous.get("number")
            and previous.get("number") == node.get("number")
            and (previous.get("text") or "").rstrip().endswith("-")
        ):
            previous["text"] = (previous["text"].rstrip().rstrip("-").rstrip()
                                + " (" + node["number"] + ") " + (node.get("text") or "")).strip()
            previous["raw_text"] = (previous.get("raw_text", "") + " " + node.get("raw_text", "")).strip()
            previous["cross_references"] = (previous.get("cross_references") or []) + (
                node.get("cross_references") or [])
            previous["join_note"] = (
                "The source broke this paragraph across two blocks and repeated its label; the "
                "halves are joined here."
            )
            previous.setdefault("children", []).extend(node.get("children", []))
            continue
        joined.append(node)
        node["children"] = join_split_labels(node.get("children", []))
    return joined


def regroup_definitions(nodes: list[dict]) -> list[dict]:
    """Put definitions under the paragraph that introduces them.

    An amending paragraph "(a) by the insertion ... of the following new
    definitions" is followed by those definitions and then by paragraphs (b) and
    (c). DEPTH ranks a definition above a paragraph, so (b) and (c) nested inside
    the last definition instead of continuing the lettered run. Rather than move
    `definition` in DEPTH -- 97 definitions across the corpus legitimately own
    lettered children -- the run is repaired where it is seen to break.
    """
    out: list[dict] = []
    for node in nodes:
        node["children"] = regroup_definitions(node.get("children", []))
        if node.get("type") != "definition" or not node.get("children"):
            out.append(node)
            continue
        # Letters already used at this level; a child continuing that run does
        # not belong to the definition.
        used = [n.get("number") for n in out if n.get("type") == "paragraph"]
        keep, promote = [], []
        for child in node["children"]:
            label = str(child.get("number") or "")
            if child.get("type") == "paragraph" and used and label > max(used):
                promote.append(child)
            else:
                (promote if promote else keep).append(child)
        node["children"] = keep
        out.append(node)
        out.extend(promote)
    # A definition that follows a paragraph belongs to it.
    grouped: list[dict] = []
    for node in out:
        if (node.get("type") == "definition" and grouped
                and grouped[-1].get("type") == "paragraph"):
            grouped[-1].setdefault("children", []).append(node)
            continue
        grouped.append(node)
    return grouped


def restructure_insertions(node: dict, targets: list[str], principal: str) -> list[dict]:
    """Rebuild the provisions an amending section inserts as real section trees.

    The inserted text arrives flattened: "12A (1) There shall be established ..."
    lands as a loose text node, its subsections (2) and (3) as siblings of it, and
    the next inserted section's opener as another loose node further down. Read
    linearly the result claims the amending section has subsections (1) to (3)
    twice over, and a reference to "subsection (1)" inside section 12A resolves
    against the amending Act rather than the principal one.

    Returns the provisions it lifted out, and leaves `node["children"]` holding
    only what genuinely belongs to the amending section.
    """
    from build_canonical_statutes import cross_references

    from build_canonical_statutes import nest

    if not node.get("children"):
        return []

    # The inserted text is linear in the source; the tree it arrived in is an
    # artefact of reading it. "12B." came back as a child of the subsection
    # before it, so a scan of the section's own children never saw it. Flatten to
    # document order, split at each opener, and re-nest each provision.
    flat: list[dict] = []

    def walk(nodes: list[dict]) -> None:
        for child in nodes:
            kids = child.pop("children", [])
            flat.append(child)
            walk(kids)

    walk(node["children"])

    opens: list[tuple[int, str, str, str]] = []
    for index, child in enumerate(flat):
        if child["type"] != "text" or child.get("number"):
            continue
        match = INSERTED_OPEN.match((child.get("text") or "").strip())
        if match and match.group(1) in targets:
            opens.append((index, match.group(1), match.group(2) or "", match.group(3).strip()))
    if not opens:
        node["children"] = nest(flat)
        return []
    children = flat

    # The heading of an inserted section is printed just before its number:
    # "... shall have effect as section 12A ...: - Establishment of a Fund"
    # then "12A (1) There shall be established ...".
    def looks_like_heading(candidate: str) -> bool:
        return (3 < len(candidate) <= 140 and "," not in candidate
                and candidate[:1].isupper() and not candidate[:1].isdigit())

    def heading_before(index: int) -> tuple[str, dict | None]:
        """(heading, node to trim it from)."""
        if index == 0:
            tail = (node.get("text") or "").rstrip()
            cut = max(tail.rfind(":-"), tail.rfind(": -"), tail.rfind(": - "))
            candidate = tail[cut + 2:].strip(' -"') if cut >= 0 else ""
            return (candidate, node) if looks_like_heading(candidate) else ("", None)
        # The heading of a later inserted section is the closing sentence of the
        # block before it: "... members of the Board. Audit of Accounts of the
        # Fund." then "12B. (1) ...".
        previous = flat[index - 1]
        text = (previous.get("text") or "").rstrip()
        # The heading may be a block of its own ("Audit of Accounts of the
        # Fund.") or the closing sentence of the block before.
        if not previous.get("number") and looks_like_heading(text.strip(' -".')):
            return text.strip(' -".'), previous
        sentences = [s.strip() for s in re.split(r"(?<=\.)\s+", text) if s.strip()]
        if len(sentences) < 2:
            return "", None
        candidate = sentences[-1].strip(' -".')
        return (candidate, previous) if looks_like_heading(candidate) else ("", None)

    provisions, consumed = [], set()
    for order, (index, number, first_sub, remainder) in enumerate(opens):
        end = opens[order + 1][0] if order + 1 < len(opens) else len(children)
        heading, trim_from = heading_before(index)
        if heading and trim_from is not None:
            source_text = (trim_from.get("text") or "").rstrip()
            position = source_text.rfind(heading)
            if position > 0:
                trim_from["text"] = source_text[:position].rstrip(' -"')
                trim_from["heading_moved_to"] = heading
            elif position == 0 and trim_from is not node:
                # The whole block was the heading; it is not text of its own.
                consumed.add(flat.index(trim_from))
        consumed.update(range(index, end))
        kids = []
        if first_sub:
            kids.append(
                {
                    "type": "subsection",
                    "number": first_sub,
                    "raw_text": children[index].get("raw_text", ""),
                    "text": remainder,
                    "amendment_events": [],
                    "cross_references": cross_references(remainder, principal),
                }
            )
        kids.extend(children[index + 1:end])
        kids = nest(kids)

        # A reference to "subsection (1)" inside an inserted section belongs to
        # that section of the principal Act, not to the amending section.
        def retarget(nodes: list[dict]) -> None:
            for child in nodes:
                for ref in child.get("cross_references") or []:
                    if ref["kind"] == "internal":
                        ref["target_document"] = principal
                        ref["target_section"] = number
                        ref["resolved_within"] = "inserted provision"
                retarget(child.get("children", []))

        retarget(kids)
        provisions.append(
            {
                "type": "inserted_provision",
                "inserted_into": principal,
                "provision": {
                    "type": "section",
                    "number": number,
                    "heading": heading,
                    "raw_text": children[index].get("raw_text", ""),
                    "text": "" if first_sub else remainder,
                    "amendment_events": [],
                    "cross_references": [],
                    "children": kids,
                },
            }
        )

    node["children"] = nest([c for i, c in enumerate(children) if i not in consumed])
    node["inserted_provisions"] = provisions
    return provisions

# Some pages carry no CSS classes at all. Their text still runs
# heading-then-number-then-provision, so it can be read linearly.
PLAIN_SECTION = re.compile(
    r"(?P<heading>[A-Z][^.]{3,90}\.)\s+(?P<number>\d{1,3}[A-Z]{0,2})\.\s+(?=[A-Z(\"])"
)

FILE_NUMBER_YEAR = re.compile(r"^(\d{1,3})-(1[89]\d{2}|20\d{2})-(?P<slug>.+)$")
# "AN ACT TO AMEND THE APARTMENT OWNERSHIP LAW" names the target in the long title.
AMENDS = re.compile(
    r"\bTO\s+AMEND\s+THE\s+(?P<target>[A-Z][A-Z'()\s,.-]{4,90}?)"
    r"(?:\s*,?\s*N[o°]?\.?\s*(?P<number>\d{1,3})\s+OF\s+(?P<year>\d{4}))?\s*(?:\.|$|AND\b)",
    re.IGNORECASE,
)


def parse_plain(page: str, title: str) -> list[dict]:
    """Fallback for a classless page: split the flattened text into sections."""
    from build_canonical_statutes import cross_references

    body = re.sub(r"<(?:script|style)[^>]*>.*?</(?:script|style)>", " ", page, flags=re.S | re.I)
    body = re.sub(r"\s+", " ", __import__("html").unescape(re.sub(r"<[^>]+>", " ", body)))
    marks = list(PLAIN_SECTION.finditer(body))
    if not marks:
        return []
    sections = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(body)
        text = body[mark.end():end].strip()
        sections.append(
            {
                "type": "section",
                "number": mark.group("number"),
                "heading": mark.group("heading").strip(" ."),
                "raw_text": f"{mark.group('number')}. {text}",
                "text": text,
                "amendment_events": [],
                "cross_references": cross_references(text, title),
            }
        )
    return sections


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--number", type=int)
    parser.add_argument("--year", type=int)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    amends_index: dict[tuple[int, int], str] = {}
    for row in read_csv(REPORT) if REPORT.exists() else []:
        if row.get("amends"):
            amends_index[(int(row["instrument_no"]), int(row["instrument_year"]))] = row["amends"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written, totals = 0, collections.Counter()
    for file in sorted(HTML_DIR.glob("*.html")):
        match = FILE_NUMBER_YEAR.match(file.stem)
        if not match:
            continue
        number, year = int(match.group(1)), int(match.group(2))
        if args.number and (number, year) != (args.number, args.year):
            continue

        page = file.read_text(encoding="utf-8", errors="replace")
        title_match = re.search(r"<title[^>]*>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else match.group("slug")
        # Pages fetched through the subscription seat carry a site prefix in the
        # title tag: "Law Lanka Acts - NOTARIES (AMENDMENT) ACT".
        title = re.sub(r"^Law\s*Lanka[^-]*-\s*", "", title, flags=re.IGNORECASE).strip()
        title = title.title() if title.isupper() else title
        body, _chain, long_title, editorial = parse(page, title)
        markup = "semantic classes"
        if not body:
            body, editorial = parse_plain(page, title), []
            markup = "plain markup, read linearly"
        if not body:
            continue

        target = AMENDS.search(long_title or text_of(page)[:600])
        principal_title = (
            re.sub(r"\s+", " ", target.group("target")).strip(" ,.").title()
            if target
            else "the principal enactment"
        )

        instructions = []
        for node in body:
            if node["type"] != "section":
                continue
            heading = node.get("heading", "")
            basis = subtree_text(node)
            # Only a section that states an amending formula is an instruction.
            if SHORT_TITLE.match(heading) or not (
                AMENDING_HEADING.match(heading) or AMENDING_FORMULA.search(basis)
            ):
                continue
            # The heading states the instruction: "Amendment of section 25 of the
            # principal enactment". Reading the whole subtree instead pulls in
            # every section the operative words happen to quote -- the section
            # amending section 10 came back targeting 10, 9, 2, 4 and 3 -- and
            # lets an "insertion" deep in the text override an "amendment"
            # heading. So the heading wins where there is one.
            scope = basis if not AMENDING_HEADING.match(heading) else heading
            operation = next((name for name, pattern in OPERATIONS if pattern.search(scope)), "")
            targets: list[str] = []
            runs = [m.group(1) for m in TARGET_SECTIONS.finditer(scope)]
            # A damaged heading can still lose a target: the section inserting
            # 12A and 12B is headed "Insertion of new section 12A and principal
            # enactment". The operative words name both.
            inserted = INSERTED_AS.search(basis)
            if inserted:
                runs.append(inserted.group(1))
            for run in runs:
                for token in SECTION_TOKEN.findall(run):
                    if token not in targets:
                        targets.append(token)
            # A section that merely mentions a number is not an amending
            # instruction. Without a recognised operation there is nothing to say.
            if not operation:
                continue
            node["amendment_instruction"] = {
                "operation": operation,
                "target_sections": targets,
                "targets_principal_enactment": bool(PRINCIPAL.search(basis)),
                "basis": "heading" if operation and node.get("heading") else "operative text",
            }
            if operation == "insert":
                lifted = restructure_insertions(node, targets, principal_title)
                if lifted:
                    node["amendment_instruction"]["inserts"] = [
                        p["provision"]["number"] for p in lifted
                    ]
            node["children"] = regroup_definitions(join_split_labels(node.get("children", [])))
            # A reference the amending section makes to a section it is amending
            # or inserting, or one it marks "of the principal enactment", is a
            # reference to the principal Act and not to this one.
            instructions.append({"in_section": node["number"], **node["amendment_instruction"]})

        # Which references point at the principal Act rather than this one. Runs
        # over every section, including the transitional ones that carry no
        # instruction: "section 10 of the principal enactment as amended by
        # section 5 of this Act" names one section in each Act, and a
        # reference's verbatim stops at the number, so the sentence is read.
        for node in body:
            if node["type"] != "section":
                continue
            instruction = node.get("amendment_instruction") or {}
            owned = set(instruction.get("target_sections", []) + instruction.get("inserts", []))
            body_text = subtree_text(node)
            of_principal = {
                m.group(1) for m in re.finditer(
                    r"sections?\s+(\d{1,3}[A-Z]{0,2})[^.]{0,40}?of\s+the\s+principal\s+enactment",
                    body_text, re.IGNORECASE)
            }

            def retarget(nodes: list[dict]) -> None:
                for child in nodes:
                    for ref in child.get("cross_references") or []:
                        if ref["kind"] != "internal":
                            continue
                        number_ = str(ref.get("target_section", ""))
                        if (number_ in owned or number_ in of_principal
                                or PRINCIPAL.search(ref.get("verbatim", ""))):
                            ref["target_document"] = principal_title
                            ref["resolved_against"] = "principal enactment"
                    retarget(child.get("children", []))

            retarget([node])

        document = {
            "instrument_id": f"{number}-{year}",
            "title": title,
            "long_title": long_title,
            "citation": {"type": "Act", "number": number, "year": year},
            "instrument_role": "amending",
            "amends": (
                {
                    "title": re.sub(r"\s+", " ", target.group("target")).strip(" ,."),
                    "number": int(target.group("number")) if target.group("number") else None,
                    "year": int(target.group("year")) if target.group("year") else None,
                }
                if target
                else {}
            ),
            "amends_recorded_elsewhere": amends_index.get((number, year), ""),
            "language": "en",
            "edition": {
                "publisher": "lankalaw",
                "kind": "as_enacted",
                "markup": markup,
                "local_path": file.relative_to(REPO_ROOT).as_posix(),
                "caveat": "private republisher, not the Government Printer",
            },
            "amendment_instructions": instructions,
            "verification_status": "unverified",
            "editorial_notes": list({(n["text"], n["anchor_text"]): n for n in editorial}.values()),
            "quality_flags": quality_flags(text_of(page)),
            "source_location": source_location(text_of(page)),
            "body": body,
        }
        (OUT_DIR / f"{number}-{year}.json").write_text(
            json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        written += 1

        def walk(nodes):
            for node in nodes:
                totals[node["type"]] += 1
                walk(node.get("children", []))

        walk(body)
        if args.show:
            print(f"=== No. {number} of {year}: {title}")
            print(f"  amends: {document['amends'] or 'not stated in the long title'}")
            print(f"  sections: {sum(1 for n in body if n['type'] == 'section')}")
            for node in body[:6]:
                print(f"    s.{node.get('number',''):<4} {node.get('heading','')[:50]}")

    if args.number:
        return 0
    print(f"wrote {written} amending Acts to {OUT_DIR.relative_to(REPO_ROOT)}")
    for key in ("section", "subsection", "paragraph", "definition"):
        print(f"  {key:12} {totals[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
