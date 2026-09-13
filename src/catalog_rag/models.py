from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Course(BaseModel):
    course_id: str  # "ECEN 350"
    dept: str
    number: str
    title: str
    credits: str = ""
    description: str = ""
    prereq_raw: str = ""
    prereqs: list[list[str]] = Field(default_factory=list)  # AND of OR-groups
    coreqs: list[str] = Field(default_factory=list)
    crosslisted: list[str] = Field(default_factory=list)
    catalog_year: str = ""
    source_url: str = ""

    def text(self) -> str:
        """Canonical text used for indexing."""
        parts = [f"{self.course_id} {self.title}", self.description]
        if self.prereq_raw and self.prereq_raw not in self.description:
            # scraped descriptions usually already end with the prereq sentence
            parts.append(f"Prerequisite: {self.prereq_raw}")
        if self.crosslisted:
            parts.append("Cross-listed with " + ", ".join(self.crosslisted))
        return "\n".join(p for p in parts if p)


class Chunk(BaseModel):
    chunk_id: str
    course_id: str
    dept: str
    catalog_year: str
    text: str
    prereqs: list[list[str]] = Field(default_factory=list)  # AND of OR-groups, copied from Course


QuestionType = Literal["factual", "prereq", "multi_hop", "not_in_catalog"]


class GoldQuestion(BaseModel):
    id: str
    question: str
    dept: str
    type: QuestionType
    gold_course_ids: list[str] = Field(default_factory=list)
    gold_answer: str = ""
    answerable: bool = True
    notes: str = ""
    verified: bool = True  # False = drafted, not yet checked against the catalog page
    has_code: bool = False  # question text names at least one course code


class RetrievalResult(BaseModel):
    course_id: str
    score: float
    chunk_id: str | None = None
