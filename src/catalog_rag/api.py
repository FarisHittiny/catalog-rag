"""M4. Demo API: the same retriever and prompt the eval measures, behind two endpoints.

    uv run uvicorn catalog_rag.api:app --port 7860
    curl -s localhost:7860/ask -H 'content-type: application/json' \
         -d '{"question": "what do I need before ECEN 350", "generate": false}'

POST /ask always retrieves with REGISTRY["routed_v2"]; it only calls the LLM when the body sets
generate=true. Generation reuses the eval's disk cache (same model, messages and params, so a
question the eval already answered costs nothing), and is guarded by a per-client hourly rate
limit and a daily token budget so a public demo has a bounded bill. GET /health for probes.

    python -m catalog_rag.api --build-embeddings   # Docker build step: bake bge-small + embeddings.npy
"""
from __future__ import annotations

import os
import sys
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .eval.run import REGISTRY, load_jsonl
from .generate import GEN_PARAMS, build_messages, parse_answer
from .llm import LLMClient, LLMError, Retryable
from .models import Chunk, Course
from .prereq_graph import load_courses
from .retrievers.routed import RoutedRetriever

RETRIEVER_NAME = "routed_v2"
build_retriever = REGISTRY[RETRIEVER_NAME]  # the demo serves exactly the registry entry the report names

QUESTION_MAX = 300
RETRIEVE_K = 10  # rows returned in `retrieved`
GEN_K = 5  # context size handed to the generator, same as the eval's --gen-k default
DEFAULT_GENERATE_PER_HOUR = 20
DEFAULT_DAILY_TOKENS = 200_000
DEFAULT_PROXY_HOPS = 0  # 0: key the rate limit on the socket peer; N: on the Nth-from-last X-Forwarded-For entry


# ---- guards --------------------------------------------------------------------------------

class RateLimiter:
    """Sliding window: at most `limit` allowed calls per key in the last `window_s` seconds."""

    def __init__(self, limit: int, window_s: float, now: Callable[[], float] = time.monotonic) -> None:
        self.limit = limit
        self.window_s = window_s
        self._now = now
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, t: float) -> deque[float]:
        q = self._calls[key]
        while q and q[0] <= t - self.window_s:
            q.popleft()
        return q

    def allow(self, key: str) -> bool:
        with self._lock:
            t = self._now()
            q = self._prune(key, t)
            if len(q) >= self.limit:
                return False
            q.append(t)
            return True

    def retry_after(self, key: str) -> int:
        """Seconds until the oldest call in the window expires (0 if the key is under the limit)."""
        with self._lock:
            t = self._now()
            q = self._prune(key, t)
            return 0 if len(q) < self.limit else max(1, int(q[0] + self.window_s - t) + 1)


class TokenBudget:
    """Uncached generator tokens spent today (UTC); resets when the date changes."""

    def __init__(self, limit: int, now: Callable[[], float] = time.time) -> None:
        self.limit = limit
        self._now = now
        self._day = None
        self._used = 0
        self._lock = threading.Lock()

    def _roll(self) -> None:
        day = datetime.fromtimestamp(self._now(), UTC).date()
        if day != self._day:
            self._day, self._used = day, 0

    def charge(self, tokens: int) -> None:
        with self._lock:
            self._roll()
            self._used += tokens

    def remaining(self) -> int:
        with self._lock:
            self._roll()
            return max(0, self.limit - self._used)

    def allows(self) -> bool:
        return self.remaining() > 0


# ---- state -----------------------------------------------------------------------------------

@dataclass
class DemoState:
    retriever: RoutedRetriever
    courses: dict[str, Course]
    client: LLMClient | None  # None: generation disabled (no key / base URL / model)
    model: str
    limiter: RateLimiter
    budget: TokenBudget
    proxy_hops: int = DEFAULT_PROXY_HOPS


def client_key(request: Request, proxy_hops: int) -> str:
    """Who to rate-limit. With proxy_hops=0 it is the TCP peer. Behind a reverse proxy that appends
    the connecting address to X-Forwarded-For (the Space proxy), proxy_hops=1 takes the LAST entry:
    the one the proxy wrote, not a leftmost value the caller can forge. Never trust the header
    beyond the configured hops; too few entries falls back to the peer."""
    peer = request.client.host if request.client else "unknown"
    if proxy_hops <= 0:
        return peer
    xff = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()]
    return xff[-proxy_hops] if len(xff) >= proxy_hops else peer


def load_state(chunks_path: Path = Path("data/processed/chunks.jsonl"),
               courses_path: Path = Path("data/processed/courses.jsonl"),
               with_llm: bool = True) -> DemoState:
    """Load the corpus, build and index routed_v2 once, warm the dense model, open the LLM client."""
    chunks = load_jsonl(chunks_path, Chunk)
    courses = {c.course_id: c for c in load_courses(courses_path)}
    retriever = build_retriever()
    retriever.index(chunks)  # bm25_codes_id + graph in memory; dense from embeddings.npy if its key matches
    if retriever.no_code is not None:
        retriever.no_code.retrieve("warm up", k=1)  # loads bge-small now, not on the first request
    client, model = None, ""
    if with_llm:
        try:
            client = LLMClient.from_env(max_retries=2)  # also loads .env, so LLM_MODEL is visible below
        except SystemExit as e:
            print(f"[api] generation disabled: {e}", file=sys.stderr)
        model = os.environ.get("LLM_MODEL", "")
        if client is not None and not model:
            print("[api] generation disabled: LLM_MODEL is not set", file=sys.stderr)
            client = None
    return DemoState(
        retriever=retriever, courses=courses, client=client, model=model,
        limiter=RateLimiter(int(os.environ.get("DEMO_GENERATE_PER_HOUR", DEFAULT_GENERATE_PER_HOUR)), 3600),
        budget=TokenBudget(int(os.environ.get("DEMO_DAILY_TOKENS", DEFAULT_DAILY_TOKENS))),
        proxy_hops=int(os.environ.get("DEMO_PROXY_HOPS", DEFAULT_PROXY_HOPS)),
    )


# ---- schema ----------------------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=QUESTION_MAX)
    generate: bool = False


class Retrieved(BaseModel):
    course_id: str
    title: str
    rank: int  # 1-based position in the retriever's ranking
    score: float  # the retriever's own score (graph: n - position, bm25: BM25, dense: cosine)


class AskResponse(BaseModel):
    route: Literal["prereq", "other"]
    retriever_used: str  # "graph", "bm25_codes_id" or "dense"
    retrieved: list[Retrieved]
    context_course_ids: list[str]  # what the generator would see (routed_v2.context)
    answer: str | None = None
    cited_course_ids: list[str] = Field(default_factory=list)
    abstained: bool = False
    cached: bool = False  # answer came from the LLM disk cache (no tokens spent)


def _retriever_used(r: RoutedRetriever, question: str) -> str:
    """Mirror RoutedRetriever.retrieve's two checks without adding state to the retriever."""
    if r.route(question) == "prereq" and r.prereq.retrieve(question, k=1):
        return r.prereq.name
    return r._fallback_for(question).name


# ---- app -------------------------------------------------------------------------------------

def create_app(state_factory: Callable[[], DemoState] = load_state) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.demo = state_factory()
        yield

    app = FastAPI(title="catalog-rag demo", lifespan=lifespan)
    origins = [o.strip() for o in os.environ.get("DEMO_ORIGINS", "").split(",") if o.strip()]
    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                           allow_headers=["*"])

    @app.get("/health")
    def health(request: Request) -> dict:
        s: DemoState = request.app.state.demo
        return {"status": "ok", "retriever": s.retriever.name, "courses": len(s.courses),
                "generation": s.client is not None}

    @app.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest, request: Request) -> AskResponse:  # sync: the LLM call blocks
        s: DemoState = request.app.state.demo
        r, q = s.retriever, req.question
        hits = r.retrieve(q, k=RETRIEVE_K)
        ctx = r.context(q, GEN_K)
        resp = AskResponse(
            route=r.route(q), retriever_used=_retriever_used(r, q),
            retrieved=[Retrieved(course_id=h.course_id, rank=i + 1, score=h.score,
                                 title=s.courses[h.course_id].title if h.course_id in s.courses else "")
                       for i, h in enumerate(hits)],
            context_course_ids=ctx,
        )
        if not req.generate:
            return resp

        if s.client is None:
            raise HTTPException(503, "Generation is not configured on this server (no LLM key, base URL "
                                     "or model). Retrieval still works with generate=false.")
        ip = client_key(request, s.proxy_hops)
        if not s.limiter.allow(ip):
            raise HTTPException(429, f"Rate limit: {s.limiter.limit} generated answers per hour per "
                                     f"client. Try again in {s.limiter.retry_after(ip)} s, or ask with "
                                     f"generate=false for retrieval only.")
        msgs = build_messages(q, [s.courses[c] for c in ctx if c in s.courses])
        if not s.client.is_cached(s.model, msgs, GEN_PARAMS) and not s.budget.allows():
            raise HTTPException(429, "The demo's daily token budget is used up; fresh answers resume at "
                                     "00:00 UTC. Cached answers and retrieval (generate=false) still work.")
        try:
            res = s.client.chat(s.model, msgs, **GEN_PARAMS)
        except (LLMError, Retryable) as e:
            raise HTTPException(502, f"The LLM endpoint failed: {e}") from e
        if not res.cached:
            s.budget.charge(int(res.usage.get("prompt_tokens", 0)) + int(res.usage.get("completion_tokens", 0)))
        g = parse_answer(res.content)
        resp.answer, resp.cited_course_ids, resp.abstained, resp.cached = (
            g.answer, g.cited_course_ids, g.abstained, res.cached)
        return resp

    return app


app = create_app()


if __name__ == "__main__":
    if "--build-embeddings" in sys.argv[1:]:
        s = load_state(with_llm=False)  # downloads bge-small into HF_HOME and writes embeddings.npy
        print(f"indexed {len(s.courses)} courses with {s.retriever.name}")
    else:
        print(__doc__)
