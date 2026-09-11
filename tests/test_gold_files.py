"""Structural checks on the committed gold files (verified set + unverified stubs)."""
from pathlib import Path

import pytest

from catalog_rag.models import GoldQuestion
from catalog_rag.retrievers.tokenize import CODE_RE

GOLD_DIR = Path(__file__).resolve().parents[1] / "data" / "gold"
FILES = [GOLD_DIR / "gold_set.jsonl", GOLD_DIR / "gold_stubs.jsonl"]


def _load(path: Path) -> list[GoldQuestion]:
    assert path.exists(), f"missing {path}"
    return [GoldQuestion.model_validate_json(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def rows() -> dict[str, list[GoldQuestion]]:
    return {p.name: _load(p) for p in FILES}


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


def test_stubs_are_all_unverified(rows):
    assert all(not q.verified for q in rows["gold_stubs.jsonl"])
