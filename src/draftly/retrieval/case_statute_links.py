from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

from .corpus import sources_for_ui
from .paths import REPO_ROOT

LINKS_CSV = REPO_ROOT / "scripts" / "case-law-statute-linking" / "output" / "resolved_links.csv"


@dataclass(frozen=True)
class CaseStatuteLink:
    case_id: str
    rule_id: str
    citation: str
    source_id: str
    section_number: str
    section_id: str
    statute_title: str
    band: str
    reason: str
    extractor_method: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@lru_cache(maxsize=1)
def load_case_statute_links() -> tuple[CaseStatuteLink, ...]:
    if not LINKS_CSV.exists():
        return ()

    source_titles = {row["source_id"]: row["title"] for row in sources_for_ui()}
    links: list[CaseStatuteLink] = []
    with LINKS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source_id = (row.get("source_id") or "").strip().upper()
            section_number = (row.get("section_number") or "").strip()
            section_id = f"{source_id}:s{section_number}" if source_id and section_number else ""
            links.append(
                CaseStatuteLink(
                    case_id=(row.get("case_id") or "").strip(),
                    rule_id=(row.get("rule_id") or "").strip(),
                    citation=(row.get("citation") or "").strip(),
                    source_id=source_id,
                    section_number=section_number,
                    section_id=section_id,
                    statute_title=source_titles.get(source_id, ""),
                    band=(row.get("band") or "").strip(),
                    reason=(row.get("reason") or "").strip(),
                    extractor_method=(row.get("extractor_method") or "").strip(),
                )
            )
    return tuple(links)


def case_statute_links(
    *,
    case_id: str | None = None,
    source_id: str | None = None,
    band: str | None = None,
    limit: int = 100,
) -> list[CaseStatuteLink]:
    normalized_case_id = case_id.strip().lower() if case_id else None
    normalized_source_id = source_id.strip().upper() if source_id else None
    normalized_band = band.strip().lower() if band else None

    matches: list[CaseStatuteLink] = []
    for link in load_case_statute_links():
        if normalized_case_id and link.case_id.lower() != normalized_case_id:
            continue
        if normalized_source_id and link.source_id != normalized_source_id:
            continue
        if normalized_band and link.band.lower() != normalized_band:
            continue
        matches.append(link)
        if len(matches) >= limit:
            break
    return matches
