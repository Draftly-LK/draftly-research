from draftly.retrieval.evaluation import read_gold, score_question

from lawchain.compare import filtered_gold_rows


def test_precision_at_5_is_present_and_correct() -> None:
    scores = score_question("q1", {"SRC001:s2"}, ["SRC001:s2", "x", "y", "z", "w"])
    assert "precision_at_5" in scores
    assert scores["precision_at_5"] == 1 / 5


def test_filtered_gold_rows_is_nonempty_and_smaller() -> None:
    full = read_gold()
    filtered = filtered_gold_rows()
    assert filtered
    assert len(filtered) < len(full)
