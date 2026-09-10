"""One command: index, run every retriever over the gold set, write the table.

    python -m catalog_rag.eval.run --retrievers bm25

Writes reports/<timestamp>.json and prints Markdown. M2 adds generation + judge.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich import print

from ..models import Chunk, GoldQuestion
from ..retrievers import BM25CodesIdRetriever, BM25CodesRetriever, BM25Retriever
from ..retrievers.tokenize import CODE_RE
from .metrics import aggregate, to_markdown

REGISTRY = {
    "bm25": BM25Retriever,
    "bm25_codes": BM25CodesRetriever,
    "bm25_codes_id": BM25CodesIdRetriever,
}  # M1: add "dense", "hybrid"


def load_jsonl(path: Path, model):
    return [model.model_validate_json(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def validate_gold(gold: list[GoldQuestion], corpus_ids: set[str]) -> None:
    """Fail loudly on placeholders and unverified rows; warn on gold ids the corpus doesn't contain.

    A placeholder silently scores as a miss and drags recall down, which is worse than a crash.
    """
    problems = []
    for q in gold:
        if any("FILL" in cid for cid in q.gold_course_ids) or "FILL" in q.gold_answer:
            problems.append(f"{q.id}: placeholder still present")
        if q.answerable and not q.gold_course_ids:
            problems.append(f"{q.id}: answerable but no gold_course_ids")
        if not q.verified:
            problems.append(f"{q.id}: not verified")
        if q.has_code != bool(CODE_RE.search(q.question)):
            problems.append(f"{q.id}: has_code={q.has_code} disagrees with question text")
        if not q.answerable and q.gold_course_ids:
            problems.append(f"{q.id}: not answerable but has gold_course_ids")
    if problems:
        raise SystemExit("gold set invalid:\n  " + "\n  ".join(problems))
    missing = sorted({cid for q in gold for cid in q.gold_course_ids if cid not in corpus_ids})
    if missing:
        print(f"[yellow]warning:[/] {len(missing)} gold course ids not in corpus (recall capped): {missing[:10]}")


def main(
    retrievers: list[str] = typer.Option(["bm25"]),
    chunks_path: Path = Path("data/processed/chunks.jsonl"),
    gold_path: Path = Path("data/gold/gold_set.jsonl"),
    k: int = 10,
    reports: Path = Path("reports"),
    note: str = typer.Option("", help="one-line provenance note written above the table"),
):
    chunks = load_jsonl(chunks_path, Chunk)
    gold = load_jsonl(gold_path, GoldQuestion)
    corpus_ids = {c.course_id for c in chunks}
    corpus_size = len(corpus_ids)
    validate_gold(gold, corpus_ids)
    results = {}
    for name in retrievers:
        r = REGISTRY[name]()
        r.index(chunks)
        rows = []
        for q in gold:
            ranked = [x.course_id for x in r.retrieve(q.question, k=k)]
            rows.append({"id": q.id, "type": q.type, "has_code": q.has_code,
                         "ranked": ranked, "gold": q.gold_course_ids})
        results[r.name] = aggregate(rows)
        misses = [row["id"] for row in rows if row["gold"] and not set(row["gold"]) & set(row["ranked"][:5])]
        if misses:
            print(f"[dim]{r.name} recall@5 misses:[/] {', '.join(misses)}")
    md = to_markdown(results, corpus_size)
    if note:
        md = f"> {note}\n\n" + md
    print(md)
    reports.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (reports / f"{stamp}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (reports / "latest.md").write_text(md + "\n", encoding="utf-8")


if __name__ == "__main__":
    typer.run(main)
