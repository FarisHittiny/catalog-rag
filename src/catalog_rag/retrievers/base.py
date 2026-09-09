from __future__ import annotations

from typing import Protocol

from ..models import Chunk, RetrievalResult


class Retriever(Protocol):
    name: str

    def index(self, chunks: list[Chunk]) -> None: ...

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        """Return up to k results, best first, deduplicated by course_id."""
        ...
