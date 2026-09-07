"""Hashing rules for `finalized-sources/` manifests, shared by writer and verifier.

Two modes, recorded per file as `hash_mode` so the semantics travel with the hash:

- `bytes`: the SHA-256 of the file exactly as stored. Used for PDFs and every
  other binary. Any change to the bytes fails verification.
- `text-lf`: the SHA-256 of the text after every CRLF and lone CR is folded to
  LF. Used for the HTML, TXT, MD, CSV and JSON evidence files. Git on Windows
  checks these out with CRLF (`core.autocrlf=true`), which changed the raw hash
  of every text file in ten packages without changing a character of the text.
  A real edit to the text still fails; only the line-ending convention is
  ignored. `bytes` for a `text-lf` entry is the normalised length.

Manifest entries written before `hash_mode` existed carry raw-byte hashes
computed on an LF checkout. The verifier accepts such a legacy entry when
either the raw or the normalised hash matches, and reports it as `legacy`;
`verify_finalized_packages.py --migrate` rewrites it with an explicit mode.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

TEXT_SUFFIXES = {".html", ".htm", ".txt", ".md", ".json", ".csv"}
BYTES = "bytes"
TEXT_LF = "text-lf"


def hash_mode_for(path: Path) -> str:
    return TEXT_LF if path.suffix.lower() in TEXT_SUFFIXES else BYTES


def normalise_newlines(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def content(path: Path, mode: str) -> bytes:
    data = path.read_bytes()
    if mode == TEXT_LF:
        return normalise_newlines(data)
    if mode == BYTES:
        return data
    raise ValueError(f"unknown hash_mode {mode!r}")


def digest(path: Path, mode: str | None = None) -> tuple[str, int, str]:
    """Return (sha256, size, mode) for the file under the given or default mode."""
    mode = mode or hash_mode_for(path)
    data = content(path, mode)
    return hashlib.sha256(data).hexdigest(), len(data), mode


def file_entry(path: Path, repo_root: Path, **fields) -> dict:
    """A manifest `files[]` entry for `path`, with hash_mode recorded.

    Key order matches the manifests already on disk: file, role, edition, ...,
    then bytes / sha256 / hash_mode / copied_from, then used_for last.
    """
    sha, size, mode = digest(path)
    used_for = fields.pop("used_for", None)
    entry = {"file": fields.pop("file", path.name)}
    entry.update(fields)
    entry.update(
        {
            "bytes": size,
            "sha256": sha,
            "hash_mode": mode,
            "copied_from": path.relative_to(repo_root).as_posix(),
        }
    )
    if used_for is not None:
        entry["used_for"] = used_for
    return entry


def check_entry(package_dir: Path, entry: dict) -> tuple[str, str]:
    """Verify one manifest entry against the copy in the package folder.

    Returns (status, detail) where status is one of:
    `ok`, `legacy` (no hash_mode; matched raw or normalised), `missing`,
    `mismatch`, `bad-mode`.
    """
    path = package_dir / entry["file"]
    if not path.exists():
        return "missing", f"{entry['file']} is listed but not on disk"
    mode = entry.get("hash_mode")
    if mode is None:
        raw_sha, raw_len, _ = digest(path, BYTES)
        if raw_sha == entry["sha256"] and raw_len == entry.get("bytes", raw_len):
            return "legacy", "raw bytes match; no hash_mode recorded"
        lf_sha, lf_len, _ = digest(path, TEXT_LF)
        if lf_sha == entry["sha256"]:
            return "legacy", (
                f"matches after CRLF->LF normalisation ({raw_len} bytes on disk, "
                f"{lf_len} normalised); no hash_mode recorded"
            )
        return "mismatch", (
            f"{entry['file']}: sha256 {raw_sha[:12]} (raw) / {lf_sha[:12]} (lf) "
            f"!= manifest {entry['sha256'][:12]}"
        )
    try:
        sha, size, _ = digest(path, mode)
    except ValueError as exc:
        return "bad-mode", str(exc)
    if sha != entry["sha256"]:
        return "mismatch", f"{entry['file']}: sha256 {sha[:12]} != manifest {entry['sha256'][:12]} (mode {mode})"
    if size != entry.get("bytes", size):
        return "mismatch", f"{entry['file']}: {size} bytes != manifest {entry['bytes']} (mode {mode})"
    return "ok", ""


def migrate_entry(package_dir: Path, entry: dict) -> dict:
    """Rewrite a legacy entry with an explicit hash_mode, if the copy matches."""
    status, _ = check_entry(package_dir, entry)
    if status != "legacy":
        return entry
    path = package_dir / entry["file"]
    sha, size, mode = digest(path)
    updated = dict(entry)
    updated["bytes"] = size
    updated["sha256"] = sha
    updated["hash_mode"] = mode
    return updated
