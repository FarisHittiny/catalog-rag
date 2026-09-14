"""Row-level drift between two --generate reports for one retriever.

    python -m catalog_rag.eval.compare reports/A.json reports/B.json --retriever routed

Counts rows whose generated answer changed, rows whose judge verdict changed, and rows whose
answer is identical but the verdict flipped (judge drift on its own).
"""
from __future__ import annotations

import json
from pathlib import Path

import typer


def compare(a: dict, b: dict, retriever: str) -> dict:
    ra = {r["id"]: r for r in a["generation"]["rows"][retriever]}
    rb = {r["id"]: r for r in b["generation"]["rows"][retriever]}
    ids = [i for i in ra if i in rb]
    answer_changed = [i for i in ids if ra[i]["answer"] != rb[i]["answer"]]
    verdict_changed = [i for i in ids if ra[i]["correct"] != rb[i]["correct"]]
    same_flip = [i for i in verdict_changed if i not in answer_changed]

    def acc(rows):
        return sum(rows[i]["correct"] for i in ids) / len(ids) if ids else float("nan")

    return {"n": len(ids), "answer_changed": answer_changed, "verdict_changed": verdict_changed,
            "same_answer_verdict_flipped": same_flip, "correctness": (acc(ra), acc(rb))}


def main(a: Path, b: Path, retriever: str = "routed"):
    d = compare(json.loads(Path(a).read_text(encoding="utf-8")),
                json.loads(Path(b).read_text(encoding="utf-8")), retriever)
    n = d["n"]
    print(f"{retriever}: {n} rows paired")
    print(f"answers changed: {len(d['answer_changed'])}/{n} {d['answer_changed']}")
    print(f"verdicts changed: {len(d['verdict_changed'])}/{n} {d['verdict_changed']}")
    print(f"same answer, verdict flipped: {len(d['same_answer_verdict_flipped'])} {d['same_answer_verdict_flipped']}")
    print(f"correctness: {d['correctness'][0]:.3f} -> {d['correctness'][1]:.3f}")


if __name__ == "__main__":
    typer.run(main)
