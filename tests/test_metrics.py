import math

from catalog_rag.eval.metrics import aggregate, recall_at_k, reciprocal_rank, to_markdown


def test_recall_at_k():
    assert recall_at_k(["a", "b", "c"], {"a"}, 1) == 1.0
    assert recall_at_k(["a", "b", "c"], {"c"}, 1) == 0.0
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, 2) == 0.5
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, 3) == 1.0
    assert math.isnan(recall_at_k(["a"], set(), 5))


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b"], {"a"}) == 1.0
    assert reciprocal_rank(["a", "b"], {"b"}) == 0.5
    assert reciprocal_rank(["a", "b"], {"z"}) == 0.0


def test_aggregate_splits_and_excludes_unanswerable():
    rows = [
        {"type": "factual", "ranked": ["a", "b"], "gold": ["a"]},
        {"type": "prereq", "ranked": ["x", "b"], "gold": ["b"]},
        {"type": "not_in_catalog", "ranked": ["q"], "gold": []},
    ]
    agg = aggregate(rows, ks=(1, 5))
    assert agg["overall"]["n"] == 2
    assert agg["overall"]["recall@1"] == 0.5
    assert agg["overall"]["recall@5"] == 1.0
    assert agg["overall"]["mrr"] == 0.75
    assert agg["prereq"]["recall@1"] == 0.0
    assert "not_in_catalog" not in agg


def test_markdown_renders():
    rows = [{"type": "factual", "ranked": ["a"], "gold": ["a"]}]
    md = to_markdown({"bm25": aggregate(rows, ks=(1,))}, corpus_size=412)
    assert "| bm25 | 412 | overall | 1 | 1.000 | 1.000 |" in md


def test_aggregate_splits_on_has_code_when_present():
    rows = [
        {"type": "factual", "has_code": True, "ranked": ["a"], "gold": ["a"]},
        {"type": "factual", "has_code": False, "ranked": ["x"], "gold": ["a"]},
    ]
    agg = aggregate(rows, ks=(1,))
    assert agg["has_code"]["n"] == 1 and agg["has_code"]["recall@1"] == 1.0
    assert agg["no_code"]["n"] == 1 and agg["no_code"]["recall@1"] == 0.0
    plain = aggregate([{"type": "factual", "ranked": ["a"], "gold": ["a"]}], ks=(1,))
    assert "has_code" not in plain and "no_code" not in plain
