"""M2. LLM-as-judge for answer correctness, 0 or 1.

RUBRIC below is the committed eval definition; changing it changes every correctness
number. Use a different model from the generator (JUDGE_MODEL vs LLM_MODEL). Report
agreement with the human labels in data/gold/human_labels.jsonl next to correctness.
"""
from __future__ import annotations

import json
from typing import Protocol

from pydantic import BaseModel, ValidationError

RUBRIC = """You grade answers about a university course catalog. You are given a question, a GOLD answer written by a human from the catalog, and a GENERATED answer. Output a score of 1 (correct) or 0 (incorrect).

Score 1 only if ALL of these hold:
- The generated answer states the same facts as the gold answer (course numbers, credits, titles, prerequisites, lists of courses). Paraphrase is fine.
- Nothing in the generated answer contradicts the gold answer.
- The generated answer does not invent specifics (numbers, courses, requirements) that the gold answer does not support.
- If the gold answer lists several courses, the generated answer names them all.
Extra detail that is correct and consistent with the gold answer is fine and does not lower the score.

Abstention: "The catalog doesn't cover that." (or an equivalent refusal) scores 0 whenever the gold answer gives a substantive answer. It scores 1 only when the gold answer itself says the catalog does not cover the question.

Ignore citations in square brackets like [ECEN 350]; grade the facts.

Reply with JSON only, exactly this shape and nothing else:
{"correct": 0 or 1, "reason": "<one sentence>"}"""



class LLMLike(Protocol):
    def chat(self, model: str, messages: list[dict]): ...


class Verdict(BaseModel):
    correct: int
    reason: str


def parse_verdict(text: str) -> Verdict:
    head = text.strip().replace("\n", " ")[:120]
    dec = json.JSONDecoder()
    for start in (i for i, ch in enumerate(text) if ch == "{"):  # greedy from each brace
        try:
            obj, _ = dec.raw_decode(text, start)
            v = Verdict.model_validate(obj)
        except (json.JSONDecodeError, ValidationError):
            continue
        if v.correct in (0, 1):
            return v
    return Verdict(correct=0, reason=f"unparseable judge output: {head}")


def build_messages(question: str, gold_answer: str, generated_answer: str) -> list[dict]:
    user = (f"Question: {question}\n\nGOLD answer: {gold_answer}\n\n"
            f"GENERATED answer: {generated_answer}")
    return [{"role": "system", "content": RUBRIC}, {"role": "user", "content": user}]


def judge(question: str, gold_answer: str, generated_answer: str, client: LLMLike, model: str) -> Verdict:
    return parse_verdict(client.chat(model, build_messages(question, gold_answer, generated_answer)).content)
