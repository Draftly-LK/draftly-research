"""Reconcile topic membership using source-registry.csv as the single source of truth.

The registry `topics` column is authoritative. This regenerates, from it:
  - each topic file's `## Source IDs` table + YAML frontmatter
    (Purpose / Status prose and existing role notes are preserved)
  - manifests/topics.csv, topic-sources.csv, topics.json

Run after editing the registry's `topics` column. Idempotent.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPICS = ROOT / "data/legal-sources/topics"
MAN = ROOT / "data/legal-sources/manifests"

STOP = set("""the a an and or of for to in on with by from as at is are be this that
these those such other related including etc its their his her which who whom what
when where how also into over under more most main source sources area follow up
concepts topic notarial deeds deed law laws act acts ordinance ordinances""".split())
FM = re.compile(r"^---\n.*?\n---\n+", re.S)


def section(body: str, name: str) -> str:
    m = re.search(rf"^##\s+{re.escape(name)}\s*\n(.*?)(?=^##\s|\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


def keywords(name: str, purpose: str) -> list[str]:
    kws, seen = [name.lower()], {w for w in name.lower().split()}
    for w in re.findall(r"[a-z][a-z-]{3,}", (name + " " + purpose).lower()):
        if w not in STOP and w not in seen:
            kws.append(w); seen.add(w)
    return kws[:10]


# --- load registry (authoritative) ---
with (MAN / "source-registry.csv").open(encoding="utf-8-sig") as fh:
    reg = list(csv.DictReader(fh))
title = {r["source_id"]: r["official_title"] for r in reg}
topic_members: dict[str, list[str]] = {}
for r in reg:
    for t in re.split(r"[;\s]+", (r.get("topics") or "").strip()):
        if t and t != "00":
            topic_members.setdefault(t.zfill(2), []).append(r["source_id"])

# --- preserve existing role notes (topic_id, source_id) -> role ---
roles = {}
ts_path = MAN / "topic-sources.csv"
if ts_path.exists():
    with ts_path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            roles[(r["topic_id"], r["source_id"])] = r["role"]

slug_by_id = {
    path.stem[:2]: path.stem
    for path in sorted(TOPICS.glob("[0-9][0-9]-*.md"))
}

topics_out = []
for tid in sorted(topic_members):
    slug = slug_by_id.get(tid)
    if not slug:
        print(f"[warn] topic {tid} has sources but no topic file; skipping rewrite")
        continue
    md = TOPICS / f"{slug}.md"
    raw = md.read_text(encoding="utf-8", errors="ignore")
    body = FM.sub("", raw)
    h1 = re.search(r"^#\s+Topic\s+\d+:\s*(.+)$", body, re.M)
    name = h1.group(1).strip() if h1 else slug
    purpose = section(body, "Purpose")
    status = section(body, "Status")

    sids = sorted(set(topic_members[tid]), key=lambda s: int(s[3:]))
    rows = [(s, roles.get((tid, s)) or title.get(s, "").rstrip(".")) for s in sids]

    kw = keywords(name, purpose)
    fm = ("---\n"
          f'topic_id: "{tid}"\n'
          f"slug: {slug}\n"
          f"name: {name}\n"
          f"source_ids: [{', '.join(sids)}]\n"
          f"keywords: [{', '.join(kw)}]\n"
          "---\n\n")
    parts = [f"# Topic {tid}: {name}\n\n## Purpose\n\n{purpose}\n\n## Source IDs\n\n"
             "| Source ID | Role |\n| --- | --- |\n"]
    parts += [f"| {s} | {role}. |\n" for s, role in rows]
    if status:
        parts.append(f"\n## Status\n\n{status}\n")
    md.write_text(fm + "".join(parts), encoding="utf-8")

    topics_out.append({"topic_id": tid, "slug": slug, "name": name, "purpose": purpose,
                       "status": status, "keywords": kw,
                       "sources": [{"source_id": s, "role": r} for s, r in rows]})

# --- normalized tables ---
with (MAN / "topics.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh); w.writerow(["topic_id", "slug", "name", "n_sources", "source_ids", "keywords"])
    for t in topics_out:
        w.writerow([t["topic_id"], t["slug"], t["name"], len(t["sources"]),
                    ";".join(s["source_id"] for s in t["sources"]), ";".join(t["keywords"])])
with (MAN / "topic-sources.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh); w.writerow(["topic_id", "slug", "source_id", "role"])
    for t in topics_out:
        for s in t["sources"]:
            w.writerow([t["topic_id"], t["slug"], s["source_id"], s["role"]])
(MAN / "topics.json").write_text(json.dumps(topics_out, indent=2, ensure_ascii=False), encoding="utf-8")

edges = sum(len(t["sources"]) for t in topics_out)
print(f"reconciled {len(topics_out)} topics | {edges} topic-source edges (from registry)")
