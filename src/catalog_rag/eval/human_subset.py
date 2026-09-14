"""The 30-question human-label subset that anchors judge agreement.

Stratified 12 factual / 8 prereq / 6 multi_hop / 4 not_in_catalog, chosen with a fixed
seed over ids sorted per type so the selection is stable across runs. Each row stores the
generated answer it was labeled against, so a label is only applied while that answer is
unchanged. The file is hand-edited (human_correct: null -> true/false) and never
overwritten by the eval.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

COUNTS = {"factual": 12, "prereq": 8, "multi_hop": 6, "not_in_catalog": 4}
SEED = 0


def select_ids(rows: list[dict], counts: dict[str, int] = COUNTS, seed: int = SEED) -> list[str]:
    """rows need "id" and "type". Returns ids in type order, sorted within type."""
    rng = random.Random(seed)
    out: list[str] = []
    for t, n in counts.items():
        pool = sorted(r["id"] for r in rows if r["type"] == t)
        if len(pool) < n:
            raise ValueError(f"need {n} {t} rows for the human subset, have {len(pool)}")
        out.extend(sorted(rng.sample(pool, n)))
    return out


def write_human_subset(rows: list[dict], path: Path, counts: dict[str, int] = COUNTS) -> int:
    """rows need id, type, question, gold_answer, answer. Refuses to overwrite: labels are hand work."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists; delete it by hand to regenerate (labels would be lost)")
    by_id = {r["id"]: r for r in rows}
    ids = select_ids(rows, counts)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for i in ids:
            r = by_id[i]
            f.write(json.dumps({"id": i, "question": r["question"], "gold_answer": r["gold_answer"],
                                "generated_answer": r["answer"], "human_correct": None},
                               ensure_ascii=False) + "\n")
    return len(ids)


def load_human_labels(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
