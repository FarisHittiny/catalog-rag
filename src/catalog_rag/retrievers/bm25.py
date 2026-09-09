from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from ..models import Chunk, RetrievalResult

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(s: str) -> list[str]:
    return TOKEN_RE.findall(s.lower())


class BM25Retriever:
    name = "bm25"

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._bm25 = BM25Okapi([tokenize(c.text) for c in chunks])

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        assert self._bm25 is not None, "call index() first"
        scores = self._bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: -scores[i])
        seen: set[str] = set()
        out: list[RetrievalResult] = []
        for i in order:
            c = self._chunks[i]
            if c.course_id in seen:
                continue
            seen.add(c.course_id)
            out.append(RetrievalResult(course_id=c.course_id, score=float(scores[i]), chunk_id=c.chunk_id))
            if len(out) == k:
                break
        return out
