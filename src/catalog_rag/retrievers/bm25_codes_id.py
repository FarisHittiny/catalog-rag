"""M1 experiment 2: bm25_codes, but courses explicitly named in the query are pinned
to the top of the ranking (in query order), then the bm25_codes ranking with those
courses removed.
"""
from __future__ import annotations

from ..models import Chunk, RetrievalResult
from .bm25_codes import BM25CodesRetriever
from .tokenize import extract_codes


class BM25CodesIdRetriever(BM25CodesRetriever):
    name = "bm25_codes_id"

    def __init__(self) -> None:
        super().__init__()
        self._chunk_by_course: dict[str, Chunk] = {}

    def index(self, chunks: list[Chunk]) -> None:
        super().index(chunks)
        self._chunk_by_course = {}
        for c in chunks:
            self._chunk_by_course.setdefault(c.course_id, c)

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        pinned = [c for c in extract_codes(query) if c in self._chunk_by_course]
        base = super().retrieve(query, k=k + len(pinned))
        top = max((r.score for r in base), default=0.0) + 1.0
        out = [
            RetrievalResult(course_id=c, score=top, chunk_id=self._chunk_by_course[c].chunk_id)
            for c in pinned
        ]
        out.extend(r for r in base if r.course_id not in pinned)
        return out[:k]
