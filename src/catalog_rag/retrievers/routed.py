"""M2. Route each query: prereq questions go to the graph retriever, everything else to
the fallback (bm25_codes_id in the registry). A prereq-routed query the graph cannot
answer (no known course code named) falls through to the fallback rather than returning
nothing."""
from __future__ import annotations

from collections.abc import Callable

from ..models import Chunk, RetrievalResult
from .base import Retriever


class RoutedRetriever:
    name = "routed"

    def __init__(self, prereq: Retriever, fallback: Retriever,
                 route: Callable[[str], str] | None = None) -> None:
        if route is None:
            from ..router import route  # lazy: router imports retrievers.tokenize, avoid a cycle
        self.prereq = prereq
        self.fallback = fallback
        self.route = route

    def index(self, chunks: list[Chunk]) -> None:
        self.prereq.index(chunks)
        self.fallback.index(chunks)

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        if self.route(query) == "prereq":
            out = self.prereq.retrieve(query, k=k)
            if out:
                return out
        return self.fallback.retrieve(query, k=k)
