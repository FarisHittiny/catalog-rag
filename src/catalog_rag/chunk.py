"""courses.jsonl -> chunks.jsonl. One chunk per course for now.

Course descriptions are short (usually < 150 words), so a course IS a chunk. If you
later add degree-plan pages or long prose, split those at ~300 tokens with overlap.
"""
from __future__ import annotations

from pathlib import Path

import typer

from .models import Chunk
from .prereq_graph import load_courses


def main(inp: Path = Path("data/processed/courses.jsonl"), out: Path = Path("data/processed/chunks.jsonl")):
    courses = load_courses(inp)
    with out.open("w") as f:
        for c in courses:
            ch = Chunk(chunk_id=f"{c.course_id}#0", course_id=c.course_id, dept=c.dept,
                       catalog_year=c.catalog_year, text=c.text())
            f.write(ch.model_dump_json() + "\n")
    print(f"wrote {len(courses)} chunks to {out}")


if __name__ == "__main__":
    typer.run(main)
