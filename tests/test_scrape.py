"""Parser tests against a hand-written CourseLeaf-shaped fixture.

The fixture mirrors the standard CourseLeaf markup but is NOT a saved catalog page. Once
data/raw/ecen.html exists, copy two or three real <div class="courseblock"> blocks into
tests/fixtures/courseblocks.html and update the expectations here. That's the real check.
"""
from pathlib import Path

from catalog_rag.scrape import parse, parse_title

FIX = Path(__file__).parent / "fixtures" / "courseblocks.html"


def test_parse_title_strips_crosslist_and_credits():
    assert parse_title("ECEN 350/CSCE 350 Computer Architecture and Design") == (
        "ECEN 350", ["CSCE 350"], "Computer Architecture and Design")
    assert parse_title("ECEN 248 Introduction to Digital Systems Design Credits 4. 3 Lecture Hours.") == (
        "ECEN 248", [], "Introduction to Digital Systems Design")
    assert parse_title("not a course") is None


def test_parse_fixture():
    courses = {c.course_id: c for c in parse(FIX.read_text(), "ECEN", "2026-2027", "u")}
    assert set(courses) == {"ECEN 350", "ECEN 248", "ECEN 485"}

    c = courses["ECEN 350"]
    assert c.title == "Computer Architecture and Design"
    assert c.credits == "4"
    assert c.crosslisted == ["CSCE 350"]
    assert c.prereq_raw.startswith("Grade of C or better in ECEN 248")
    assert "Cross Listing" not in c.prereq_raw
    assert c.prereqs == [["ECEN 248"], ["CSCE 312", "ECEN 250"]]

    c = courses["ECEN 248"]
    assert c.prereqs == [["ENGR 217", "PHYS 207"]]
    assert c.coreqs == ["MATH 251"]
    assert "Corequisite" not in c.prereq_raw

    c = courses["ECEN 485"]
    assert c.credits == "1 to 4"
    assert c.prereqs == []  # no course codes in "junior or senior classification"
    assert c.prereq_raw.startswith("Junior or senior classification")
