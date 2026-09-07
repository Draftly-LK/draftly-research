"""Integrity rules for `finalized-sources/` manifests.

Covers the two hash modes in `scripts/package_integrity.py`, the legacy
fallback and migration, and finally verifies every package on disk.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from package_integrity import (  # noqa: E402
    BYTES,
    TEXT_LF,
    check_entry,
    digest,
    file_entry,
    hash_mode_for,
    migrate_entry,
)
from verify_finalized_packages import verify  # noqa: E402

TEXT = b"<html>\n<p>Section 1.</p>\n<p>Section 2.</p>\n"


class HashModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, name: str, data: bytes) -> Path:
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_mode_is_chosen_by_suffix(self) -> None:
        self.assertEqual(hash_mode_for(Path("x.html")), TEXT_LF)
        self.assertEqual(hash_mode_for(Path("x.TXT")), TEXT_LF)
        self.assertEqual(hash_mode_for(Path("x.pdf")), BYTES)
        self.assertEqual(hash_mode_for(Path("x.png")), BYTES)

    def test_lf_and_crlf_text_hash_identically(self) -> None:
        lf = self.write("lf.html", TEXT)
        crlf = self.write("crlf.html", TEXT.replace(b"\n", b"\r\n"))
        cr = self.write("cr.html", TEXT.replace(b"\n", b"\r"))
        self.assertEqual(digest(lf), digest(crlf))
        self.assertEqual(digest(lf), digest(cr))
        self.assertEqual(digest(lf)[1], len(TEXT))

    def test_textual_change_fails_verification(self) -> None:
        original = self.write("a.html", TEXT)
        entry = file_entry(original, self.root, role="principal statute", edition="consolidated")
        self.assertEqual(entry["hash_mode"], TEXT_LF)
        self.assertEqual(check_entry(self.root, entry)[0], "ok")
        original.write_bytes(TEXT.replace(b"Section 2", b"Section 3"))
        self.assertEqual(check_entry(self.root, entry)[0], "mismatch")

    def test_crlf_checkout_of_recorded_text_still_verifies(self) -> None:
        original = self.write("a.txt", TEXT)
        entry = file_entry(original, self.root, role="amending Act", edition="as_enacted")
        original.write_bytes(TEXT.replace(b"\n", b"\r\n"))
        self.assertEqual(check_entry(self.root, entry)[0], "ok")

    def test_binary_change_fails_verification(self) -> None:
        pdf = self.write("a.pdf", b"%PDF-1.4\r\n1 0 obj\r\n")
        entry = file_entry(pdf, self.root, role="principal statute", edition="scan")
        self.assertEqual(entry["hash_mode"], BYTES)
        self.assertEqual(check_entry(self.root, entry)[0], "ok")
        # For binaries even a line-ending change is a change.
        pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n")
        self.assertEqual(check_entry(self.root, entry)[0], "mismatch")

    def test_missing_file_is_reported(self) -> None:
        entry = {"file": "gone.pdf", "sha256": "0" * 64, "bytes": 1}
        self.assertEqual(check_entry(self.root, entry)[0], "missing")

    def test_legacy_entry_matches_raw_or_normalised_and_migrates(self) -> None:
        original = self.write("a.html", TEXT)
        raw_sha, raw_len, _ = digest(original, BYTES)
        legacy = {"file": "a.html", "sha256": raw_sha, "bytes": raw_len}
        self.assertEqual(check_entry(self.root, legacy)[0], "legacy")
        # Same entry after a CRLF checkout: still accepted as legacy.
        original.write_bytes(TEXT.replace(b"\n", b"\r\n"))
        status, detail = check_entry(self.root, legacy)
        self.assertEqual(status, "legacy")
        self.assertIn("normalisation", detail)
        migrated = migrate_entry(self.root, legacy)
        self.assertEqual(migrated["hash_mode"], TEXT_LF)
        self.assertEqual(migrated["sha256"], raw_sha)  # LF content is unchanged
        self.assertEqual(migrated["bytes"], len(TEXT))
        self.assertEqual(check_entry(self.root, migrated)[0], "ok")
        # A legacy entry whose text really changed is a mismatch, not legacy.
        original.write_bytes(TEXT.replace(b"Section 2", b"Section 9"))
        self.assertEqual(check_entry(self.root, legacy)[0], "mismatch")
        self.assertIs(migrate_entry(self.root, legacy), legacy)

    def test_file_entry_key_order_matches_existing_manifests(self) -> None:
        original = self.write("a.pdf", b"%PDF")
        entry = file_entry(original, self.root, role="r", edition="e", used_for="u")
        self.assertEqual(
            list(entry), ["file", "role", "edition", "bytes", "sha256", "hash_mode", "copied_from", "used_for"]
        )


class VerifyReportTests(unittest.TestCase):
    def test_verify_flags_unlisted_files_missing_trees_and_notes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            finalized = root / "finalized"
            sources = root / "finalized-sources"
            (finalized / "1-2000-x").mkdir(parents=True)
            (finalized / "1-2000-x" / "1-2000-x.json").write_text("{}", encoding="utf-8")
            (finalized / "2-2001-orphan-tree").mkdir()
            pkg = sources / "1-2000-x"
            pkg.mkdir(parents=True)
            src = pkg / "1-2000-x.html"
            src.write_bytes(TEXT)
            (pkg / "stray.txt").write_bytes(b"x")
            entry = file_entry(src, root, role="principal statute", edition="consolidated")
            (pkg / "manifest.json").write_text(json.dumps({"files": [entry]}), encoding="utf-8")
            (sources / "3-2002-no-tree").mkdir()
            (sources / "3-2002-no-tree" / "manifest.json").write_text(
                json.dumps({"files": [], "statute_note": "n"}), encoding="utf-8"
            )
            report = verify(finalized, sources)
        self.assertEqual(report["trees_without_package"], ["2-2001-orphan-tree"])
        self.assertIn("1-2000-x: stray.txt is in the folder but not in the manifest", report["warnings"])
        self.assertIn("1-2000-x: manifest has no statute_note", report["warnings"])
        self.assertTrue(any("3-2002-no-tree" in e and "no finalized" in e for e in report["errors"]))
        self.assertEqual(report["packages"]["1-2000-x"]["ok"], 1)


class RepositoryPackagesTest(unittest.TestCase):
    """Every package on disk verifies. Legacy entries are allowed; mismatches are not."""

    def test_every_finalized_package_verifies(self) -> None:
        report = verify()
        self.assertGreater(len(report["packages"]), 0)
        self.assertEqual(report["errors"], [], "\n".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
