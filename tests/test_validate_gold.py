import pytest

from catalog_rag.eval.run import validate_gold
from catalog_rag.models import GoldQuestion


def _q(**kw) -> GoldQuestion:
    base = dict(id="g001", question="q?", dept="ECEN", type="factual", gold_course_ids=["ECEN 350"])
    return GoldQuestion(**{**base, **kw})


def test_verified_defaults_true_and_passes():
    assert _q().verified is True
    validate_gold([_q()], {"ECEN 350"})


def test_unverified_rows_are_listed_in_error():
    with pytest.raises(SystemExit) as exc:
        validate_gold([_q(id="g001", verified=False), _q(id="g002", verified=False)], {"ECEN 350"})
    msg = str(exc.value)
    assert "g001: not verified" in msg
    assert "g002: not verified" in msg
