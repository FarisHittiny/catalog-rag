from catalog_rag.models import Course


def _c(description: str, prereq_raw: str) -> Course:
    return Course(course_id="ECEN 325", dept="ECEN", number="325", title="Electronics",
                  description=description, prereq_raw=prereq_raw)


def test_text_does_not_duplicate_prereq_already_in_description():
    t = _c("Electronic systems. Prerequisite: Grade of C or better in ECEN 314.",
           "Grade of C or better in ECEN 314").text()
    assert t.count("Grade of C or better in ECEN 314") == 1
    assert not t.endswith("Prerequisite: Grade of C or better in ECEN 314")


def test_text_appends_prereq_when_description_lacks_it():
    t = _c("Electronic systems.", "Grade of C or better in ECEN 314").text()
    assert t.endswith("Prerequisite: Grade of C or better in ECEN 314")


def test_text_without_prereq_appends_nothing():
    assert _c("Electronic systems.", "").text() == "ECEN 325 Electronics\nElectronic systems."
