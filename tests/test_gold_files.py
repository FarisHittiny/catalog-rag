"""Structural checks on the committed gold files (verified set + unverified stubs)."""
import re
from pathlib import Path

import pytest

from catalog_rag.models import GoldQuestion
from catalog_rag.prereq_graph import build_graph, load_courses, unlocked_by
from catalog_rag.retrievers.tokenize import CODE_RE

ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = ROOT / "data" / "gold"
FILES = [GOLD_DIR / "gold_set.jsonl", GOLD_DIR / "gold_stubs.jsonl"]
COURSES = ROOT / "data" / "processed" / "courses.jsonl"

# words a question needs to ask anything; they are not the course's vocabulary
GENERIC = {
    "the", "one", "ones", "class", "classes", "course", "courses", "credit", "credits", "hours", "lab",
    "prereq", "prereqs", "need", "take", "taken", "before", "into", "what", "which", "does", "have",
    "with", "that", "this", "many", "how", "there", "where", "from", "your", "you", "get", "for",
    "and", "are", "any", "now", "csce", "ecen", "list", "their", "actually", "about", "really",
    "required", "eligible", "intro",
}
UNLOCKED_RE = re.compile(r"unlocked_by\((" + CODE_RE.pattern + r")\)")


def _load(path: Path) -> list[GoldQuestion]:
    return [GoldQuestion.model_validate_json(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def rows() -> dict[str, list[GoldQuestion]]:
    """gold_set.jsonl is required; gold_stubs.jsonl exists only while drafts are pending."""
    assert FILES[0].exists(), f"missing {FILES[0]}"
    return {p.name: _load(p) for p in FILES if p.exists()}


@pytest.fixture(scope="module")
def courses():
    return {c.course_id: c for c in load_courses(COURSES)}


def test_ids_unique_across_files(rows):
    ids = [q.id for qs in rows.values() for q in qs]
    assert len(ids) == len(set(ids))


def test_has_code_matches_question_text(rows):
    bad = [q.id for qs in rows.values() for q in qs if q.has_code != bool(CODE_RE.search(q.question))]
    assert bad == []


def test_unanswerable_rows_have_no_gold_ids(rows):
    bad = [q.id for qs in rows.values() for q in qs if not q.answerable and q.gold_course_ids]
    assert bad == []


def test_answerable_rows_have_answer_and_gold_ids(rows):
    bad = [q.id for qs in rows.values() for q in qs if q.answerable and (not q.gold_course_ids or not q.gold_answer)]
    assert bad == []


# ---- paraphrase stubs (g101+): out-of-sample vocabulary -------------------------------
def _stubs(rows) -> list[GoldQuestion]:
    if "gold_stubs.jsonl" not in rows:
        pytest.skip("no gold_stubs.jsonl")
    return rows["gold_stubs.jsonl"]


def _referenced(q: GoldQuestion) -> str:
    """The record a paraphrase question describes: the gold record for factual rows, the
    unlocked_by(X) source named in notes for prereq rows."""
    if q.type == "prereq":
        m = UNLOCKED_RE.search(q.notes)
        assert m, f"{q.id}: prereq paraphrase row must name unlocked_by(CODE) in notes"
        return m.group(1)
    assert len(q.gold_course_ids) == 1, f"{q.id}: factual paraphrase row must have one gold record"
    return q.gold_course_ids[0]


def test_stubs_are_unverified_code_free_paraphrases(rows):
    stubs = _stubs(rows)
    assert stubs, "stubs file present but empty"
    assert all(not q.verified and not q.has_code and q.paraphrase for q in stubs)


def test_paraphrase_questions_do_not_quote_the_record(rows, courses):
    bad = {}
    for q in _stubs(rows):
        if not q.paraphrase:
            continue
        c = courses[_referenced(q)]
        record = set(re.findall(r"[a-z0-9]+", (c.title + " " + c.description).lower()))
        words = [w for w in re.findall(r"[a-z0-9]+", q.question.lower()) if len(w) >= 3 and w not in GENERIC]
        hits = [w for w in words if w in record]
        if hits:
            bad[q.id] = hits
    assert bad == {}


def test_paraphrase_prereq_gold_is_unlocked_by(rows, courses):
    g = build_graph(list(courses.values()))
    for q in _stubs(rows):
        if q.paraphrase and q.type == "prereq":
            assert q.gold_course_ids == unlocked_by(g, _referenced(q)), q.id
