"""M2. Route each query: prereq questions go to the graph retriever, everything else to
the fallback (bm25_codes_id in the registry). A prereq-routed query the graph cannot
answer (no known course code named) falls through to the fallback rather than returning
nothing.

Post-hoc variant (registry name "routed_v2"): pass `no_code=DenseRetriever()` and non-prereq
questions that name no course code go to it instead of the fallback. Designed after the
paraphrase split showed dense at 0.711 recall@5 against 0.296 for routed, so that split is
no longer held-out for this variant; see reports/eval_report.md."""
from __future__ import annotations

from collections.abc import Callable

from ..models import Chunk, RetrievalResult
from .base import Retriever
from .tokenize import extract_codes


class RoutedRetriever:
    name = "routed"

    def __init__(self, prereq: Retriever, fallback: Retriever,
                 route: Callable[[str], str] | None = None,
                 no_code: Retriever | None = None, name: str = "routed") -> None:
        if route is None:
            from ..router import route  # lazy: router imports retrievers.tokenize, avoid a cycle
        self.prereq = prereq
        self.fallback = fallback
        self.no_code = no_code
        self.route = route
        self.name = name

    def index(self, chunks: list[Chunk]) -> None:
        self.prereq.index(chunks)
        self.fallback.index(chunks)
        if self.no_code is not None:
            self.no_code.index(chunks)

    def _fallback_for(self, query: str) -> Retriever:
        if self.no_code is not None and not extract_codes(query):
            return self.no_code
        return self.fallback

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        if self.route(query) == "prereq":
            out = self.prereq.retrieve(query, k=k)
            if out:
                return out
        return self._fallback_for(query).retrieve(query, k=k)

    def context(self, query: str, k: int = 5) -> list[str]:
        """Course ids to hand the generator. A prereq-routed query with graph results gets the
        queried course(s) first, then every graph result (lists are short, so no cap): the
        generator abstained when the course the student asked about was missing from its
        context. Anything else gets the fallback's top-k, like every other retriever."""
        if self.route(query) == "prereq":
            out = self.prereq.retrieve(query, k=10**6)
            if out:
                asked = extract_codes(query)
                return asked + [x.course_id for x in out if x.course_id not in asked]
        return [x.course_id for x in self._fallback_for(query).retrieve(query, k=k)]
