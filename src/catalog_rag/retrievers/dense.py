"""M1. Embed chunks with sentence-transformers, cosine search with numpy.

Cache embeddings to data/processed/<model>.npy keyed by chunk order so CI doesn't
re-embed on every run.
"""
from __future__ import annotations

from ..models import Chunk, RetrievalResult


class DenseRetriever:
    name = "dense"

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.model_name = model_name
        raise NotImplementedError("M1")

    def index(self, chunks: list[Chunk]) -> None:
        raise NotImplementedError("M1")

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        raise NotImplementedError("M1")
