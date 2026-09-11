"""M1. Embed chunks with sentence-transformers (BAAI/bge-small-en-v1.5), cosine search via
numpy dot product over normalized vectors.

Embeddings are cached at data/processed/embeddings.npy with a sidecar .meta.json holding a
sha256 over the model name and every chunk (id + text, in order), so re-runs on an unchanged
corpus never re-embed. The embedder is injectable so tests use a fake and never load torch.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np

from ..models import Chunk, RetrievalResult
from .base import top_by_course

Embedder = Callable[[list[str]], np.ndarray]

# bge recommends this instruction on the query side for short-query -> passage retrieval.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class DenseRetriever:
    name = "dense"

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        cache_path: Path = Path("data/processed/embeddings.npy"),
        embedder: Embedder | None = None,
        query_prefix: str = BGE_QUERY_PREFIX,
    ) -> None:
        self.model_name = model_name
        self.cache_path = Path(cache_path)
        self.query_prefix = query_prefix
        self._embedder = embedder
        self._chunks: list[Chunk] = []
        self._emb: np.ndarray | None = None

    # -- embedding -------------------------------------------------------------------
    def _embed(self, texts: list[str]) -> np.ndarray:
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer  # lazy: keeps import cheap

            model = SentenceTransformer(self.model_name)
            self._embedder = lambda t: np.asarray(model.encode(t, normalize_embeddings=True), dtype=np.float32)
        return np.asarray(self._embedder(texts), dtype=np.float32)

    def _key(self, chunks: list[Chunk]) -> str:
        h = hashlib.sha256(self.model_name.encode("utf-8"))
        for c in chunks:
            h.update(f"{c.chunk_id}\n{c.text}\n".encode("utf-8"))
        return h.hexdigest()

    @property
    def _meta_path(self) -> Path:
        return self.cache_path.with_name(self.cache_path.name + ".meta.json")

    # -- Retriever protocol ----------------------------------------------------------
    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        key = self._key(chunks)
        if self.cache_path.exists() and self._meta_path.exists():
            meta = json.loads(self._meta_path.read_text(encoding="utf-8"))
            if meta.get("key") == key:
                self._emb = np.load(self.cache_path)
                return
        self._emb = self._embed([c.text for c in chunks])
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self.cache_path, self._emb)
        self._meta_path.write_text(
            json.dumps({"key": key, "model": self.model_name, "n": len(chunks)}), encoding="utf-8"
        )

    def retrieve(self, query: str, k: int = 10) -> list[RetrievalResult]:
        assert self._emb is not None, "call index() first"
        q = self._embed([self.query_prefix + query])[0]
        scores = self._emb @ q
        return top_by_course(self._chunks, scores, k)
