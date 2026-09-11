"""DenseRetriever with an injected fake embedder: no model download, no torch."""
import numpy as np

from catalog_rag.models import Chunk
from catalog_rag.retrievers.dense import DenseRetriever

DIM = 32


class FakeEmbedder:
    """Hashed bag-of-words, L2-normalized. Deterministic; counts calls."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, texts: list[str]) -> np.ndarray:
        self.calls += 1
        out = np.zeros((len(texts), DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in t.lower().split():
                out[i, sum(map(ord, w)) % DIM] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return out / norms


def _chunks() -> list[Chunk]:
    rows = [
        ("ECEN 350", "computer architecture and design pipelines memory"),
        ("CSCE 410", "operating systems scheduling memory allocation"),
        ("CSCE 434", "compiler design parsing code generation"),
    ]
    return [Chunk(chunk_id=f"{c}#0", course_id=c, dept=c[:4], catalog_year="2026", text=t) for c, t in rows]


def _retriever(tmp_path, emb=None):
    return DenseRetriever(model_name="fake", cache_path=tmp_path / "emb.npy", embedder=emb or FakeEmbedder(),
                          query_prefix="")


def test_nearest_chunk_ranks_first(tmp_path):
    r = _retriever(tmp_path)
    r.index(_chunks())
    out = r.retrieve("compiler design parsing", k=3)
    assert out[0].course_id == "CSCE 434"
    assert len(out) == 3 and len({o.course_id for o in out}) == 3


def test_results_deduped_by_course(tmp_path):
    chunks = _chunks() + [Chunk(chunk_id="CSCE 434#1", course_id="CSCE 434", dept="CSCE", catalog_year="2026",
                                text="compiler design parsing again")]
    r = _retriever(tmp_path)
    r.index(chunks)
    out = r.retrieve("compiler design parsing", k=10)
    assert [o.course_id for o in out].count("CSCE 434") == 1


def test_cache_hit_skips_embedding(tmp_path):
    emb = FakeEmbedder()
    r1 = _retriever(tmp_path, emb)
    r1.index(_chunks())
    assert emb.calls == 1
    r2 = _retriever(tmp_path, emb)
    r2.index(_chunks())
    assert emb.calls == 1, "second index on identical chunks must load the cache"
    assert r2.retrieve("operating systems", k=1)[0].course_id == "CSCE 410"


def test_changed_chunk_reembeds(tmp_path):
    emb = FakeEmbedder()
    r = _retriever(tmp_path, emb)
    r.index(_chunks())
    changed = _chunks()
    changed[0] = changed[0].model_copy(update={"text": "something else entirely"})
    r.index(changed)
    assert emb.calls == 2


def test_retrieve_requires_index(tmp_path):
    r = _retriever(tmp_path)
    try:
        r.retrieve("x")
    except AssertionError:
        return
    raise AssertionError("retrieve before index should assert")
