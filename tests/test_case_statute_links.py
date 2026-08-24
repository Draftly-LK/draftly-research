from __future__ import annotations

import unittest

from draftly.retrieval.case_statute_links import case_statute_links, load_case_statute_links


class CaseStatuteLinksTests(unittest.TestCase):
    def test_load_returns_rows_from_all_bands(self) -> None:
        links = load_case_statute_links()

        bands = {link.band for link in links}
        self.assertTrue(links)
        self.assertIn("verified", bands)

    def test_filters_by_case_id(self) -> None:
        links = case_statute_links(case_id="commonlii-LKCA-1894-3")

        self.assertTrue(links)
        self.assertTrue(all(link.case_id == "commonlii-LKCA-1894-3" for link in links))

    def test_filters_by_source_id(self) -> None:
        links = case_statute_links(source_id="SRC030", limit=10)

        self.assertTrue(links)
        self.assertTrue(all(link.source_id == "SRC030" for link in links))

    def test_filters_by_band_case_insensitively(self) -> None:
        links = case_statute_links(band="VERIFIED", limit=10)

        self.assertTrue(links)
        self.assertTrue(all(link.band == "verified" for link in links))

    def test_verified_link_carries_a_resolved_section_id_and_title(self) -> None:
        links = case_statute_links(case_id="commonlii-LKCA-1894-3", band="verified")

        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link.source_id, "SRC030")
        self.assertEqual(link.section_number, "241")
        self.assertEqual(link.section_id, "SRC030:s241")
        self.assertEqual(link.statute_title, "Civil Procedure Code")

    def test_limit_caps_the_result_count(self) -> None:
        links = case_statute_links(band="verified", limit=5)

        self.assertLessEqual(len(links), 5)

    def test_unknown_case_id_returns_no_links(self) -> None:
        links = case_statute_links(case_id="not-a-real-case-id")

        self.assertEqual(links, [])


if __name__ == "__main__":
    unittest.main()
