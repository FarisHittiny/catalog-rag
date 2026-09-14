"""generate() with a fake client: checks prompt content, citation parsing, abstention."""
from catalog_rag.generate import ABSTAIN, SYSTEM_PROMPT, Generation, format_courses, generate, parse_answer
from catalog_rag.models import Course


class FakeClient:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.seen: list[tuple[str, list[dict]]] = []

    def chat(self, model, messages):
        self.seen.append((model, messages))

        class R:
            content = self.reply
            usage = {}
            cached = False

        return R()


COURSES = [
    Course(course_id="ECEN 350", dept="ECEN", number="350", title="Computer Architecture", credits="4",
           description="Pipelines and memory.", prereq_raw="ECEN 248", crosslisted=["CSCE 350"]),
    Course(course_id="CSCE 121", dept="CSCE", number="121", title="Intro Programming", credits="4",
           description="C++ basics."),
]


def test_format_courses_includes_every_field():
    s = format_courses(COURSES)
    for needle in ("ECEN 350", "Computer Architecture", "credits: 4", "Pipelines and memory.",
                   "prerequisite: ECEN 248", "cross-listed: CSCE 350", "CSCE 121", "C++ basics."):
        assert needle in s
    assert s.index("ECEN 350") < s.index("CSCE 121")


def test_generate_sends_system_prompt_and_courses_and_parses_citations():
    c = FakeClient("ECEN 350 is 4 credits [ECEN 350]. It builds on [ECEN 248] and again [ECEN 350].")
    g = generate("how many credits is ECEN 350?", COURSES, c, model="gen")
    assert isinstance(g, Generation)
    model, msgs = c.seen[0]
    assert model == "gen" and msgs[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert "how many credits is ECEN 350?" in msgs[1]["content"] and "Pipelines and memory." in msgs[1]["content"]
    assert g.cited_course_ids == ["ECEN 350", "ECEN 248"]
    assert g.abstained is False


def test_citation_regex_is_strict_about_case_but_tolerates_missing_space():
    g = parse_answer("see [ECEN350] and [ecen 350] and [MATH 1519] and [fall 2026]")
    assert g.cited_course_ids == ["ECEN 350"]


def test_abstention_detected_exactly_and_with_curly_quotes():
    assert parse_answer(ABSTAIN).abstained is True
    assert parse_answer("  “The catalog doesn’t cover that.”\n").abstained is True
    assert parse_answer("the catalog doesn't cover that.").abstained is True
    assert parse_answer("The catalog doesn't cover that, but ECEN 350 is 4 credits [ECEN 350].").abstained is False
    assert parse_answer("ECEN 350 is 4 credits [ECEN 350].").abstained is False


def test_abstention_that_keeps_talking_is_not_an_abstention():
    assert parse_answer("The catalog doesn't cover that. [ECEN 350]").abstained is False
    assert parse_answer("[ECEN 350] " + ABSTAIN).abstained is False


def test_abstention_tolerates_markdown_and_missing_period():
    assert parse_answer("**The catalog doesn't cover that.**").abstained is True
    assert parse_answer("The catalog doesn't cover that").abstained is True


def test_format_courses_does_not_repeat_a_prereq_already_in_the_description():
    c = Course(course_id="ECEN 209", dept="ECEN", number="209", title="T",
               description="Stuff. Prerequisites: Grade of C or better in ENGR 102.",
               prereq_raw="Grade of C or better in ENGR 102.")
    assert format_courses([c]).count("ENGR 102") == 1
