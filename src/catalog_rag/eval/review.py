"""Print unverified gold stubs beside the raw course records they were drafted from.

    uv run python -m catalog_rag.eval.review            # verified=false rows only
    uv run python -m catalog_rag.eval.review --all      # every row

Plain stdout, grouped by question type, so it pipes into less/grep while you check each
draft against the catalog page and flip `verified` to true.
"""
from __future__ import annotations

from pathlib import Path

import typer

from ..models import GoldQuestion
from ..prereq_graph import load_courses
from .run import load_jsonl

TYPE_ORDER = ["factual", "prereq", "multi_hop", "not_in_catalog"]


def main(
    gold_path: Path = Path("data/gold/gold_stubs.jsonl"),
    courses_path: Path = Path("data/processed/courses.jsonl"),
    all: bool = typer.Option(False, "--all", help="include rows already marked verified"),
    desc_chars: int = 200,
) -> None:
    gold = load_jsonl(gold_path, GoldQuestion)
    courses = {c.course_id: c for c in load_courses(courses_path)}
    rows = gold if all else [q for q in gold if not q.verified]

    for qtype in TYPE_ORDER:
        group = [q for q in rows if q.type == qtype]
        if not group:
            continue
        print(f"== {qtype} ({len(group)}) ==")
        for q in group:
            print(f"{q.id}  {q.type}  verified={str(q.verified).lower()}")
            print(f"  Q: {q.question}")
            print(f"  draft: {q.gold_answer}")
            if not q.gold_course_ids:
                print(f"  (no gold courses; answerable={str(q.answerable).lower()})")
            for cid in q.gold_course_ids:
                c = courses.get(cid)
                if c is None:
                    print(f"    {cid}: NOT IN CORPUS")
                    continue
                desc = c.description if len(c.description) <= desc_chars else c.description[:desc_chars] + "..."
                print(f"    {c.course_id} | {c.title} | credits={c.credits} | crosslisted={c.crosslisted}")
                print(f"      prereq_raw: {c.prereq_raw}")
                print(f"      description: {desc}")
            print()
    print(f"shown {len(rows)} of {len(gold)} rows ({'all' if all else 'verified=false only'})")


if __name__ == "__main__":
    typer.run(main)
