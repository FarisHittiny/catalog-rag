"""Rule-based query router: "prereq" (what does X unlock / what comes after X) vs "other".

Reads only the question text. Reverse-direction phrasings ("what do I need before X",
"what does X build on?", "which courses lead to X") ask for X's prerequisites, which the
graph retriever does not answer, so they are routed "other" even when a forward pattern
would otherwise match. Patterns were written against the 100-question gold set, so the
accuracy the eval reports for them is in-sample.
"""
from __future__ import annotations

import re
from typing import Literal

from .retrievers.tokenize import CODE_RE

Route = Literal["prereq", "other"]

CODE = CODE_RE.pattern  # single source of truth for what a course code looks like

_REVERSE = [
    r"\bbefore\b",                      # what do I need before X / do I need X before Y
    rf"\blead(s)? to {CODE}",           # which courses lead to X
    r"\bbuilds? on\W*$",                # what does X build on?
]
_FORWARD = [
    r"\bunlock",
    r"\bas (a )?prereq",
    r"\bin their prereqs?\b",
    r"\bprereq(uisite)?s? for (what|anything)\b",
    r"\ba prereq(uisite)? for\b",       # "is X a prereq for", "be a prerequisite for anything"
    r"\bbuilds? on\b",
    r"\bopens? up\b",
    r"\bgated behind\b",
    r"\bqualif(y|ies) me for\b",
    r"\blead(s)? to\b",
    r"\bwhere does .+ lead\b",
    rf"\b(need|needs|want|wants|require|requires) {CODE} first\b",
    rf"\bafter (completing |passing |finishing |taking )?{CODE}",
    r"\b(can|could) (i )?take next\b",
    r"\bonce i.ve (passed|finished|completed|taken)\b",
    rf"\b(class|course)e?s? (that )?(need|require)s? {CODE}",
]
REVERSE_RE = re.compile("|".join(f"(?:{p})" for p in _REVERSE), re.IGNORECASE)
PREREQ_RE = re.compile("|".join(f"(?:{p})" for p in _FORWARD), re.IGNORECASE)


def route(question: str) -> Route:
    if REVERSE_RE.search(question):
        return "other"
    return "prereq" if PREREQ_RE.search(question) else "other"
