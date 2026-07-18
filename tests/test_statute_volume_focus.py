from __future__ import annotations

import unittest
from pathlib import Path

from draftly.retrieval.section_parser import find_boundaries, focus_document_text, parse_sections


STATUTE_DOCS = Path("data/processed/docs/statutes")


class StatuteVolumeFocusTests(unittest.TestCase):
    def focus(self, filename: str, title: str) -> str:
        text = (STATUTE_DOCS / filename).read_text(encoding="utf-8")
        return focus_document_text(text, title)

    def test_registration_of_old_deeds_excludes_preceding_naval_law(self) -> None:
        focused = self.focus(
            "src077-registration-of-old-deeds-and-instruments-ordinance.md",
            "Registration of Old Deeds and Instruments Ordinance",
        )

        self.assertTrue(focused.startswith("Cap. 137] REGISTRATION OF OLD DEEDS AND INSTRUMENTS"))
        self.assertNotIn("subject to naval law", focused)
        self.assertNotIn("[Cap. 582", focused)

    def test_sannases_excludes_later_corporations(self) -> None:
        focused = self.focus(
            "src078-sannases-and-old-deeds-ordinance.md",
            "Sannases and Old Deeds Ordinance",
        )

        self.assertTrue(focused.startswith("Cap. 136] SANNASES AND OLD DEEDS"))
        self.assertNotIn("CORPORATION", focused)
        self.assertNotIn("[Cap. 167", focused)

    def test_prescription_stops_before_partnership(self) -> None:
        focused = self.focus("src071-prescription-ordinance.md", "Prescription Ordinance")

        self.assertTrue(focused.startswith("Cap. 81] PRESCRIPTION"))
        self.assertNotIn("Cap. 179] PARTNERSHIP", focused)

    def test_rent_title_does_not_match_apprenticeship(self) -> None:
        focused = self.focus("src028-rent-act.md", "Rent Act")

        self.assertIn("RENT", focused[:300])
        self.assertNotIn("Every warrant issued to a notary", focused)

    def test_ocr_and_title_variants_still_find_the_target_enactment(self) -> None:
        thesawalamai = self.focus(
            "src046-tesawalamai-pre-emption-ordinance.md",
            "Tesawalamai Pre-emption Ordinance",
        )
        state_land = self.focus(
            "src057-state-lands-claims-ordinance.md",
            "State Lands (Claims) Ordinance",
        )

        self.assertIn("THESA WALAMAI PRE-EMPTION", thesawalamai[:200])
        self.assertIn("STATE LAND (CLAIMS)", state_land[:200])

    def test_standalone_large_act_is_preserved(self) -> None:
        text = "A LAW TO PROVIDE FOR A STANDALONE AUTHORITY.\n" + ("1. Powers of the authority.\n" * 20_000)

        self.assertIs(focus_document_text(text, "Standalone Authority Act"), text)

    def test_numeric_chapter_header_can_end_an_enactment(self) -> None:
        text = (
            "Cap. 10] TARGET ENACTMENT\n"
            + ("1. Target provision.\n" * 20_000)
            + "CHAPTER 11\nNEXT ENACTMENT\n"
            + "Cap. 12] LATER ENACTMENT\n"
            + "Cap. 13] FINAL ENACTMENT\n"
        )

        focused = focus_document_text(text, "Target Enactment Act")

        self.assertNotIn("CHAPTER 11", focused)
        self.assertNotIn("NEXT ENACTMENT", focused)


class BoundaryAndAliasTests(unittest.TestCase):
    def test_reporter_and_number_headers_are_not_sections(self) -> None:
        lines = [
            "No. 118. DR. PERERA v. SILVA",
            "118. SRI LANKA LAW REPORTS [2009] 1 S.L.R.",
            "119. DR. PERERA v. SILVA",
            "3. Valid statutory provision.",
        ]

        boundaries = find_boundaries(lines)

        self.assertEqual([boundary.number for boundary in boundaries], ["3"])

    def test_amendment_alias_records_principal_section_target(self) -> None:
        nodes = parse_sections(
            source_id="SRC-AMEND",
            doc_id="doc-amend",
            kind="amendment",
            title="Example Amendment Act",
            act_number="1",
            year="2026",
            topics=(),
            public_source_url="",
            source_sha256="sha",
            text=(
                "1. Section 12 of the principal enactment is hereby amended.\n"
                "2. This Act comes into operation immediately."
            ),
        )

        alias = next(node for node in nodes if node.section_id == "SRC-AMEND:s12")
        self.assertEqual(alias.metadata["alias_kind"], "principal_section_target")
        self.assertEqual(alias.metadata["target_section"], "12")


if __name__ == "__main__":
    unittest.main()
