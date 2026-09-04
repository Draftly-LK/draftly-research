from __future__ import annotations

import unittest
from unittest import mock

from draftly.case_retrieval import graph as case_graph
from draftly.case_retrieval.corpus import corpus_fingerprint, load_conveyancing_case_rows
from draftly.case_retrieval.index import build_index
from draftly.case_retrieval.models import CaseHit
from draftly.case_retrieval.search import _rare_tokens, find_similar, fuse_rankings, query_tokens


def make_hit(case_id: str) -> CaseHit:
    return CaseHit(case_id=case_id, citation="", title="", court="", year="", url="", excerpt="", score=0.0)


class CorpusScopeTests(unittest.TestCase):
    def test_population_is_conveyancing_flagged_only(self) -> None:
        rows = load_conveyancing_case_rows()

        self.assertTrue(rows)
        self.assertTrue(all(row["conveyancing_match"] is True for row in rows))

    def test_fingerprint_is_stable_across_calls(self) -> None:
        rows = load_conveyancing_case_rows()

        self.assertEqual(corpus_fingerprint(rows), corpus_fingerprint(rows))

    def test_fingerprint_changes_when_population_changes(self) -> None:
        rows = load_conveyancing_case_rows()

        self.assertNotEqual(corpus_fingerprint(rows), corpus_fingerprint(rows[:-1]))


class IndexTests(unittest.TestCase):
    def test_build_index_is_scoped_to_conveyancing_population(self) -> None:
        stats = build_index(force=False)

        self.assertEqual(stats.cases, len(load_conveyancing_case_rows()))


class FuseRankingsTests(unittest.TestCase):
    def test_rrf_prefers_case_ranked_first_in_more_channels(self) -> None:
        fused = fuse_rankings(
            [
                ("lexical", [make_hit("a"), make_hit("b")], 1.0),
                ("graph", [make_hit("a")], 1.0),
            ],
            limit=5,
        )

        self.assertEqual(fused[0].case_id, "a")
        self.assertEqual(set(fused[0].matched_signals), {"lexical", "graph"})

    def test_deduplicates_across_channels(self) -> None:
        fused = fuse_rankings(
            [
                ("lexical", [make_hit("a")], 1.0),
                ("dense", [make_hit("a")], 0.8),
            ],
            limit=5,
        )

        self.assertEqual(len(fused), 1)

    def test_respects_limit(self) -> None:
        hits = [make_hit(str(i)) for i in range(10)]
        fused = fuse_rankings([("lexical", hits, 1.0)], limit=3)

        self.assertEqual(len(fused), 3)


class QueryTokensTests(unittest.TestCase):
    def test_drops_stopwords_and_short_tokens(self) -> None:
        tokens = query_tokens("The notary attested a deed of gift for the son")

        self.assertIn("notary", tokens)
        self.assertIn("attested", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("of", tokens)

    def test_deduplicates_preserving_order(self) -> None:
        tokens = query_tokens("deed deed gift deed")

        self.assertEqual(tokens, ["deed", "gift"])


class FindSimilarTests(unittest.TestCase):
    def test_abstains_on_an_off_domain_query(self) -> None:
        result = find_similar(
            "quantum entanglement in superconducting qubit arrays for fault-tolerant computing"
        )

        self.assertEqual(result.outcome, "no_similar_cases")
        self.assertEqual(result.hits, ())
        self.assertTrue(result.reason)

    def test_finds_cases_for_a_real_conveyancing_fact_pattern(self) -> None:
        result = find_similar(
            "A notary public attested a deed of gift of land, gifted subject to a "
            "life interest of the donor. The donee later claimed prescriptive "
            "title to the property against the fideicommissary substitutes."
        )

        self.assertEqual(result.outcome, "similar_cases_found")
        self.assertTrue(result.hits)
        for hit in result.hits:
            self.assertTrue(set(hit.matched_signals) & {"lexical", "graph"})

    def test_every_returned_hit_is_corroborated_not_dense_only(self) -> None:
        result = find_similar("prescription servitude co-ownership partition deed notary")

        for hit in result.hits:
            self.assertTrue(set(hit.matched_signals) & {"lexical", "graph"})


class GraphVerifiedOnlyToggleTests(unittest.TestCase):
    def test_verified_only_drops_the_topic_bridge_and_shrinks_the_graph(self) -> None:
        from draftly.case_retrieval.index import connect

        with connect() as conn:
            baseline_adjacency = case_graph.build_graph(
                conn, verified_only=False, fanout_weight=False, catchword_edges=False, catchword_statute_links=False
            )
            verified_adjacency = case_graph.build_graph(
                conn, verified_only=True, fanout_weight=False, catchword_edges=False, catchword_statute_links=False
            )

        baseline_edges = sum(len(n) for n in baseline_adjacency.values())
        verified_edges = sum(len(n) for n in verified_adjacency.values())
        self.assertLess(verified_edges, baseline_edges)
        self.assertGreater(verified_edges, 0)

    def test_verified_only_env_var_is_read_by_get_graph(self) -> None:
        with mock.patch.dict("os.environ", {"DRAFTLY_CASE_GRAPH_VERIFIED_ONLY": "1"}):
            self.assertTrue(case_graph._verified_only())
        with mock.patch.dict("os.environ", {"DRAFTLY_CASE_GRAPH_VERIFIED_ONLY": "0"}):
            self.assertFalse(case_graph._verified_only())


class CatchwordEdgesToggleTests(unittest.TestCase):
    def test_catchword_edges_default_on_unless_explicitly_disabled(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=False):
            import os as _os

            _os.environ.pop("DRAFTLY_CASE_CATCHWORD_EDGES", None)
            self.assertTrue(case_graph._catchword_edges_enabled())
        with mock.patch.dict("os.environ", {"DRAFTLY_CASE_CATCHWORD_EDGES": "0"}):
            self.assertFalse(case_graph._catchword_edges_enabled())

    def test_catchword_edges_add_a_second_independent_bridge(self) -> None:
        from draftly.case_retrieval.index import connect

        with connect() as conn:
            baseline_adjacency = case_graph.build_graph(
                conn, verified_only=False, fanout_weight=False, catchword_edges=False, catchword_statute_links=False
            )
            with_catchwords = case_graph.build_graph(
                conn, verified_only=False, fanout_weight=False, catchword_edges=True, catchword_statute_links=False
            )

        baseline_edges = sum(len(n) for n in baseline_adjacency.values())
        catchword_edges_count = sum(len(n) for n in with_catchwords.values())
        self.assertGreater(catchword_edges_count, baseline_edges)


class FanoutDiscountTests(unittest.TestCase):
    def test_discount_shrinks_as_member_count_grows(self) -> None:
        low = case_graph.fanout_discount(2)
        high = case_graph.fanout_discount(13)

        self.assertGreater(low, high)
        self.assertGreater(high, 0.0)


class LexicalIdfToggleTests(unittest.TestCase):
    def test_rare_tokens_drops_common_corpus_words(self) -> None:
        # "land" is a near-universal term in this corpus; "fideicommissary"
        # and "anuradhapura" are not.
        tokens = ["land", "fideicommissary", "anuradhapura"]

        rare = _rare_tokens(tokens)

        self.assertNotIn("land", rare)
        self.assertIn("fideicommissary", rare)
        self.assertIn("anuradhapura", rare)


if __name__ == "__main__":
    unittest.main()
