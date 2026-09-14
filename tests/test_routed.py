from catalog_rag.models import Chunk, RetrievalResult
from catalog_rag.retrievers.routed import RoutedRetriever


class Stub:
    def __init__(self, name: str, empty: bool = False) -> None:
        self.name = name
        self.empty = empty
        self.indexed = False
        self.queries: list[str] = []

    def index(self, chunks: list[Chunk]) -> None:
        self.indexed = True

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        self.queries.append(query)
        return [] if self.empty else [RetrievalResult(course_id=self.name, score=1.0)]


def test_dispatches_on_route_and_indexes_both():
    g, f = Stub("graph"), Stub("fallback")
    r = RoutedRetriever(g, f, route=lambda q: "prereq" if "after" in q else "other")
    r.index([])
    assert g.indexed and f.indexed
    assert r.retrieve("what comes after X")[0].course_id == "graph"
    assert r.retrieve("how many credits is X")[0].course_id == "fallback"
    assert g.queries == ["what comes after X"] and f.queries == ["how many credits is X"]
    assert r.name == "routed"


def test_prereq_route_with_empty_graph_result_falls_back():
    g, f = Stub("graph", empty=True), Stub("fallback")
    r = RoutedRetriever(g, f, route=lambda q: "prereq")
    r.index([])
    assert r.retrieve("what does the data structures class unlock?")[0].course_id == "fallback"
    assert g.queries == f.queries  # graph was consulted first


def test_default_route_is_the_real_router():
    g, f = Stub("graph"), Stub("fallback")
    r = RoutedRetriever(g, f)
    r.index([])
    assert r.retrieve("what does ECEN 350 unlock?")[0].course_id == "graph"
    assert r.retrieve("what is ECEN 350 about?")[0].course_id == "fallback"


class ManyStub(Stub):
    """Graph-like: returns as many results as asked for."""

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        self.queries.append(query)
        return [RetrievalResult(course_id=f"{self.name}{i}", score=1.0) for i in range(min(k, 12))]


def test_context_for_prereq_route_is_queried_course_plus_all_graph_results():
    g, f = ManyStub("g"), Stub("fallback")
    r = RoutedRetriever(g, f, route=lambda q: "prereq")
    r.index([])
    ids = r.context("what can I take after ECEN 248 and ecen350?", k=5)
    assert ids[:2] == ["ECEN 248", "ECEN 350"]  # queried courses first, in question order
    assert ids[2:] == [f"g{i}" for i in range(12)]  # every graph result, not capped at k


def test_context_for_other_route_or_empty_graph_is_fallback_top_k():
    g, f = Stub("graph", empty=True), ManyStub("f")
    r = RoutedRetriever(g, f, route=lambda q: "prereq" if "after" in q else "other")
    r.index([])
    assert r.context("credits for ECEN 248?", k=5) == [f"f{i}" for i in range(5)]
    assert r.context("what comes after ECEN 999?", k=3) == [f"f{i}" for i in range(3)]
