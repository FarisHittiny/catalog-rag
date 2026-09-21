"""Retrieval and answer metrics. Pure functions over row dicts. Unit-tested.

Retrieval functions take `ranked` (retrieved course ids, best first) and `gold` (set of
course ids a correct answer must draw from). Answer metrics (M2) read generated-row keys:
`answerable`, `cited`, `abstained`, `correct` (the judge's 0/1).
"""
from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable

GEN_COLS = ("n_gen", "correctness", "citation_prec", "abstain_acc")


def recall_at_k(ranked: list[str], gold: Iterable[str], k: int) -> float:
    gold = set(gold)
    if not gold:
        return float("nan")
    return len(gold & set(ranked[:k])) / len(gold)


def reciprocal_rank(ranked: list[str], gold: Iterable[str]) -> float:
    gold = set(gold)
    for i, cid in enumerate(ranked, start=1):
        if cid in gold:
            return 1.0 / i
    return 0.0


def _mean(xs: list[float]) -> float:
    xs = [x for x in xs if x == x]  # drop nan
    return sum(xs) / len(xs) if xs else float("nan")


# ---- answer metrics (M2) --------------------------------------------------------------
def correctness(rows: list[dict]) -> float:
    """Mean of the judge's 0/1 over every row (answerable or not)."""
    return _mean([float(r["correct"]) for r in rows])


def citation_precision(rows: list[dict]) -> float:
    """|cited & gold| / |cited|, over answerable rows that cite at least one course."""
    vals = []
    for r in rows:
        if r["answerable"] and r["cited"]:
            cited = set(r["cited"])
            vals.append(len(cited & set(r["gold"])) / len(cited))
    return _mean(vals)


def abstention_accuracy(rows: list[dict]) -> float:
    """not_in_catalog rows should abstain; answerable rows should not."""
    return _mean([float(bool(r["abstained"]) == (not r["answerable"])) for r in rows])


def judge_agreement(judge_by_id: dict[str, int], human: list[dict]) -> float | None:
    """Fraction of human-labeled rows where the judge agrees. None until every row is labeled
    and has a judge value (a partial number would look like a result)."""
    if not human:
        return None
    hits = []
    for h in human:
        if h.get("human_correct") is None or h["id"] not in judge_by_id:
            return None
        hits.append(float(bool(judge_by_id[h["id"]]) == bool(h["human_correct"])))
    return sum(hits) / len(hits)


# ---- aggregation ----------------------------------------------------------------------
def _splits(r: dict) -> list[str]:
    out = ["overall", r["type"]]
    if "has_code" in r:
        out.append("has_code" if r["has_code"] else "no_code")
    if r.get("paraphrase"):
        out.append("paraphrase")
    if r.get("holdout_b"):
        out.append("holdout_b")
    return out


def aggregate(
    rows: list[dict],
    ks: tuple[int, ...] = (1, 5, 10),
) -> dict[str, dict[str, float]]:
    """rows: [{"type": str, "ranked": [...], "gold": [...], optional "has_code", optional
    generation keys}, ...]

    Returns {"overall": {...}, "<type>": {...}, ...} with recall@k and mrr. Questions with
    empty gold (not_in_catalog) are excluded from retrieval metrics. When rows carry a
    judge score, every row (including not_in_catalog) also feeds correctness,
    citation_prec, abstain_acc and n_gen per split.
    """
    ret: dict[str, list[dict]] = defaultdict(list)
    gen: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["gold"]:
            for s in _splits(r):
                ret[s].append(r)
        if "correct" in r:
            for s in _splits(r):
                gen[s].append(r)

    out: dict[str, dict[str, float]] = {}
    for name in list(dict.fromkeys([*ret, *gen])):
        rs = ret.get(name, [])
        m: dict[str, float] = {"n": float(len(rs))}
        for k in ks:
            m[f"recall@{k}"] = _mean([recall_at_k(r["ranked"], r["gold"], k) for r in rs])
        m["mrr"] = _mean([reciprocal_rank(r["ranked"], r["gold"]) for r in rs])
        if name in gen:
            gs = gen[name]
            m["n_gen"] = float(len(gs))
            m["correctness"] = correctness(gs)
            m["citation_prec"] = citation_precision(gs)
            m["abstain_acc"] = abstention_accuracy(gs)
        out[name] = m
    return out


def _fmt(x: float) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def nan_to_none(obj):
    """Recursively replace NaN so the JSON report stays valid JSON."""
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: nan_to_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [nan_to_none(v) for v in obj]
    return obj


def to_markdown(
    results: dict[str, dict[str, dict[str, float]]],
    corpus_size: int,
    agreement: dict[str, str] | None = None,
) -> str:
    """results: {retriever_name: aggregate(...)}. agreement: {retriever_name: "0.933 (30/30)" | "unlabeled"},
    rendered on the overall row only. Generation columns appear when any retriever has them."""
    ks = [c for c in next(iter(results.values()))["overall"] if c.startswith("recall@")]
    with_gen = any("correctness" in agg.get("overall", {}) for agg in results.values())
    cols = ["retriever", "corpus", "split", "n", *ks, "mrr"]
    if with_gen:
        cols += [*GEN_COLS, "judge_agr"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for name, agg in results.items():
        for split, m in agg.items():
            vals = [name, str(corpus_size), split, str(int(m["n"]))]
            vals += [_fmt(m[k]) for k in ks] + [_fmt(m["mrr"])]
            if with_gen:
                vals += [str(int(m["n_gen"])) if "n_gen" in m else "-"]
                vals += [_fmt(m.get(c, float("nan"))) for c in GEN_COLS[1:]]
                vals.append((agreement or {}).get(name, "-") if split == "overall" and "correctness" in m else "-")
            lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)
