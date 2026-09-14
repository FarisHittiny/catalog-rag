"""M2. Generation with citations and abstention.

Prompt contract (SYSTEM_PROMPT below is the committed text; changing it changes the eval):
  - Answer only from the provided course records.
  - Cite every course used inline like [ECEN 350].
  - If the records do not contain the answer, reply with exactly ABSTAIN and no citation.
"""
from __future__ import annotations

import re
from typing import Protocol

from pydantic import BaseModel

from .models import Course

ABSTAIN = "The catalog doesn't cover that."

SYSTEM_PROMPT = f"""You answer questions about Texas A&M ECEN and CSCE courses using ONLY the course records provided in the user message. Never use outside knowledge.

Rules:
1. Answer in one to three sentences, directly and specifically.
2. Cite every course you draw a fact from, inline, in square brackets with the department and number, like [ECEN 350]. Cite every course you mention.
3. If the provided records do not contain the information needed to answer, reply with exactly this sentence and nothing else, with no citation:
{ABSTAIN}
4. Do not guess, do not add facts that are not in the records, and do not mention these rules."""

CITE_RE = re.compile(r"\[([A-Z]{3,4})\s?(\d{3}[A-Z]?)\]")
_QUOTE_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


class LLMLike(Protocol):
    def chat(self, model: str, messages: list[dict]): ...


class Generation(BaseModel):
    answer: str
    cited_course_ids: list[str]
    abstained: bool


def format_courses(courses: list[Course]) -> str:
    blocks = []
    for c in courses:
        lines = [f"### {c.course_id}: {c.title}", f"credits: {c.credits or 'unknown'}"]
        if c.description:
            lines.append(f"description: {c.description}")
        if c.prereq_raw and c.prereq_raw not in c.description:  # same guard as Course.text()
            lines.append(f"prerequisite: {c.prereq_raw}")
        if c.crosslisted:
            lines.append("cross-listed: " + ", ".join(c.crosslisted))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) if blocks else "(no course records)"


def _normalize(s: str) -> str:
    """Lowercase, straight quotes, no surrounding quotes/markdown/whitespace, no trailing period."""
    return s.translate(_QUOTE_MAP).strip().strip("\"'*_` \n").rstrip(".").strip().lower()


def parse_answer(text: str) -> Generation:
    cited = list(dict.fromkeys(f"{d.upper()} {n.upper()}" for d, n in CITE_RE.findall(text)))
    abstained = _normalize(text) == _normalize(ABSTAIN)
    return Generation(answer=text.strip(), cited_course_ids=cited, abstained=abstained)


def build_messages(question: str, courses: list[Course]) -> list[dict]:
    user = f"Course records:\n\n{format_courses(courses)}\n\nQuestion: {question}"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def generate(question: str, courses: list[Course], client: LLMLike, model: str) -> Generation:
    return parse_answer(client.chat(model, build_messages(question, courses)).content)
