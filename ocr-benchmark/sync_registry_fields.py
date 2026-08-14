"""Regenerate schemas/registry-fields.json from the platform's field registry.

The platform registry is the authoritative field contract
(draftly-platform/backend/src/modules/document/domain/registry.py). It cannot be
imported across repos, so the key list is mirrored here — keys, labels, and
validator names only, never values.

Run after any registry change:

    uv run python ocr-benchmark/sync_registry_fields.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import config

REGISTRY = (
    config.ROOT.parent
    / "draftly-platform"
    / "backend"
    / "src"
    / "modules"
    / "document"
    / "domain"
    / "registry.py"
)
OUT = config.SCHEMAS / "registry-fields.json"

TEMPLATE_RE = re.compile(r'DocumentTemplate\(\s*kind="([a-z0-9-]+)"(.*?)\n\)', re.S)
FIELD_RE = re.compile(
    r'FieldDef\(\s*"(?P<key>[A-Za-z0-9_]+)"\s*,\s*"(?P<label>[^"]*)"(?:\s*,\s*(?P<validator>[A-Za-z_][A-Za-z0-9_]*))?'
)


def parse(source: str) -> dict[str, list[dict[str, str | None]]]:
    kinds: dict[str, list[dict[str, str | None]]] = {}
    for match in TEMPLATE_RE.finditer(source):
        kind, body = match.group(1), match.group(2)
        kinds[kind] = [
            {
                "key": fm.group("key"),
                "label": fm.group("label"),
                "validator": fm.group("validator"),
            }
            for fm in FIELD_RE.finditer(body)
        ]
    return kinds


def main() -> int:
    if not REGISTRY.is_file():
        print(f"registry not found: {REGISTRY}", file=sys.stderr)
        return 1
    kinds = parse(REGISTRY.read_text(encoding="utf-8"))
    if not kinds:
        print("parsed zero templates - the registry format changed", file=sys.stderr)
        return 1
    payload = {
        "_provenance": {
            "source": "draftly-platform/backend/src/modules/document/domain/registry.py",
            "note": "Keys, labels, and validator names only. No field values.",
        },
        "kinds": kinds,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(len(v) for v in kinds.values())
    for kind, fields in kinds.items():
        print(f"{len(fields):3d}  {kind}")
    print(f"wrote {OUT} ({total} fields across {len(kinds)} kinds)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
