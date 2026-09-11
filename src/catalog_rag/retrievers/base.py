from __future__ import annotations

from typing import Protocol

from ..models import Chunk, RetrievalResult


class Retriever(Protocol):
    name: str

    def index(self, chunks: list[Chunk]) -> None: ...

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        """Return up to k results, best first, deduplicated by course_id."""
        ...


def top_by_course(chunks: list[Chunk], scores, k: int) -> list[RetrievalResult]:
    """Best-first over chunk scores, keeping the first chunk seen per course_id, capped at k."""
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    seen: set[str] = set()
    out: list[RetrievalResult] = []
    for i in order:
        c = chunks[i]
        if c.course_id in seen:
            continue
        seen.add(c.course_id)
        out.append(RetrievalResult(course_id=c.course_id, score=float(scores[i]), chunk_id=c.chunk_id))
        if len(out) == k:
            break
    return out
