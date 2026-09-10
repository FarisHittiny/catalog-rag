from catalog_rag.models import Chunk
from catalog_rag.retrievers import BM25CodesIdRetriever, BM25CodesRetriever


def _chunks() -> list[Chunk]:
    rows = [
        ("ECEN 350", "ECEN 350 Computer Architecture\nPrerequisite: Grade of C or better in ECEN 248"),
        ("ECEN 248", "ECEN 248 Digital Systems\nCombinational and sequential design"),
        ("CSCE 221", "CSCE 221 Data Structures\nStacks queues lists; prerequisite CSCE 120"),
        ("ECEN 449", "ECEN 449 Microprocessors\nPrerequisite: Grade of C or better in ECEN 248"),
    ]
    return [Chunk(chunk_id=f"{cid}#0", course_id=cid, dept=cid[:4], catalog_year="2026", text=t) for cid, t in rows]


def _ids(rs):
    return [r.course_id for r in rs]


def test_named_course_is_pinned_first():
    r = BM25CodesIdRetriever(); r.index(_chunks())
    out = r.retrieve("what can I take after ECEN 248?", k=10)
    assert out[0].course_id == "ECEN 248"
    assert len(set(_ids(out))) == len(out)


def test_multiple_codes_keep_query_order():
    r = BM25CodesIdRetriever(); r.index(_chunks())
    assert _ids(r.retrieve("is CSCE 221 like ecen350?", k=10))[:2] == ["CSCE 221", "ECEN 350"]


def test_unknown_code_falls_through_to_bm25_codes_order():
    a, b = BM25CodesIdRetriever(), BM25CodesRetriever()
    a.index(_chunks()); b.index(_chunks())
    q = "prerequisite for ECEN 999 digital design"
    assert _ids(a.retrieve(q, k=10)) == _ids(b.retrieve(q, k=10))


def test_result_respects_k():
    r = BM25CodesIdRetriever(); r.index(_chunks())
    assert len(r.retrieve("ECEN 350 and ECEN 248 and CSCE 221", k=2)) == 2
