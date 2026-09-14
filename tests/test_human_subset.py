import json
from collections import Counter

import pytest

from catalog_rag.eval.human_subset import COUNTS, select_ids, write_human_subset

ROWS = ([{"id": f"f{i:02d}", "type": "factual"} for i in range(40)]
        + [{"id": f"p{i:02d}", "type": "prereq"} for i in range(25)]
        + [{"id": f"m{i:02d}", "type": "multi_hop"} for i in range(20)]
        + [{"id": f"n{i:02d}", "type": "not_in_catalog"} for i in range(15)])


def test_counts_are_the_spec():
    assert COUNTS == {"factual": 12, "prereq": 8, "multi_hop": 6, "not_in_catalog": 4}


def test_select_is_stratified_and_deterministic():
    ids = select_ids(ROWS)
    assert len(ids) == 30 and len(set(ids)) == 30
    by_type = {r["id"]: r["type"] for r in ROWS}
    assert Counter(by_type[i] for i in ids) == COUNTS
    assert ids == select_ids(list(reversed(ROWS)))  # order of input rows does not matter


def test_write_rows_and_refuse_overwrite(tmp_path):
    gen = [dict(r, question=f"q {r['id']}", gold_answer="g", answer=f"a {r['id']}") for r in ROWS]
    path = tmp_path / "human_labels.jsonl"
    written = write_human_subset(gen, path)
    assert written == 30
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 30
    assert set(rows[0]) == {"id", "question", "gold_answer", "generated_answer", "human_correct"}
    assert all(r["human_correct"] is None for r in rows)
    assert rows[0]["generated_answer"] == f"a {rows[0]['id']}"
    with pytest.raises(FileExistsError):
        write_human_subset(gen, path)


def test_select_raises_when_a_type_is_short():
    with pytest.raises(ValueError):
        select_ids([r for r in ROWS if r["type"] != "prereq"])
