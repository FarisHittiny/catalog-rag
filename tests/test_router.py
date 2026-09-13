import pytest

from catalog_rag.router import route

# gold-set phrasings (in-sample)
PREREQ = [
    "what does ECEN 350 unlock?",
    "which classes need ECEN 314 as a prereq?",
    "anything that requires ECEN 454 as a prerequisite?",
    "courses that have CSCE 120 in their prereqs?",
    "ECEN 214 is a prereq for what?",
    "would CSCE 462 be a prerequisite for anything else?",
    "list everything that builds on ECEN 303",
    "if I've got ECEN 370 done, which classes open up?",
    "what's gated behind CSCE 314?",
    "I took CSCE 121 instead of 120, what does that qualify me for?",
    "what does CSCE 222 lead to?",
    "where does ECEN 326 lead?",
    "what courses need CSCE 411 first?",
    "which upper-level classes want ECEN 449 first?",
    "what can I take after ECEN 248?",
    "what can I take after completing CSCE 441?",
    "so after ECEN 403 the next thing is what exactly",
    "I just finished ECEN 325, what's is something I can take next?",
    "what can I take once I've passed ECEN 322?",
    "give me the full list of classes that need CSCE 315",
    "what courses require ECEN 340?",
    "what does the data structures class unlock?",  # code-free phrasing still routes
]

# held-out paraphrases never seen while writing the patterns
PREREQ_HELD_OUT = [
    "what is ECEN 248 a prereq for?",
    "what is ECEN 248 a prerequisite for?",
    "which classes have ECEN 248 as prerequisite?",
    "what course requires ECEN 340?",
    "which course needs CSCE 221 first?",
]

OTHER = [
    "what do I need before ECEN 350?",
    "do I need ECEN 314 before ECEN 420?",
    "what are the prereqs for ECEN 325?",
    "prerequisite for the virtual reality course?",
    "I want to take the computer animation course, what has to come first?",
    "can I take the compiler design class right after programming studio?",
    "does CSCE 435 or CSCE 438 require CSCE 313?",
    "which of ECEN 449 or ECEN 454 requires ECEN 350?",
    "how do I get from CSCE 221 to CSCE 410, prereq-wise?",
    "should a sophomore take ECEN 248 next semester or wait?",
    "with only ECEN 248 done can I register for ECEN 468 and ECEN 454?",
    "how many credits is ECEN 248?",
    "who's teaching ECEN 350 this fall?",
]

# reverse direction: asks for X's prerequisites, which the graph retriever cannot answer
REVERSE = [
    "what does ECEN 350 build on?",
    "which courses lead to ECEN 350?",
    "can I take ECEN 420 after ECEN 314 or do I need something before it?",
]

# unanchored code lookalikes must not count as codes
NOT_CODES = [
    "which ECEN classes are offered after fall 2026",
    "I just finished year 2025, which ECEN courses are open?",
]


@pytest.mark.parametrize("q", PREREQ + PREREQ_HELD_OUT)
def test_prereq_phrasings_route_to_prereq(q):
    assert route(q) == "prereq"


@pytest.mark.parametrize("q", OTHER + REVERSE + NOT_CODES)
def test_non_prereq_phrasings_route_to_other(q):
    assert route(q) == "other"


def test_route_is_case_insensitive_and_returns_only_two_labels():
    assert route("WHAT DOES ECEN 350 UNLOCK") == "prereq"
    assert route("") == "other"
