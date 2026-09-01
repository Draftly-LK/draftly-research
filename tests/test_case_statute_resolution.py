from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_DIR = REPO_ROOT / "scripts" / "case-law-statute-linking"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, STAGE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


resolver = _load("lsl_resolver_under_test", "02_resolve_links.py")
proposer = _load("lsl_proposer_under_test", "propose_aliases.py")
sampler = _load("lsl_sampler_under_test", "build_review_sample.py")


class NormalizeFragmentTests(unittest.TestCase):
    def test_collapses_abbreviation_punctuation_variants(self) -> None:
        variants = ["CPC", "C.P.C.", "C. P. C.", "cpc"]
        normalized = {resolver.normalize_fragment(v) for v in variants}
        self.assertEqual(normalized, {"cpc"})

    def test_collapses_ampersand_and_whitespace(self) -> None:
        self.assertEqual(
            resolver.normalize_fragment("Prevention  &   Frauds"),
            "prevention and frauds",
        )


class MatchActTests(unittest.TestCase):
    def setUp(self) -> None:
        self.aliases = resolver.load_alias(None)  # STARTER_ALIASES fallback
        # add a short auto-derived-style alias for the boundary test
        self.aliases_with_short = self.aliases + [("to", "SRC059")]

    def test_matches_full_name(self) -> None:
        match = resolver.match_act("Civil Procedure Code, s. 241", self.aliases)
        self.assertIsNotNone(match)
        self.assertEqual(match[0], "SRC030")

    def test_matches_abbreviation_after_normalization(self) -> None:
        for citation in ["s. 326 C.P.C", "s.772 CPC", "s. 772 of the C. P. C."]:
            aliases = self.aliases + [("cpc", "SRC030")]
            match = resolver.match_act(citation, aliases)
            self.assertIsNotNone(match, citation)
            self.assertEqual(match[0], "SRC030", citation)

    def test_short_alias_does_not_match_inside_a_longer_word(self) -> None:
        # Boundary matching must not let "to" fire inside "automobile".
        match = resolver.match_act("an automobile insurance claim", self.aliases_with_short)
        self.assertIsNone(match)

    def test_short_alias_matches_as_a_standalone_word(self) -> None:
        # A standalone "to" DOES match -- word-boundary matching only rules
        # out substring-inside-a-word false positives, not this one. This is
        # exactly why propose_aliases.py never auto-applies an acronym like
        # "to": a human has to judge whether the false-positive rate on an
        # ordinary word is acceptable before it goes live for a real statute.
        match = resolver.match_act("the claim is subject to control by the court", self.aliases_with_short)
        self.assertIsNotNone(match)
        self.assertEqual(match[0], "SRC059")


class MatchActNumberTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = {("2", "1877"): "SRC099", ("30", "2022"): "SRC002"}

    def test_resolves_ordinance_no_of_year_with_no_statute_name(self) -> None:
        match = resolver.match_act_number("Ordinance No. 2 of 1877, s. 26, sub-section 13", self.index)
        self.assertEqual(match, ("SRC099", "no.2-of-1877"))

    def test_resolves_act_no_of_year(self) -> None:
        match = resolver.match_act_number("Act No. 30 of 2022", self.index)
        self.assertEqual(match, ("SRC002", "no.30-of-2022"))

    def test_returns_none_when_number_year_pair_not_in_registry(self) -> None:
        self.assertIsNone(resolver.match_act_number("Ordinance No. 99 of 1999", self.index))

    def test_returns_none_for_a_citation_with_no_number_year_pattern(self) -> None:
        self.assertIsNone(resolver.match_act_number("Civil Procedure Code, s. 241", self.index))


class ResolveLinksIntegrationTests(unittest.TestCase):
    def test_disagreement_between_name_and_number_paths_is_not_silently_resolved(self) -> None:
        # Constructed citation: the name alias says SRC030 (Civil Procedure
        # Code), but the No.-of-year in the same string maps to a different
        # statute in the fixture index -- this must not be auto-resolved to
        # either one silently.
        aliases = [("civil procedure code", "SRC030")]
        number_index = {("2", "1889"): "SRC999"}
        citation = "Civil Procedure Code, Ordinance No. 2 of 1889, s. 5"

        name_act = resolver.match_act(citation, aliases)
        number_act = resolver.match_act_number(citation, number_index)

        self.assertEqual(name_act[0], "SRC030")
        self.assertEqual(number_act[0], "SRC999")
        self.assertNotEqual(name_act[0], number_act[0])


class ProposeAliasesTests(unittest.TestCase):
    def test_derives_expected_acronyms(self) -> None:
        self.assertEqual(proposer.derive_acronym("Civil Procedure Code"), "cpc")
        self.assertEqual(proposer.derive_acronym("Trusts Ordinance"), "to")
        self.assertEqual(proposer.derive_acronym("Evidence Ordinance"), "eo")

    def test_single_word_title_is_too_short_to_propose(self) -> None:
        self.assertEqual(len(proposer.derive_acronym("Constitution")), 1)


class BuildReviewSampleTests(unittest.TestCase):
    def test_stratum_for_classifies_mismatch_first(self) -> None:
        row = {"reason": "name-number-mismatch:SRC004-vs-SRC045", "citation": "Ordinance No. 2 of 1889"}
        self.assertEqual(sampler.stratum_for(row), "name-number-mismatch")

    def test_stratum_for_detects_number_plus_year_citations(self) -> None:
        row = {"reason": "act+section+echo", "citation": "Ordinance No. 22 of 1871, s. 3"}
        self.assertEqual(sampler.stratum_for(row), "number-plus-year-path")

    def test_stratum_for_defaults_to_name_alias_path(self) -> None:
        row = {"reason": "act+section+echo", "citation": "Civil Procedure Code, s. 241"}
        self.assertEqual(sampler.stratum_for(row), "name-alias-path")

    def test_build_sample_is_deterministic_and_caps_per_stratum(self) -> None:
        rows = [
            {
                "case_id": f"case-{i}",
                "rule_id": f"rule-{i}",
                "citation": "Civil Procedure Code, s. 241",
                "source_id": "SRC030",
                "section_number": "241",
                "band": "verified",
                "reason": "act+section+echo",
            }
            for i in range(20)
        ]
        first = sampler.build_sample(rows)
        second = sampler.build_sample(rows)
        self.assertEqual(len(first), sampler.SAMPLE_PER_STRATUM)
        self.assertEqual([r["case_id"] for r in first], [r["case_id"] for r in second])


if __name__ == "__main__":
    unittest.main()
