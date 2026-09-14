from catalog_rag.eval.judge import RUBRIC, Verdict, judge, parse_verdict


class FakeClient:
    def __init__(self, reply: str) -> None:
        self.reply, self.seen = reply, []

    def chat(self, model, messages):
        self.seen.append((model, messages))

        class R:
            content = self.reply

        return R()


def test_parse_clean_json():
    v = parse_verdict('{"correct": 1, "reason": "same facts"}')
    assert v == Verdict(correct=1, reason="same facts")


def test_parse_json_wrapped_in_prose_or_fences():
    v = parse_verdict('Sure.\n```json\n{"correct": 0, "reason": "invented credits"}\n```')
    assert v.correct == 0 and v.reason == "invented credits"


def test_garbage_scores_zero_with_visible_reason():
    v = parse_verdict("I think it is fine")
    assert v.correct == 0 and v.reason.startswith("unparseable judge output")
    v2 = parse_verdict('{"correct": "maybe"}')
    assert v2.correct == 0 and "unparseable" in v2.reason
    v3 = parse_verdict('{"correct": 2, "reason": "x"}')
    assert v3.correct == 0 and "unparseable" in v3.reason


def test_judge_sends_rubric_and_all_three_inputs():
    c = FakeClient('{"correct": 1, "reason": "ok"}')
    v = judge("q?", "gold text", "gen text", c, model="judge-m")
    assert v.correct == 1
    model, msgs = c.seen[0]
    assert model == "judge-m"
    assert msgs[0]["content"] == RUBRIC
    user = msgs[1]["content"]
    assert "q?" in user and "gold text" in user and "gen text" in user


def test_braces_inside_reason_do_not_break_parsing():
    v = parse_verdict('{"correct": 1, "reason": "same set {ECEN 248, ECEN 314}"}')
    assert v.correct == 1 and "ECEN 248" in v.reason
