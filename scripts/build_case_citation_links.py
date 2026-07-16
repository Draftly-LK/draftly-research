"""Build deterministic case-to-statute-section citation edges.

The parser pairs each explicit section expression with an identified registry
law using grammatical adjacency, same-sentence context, or a bounded nearest-
title fallback. Ambiguous or unmatched section expressions can be written to a
separate review queue. No LLM or network service is used.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
LAW_TYPES = {"statute", "amendment"}
CONFIDENCE = {"explicit": 1.0, "same_sentence": 0.8, "nearest_unique": 0.55}

SECTION_RX = re.compile(
    r"\b(?:sections?|secs?\.?|ss?\.?|s\.)\s*"
    r"((?:\d+[A-Za-z]?(?:\s*\([A-Za-z0-9]+\))?"
    r"(?:\s*(?:,|and|or|&|to|-)\s*\d+[A-Za-z]?(?:\s*\([A-Za-z0-9]+\))?)*))",
    re.I,
)
LAW_IDENTITY_RX = re.compile(
    r"\b(?:Act|Ordinance|Law|Statute)\s*(?:No\.?\s*)?(\d+)\s+of\s+(\d{4})\b",
    re.I,
)
DIRECT_AFTER_SECTION_RX = re.compile(
    r"^[\s,;:()\-]*(?:\([A-Za-z0-9]+\)\s*)?"
    r"(?:of|under|in|by|read\s+with|in\s+terms\s+of)"
    r"(?:\s+the|\s+said|\s+aforesaid)?[\s,;:()\-]*$",
    re.I,
)
DIRECT_BEFORE_SECTION_RX = re.compile(
    r"^[\s,;:()\-]*(?:,|under|by|in|of|read\s+with)?[\s,;:()\-]*$",
    re.I,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def law_pattern(title: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", unicodedata.normalize("NFKC", title))
    return r"\b" + r"[^A-Za-z0-9]+".join(map(re.escape, tokens)) + r"\b"


def build_law_matcher() -> list[dict]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(PROCESSED / "source-registry.csv"):
        if row["source_type"] in LAW_TYPES:
            grouped[law_pattern(row["official_title"])].append(row)
    matchers = []
    ignored_anchors = {"act", "law", "ordinance", "amendment", "special", "provisions"}
    for number, (pattern, rows) in enumerate(grouped.items()):
        tokens = [
            token.casefold()
            for token in re.findall(r"[A-Za-z0-9]+", rows[0]["official_title"])
            if token.casefold() not in ignored_anchors
        ]
        anchor = max(tokens, key=len) if tokens else max(
            re.findall(r"[A-Za-z0-9]+", rows[0]["official_title"]), key=len
        ).casefold()
        matchers.append({
            "group": number,
            "anchor": anchor,
            "title_rx": re.compile(pattern, re.I),
            "candidates": rows,
        })
    return matchers


def load_cases() -> list[dict]:
    with (PROCESSED / "cases.jsonl").open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def section_numbers(match: re.Match) -> list[str]:
    values = re.findall(r"\d+[A-Za-z]?(?:\s*\([A-Za-z0-9]+\))?", match.group(1))
    return [re.sub(r"\s+", "", value) for value in values]


def snippet(text: str, start: int, end: int, radius: int = 180) -> str:
    value = text[max(0, start - radius): min(len(text), end + radius)]
    return re.sub(r"\s+", " ", value).strip()[:500]


def sentence_bounds(text: str, start: int, end: int, radius: int = 500) -> tuple[int, int]:
    left_floor = max(0, start - radius)
    right_ceiling = min(len(text), end + radius)
    left = max(text.rfind(".", left_floor, start), text.rfind("\n", left_floor, start))
    right_period = text.find(".", end, right_ceiling)
    right_newline = text.find("\n", end, right_ceiling)
    rights = [value for value in (right_period, right_newline) if value >= 0]
    return (left + 1 if left >= 0 else left_floor, min(rights) + 1 if rights else right_ceiling)


def resolve_law(
    candidates: list[dict[str, str]],
    context: str,
) -> tuple[dict[str, str] | None, str]:
    if len(candidates) == 1:
        return candidates[0], ""
    identified = []
    for law in candidates:
        number = law.get("act_or_ordinance_no", "").strip()
        year = law.get("year", "").strip()
        if not number or not year or year == "0":
            continue
        if re.search(rf"\b(?:No\.?\s*)?{re.escape(number)}\s+of\s+{re.escape(year)}\b", context, re.I):
            identified.append(law)
    if len(identified) == 1:
        return identified[0], ""
    return None, "ambiguous_law_identity"


def choose_law_mention(
    text: str,
    section: re.Match,
    law_mentions: list[dict],
) -> tuple[dict | None, str, str]:
    nearby = [
        mention for mention in law_mentions
        if mention["start"] <= section.end() + 450 and mention["end"] >= section.start() - 450
    ]
    if not nearby:
        return None, "", "no_law_title_within_450_chars"

    explicit = []
    for mention in nearby:
        if section.end() <= mention["start"]:
            gap = text[section.end(): mention["start"]]
            if len(gap) <= 100 and DIRECT_AFTER_SECTION_RX.fullmatch(gap):
                explicit.append(mention)
        elif mention["end"] <= section.start():
            gap = text[mention["end"]: section.start()]
            if len(gap) <= 80 and DIRECT_BEFORE_SECTION_RX.fullmatch(gap):
                explicit.append(mention)
    if explicit:
        explicit.sort(key=lambda item: min(abs(item["start"] - section.end()), abs(section.start() - item["end"])))
        return explicit[0], "explicit", ""

    sentence_start, sentence_end = sentence_bounds(text, section.start(), section.end())
    same_sentence = [
        mention for mention in nearby
        if mention["start"] >= sentence_start and mention["end"] <= sentence_end
    ]
    unique_groups = {mention["group"] for mention in same_sentence}
    if len(unique_groups) == 1 and same_sentence:
        same_sentence.sort(key=lambda item: abs(item["start"] - section.start()))
        return same_sentence[0], "same_sentence", ""

    unique_groups = {mention["group"] for mention in nearby}
    if len(unique_groups) == 1:
        nearby.sort(key=lambda item: min(abs(item["start"] - section.end()), abs(section.start() - item["end"])))
        return nearby[0], "nearest_unique", ""
    return None, "", "multiple_law_titles_in_context"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def build(write_unresolved: bool) -> tuple[list[dict], list[dict]]:
    law_matchers = build_law_matcher()
    identity_map: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(PROCESSED / "source-registry.csv"):
        number = row.get("act_or_ordinance_no", "").strip()
        year = row.get("year", "").strip()
        if row["source_type"] in LAW_TYPES and number and year and year != "0":
            identity_map[(number, year)].append(row)
    cases = load_cases()
    best_edges: dict[tuple[str, str, str], dict] = {}
    unresolved = []

    for count, case in enumerate(cases, 1):
        path = ROOT / case["text_path"]
        text = path.read_text(encoding="utf-8", errors="replace")
        law_mentions = []
        folded_text = text.casefold()
        for law_matcher in law_matchers:
            if law_matcher["anchor"] not in folded_text:
                continue
            for match in law_matcher["title_rx"].finditer(text):
                law_mentions.append({
                    "start": match.start(), "end": match.end(),
                    "group": law_matcher["group"],
                    "candidates": law_matcher["candidates"],
                })
        for identity in LAW_IDENTITY_RX.finditer(text):
            candidates = identity_map.get((identity.group(1), identity.group(2)), [])
            if candidates:
                law_mentions.append({
                    "start": identity.start(), "end": identity.end(),
                    "group": f"identity-{identity.group(1)}-{identity.group(2)}",
                    "candidates": candidates,
                })

        for section in SECTION_RX.finditer(text):
            mention, method, reason = choose_law_mention(text, section, law_mentions)
            evidence = snippet(text, section.start(), section.end())
            if mention is None:
                for number in section_numbers(section):
                    unresolved.append({
                        "case_id": case["case_id"], "citation": case.get("citation", ""),
                        "title": case.get("title", ""), "section": number,
                        "evidence_snippet": evidence, "reason": reason,
                        "review_status": "unresolved",
                    })
                continue

            context = text[max(0, mention["start"] - 250): min(len(text), mention["end"] + 250)]
            law, identity_reason = resolve_law(mention["candidates"], context)
            if law is None:
                for number in section_numbers(section):
                    unresolved.append({
                        "case_id": case["case_id"], "citation": case.get("citation", ""),
                        "title": case.get("title", ""), "section": number,
                        "evidence_snippet": evidence, "reason": identity_reason,
                        "review_status": "unresolved",
                    })
                continue

            for number in section_numbers(section):
                edge = {
                    "case_id": case["case_id"], "source_id": law["source_id"],
                    "section": number, "confidence": f"{CONFIDENCE[method]:.2f}",
                    "confidence_label": method, "evidence_snippet": evidence,
                    "case_citation": case.get("citation", ""),
                    "case_title": case.get("title", ""), "mention_count": "1",
                    "review_status": "unverified",
                }
                key = (case["case_id"], law["source_id"], number.casefold())
                current = best_edges.get(key)
                if current is None:
                    best_edges[key] = edge
                else:
                    current["mention_count"] = str(int(current["mention_count"]) + 1)
                    if float(edge["confidence"]) > float(current["confidence"]):
                        edge["mention_count"] = current["mention_count"]
                        best_edges[key] = edge

        if count % 1000 == 0:
            print(f"processed {count}/{len(cases)} cases", flush=True)

    edges = sorted(best_edges.values(), key=lambda row: (row["case_id"], row["source_id"], row["section"]))
    edge_fields = [
        "case_id", "source_id", "section", "confidence", "confidence_label",
        "evidence_snippet", "case_citation", "case_title", "mention_count", "review_status",
    ]
    write_csv(PROCESSED / "case_statute_section_links.csv", edges, edge_fields)
    if write_unresolved:
        unresolved_fields = [
            "case_id", "citation", "title", "section", "evidence_snippet",
            "reason", "review_status",
        ]
        write_csv(PROCESSED / "unresolved_citations.csv", unresolved, unresolved_fields)
    return edges, unresolved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-unresolved", action="store_true")
    args = parser.parse_args()
    edges, unresolved = build(args.write_unresolved)
    print(f"section_links={len(edges)} unresolved_section_mentions={len(unresolved)}")


if __name__ == "__main__":
    main()
