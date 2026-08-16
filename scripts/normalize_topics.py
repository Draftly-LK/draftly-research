"""Normalize the 20 conveyancing topic files into machine-readable rule tables.

Each `data/legal-sources/topics/NN-slug.md` has a consistent shape
(`# Topic NN: Name`, `## Purpose`, `## Source IDs` table, `## Status`). This:

  1. Parses every topic file → topic_id, slug, name, purpose, status,
     source_ids+roles.
  2. Writes normalized tables under manifests/:
       - topics.csv          (one row per topic)
       - topic-sources.csv   (long form: topic_id, source_id, role  — the rule edge table)
       - topics.json         (full nested)
  3. Adds/refreshes YAML frontmatter on each topic file (topic_id, slug, name,
     source_ids, keywords) so agents can parse them deterministically. Keywords
     are auto-seeded from the name + purpose (grounded, editable) for the
     rule-based topic router.

Idempotent: re-running replaces existing frontmatter, never duplicates it, and
leaves the prose untouched.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TOPICS = Path("data/legal-sources/topics")
MAN = Path("data/legal-sources/manifests")

STOP = set("""the a an and or of for to in on with by from as at is are be this that
these those such other related including etc its their his her which who whom what
when where how also into over under more most main source sources area follow up
concepts topic notarial deeds deed law laws act acts ordinance ordinances""".split())

FM = re.compile(r"^---\n.*?\n---\n+", re.S)


def section(body: str, name: str) -> str:
    m = re.search(rf"^##\s+{re.escape(name)}\s*\n(.*?)(?=^##\s|\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


def parse(md: Path) -> dict:
    raw = md.read_text(encoding="utf-8", errors="ignore")
    body = FM.sub("", raw)  # ignore any existing frontmatter when parsing
    h1 = re.search(r"^#\s+Topic\s+(\d+):\s*(.+)$", body, re.M)
    topic_id = h1.group(1) if h1 else md.stem[:2]
    name = h1.group(2).strip() if h1 else md.stem
    purpose = re.sub(r"\s+", " ", section(body, "Purpose"))
    status = re.sub(r"\s+", " ", section(body, "Status"))
    sources = [
        {"source_id": sid, "role": role.strip().rstrip(".")}
        for sid, role in re.findall(r"\|\s*(SRC\d+)\s*\|\s*([^|]+?)\s*\|", body)
    ]
    return {
        "topic_id": topic_id, "slug": md.stem, "name": name,
        "purpose": purpose, "status": status, "sources": sources,
    }


def keywords(name: str, purpose: str) -> list[str]:
    kws = [name.lower()]
    seen = {w for k in kws for w in k.split()}
    for w in re.findall(r"[a-z][a-z-]{3,}", (name + " " + purpose).lower()):
        if w not in STOP and w not in seen:
            kws.append(w)
            seen.add(w)
    return kws[:10]


def write_frontmatter(md: Path, t: dict, kws: list[str]) -> None:
    raw = md.read_text(encoding="utf-8", errors="ignore")
    body = FM.sub("", raw).lstrip("\n")
    sids = ", ".join(s["source_id"] for s in t["sources"])
    kw = ", ".join(kws)
    fm = (
        "---\n"
        f'topic_id: "{t["topic_id"]}"\n'
        f"slug: {t['slug']}\n"
        f"name: {t['name']}\n"
        f"source_ids: [{sids}]\n"
        f"keywords: [{kw}]\n"
        "---\n\n"
    )
    md.write_text(fm + body, encoding="utf-8")


def main() -> None:
    topics = []
    for md in sorted(TOPICS.glob("[0-9][0-9]-*.md")):
        t = parse(md)
        t["keywords"] = keywords(t["name"], t["purpose"])
        write_frontmatter(md, t, t["keywords"])
        topics.append(t)

    # topics.csv
    with (MAN / "topics.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["topic_id", "slug", "name", "n_sources", "source_ids", "keywords"])
        for t in topics:
            w.writerow([t["topic_id"], t["slug"], t["name"], len(t["sources"]),
                        ";".join(s["source_id"] for s in t["sources"]),
                        ";".join(t["keywords"])])

    # topic-sources.csv (edge table)
    with (MAN / "topic-sources.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["topic_id", "slug", "source_id", "role"])
        for t in topics:
            for s in t["sources"]:
                w.writerow([t["topic_id"], t["slug"], s["source_id"], s["role"]])

    # topics.json
    (MAN / "topics.json").write_text(
        json.dumps(topics, indent=2, ensure_ascii=False), encoding="utf-8")

    edges = sum(len(t["sources"]) for t in topics)
    print(f"normalized {len(topics)} topics | {edges} topic-source edges")
    print("wrote: topics.csv, topic-sources.csv, topics.json + frontmatter on each topic file")


if __name__ == "__main__":
    main()
