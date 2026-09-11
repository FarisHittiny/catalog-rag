from catalog_rag.models import Chunk, RetrievalResult
from catalog_rag.retrievers.hybrid import HybridRetriever


class Fixed:
    """Retriever stub returning a fixed course ranking."""

    def __init__(self, name: str, order: list[str]) -> None:
        self.name = name
        self.order = order
        self.indexed = False

    def index(self, chunks: list[Chunk]) -> None:
        self.indexed = True

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        return [RetrievalResult(course_id=c, score=float(len(self.order) - i), chunk_id=f"{c}#{self.name}")
                for i, c in enumerate(self.order[:k])]


def test_rrf_order_hand_computed():
    a, b = Fixed("a", ["x", "y", "z"]), Fixed("b", ["y", "z", "x"])
    h = HybridRetriever([a, b])
    h.index([])
    assert a.indexed and b.indexed
    out = h.retrieve("q", k=10)
    assert [o.course_id for o in out] == ["y", "x", "z"]
    k = 60
    assert abs(out[0].score - (1 / (k + 2) + 1 / (k + 1))) < 1e-12
    assert out[0].chunk_id == "y#a", "chunk_id comes from the first retriever that returned the course"


def test_course_in_only_one_list_still_appears_and_k_respected():
    h = HybridRetriever([Fixed("a", ["x", "y"]), Fixed("b", ["y", "w"])])
    h.index([])
    ids = [o.course_id for o in h.retrieve("q", k=10)]
    assert ids[0] == "y" and set(ids) == {"x", "y", "w"}
    assert len(h.retrieve("q", k=2)) == 2


def test_name_reflects_reranker_flag():
    assert HybridRetriever([]).name == "hybrid"
    assert HybridRetriever([], rerank_model="x").name == "hybrid+rerank"
