"""Parse prerequisite strings into AND-of-OR groups and build a directed graph.

parse_prereq_string("ECEN 248 and (CSCE 312 or ECEN 250)")
    -> [["ECEN 248"], ["CSCE 312", "ECEN 250"]]

This is a heuristic parser. Catalog prereq prose is inconsistent ("junior or senior
classification", "grade of C or better in"). We extract course codes and split on
top-level 'and' vs 'or'. Log anything ambiguous; the gold set will catch mistakes.
"""
from __future__ import annotations

import re
from pathlib import Path

import networkx as nx

from .models import Course

CODE_RE = re.compile(r"\b([A-Z]{3,4})\s(\d{3}[A-Z]?)\b")


def _codes(s: str) -> list[str]:
    return [f"{a} {b}" for a, b in CODE_RE.findall(s)]


def parse_prereq_string(raw: str) -> list[list[str]]:
    if not raw:
        return []
    # Split on ';' or ' and ' at top level, then each piece is an OR-group.
    pieces = re.split(r";|\band\b", raw)
    groups: list[list[str]] = []
    for p in pieces:
        codes = _codes(p)
        if codes:
            groups.append(list(dict.fromkeys(codes)))  # dedupe, keep order
    return groups


def build_graph(courses: list[Course]) -> nx.DiGraph:
    """Edge prereq -> course. Node attr 'groups' keeps the AND/OR structure."""
    g = nx.DiGraph()
    for c in courses:
        g.add_node(c.course_id, title=c.title, groups=c.prereqs)
        for group in c.prereqs:
            for p in group:
                g.add_edge(p, c.course_id)
    return g


def unlocked_by(g: nx.DiGraph, course_id: str) -> list[str]:
    """Courses that list course_id as a prerequisite (direct successors)."""
    return sorted(g.successors(course_id)) if course_id in g else []


def required_for(g: nx.DiGraph, course_id: str) -> list[list[str]]:
    """Direct prerequisite groups for course_id."""
    return g.nodes[course_id].get("groups", []) if course_id in g else []


def load_courses(path: Path = Path("data/processed/courses.jsonl")) -> list[Course]:
    return [Course.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
