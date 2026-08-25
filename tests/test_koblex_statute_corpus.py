"""Validation for the KoBLEX-inspired statute retrieval corpus.

Checks the committed statute.jsonl against its source JSON, and re-runs the
builder to confirm determinism. Everything here is offline and read-only over
data/; rebuilds go to a temporary directory.

Per-record checks collect offenders and assert once rather than using subTest
per record -- at 5k+ records the subTest bookkeeping dominates the runtime.

    uv run pytest tests/test_koblex_statute_corpus.py -q
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "koblex-inspired-retrieval"
sys.path.insert(0, str(EXPERIMENT))

import build_statute_corpus as bsc  # noqa: E402

CORPUS = EXPERIMENT / "data" / "statute.jsonl"
REPORT = EXPERIMENT / "data" / "generation-report.md"

ACT_ID_RE = re.compile(r"^\d+[A-Za-z]?-\d{4}$")
BRACKET_RE = re.compile(r"\(([^)]+)\)")
STUB_TRIM = "()[]*—- "

FORBIDDEN_SUBSTRINGS = (
    "answer", "context", "n_hop", "gold", "parametric", "question",
    "prediction", "supporting_quote",
)

MAX_REPORTED = 5


def collect_source_texts() -> dict[str, set[str]]:
    """Normalized text of every node in each selected edition, by source file."""
    kept, _skipped, _problems = bsc.select_editions(bsc.FINALIZED)
    by_file: dict[str, set[str]] = {}

    def walk(nodes, sink: set[str]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            text = bsc.own_text(node)
            if text:
                sink.add(text)
            inner = node.get("provision")
            if isinstance(inner, dict):
                walk([inner], sink)
            walk(bsc.children_of(node), sink)

    for path, doc in kept:
        sink: set[str] = set()
        walk(doc.get("body") or [], sink)
        for schedule in doc.get("schedules") or []:
            if not isinstance(schedule, dict):
                continue
            text = bsc.normalize_text(schedule.get("text") or "")
            if text:
                sink.add(text)
            for item in schedule.get("items") or []:
                if isinstance(item, dict):
                    item_text = bsc.normalize_text(item.get("text") or "")
                    if item_text:
                        sink.add(item_text)
        by_file[path.name] = sink
    return by_file


class CorpusTestCase(unittest.TestCase):
    """Shared loading plus an offender-list assertion helper."""

    @classmethod
    def setUpClass(cls) -> None:
        if not CORPUS.exists():
            raise unittest.SkipTest(
                f"{CORPUS} missing -- run build_statute_corpus.py first")
        cls.raw_lines = CORPUS.read_text(encoding="utf-8").splitlines()
        cls.records = [json.loads(line) for line in cls.raw_lines]
        cls.ids = {r["node_id"] for r in cls.records}

    def assertNoOffenders(self, offenders: list[str], what: str) -> None:
        if not offenders:
            return
        shown = "\n  ".join(offenders[:MAX_REPORTED])
        extra = ("" if len(offenders) <= MAX_REPORTED
                 else f"\n  ... and {len(offenders) - MAX_REPORTED} more")
        self.fail(f"{len(offenders)} record(s) with {what}:\n  {shown}{extra}")


class StatuteCorpusTests(CorpusTestCase):
    """Static checks over the committed corpus."""

    # 1 ---------------------------------------------------------------- #
    def test_every_line_is_valid_json_object(self):
        self.assertTrue(self.raw_lines, "corpus is empty")
        offenders = [
            f"line {i}" for i, line in enumerate(self.raw_lines, start=1)
            if not isinstance(json.loads(line), dict)
        ]
        self.assertNoOffenders(offenders, "a non-object JSON payload")

    # 2 ---------------------------------------------------------------- #
    def test_fields_match_the_allowlist_exactly(self):
        expected = frozenset(bsc.FIELDS)
        shapes = {frozenset(r) for r in self.records}
        self.assertEqual(shapes, {expected})

    def test_allowlist_field_order_is_stable(self):
        orders = {tuple(r) for r in self.records}
        self.assertEqual(orders, {tuple(bsc.FIELDS)})

    # 3 ---------------------------------------------------------------- #
    def test_node_ids_are_unique(self):
        counts = Counter(r["node_id"] for r in self.records)
        self.assertNoOffenders(
            [f"{nid} x{c}" for nid, c in counts.items() if c > 1],
            "a duplicated node_id")

    # 5 ---------------------------------------------------------------- #
    def test_every_record_has_non_empty_text(self):
        self.assertNoOffenders(
            [r["node_id"] for r in self.records if not r["text"].strip()],
            "empty text")

    # 6 ---------------------------------------------------------------- #
    def test_required_fields_are_well_formed(self):
        offenders: list[str] = []
        for record in self.records:
            problems: list[str] = []
            if not ACT_ID_RE.match(record["act_id"] or ""):
                problems.append(f"act_id={record['act_id']!r}")
            if record["node_type"] not in bsc.KNOWN_TYPES:
                problems.append(f"node_type={record['node_type']!r}")
            for field in ("act_title", "citation", "provision_label",
                          "search_text", "source_file"):
                if not record[field]:
                    problems.append(f"empty {field}")
            if not isinstance(record["act_number"], int):
                problems.append(f"act_number={record['act_number']!r}")
            if not isinstance(record["act_year"], int):
                problems.append(f"act_year={record['act_year']!r}")
            hierarchy = record["hierarchy"]
            if not hierarchy:
                problems.append("empty hierarchy")
            elif hierarchy[0]["type"] != "act":
                problems.append("hierarchy does not start at act")
            elif any(set(e) != {"type", "label"} for e in hierarchy):
                problems.append("hierarchy entry shape")
            if problems:
                offenders.append(f"{record['node_id']}: {'; '.join(problems)}")
        self.assertNoOffenders(offenders, "malformed required fields")

    # 7 ---------------------------------------------------------------- #
    def test_text_comes_verbatim_from_the_source_json(self):
        """No paraphrase, no OCR repair, no arbitrary chunking."""
        source_texts = collect_source_texts()
        offenders: list[str] = []
        for record in self.records:
            pool = source_texts.get(record["source_file"])
            if pool is None:
                offenders.append(
                    f"{record['node_id']}: unknown source {record['source_file']!r}")
            elif record["text"] not in pool:
                offenders.append(
                    f"{record['node_id']}: text absent from source "
                    f"({record['text'][:60]!r})")
        self.assertNoOffenders(offenders, "text not traceable to the source JSON")

    # 8 ---------------------------------------------------------------- #
    def test_no_question_or_gold_label_fields_leak_in(self):
        """The allowlist is the boundary; assert the allowlist itself is clean."""
        offenders = [
            f"{field} contains {banned!r}"
            for field in bsc.FIELDS
            for banned in FORBIDDEN_SUBSTRINGS
            if banned in field.lower()
        ]
        self.assertNoOffenders(offenders, "a forbidden field name")
        # And that no record carries a key outside it.
        self.assertEqual({frozenset(r) for r in self.records},
                         {frozenset(bsc.FIELDS)})

    # 9 ---------------------------------------------------------------- #
    def test_citation_matches_title_and_provision_label(self):
        offenders: list[str] = []
        for record in self.records:
            joiner = ", " if record["node_type"] in bsc.SYNTHETIC_TYPES else ", s "
            expected = f"{record['act_title']}{joiner}{record['provision_label']}"
            if record["citation"] != expected:
                offenders.append(
                    f"{record['node_id']}: {record['citation']!r} != {expected!r}")
        self.assertNoOffenders(offenders, "a citation inconsistent with its label")

    def test_provision_label_agrees_with_hierarchy_labels(self):
        offenders: list[str] = []
        for record in self.records:
            if record["node_type"] in bsc.SYNTHETIC_TYPES:
                continue
            label = record["provision_label"]
            sections = [e for e in record["hierarchy"] if e["type"] == "section"]
            if not sections:
                offenders.append(f"{record['node_id']}: no section ancestor")
                continue
            number = sections[-1]["label"].split(" ", 1)[1]
            if not label.startswith(number):
                offenders.append(
                    f"{record['node_id']}: {label!r} does not start with {number!r}")
                continue
            cursor = len(number)
            for entry in record["hierarchy"]:
                if entry["type"] not in {"subsection", "paragraph", "subparagraph"}:
                    continue
                token = BRACKET_RE.search(entry["label"])
                if not token:
                    continue
                fragment = f"({token.group(1)})"
                found = label.find(fragment, cursor)
                if found == -1:
                    offenders.append(
                        f"{record['node_id']}: {fragment!r} missing from {label!r}")
                    break
                cursor = found + len(fragment)
        self.assertNoOffenders(offenders, "a provision_label out of step with hierarchy")

    # 10 --------------------------------------------------------------- #
    def test_parent_id_resolves_to_a_record_or_the_act_root(self):
        offenders = [
            f"{r['node_id']}: parent {r['parent_id']!r}"
            for r in self.records
            if not r["parent_id"]
            or (r["parent_id"] != r["act_id"] and r["parent_id"] not in self.ids)
        ]
        self.assertNoOffenders(offenders, "an unresolvable parent_id")

    def test_node_id_is_prefixed_by_its_act(self):
        offenders = [
            r["node_id"] for r in self.records
            if not r["node_id"].startswith(r["act_id"] + "/")
        ]
        self.assertNoOffenders(offenders, "a node_id not under its act_id")

    def test_section_id_is_consistent_with_hierarchy(self):
        offenders: list[str] = []
        for record in self.records:
            section_id = record["section_id"]
            has_section = any(e["type"] == "section" for e in record["hierarchy"])
            if record["node_type"] in bsc.SYNTHETIC_TYPES:
                if section_id is not None:
                    offenders.append(f"{record['node_id']}: schedule has section_id")
            elif has_section:
                if not section_id:
                    offenders.append(f"{record['node_id']}: missing section_id")
                elif not record["node_id"].startswith(section_id):
                    offenders.append(
                        f"{record['node_id']}: not under section {section_id!r}")
        self.assertNoOffenders(offenders, "an inconsistent section_id")

    def test_temporal_metadata_is_absent_not_guessed(self):
        offenders = [
            r["node_id"] for r in self.records
            if r["effective_from"] is not None or r["effective_to"] is not None
        ]
        self.assertNoOffenders(offenders, "invented temporal metadata")

    # 11 --------------------------------------------------------------- #
    def test_report_records_the_counts_and_duplicates(self):
        report = REPORT.read_text(encoding="utf-8")
        text_keys = Counter(
            re.sub(r"\s+", " ", r["text"]).casefold() for r in self.records)
        duplicates = {k: v for k, v in text_keys.items() if v > 1}
        self.assertIn(f"- Records: {len(self.records)}", report)
        self.assertIn(
            f"Duplicate evidence texts: {len(duplicates)} distinct strings", report)
        self.assertIn("## Consolidation gaps", report)
        self.assertIn("## Regeneration", report)


class DeterminismTests(unittest.TestCase):
    """4 and 12 -- rebuilds must be identical, and match what is committed."""

    def _build_to(self, directory: Path) -> Path:
        records, _meta = bsc.build(bsc.FINALIZED)
        target = directory / "statute.jsonl"
        bsc.write_jsonl(records, target)
        return target

    def test_two_rebuilds_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as first, \
                tempfile.TemporaryDirectory() as second:
            one = self._build_to(Path(first))
            two = self._build_to(Path(second))
            self.assertEqual(hashlib.sha256(one.read_bytes()).hexdigest(),
                             hashlib.sha256(two.read_bytes()).hexdigest())

    def test_rebuild_matches_the_committed_corpus(self):
        if not CORPUS.exists():
            self.skipTest("corpus not built")
        with tempfile.TemporaryDirectory() as tmp:
            rebuilt = self._build_to(Path(tmp))
            self.assertEqual(
                hashlib.sha256(rebuilt.read_bytes()).hexdigest(),
                hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
                "committed statute.jsonl is stale -- re-run build_statute_corpus.py")

    def test_node_ids_are_stable_across_rebuilds(self):
        first, _ = bsc.build(bsc.FINALIZED)
        second, _ = bsc.build(bsc.FINALIZED)
        self.assertEqual([r["node_id"] for r in first],
                         [r["node_id"] for r in second])


class ExclusionTests(unittest.TestCase):
    """The edition and repealed-stub rules the corpus depends on."""

    def test_one_base_statute_per_directory(self):
        kept, skipped, _problems = bsc.select_editions(bsc.FINALIZED)
        kept_names = {path.name for path, _doc in kept}
        self.assertEqual(len(kept_names), len(kept))
        for entry in skipped:
            self.assertNotIn(entry["file"], kept_names)
        directories = [path.parent.name for path, _doc in kept]
        self.assertEqual(len(directories), len(set(directories)))

    def test_amending_acts_are_skipped(self):
        _kept, skipped, _problems = bsc.select_editions(bsc.FINALIZED)
        reasons = [e["reason"] for e in skipped]
        self.assertTrue(any("amending Act" in r for r in reasons))
        self.assertTrue(any("superseded edition" in r for r in reasons))

    def test_latest_wills_consolidation_is_selected(self):
        kept, _skipped, _problems = bsc.select_editions(bsc.FINALIZED)
        wills = [doc for path, doc in kept if path.parent.name.startswith("21-1844")]
        self.assertEqual(len(wills), 1)
        self.assertEqual(bsc.edition_kind(wills[0]), "consolidated-2024")

    def test_repealed_stub_detection(self):
        self.assertTrue(bsc.is_repealed_stub("Repealed By", {"type": "section"}))
        self.assertTrue(bsc.is_repealed_stub(
            "(*Repealed and replaced by the Companies Act, No. 17 of 1982.)",
            {"type": "closing_text"}))

    def test_operative_repealing_provisions_are_kept(self):
        """A provision that repeals another Act is a live rule, not a stub."""
        self.assertFalse(bsc.is_repealed_stub(
            "The Condominium Property Act, No. 12 of 1970, is hereby repealed.",
            {"type": "section"}))

    def test_stub_with_substantive_children_is_kept(self):
        node = {
            "type": "section",
            "children": [{"type": "subsection", "text": "Live obligation text."}],
        }
        self.assertFalse(bsc.is_repealed_stub("Repealed By", node))

    def test_no_repealed_stub_survives_in_the_corpus(self):
        if not CORPUS.exists():
            self.skipTest("corpus not built")
        offenders = []
        for line in CORPUS.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            trimmed = record["text"].strip().strip(STUB_TRIM).strip()
            if bsc.REPEAL_STUB_RE.match(trimmed):
                offenders.append(f"{record['node_id']}: {trimmed[:60]!r}")
        self.assertFalse(offenders, f"repealed stubs in corpus: {offenders[:5]}")


if __name__ == "__main__":
    unittest.main()
