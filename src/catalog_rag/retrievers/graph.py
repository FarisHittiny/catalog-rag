"""M2. Prereq-graph retriever: courses that list the code(s) named in the query as a
prerequisite (prereq_graph.unlocked_by), ordered by course number.

The graph is built from the indexed chunks' `prereqs` field, so it covers exactly the
corpus the other retrievers see. Chunk files written before that field existed carry no
prereqs; for those, `courses` (or `courses_path`) is used instead.

Meant to be reached through RoutedRetriever for prereq-routed questions; standalone it
answers every query the same way (and returns nothing when no known code is named).
"""
from __future__ import annotations

import re
from pathlib import Path

import networkx as nx

from ..models import Chunk, Course, RetrievalResult
from ..prereq_graph import build_graph, load_courses, unlocked_by
from .tokenize import extract_codes

_NUM = re.compile(r"\d+")


def _sort_key(course_id: str) -> tuple[int, str]:
    m = _NUM.search(course_id)
    return (int(m[0]) if m else 0, course_id)


def graph_from_chunks(chunks: list[Chunk]) -> nx.DiGraph:
    """Edge prereq -> course, one node per indexed course (first chunk's prereqs win)."""
    g = nx.DiGraph()
    seen: set[str] = set()
    for c in chunks:
        if c.course_id in seen:
            continue
        seen.add(c.course_id)
        g.add_node(c.course_id, groups=c.prereqs)
        for group in c.prereqs:
            for p in group:
                g.add_edge(p, c.course_id)
    return g


class GraphRetriever:
    name = "graph"

    def __init__(self, courses: list[Course] | None = None,
                 courses_path: Path = Path("data/processed/courses.jsonl")) -> None:
        self._courses = courses
        self.courses_path = courses_path
        self._g: nx.DiGraph | None = None
        self._chunk_of: dict[str, str] = {}

    def index(self, chunks: list[Chunk]) -> None:
        if any(c.prereqs for c in chunks):
            self._g = graph_from_chunks(chunks)
        elif self._courses is not None:
            self._g = build_graph(self._courses)
        else:
            if not self.courses_path.exists():
                raise FileNotFoundError(
                    f"chunks carry no prereqs and {self.courses_path} is missing; re-run catalog_rag.chunk")
            self._g = build_graph(load_courses(self.courses_path))
        self._chunk_of = {}
        for c in chunks:
            self._chunk_of.setdefault(c.course_id, c.chunk_id)

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        assert self._g is not None, "call index() first"
        found: list[str] = []
        for code in extract_codes(query):
            for succ in unlocked_by(self._g, code):
                if succ not in found:
                    found.append(succ)
        found.sort(key=_sort_key)
        n = len(found)
        return [RetrievalResult(course_id=c, score=float(n - i), chunk_id=self._chunk_of.get(c))
                for i, c in enumerate(found[:k])]
