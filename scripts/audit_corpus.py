"""Cross-check the legal-source registries against each other and the files on disk.

Verifies:
  - source-registry is the catalog (unique ids, id numbering gaps)
  - every registry source's local PDF + markdown paths actually exist
  - every source has a conversion-registry row (and its status)
  - topic-sources ids all exist in the registry; sources with no topic (orphans)
  - registry `topics` column agrees with topic-sources membership
  - conversion-registry ids (incl. multi-id consolidated rows) all exist
Prints a report; exits 0 always (audit, not a gate).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAN = ROOT / "data/legal-sources/manifests"


def read(name: str, bom: bool = False):
    enc = "utf-8-sig" if bom else "utf-8"
    with (MAN / name).open(encoding=enc) as fh:
        return list(csv.DictReader(fh))


def hdr(t): print("\n" + "=" * 4, t)


reg = read("source-registry.csv", bom=True)
conv = read("conversion-registry.csv")
tsrc = read("topic-sources.csv")

reg_ids = [r["source_id"] for r in reg]
reg_set = set(reg_ids)

# 1. uniqueness + numbering
hdr("1. source-registry")
print(f"sources: {len(reg_ids)} | unique: {len(reg_set)} | dups: {len(reg_ids) - len(reg_set)}")
nums = sorted(int(m.group(1)) for i in reg_ids if (m := re.match(r"SRC(\d+)", i)))
missing_nums = sorted(set(range(1, nums[-1] + 1)) - set(nums)) if nums else []
print(f"id range: SRC{nums[0]:03d}..SRC{nums[-1]:03d} | gaps: "
      f"{['SRC%03d' % n for n in missing_nums] or 'none'}")

# 2. file existence
hdr("2. files on disk (per registry source)")
no_pdf, no_md = [], []
for r in reg:
    pdf = (r.get("local_pdf_path") or "").strip()
    md = (r.get("local_markdown_path") or "").strip()
    if pdf and not (ROOT / pdf).exists():
        no_pdf.append(r["source_id"])
    if md and not (ROOT / md).exists():
        no_md.append(r["source_id"])
have_pdf = sum(1 for r in reg if (r.get("local_pdf_path") or "").strip())
have_md = sum(1 for r in reg if (r.get("local_markdown_path") or "").strip())
print(f"have local_pdf_path set: {have_pdf}/{len(reg)} | missing on disk: {no_pdf or 'none'}")
print(f"have local_markdown_path set: {have_md}/{len(reg)} | missing on disk: {no_md or 'none'}")

# 3. conversion coverage
hdr("3. conversion-registry coverage")
conv_ids = set()
for r in conv:
    for sid in re.split(r"[;\s]+", r["source_id"].strip()):
        if sid:
            conv_ids.add(sid)
unknown_conv = sorted(conv_ids - reg_set)
never_converted = sorted(reg_set - conv_ids)
bad_status = [r["source_id"] for r in conv if r.get("status") not in ("converted", "fallback-pdftotext")]
print(f"conversion rows: {len(conv)} | distinct source_ids covered: {len(conv_ids)}")
print(f"conv ids NOT in registry: {unknown_conv or 'none'}")
print(f"registry sources with NO conversion row: {len(never_converted)} -> {never_converted or 'none'}")
print(f"conversion status != converted/fallback: {sorted(set(bad_status)) or 'none'}")

# 4. topic-sources integrity
hdr("4. topic-sources integrity")
tsrc_ids = {r["source_id"] for r in tsrc}
unknown_topic = sorted(tsrc_ids - reg_set)
orphans = sorted(reg_set - tsrc_ids)  # sources not linked to any topic
print(f"topic-source edges: {len(tsrc)} | distinct sources used: {len(tsrc_ids)}")
print(f"topic-sources ids NOT in registry: {unknown_topic or 'none'}")
print(f"registry sources in NO topic (orphans): {len(orphans)} -> {orphans or 'none'}")

# 5. registry.topics vs topic-sources agreement
hdr("5. registry `topics` column vs topic-sources membership")
ts_by_src = {}
for r in tsrc:
    ts_by_src.setdefault(r["source_id"], set()).add(r["topic_id"])
mism = []
for r in reg:
    reg_topics = {t.zfill(2) for t in re.split(r"[;\s]+", (r.get("topics") or "").strip()) if t}
    ts_topics = ts_by_src.get(r["source_id"], set())
    if reg_topics != ts_topics:
        mism.append((r["source_id"], sorted(reg_topics - ts_topics), sorted(ts_topics - reg_topics)))
print(f"sources where registry.topics != topic-sources: {len(mism)}")
for sid, only_reg, only_ts in mism[:25]:
    print(f"  {sid}: in registry-only={only_reg} in topic-sources-only={only_ts}")

hdr("SUMMARY")
problems = (len(reg_ids) - len(reg_set)) + len(no_pdf) + len(no_md) + len(unknown_conv) + \
           len(unknown_topic) + len(mism)
print(f"hard inconsistencies: {problems}")
print(f"advisories: {len(never_converted)} not-converted, {len(orphans)} orphan sources, "
      f"{len(missing_nums)} id gaps")
