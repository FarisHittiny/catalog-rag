"""Retrieval metrics. Pure functions over lists of course ids. Unit-tested.

All functions take `ranked` (retrieved course ids, best first) and `gold` (set of
course ids a correct answer must draw from).
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable


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


def aggregate(
    rows: list[dict],
    ks: tuple[int, ...] = (1, 5, 10),
) -> dict[str, dict[str, float]]:
    """rows: [{"type": str, "ranked": [...], "gold": [...]}, ...]

    Returns {"overall": {...}, "<type>": {...}} with recall@k and mrr.
    Questions with empty gold (not_in_catalog) are excluded from retrieval metrics.
    """
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if not r["gold"]:
            continue
        buckets["overall"].append(r)
        buckets[r["type"]].append(r)

    out: dict[str, dict[str, float]] = {}
    for name, rs in buckets.items():
        m: dict[str, float] = {"n": float(len(rs))}
        for k in ks:
            m[f"recall@{k}"] = _mean([recall_at_k(r["ranked"], r["gold"], k) for r in rs])
        m["mrr"] = _mean([reciprocal_rank(r["ranked"], r["gold"]) for r in rs])
        out[name] = m
    return out


def to_markdown(results: dict[str, dict[str, dict[str, float]]], corpus_size: int) -> str:
    """results: {retriever_name: aggregate(...)}"""
    ks = [c for c in next(iter(results.values()))["overall"] if c.startswith("recall@")]
    header = "| retriever | corpus | split | n | " + " | ".join(ks) + " | mrr |"
    sep = "|" + "---|" * (5 + len(ks))
    lines = [header, sep]
    for name, agg in results.items():
        for split, m in agg.items():
            vals = " | ".join(f"{m[k]:.3f}" for k in ks)
            lines.append(f"| {name} | {corpus_size} | {split} | {int(m['n'])} | {vals} | {m['mrr']:.3f} |")
    return "\n".join(lines)
