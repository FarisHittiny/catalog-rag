"""M1. Reciprocal rank fusion of several retrievers (bm25_codes + dense in the registry).

RRF: score(course) = sum over retrievers of 1 / (rrf_k + rank), rank starting at 1.
Optional cross-encoder rerank is reserved for later ("hybrid+rerank"), not implemented.
"""
from __future__ import annotations

from ..models import Chunk, RetrievalResult
from .base import Retriever


class HybridRetriever:
    name = "hybrid"

    def __init__(self, retrievers: list[Retriever], rerank_model: str | None = None, rrf_k: int = 60,
                 depth: int = 50) -> None:
        self.retrievers = retrievers
        self.rerank_model = rerank_model
        self.rrf_k = rrf_k
        self.depth = depth  # candidates pulled from each retriever before fusing
        if rerank_model:
            self.name = "hybrid+rerank"

    def index(self, chunks: list[Chunk]) -> None:
        for r in self.retrievers:
            r.index(chunks)

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        if self.rerank_model:
            raise NotImplementedError("hybrid+rerank")
        fused: dict[str, float] = {}
        chunk_of: dict[str, str | None] = {}
        for r in self.retrievers:
            for rank, res in enumerate(r.retrieve(query, k=max(k, self.depth)), start=1):
                fused[res.course_id] = fused.get(res.course_id, 0.0) + 1.0 / (self.rrf_k + rank)
                chunk_of.setdefault(res.course_id, res.chunk_id)
        ranked = sorted(fused.items(), key=lambda kv: -kv[1])[:k]
        return [RetrievalResult(course_id=c, score=s, chunk_id=chunk_of[c]) for c, s in ranked]
