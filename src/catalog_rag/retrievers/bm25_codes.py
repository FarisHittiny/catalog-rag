"""M1 experiment 1: BM25 over tokens with fused course codes ("ecen350").

Same scoring and dedupe as BM25Retriever; only the tokenizer differs. bm25.py is
the untouched baseline.
"""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from ..models import Chunk, RetrievalResult
from .base import top_by_course
from .tokenize import tokenize


class BM25CodesRetriever:
    name = "bm25_codes"

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    @staticmethod
    def _tok(s: str) -> list[str]:
        return tokenize(s, fuse_codes=True)

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._bm25 = BM25Okapi([self._tok(c.text) for c in chunks])

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        assert self._bm25 is not None, "call index() first"
        scores = self._bm25.get_scores(self._tok(query))
        return top_by_course(self._chunks, scores, k)
