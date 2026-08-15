"""Quick manual progress check for the running extraction/normalize job.

Usage:
    .venv\\Scripts\\python.exe scripts\\case-law-information-extraction\\check_progress.py
"""
import json
from collections import Counter

import config

by_track_status = Counter()
total = 0
for cf in config.CACHE.glob("*.json"):
    try:
        rec = json.loads(cf.read_text(encoding="utf-8"))
    except Exception:
        continue
    total += 1
    by_track_status[(rec.get("track", "?"), rec.get("status", "?"))] += 1

print(f"total cached cases: {total}")
print()
for (track, status), n in sorted(by_track_status.items(), key=lambda kv: -kv[1]):
    print(f"  track={track:8s} status={status:20s} count={n}")
