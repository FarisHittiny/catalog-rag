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
