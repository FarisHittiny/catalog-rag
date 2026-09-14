import json

from catalog_rag.eval.compare import compare, main


def _payload(rows):
    return {"generation": {"rows": {"routed": rows}}}


A = [{"id": "g1", "answer": "x", "correct": 1}, {"id": "g2", "answer": "y", "correct": 0},
     {"id": "g3", "answer": "z", "correct": 1}]
B = [{"id": "g1", "answer": "x", "correct": 1}, {"id": "g2", "answer": "y2", "correct": 1},
     {"id": "g3", "answer": "z", "correct": 0}]


def test_compare_counts_answer_and_verdict_drift():
    d = compare(_payload(A), _payload(B), "routed")
    assert d["n"] == 3
    assert d["answer_changed"] == ["g2"]
    assert d["verdict_changed"] == ["g2", "g3"]
    assert d["same_answer_verdict_flipped"] == ["g3"]
    assert d["correctness"] == (2 / 3, 2 / 3)
    same = compare(_payload(A), _payload(A), "routed")
    assert same["answer_changed"] == [] and same["verdict_changed"] == []


def test_main_prints_summary(tmp_path, capsys):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_payload(A)), encoding="utf-8")
    b.write_text(json.dumps(_payload(B)), encoding="utf-8")
    main(a, b, retriever="routed")
    out = capsys.readouterr().out
    assert "answers changed: 1/3" in out and "verdicts changed: 2/3" in out
    assert "same answer, verdict flipped: 1" in out
