"""Demo API over routed_v2: real retrievers on an in-memory corpus, fake embedder, fake LLM
transport. No network, no torch, no files outside tmp_path."""
from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from catalog_rag import api
from catalog_rag.api import DemoState, RateLimiter, TokenBudget, create_app
from catalog_rag.eval.run import REGISTRY
from catalog_rag.llm import LLMClient
from catalog_rag.models import Chunk, Course
from catalog_rag.retrievers import (
    BM25CodesIdRetriever,
    DenseRetriever,
    GraphRetriever,
    RoutedRetriever,
)

DIM = 32


class FakeEmbedder:
    """Hashed bag-of-words, L2-normalized (same as tests/test_dense.py)."""

    def __call__(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in t.lower().split():
                out[i, sum(map(ord, w)) % DIM] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return out / norms


class FakeTransport:
    def __init__(self, reply: str = "It needs ECEN 248 [ECEN 248].") -> None:
        self.calls = 0
        self.reply = reply

    def __call__(self, model: str, messages: list[dict], params: dict) -> tuple[str, dict]:
        self.calls += 1
        return self.reply, {"prompt_tokens": 10, "completion_tokens": 3}


ROWS = [
    ("ECEN 248", "Introduction to Digital Systems Design", "logic gates flip flops verilog", []),
    ("ECEN 350", "Computer Architecture and Design", "pipelines memory hierarchy instruction sets", [["ECEN 248"]]),
    ("ECEN 449", "Microprocessor Systems Design", "single board computers peripherals assembly", [["ECEN 248"]]),
    ("CSCE 410", "Operating Systems", "scheduling virtual memory allocation kernels", [["CSCE 313"]]),
]


def _courses() -> dict[str, Course]:
    out = {}
    for cid, title, desc, pre in ROWS:
        d, n = cid.split()
        out[cid] = Course(course_id=cid, dept=d, number=n, title=title, credits="3", description=desc, prereqs=pre)
    return out


def _chunks() -> list[Chunk]:
    return [Chunk(chunk_id=f"{cid}#0", course_id=cid, dept=cid[:4], catalog_year="2026",
                  text=f"{cid} {title}. {desc}", prereqs=pre) for cid, title, desc, pre in ROWS]


def _state(tmp_path, transport=None, client=True, limiter=None, budget=None, now=None) -> DemoState:
    r = RoutedRetriever(GraphRetriever(), BM25CodesIdRetriever(),
                        no_code=DenseRetriever(model_name="fake", cache_path=tmp_path / "emb.npy",
                                               embedder=FakeEmbedder(), query_prefix=""),
                        name="routed_v2")
    r.index(_chunks())
    llm = LLMClient(transport or FakeTransport(), cache_dir=tmp_path / "llm", sleep=lambda s: None) if client else None
    return DemoState(retriever=r, courses=_courses(), client=llm, model="fake-model",
                     limiter=limiter or RateLimiter(limit=20, window_s=3600, now=now or (lambda: 0.0)),
                     budget=budget or TokenBudget(limit=200_000, now=now or (lambda: 0.0)))


def _client(state: DemoState) -> TestClient:
    return TestClient(create_app(lambda: state))


# ---- the retriever is the registry entry ------------------------------------------------

def test_api_retriever_is_the_routed_v2_registry_entry():
    assert api.RETRIEVER_NAME == "routed_v2"
    assert api.build_retriever is REGISTRY["routed_v2"]
    r = api.build_retriever()
    assert isinstance(r, RoutedRetriever) and r.name == "routed_v2"
    assert isinstance(r.prereq, GraphRetriever)
    assert isinstance(r.fallback, BM25CodesIdRetriever)
    assert isinstance(r.no_code, DenseRetriever)


# ---- endpoints ---------------------------------------------------------------------------

def test_health_reports_retriever_and_generation_availability(tmp_path):
    with _client(_state(tmp_path)) as c:
        body = c.get("/health").json()
    assert body["status"] == "ok" and body["retriever"] == "routed_v2"
    assert body["courses"] == 4 and body["generation"] is True
    with _client(_state(tmp_path, client=False)) as c:
        assert c.get("/health").json()["generation"] is False


def test_prereq_question_uses_graph_and_prepends_queried_course(tmp_path):
    with _client(_state(tmp_path)) as c:
        body = c.post("/ask", json={"question": "what does ECEN 248 unlock?"}).json()
    assert body["route"] == "prereq" and body["retriever_used"] == "graph"
    assert [x["course_id"] for x in body["retrieved"]] == ["ECEN 350", "ECEN 449"]
    assert body["retrieved"][0] == {"course_id": "ECEN 350", "title": "Computer Architecture and Design",
                                    "rank": 1, "score": 2.0}
    assert body["context_course_ids"] == ["ECEN 248", "ECEN 350", "ECEN 449"]
    assert body["answer"] is None and body["cited_course_ids"] == []
    assert body["abstained"] is False and body["cached"] is False


def test_code_free_question_uses_dense(tmp_path):
    with _client(_state(tmp_path)) as c:
        body = c.post("/ask", json={"question": "the class on scheduling and virtual memory"}).json()
    assert body["route"] == "other" and body["retriever_used"] == "dense"
    assert body["retrieved"][0]["course_id"] == "CSCE 410"
    assert body["context_course_ids"][0] == "CSCE 410"


def test_code_question_uses_bm25_codes_id(tmp_path):
    with _client(_state(tmp_path)) as c:
        body = c.post("/ask", json={"question": "how many credits is ECEN 350?"}).json()
    assert body["route"] == "other" and body["retriever_used"] == "bm25_codes_id"
    assert body["retrieved"][0]["course_id"] == "ECEN 350"


def test_generate_false_never_calls_the_llm(tmp_path):
    t = FakeTransport()
    with _client(_state(tmp_path, transport=t)) as c:
        c.post("/ask", json={"question": "what does ECEN 248 unlock?"})
        c.post("/ask", json={"question": "what does ECEN 248 unlock?", "generate": False})
    assert t.calls == 0


def test_generate_answers_with_citations_and_cache_flag(tmp_path):
    t = FakeTransport()
    with _client(_state(tmp_path, transport=t)) as c:
        q = {"question": "what do I need before ECEN 350?", "generate": True}
        a = c.post("/ask", json=q).json()
        b = c.post("/ask", json=q).json()
    assert a["answer"] == "It needs ECEN 248 [ECEN 248]." and a["cited_course_ids"] == ["ECEN 248"]
    assert a["abstained"] is False and a["cached"] is False
    assert b["cached"] is True and b["answer"] == a["answer"]
    assert t.calls == 1


def test_generate_reports_abstention(tmp_path):
    t = FakeTransport(reply="The catalog doesn't cover that.")
    with _client(_state(tmp_path, transport=t)) as c:
        body = c.post("/ask", json={"question": "what do I need before ECEN 350?", "generate": True}).json()
    assert body["abstained"] is True and body["cited_course_ids"] == []


def test_generate_without_llm_config_is_503(tmp_path):
    with _client(_state(tmp_path, client=False)) as c:
        r = c.post("/ask", json={"question": "what do I need before ECEN 350?", "generate": True})
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"]


def test_generate_rate_limit_is_429_with_a_clear_message(tmp_path):
    with _client(_state(tmp_path, limiter=RateLimiter(limit=2, window_s=3600, now=lambda: 0.0))) as c:
        q = {"question": "what do I need before ECEN 350?", "generate": True}
        assert c.post("/ask", json=q).status_code == 200
        assert c.post("/ask", json=q).status_code == 200
        r = c.post("/ask", json=q)
        assert c.post("/ask", json={"question": "what does ECEN 248 unlock?"}).status_code == 200
    assert r.status_code == 429
    assert "2 generated answers per hour" in r.json()["detail"]


def test_daily_budget_is_429_but_cache_hits_are_free(tmp_path):
    with _client(_state(tmp_path, budget=TokenBudget(limit=5, now=lambda: 0.0))) as c:
        q = {"question": "what do I need before ECEN 350?", "generate": True}
        assert c.post("/ask", json=q).status_code == 200  # first fresh call is allowed, charges 13
        assert c.post("/ask", json=q).json()["cached"] is True  # cache hit costs nothing
        r = c.post("/ask", json={"question": "what does ECEN 248 unlock?", "generate": True})
    assert r.status_code == 429
    assert "daily token budget" in r.json()["detail"]


def test_question_over_300_chars_is_422(tmp_path):
    with _client(_state(tmp_path)) as c:
        assert c.post("/ask", json={"question": "x" * 301}).status_code == 422
        assert c.post("/ask", json={"question": ""}).status_code == 422
        assert c.post("/ask", json={"question": "x" * 300}).status_code == 200


def test_cors_allow_list_comes_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_ORIGINS", "https://farishittiny.com, http://localhost:5173")
    with _client(_state(tmp_path)) as c:
        ok = c.get("/health", headers={"Origin": "https://farishittiny.com"})
        bad = c.get("/health", headers={"Origin": "https://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "https://farishittiny.com"
    assert "access-control-allow-origin" not in bad.headers


# ---- limiter and budget units -------------------------------------------------------------

def test_rate_limiter_slides_per_ip():
    clock = {"t": 0.0}
    lim = RateLimiter(limit=2, window_s=60, now=lambda: clock["t"])
    assert lim.allow("a") and lim.allow("a") and not lim.allow("a")
    assert lim.allow("b")  # another ip has its own window
    clock["t"] = 61.0
    assert lim.allow("a")  # the window slid past the first two calls


def test_token_budget_resets_each_utc_day():
    clock = {"t": 0.0}
    b = TokenBudget(limit=100, now=lambda: clock["t"])
    b.charge(90)
    assert b.remaining() == 10 and b.allows()
    b.charge(20)
    assert not b.allows()
    clock["t"] = 86_400.0
    assert b.allows() and b.remaining() == 100


# ---- rate-limit key cannot be spoofed through X-Forwarded-For ------------------------------

def _limit_one(tmp_path, proxy_hops: int) -> DemoState:
    s = _state(tmp_path, limiter=RateLimiter(limit=1, window_s=3600, now=lambda: 0.0))
    s.proxy_hops = proxy_hops
    return s


def test_forwarded_header_is_ignored_unless_a_proxy_hop_is_trusted(tmp_path):
    q = {"question": "what do I need before ECEN 350?", "generate": True}
    with _client(_limit_one(tmp_path, proxy_hops=0)) as c:
        assert c.post("/ask", json=q, headers={"x-forwarded-for": "1.1.1.1"}).status_code == 200
        # a different spoofed address does not buy a fresh window: the socket peer is the key
        assert c.post("/ask", json=q, headers={"x-forwarded-for": "2.2.2.2"}).status_code == 429


def test_trusted_proxy_hop_uses_the_address_the_proxy_appended(tmp_path):
    q = {"question": "what do I need before ECEN 350?", "generate": True}
    with _client(_limit_one(tmp_path, proxy_hops=1)) as c:
        # the proxy appends the real client last; a client-supplied leftmost entry is ignored
        assert c.post("/ask", json=q, headers={"x-forwarded-for": "9.9.9.9, 5.5.5.5"}).status_code == 200
        assert c.post("/ask", json=q, headers={"x-forwarded-for": "8.8.8.8, 5.5.5.5"}).status_code == 429
        assert c.post("/ask", json=q, headers={"x-forwarded-for": "8.8.8.8, 6.6.6.6"}).status_code == 200
        # no header at all: fall back to the socket peer rather than failing
        assert c.post("/ask", json=q).status_code == 200


def test_client_key_helper():
    from starlette.requests import Request

    def req(xff: str | None, peer: str = "10.0.0.1") -> Request:
        headers = [(b"x-forwarded-for", xff.encode())] if xff else []
        return Request({"type": "http", "headers": headers, "client": (peer, 1234), "method": "GET",
                        "path": "/", "query_string": b"", "scheme": "http", "server": ("s", 80)})

    assert api.client_key(req("1.1.1.1"), proxy_hops=0) == "10.0.0.1"
    assert api.client_key(req("1.1.1.1, 2.2.2.2"), proxy_hops=1) == "2.2.2.2"
    assert api.client_key(req("1.1.1.1, 2.2.2.2, 3.3.3.3"), proxy_hops=2) == "2.2.2.2"
    assert api.client_key(req("1.1.1.1"), proxy_hops=2) == "10.0.0.1"  # too few entries: socket peer
    assert api.client_key(req(None), proxy_hops=1) == "10.0.0.1"
