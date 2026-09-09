"""Parser tests against real CourseLeaf markup.

tests/fixtures/courseblocks.html holds the actual <div class="courseblock"> blocks for ECEN 350
and ECEN 248, copied verbatim from the saved 2026-2027 ECEN catalog page. The expectations below
were checked against that page. If the catalog changes, re-scrape, re-copy the blocks, and update
the expectations here.
"""
from pathlib import Path

from catalog_rag.scrape import _clean, parse, parse_title

FIX = Path(__file__).parent / "fixtures" / "courseblocks.html"


def test_clean_collapses_space_before_punctuation():
    # get_text(" ") leaves a space between an <a> code link and the punctuation after it.
    assert _clean("MATH 152 ; grade") == "MATH 152; grade"
    assert _clean("ECEN\xa0350 .") == "ECEN 350."
    assert _clean("(a )") == "(a)"
    assert _clean("  a   b  ") == "a b"


def test_parse_title_strips_crosslist_and_credits():
    assert parse_title("ECEN 350/CSCE 350 Computer Architecture and Design") == (
        "ECEN 350", ["CSCE 350"], "Computer Architecture and Design")
    assert parse_title("ECEN 248 Introduction to Digital Systems Design Credits 4. 3 Lecture Hours.") == (
        "ECEN 248", [], "Introduction to Digital Systems Design")
    assert parse_title("not a course") is None


def test_parse_fixture():
    courses = {c.course_id: c for c in parse(FIX.read_text(encoding="utf-8"), "ECEN", "2026-2027", "u")}
    assert set(courses) == {"ECEN 350", "ECEN 248"}

    c = courses["ECEN 350"]
    assert c.dept == "ECEN" and c.number == "350"
    assert c.title == "Computer Architecture and Design"
    assert c.credits == "4"
    assert c.crosslisted == ["CSCE 350"]
    assert c.description.startswith("Credits 4. 3 Lecture Hours. 3 Lab Hours.")
    assert c.description.endswith("Cross Listing: CSCE 350/ECEN 350.")
    assert c.prereq_raw == "Grade of C or better in ECEN 248 and CSCE 120; junior or senior classification"
    assert "Cross Listing" not in c.prereq_raw
    assert c.prereqs == [["ECEN 248"], ["CSCE 120"]]
    assert c.coreqs == []

    c = courses["ECEN 248"]
    assert c.title == "Introduction to Digital Systems Design"
    assert c.credits == "4"
    assert c.crosslisted == []
    assert c.prereq_raw == (
        "Grade of C or better in MATH 152; grade of C or better in PHYS 207 or PHYS 208, "
        "or concurrent enrollment")
    assert c.prereqs == [["MATH 152"], ["PHYS 207", "PHYS 208"]]
    assert c.coreqs == []
