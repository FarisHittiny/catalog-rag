from catalog_rag.models import Chunk, Course
from catalog_rag.retrievers.graph import GraphRetriever

EDGES = {  # course -> AND-of-OR prereq groups
    "ECEN 248": [],
    "ECEN 350": [["ECEN 248"]],
    "CSCE 312": [["ECEN 248"]],
    "ECEN 449": [["ECEN 248"]],
    "ECEN 469": [["ECEN 350"]],
}


def _courses() -> list[Course]:
    return [Course(course_id=cid, dept=cid[:4], number=cid[5:], title=cid, prereqs=p) for cid, p in EDGES.items()]


def _chunks(with_prereqs: bool = True) -> list[Chunk]:
    return [Chunk(chunk_id=f"{cid}#0", course_id=cid, dept=cid[:4], catalog_year="2026", text=cid,
                  prereqs=p if with_prereqs else []) for cid, p in EDGES.items()]


def _r() -> GraphRetriever:
    r = GraphRetriever()  # no courses given: graph must come from the chunks themselves
    r.index(_chunks())
    return r


def test_graph_is_built_from_indexed_chunks_and_ordered_by_course_number():
    out = _r().retrieve("what can I take after ECEN 248?", k=10)
    assert [o.course_id for o in out] == ["CSCE 312", "ECEN 350", "ECEN 449"]
    assert out[0].score > out[1].score > out[2].score
    assert out[0].chunk_id == "CSCE 312#0"


def test_subset_corpus_only_yields_indexed_courses():
    r = GraphRetriever()
    r.index([c for c in _chunks() if c.dept == "ECEN"])  # CSCE 312 not indexed
    assert [o.course_id for o in r.retrieve("after ECEN 248")] == ["ECEN 350", "ECEN 449"]


def test_legacy_chunks_without_prereqs_fall_back_to_courses():
    r = GraphRetriever(courses=_courses())
    r.index(_chunks(with_prereqs=False))
    assert [o.course_id for o in r.retrieve("after ECEN 350")] == ["ECEN 469"]


def test_two_codes_union_in_query_order_then_sorted():
    out = _r().retrieve("after ECEN 350 and ecen248 what opens up", k=10)
    assert [o.course_id for o in out] == ["CSCE 312", "ECEN 350", "ECEN 449", "ECEN 469"]


def test_no_code_returns_empty_and_unknown_code_returns_empty():
    assert _r().retrieve("what does the data structures class unlock?") == []
    assert _r().retrieve("what does MATH 999 unlock?") == []


def test_k_respected():
    assert len(_r().retrieve("after ECEN 248", k=2)) == 2
