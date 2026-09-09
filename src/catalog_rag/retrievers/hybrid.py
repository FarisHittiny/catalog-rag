"""M1. Reciprocal rank fusion of BM25 + dense, then optional cross-encoder rerank.

RRF: score(d) = sum over retrievers of 1 / (60 + rank_r(d)).
"""
from __future__ import annotations

from ..models import Chunk, RetrievalResult
from .base import Retriever


class HybridRetriever:
    name = "hybrid"

    def __init__(self, retrievers: list[Retriever], rerank_model: str | None = None) -> None:
        self.retrievers = retrievers
        self.rerank_model = rerank_model
        if rerank_model:
            self.name = "hybrid+rerank"

    def index(self, chunks: list[Chunk]) -> None:
        for r in self.retrievers:
            r.index(chunks)

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        raise NotImplementedError("M1")
