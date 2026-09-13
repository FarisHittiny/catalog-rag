import json
from pathlib import Path

from catalog_rag.eval.review import main


def _write(tmp_path: Path):
    courses = [
        {"course_id": "ECEN 248", "dept": "ECEN", "number": "248", "title": "Intro Digital", "credits": "4",
         "description": "D" * 300, "prereq_raw": "MATH 152", "prereqs": [["MATH 152"]], "coreqs": [],
         "crosslisted": [], "catalog_year": "2026", "source_url": ""},
        {"course_id": "CSCE 410", "dept": "CSCE", "number": "410", "title": "Operating Systems", "credits": "3",
         "description": "short", "prereq_raw": "CSCE 313", "prereqs": [["CSCE 313"]], "coreqs": [],
         "crosslisted": [], "catalog_year": "2026", "source_url": ""},
    ]
    gold = [
        {"id": "g001", "question": "credits for intro digital?", "dept": "ECEN", "type": "factual",
         "gold_course_ids": ["ECEN 248"], "gold_answer": "4 credits.", "answerable": True, "notes": "",
         "verified": False, "has_code": False},
        {"id": "g002", "question": "what needs CSCE 410?", "dept": "CSCE", "type": "prereq",
         "gold_course_ids": ["CSCE 410", "CSCE 999"], "gold_answer": "CSCE 410", "answerable": True,
         "notes": "", "verified": True, "has_code": True},
        {"id": "g003", "question": "who teaches it?", "dept": "CSCE", "type": "not_in_catalog",
         "gold_course_ids": [], "gold_answer": "Not in catalog.", "answerable": False, "notes": "",
         "verified": False, "has_code": False},
    ]
    cp, gp = tmp_path / "courses.jsonl", tmp_path / "gold.jsonl"
    cp.write_text("".join(json.dumps(r) + "\n" for r in courses), encoding="utf-8")
    gp.write_text("".join(json.dumps(r) + "\n" for r in gold), encoding="utf-8")
    return gp, cp


def test_unverified_rows_printed_with_record_fields(tmp_path, capsys):
    gp, cp = _write(tmp_path)
    main(gold_path=gp, courses_path=cp, all=False, desc_chars=200)
    out = capsys.readouterr().out
    assert "g001" in out and "credits for intro digital?" in out and "draft: 4 credits." in out
    assert "ECEN 248 | Intro Digital | credits=4" in out and "prereq_raw: MATH 152" in out
    assert "D" * 200 + "..." in out and "D" * 201 not in out
    assert "g002" not in out, "verified rows hidden by default"
    assert "g003" in out and "answerable=false" in out
    assert out.index("== factual") < out.index("== not_in_catalog")
    assert "shown 2 of 3" in out


def test_all_flag_shows_verified_and_flags_missing_corpus_id(tmp_path, capsys):
    gp, cp = _write(tmp_path)
    main(gold_path=gp, courses_path=cp, all=True, desc_chars=200)
    out = capsys.readouterr().out
    assert "g002" in out and "CSCE 999: NOT IN CORPUS" in out
    assert out.index("== factual") < out.index("== prereq") < out.index("== not_in_catalog")
    assert "shown 3 of 3" in out
