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


def test_aggregate_splits_on_paraphrase_when_present():
    rows = [
        {"type": "factual", "paraphrase": True, "ranked": ["x"], "gold": ["a"]},
        {"type": "factual", "paraphrase": False, "ranked": ["a"], "gold": ["a"]},
    ]
    agg = aggregate(rows, ks=(1,))
    assert agg["paraphrase"]["n"] == 1 and agg["paraphrase"]["recall@1"] == 0.0
    assert agg["overall"]["n"] == 2
    plain = aggregate([{"type": "factual", "paraphrase": False, "ranked": ["a"], "gold": ["a"]}], ks=(1,))
    assert "paraphrase" not in plain


def test_aggregate_splits_on_holdout_b_when_present():
    rows = [
        {"type": "factual", "paraphrase": True, "holdout_b": True, "ranked": ["a"], "gold": ["a"]},
        {"type": "factual", "paraphrase": True, "holdout_b": False, "ranked": ["x"], "gold": ["a"]},
    ]
    agg = aggregate(rows, ks=(1,))
    assert agg["holdout_b"]["n"] == 1 and agg["holdout_b"]["recall@1"] == 1.0
    assert agg["paraphrase"]["n"] == 2
    assert "holdout_b" not in aggregate([{"type": "factual", "ranked": ["a"], "gold": ["a"]}], ks=(1,))


# ---- M2 answer metrics -------------------------------------------------------------
from catalog_rag.eval.metrics import (  # noqa: E402
    abstention_accuracy,
    citation_precision,
    correctness,
    judge_agreement,
)

GEN_ROWS = [
    {"id": "a", "type": "factual", "has_code": True, "ranked": ["x"], "gold": ["x"],
     "answerable": True, "cited": ["x", "y"], "abstained": False, "correct": 1},
    {"id": "b", "type": "factual", "has_code": False, "ranked": ["x"], "gold": ["z"],
     "answerable": True, "cited": [], "abstained": True, "correct": 0},
    {"id": "c", "type": "prereq", "has_code": True, "ranked": ["z"], "gold": ["z"],
     "answerable": True, "cited": ["z"], "abstained": False, "correct": 1},
    {"id": "d", "type": "not_in_catalog", "has_code": False, "ranked": ["q"], "gold": [],
     "answerable": False, "cited": ["q"], "abstained": True, "correct": 1},
    {"id": "e", "type": "not_in_catalog", "has_code": False, "ranked": ["q"], "gold": [],
     "answerable": False, "cited": [], "abstained": False, "correct": 0},
]


def test_correctness_is_mean_of_judge():
    assert correctness(GEN_ROWS) == 0.6
    assert math.isnan(correctness([]))


def test_citation_precision_only_answerable_rows_with_citations():
    # a: 1/2, c: 1/1 ; b has no citations, d/e unanswerable -> excluded
    assert citation_precision(GEN_ROWS) == 0.75
    assert math.isnan(citation_precision([GEN_ROWS[1], GEN_ROWS[3]]))


def test_abstention_accuracy_all_four_cases():
    # a: answerable, not abstained -> 1 ; b: answerable, abstained -> 0
    # c: 1 ; d: unanswerable, abstained -> 1 ; e: unanswerable, not abstained -> 0
    assert abstention_accuracy(GEN_ROWS) == 0.6


def test_judge_agreement_needs_every_label():
    judge = {"a": 1, "b": 0, "c": 1}
    human = [{"id": "a", "human_correct": True}, {"id": "b", "human_correct": True},
             {"id": "c", "human_correct": None}]
    assert judge_agreement(judge, human) is None
    human[2]["human_correct"] = True
    assert judge_agreement(judge, human) == 2 / 3
    assert judge_agreement({"a": 1}, human) is None, "label without a judge value"
    assert judge_agreement(judge, []) is None


def test_aggregate_adds_generation_columns_over_all_rows():
    agg = aggregate(GEN_ROWS, ks=(1,))
    assert agg["overall"]["n"] == 3  # retrieval n still excludes unanswerable
    assert agg["overall"]["n_gen"] == 5
    assert agg["overall"]["correctness"] == 0.6
    assert agg["overall"]["citation_prec"] == 0.75
    assert agg["overall"]["abstain_acc"] == 0.6
    assert agg["not_in_catalog"]["n_gen"] == 2 and math.isnan(agg["not_in_catalog"]["recall@1"])
    assert agg["not_in_catalog"]["correctness"] == 0.5
    assert agg["no_code"]["n_gen"] == 3
    plain = aggregate([{"type": "factual", "ranked": ["a"], "gold": ["a"]}], ks=(1,))
    assert "correctness" not in plain["overall"]


def test_markdown_renders_generation_columns_and_dashes():
    agg = aggregate(GEN_ROWS, ks=(1,))
    md = to_markdown({"routed": agg}, corpus_size=148, agreement={"routed": "unlabeled"})
    header = md.splitlines()[0]
    assert header == ("| retriever | corpus | split | n | recall@1 | mrr | n_gen | correctness | citation_prec"
                      " | abstain_acc | judge_agr |")
    assert "| routed | 148 | overall | 3 | 0.667 | 0.667 | 5 | 0.600 | 0.750 | 0.600 | unlabeled |" in md
    assert "| routed | 148 | not_in_catalog | 0 | - | - | 2 | 0.500 | - | 0.500 | - |" in md
    old = to_markdown({"bm25": aggregate([{"type": "factual", "ranked": ["a"], "gold": ["a"]}], ks=(1,))}, 148)
    assert old.splitlines()[0] == "| retriever | corpus | split | n | recall@1 | mrr |"


def test_nan_to_none_makes_payload_strict_json():
    import json
    from catalog_rag.eval.metrics import nan_to_none
    agg = aggregate(GEN_ROWS, ks=(1,))
    assert json.dumps(nan_to_none({"r": agg}), allow_nan=False)
    assert nan_to_none({"a": [float("nan"), 1.0]}) == {"a": [None, 1.0]}
