"""LLMClient with an injected fake transport: no network, no openai import."""
import json

import pytest

from catalog_rag.llm import LLMClient, LLMError, Retryable, _content_or_raise


class FakeTransport:
    def __init__(self, fail_times: int = 0) -> None:
        self.calls = 0
        self.fail_times = fail_times

    def __call__(self, model: str, messages: list[dict], params: dict) -> tuple[str, dict]:
        self.calls += 1
        self.last_params = params
        if self.calls <= self.fail_times:
            raise Retryable("429")
        return f"reply:{model}:{messages[-1]['content']}", {"prompt_tokens": 10, "completion_tokens": 3}


def _client(tmp_path, transport, **kw) -> LLMClient:
    return LLMClient(transport, cache_dir=tmp_path / "llm", sleep=lambda s: None, **kw)


def test_cache_hit_never_calls_transport(tmp_path):
    t = FakeTransport()
    c = _client(tmp_path, t)
    msgs = [{"role": "user", "content": "hi"}]
    a = c.chat("m", msgs)
    b = c.chat("m", msgs)
    assert t.calls == 1
    assert a.content == b.content == "reply:m:hi"
    assert a.cached is False and b.cached is True
    files = list((tmp_path / "llm").glob("*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8"))["content"] == "reply:m:hi"


def test_cache_key_depends_on_model_and_messages(tmp_path):
    t = FakeTransport()
    c = _client(tmp_path, t)
    c.chat("m", [{"role": "user", "content": "hi"}])
    c.chat("m2", [{"role": "user", "content": "hi"}])
    c.chat("m", [{"role": "user", "content": "bye"}])
    assert t.calls == 3
    c.chat("m", [{"role": "user", "content": "hi"}], temperature=0)  # params are part of the key
    assert t.calls == 4 and t.last_params == {"temperature": 0}
    c.chat("m", [{"role": "user", "content": "hi"}], temperature=0)
    assert t.calls == 4


def test_retries_with_backoff_then_succeeds(tmp_path):
    t = FakeTransport(fail_times=2)
    delays: list[float] = []
    c = LLMClient(t, cache_dir=tmp_path / "llm", max_retries=5, base_delay=1.0, sleep=delays.append)
    out = c.chat("m", [{"role": "user", "content": "hi"}])
    assert out.content.startswith("reply:") and t.calls == 3
    assert len(delays) == 2 and delays[1] > delays[0] >= 1.0


def test_gives_up_after_max_retries(tmp_path):
    t = FakeTransport(fail_times=99)
    c = _client(tmp_path, t, max_retries=2)
    with pytest.raises(Retryable):
        c.chat("m", [{"role": "user", "content": "hi"}])
    assert t.calls == 3  # first try + 2 retries
    assert not list((tmp_path / "llm").glob("*.json")), "failures are never cached"


def test_usage_report_counts_calls_tokens_and_cache_hits(tmp_path):
    t = FakeTransport()
    c = _client(tmp_path, t)
    c.chat("gen", [{"role": "user", "content": "a"}])
    c.chat("gen", [{"role": "user", "content": "a"}])
    c.chat("judge", [{"role": "user", "content": "b"}])
    u = c.usage
    assert u["gen"] == {"calls": 1, "cache_hits": 1, "prompt_tokens": 10, "completion_tokens": 3}
    assert u["judge"]["calls"] == 1
    report = c.usage_report()
    assert "gen" in report and "judge" in report and "total" in report
    assert "20" in report  # total prompt tokens


def test_from_env_requires_base_url_and_key(monkeypatch, tmp_path):
    for v in ("LLM_BASE_URL", "LLM_API_KEY", "TAMU_CHAT_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.chdir(tmp_path)  # no .env here
    with pytest.raises(SystemExit) as e:
        LLMClient.from_env(cache_dir=tmp_path / "llm")
    assert "LLM_BASE_URL" in str(e.value)
    monkeypatch.setenv("LLM_BASE_URL", "http://x")
    monkeypatch.setenv("TAMU_CHAT_API_KEY", "k")
    c = LLMClient.from_env(cache_dir=tmp_path / "llm")  # fallback key accepted; no call made
    assert isinstance(c, LLMClient)


def test_malformed_cache_file_is_refetched(tmp_path):
    t = FakeTransport()
    c = _client(tmp_path, t)
    msgs = [{"role": "user", "content": "hi"}]
    c.chat("m", msgs)
    path = c._cache_path(c.cache_key("m", msgs))
    path.write_text("{not json", encoding="utf-8")
    out = c.chat("m", msgs)
    assert out.cached is False and t.calls == 2
    assert json.loads(path.read_text(encoding="utf-8"))["content"] == "reply:m:hi"


def test_read_cache_false_calls_api_and_overwrites(tmp_path):
    t = FakeTransport()
    msgs = [{"role": "user", "content": "hi"}]
    _client(tmp_path, t).chat("m", msgs)
    fresh = _client(tmp_path, t, read_cache=False)
    out = fresh.chat("m", msgs)
    assert out.cached is False and t.calls == 2
    assert fresh.usage["m"]["cache_hits"] == 0
    assert _client(tmp_path, t).chat("m", msgs).cached is True  # the fresh call was written back
    assert t.calls == 2


def test_llm_error_is_not_retried_or_cached(tmp_path):
    class Broken:
        calls = 0

        def __call__(self, model, messages, params):
            self.calls += 1
            raise LLMError("400: temperature may only be set to 1")

    b = Broken()
    c = _client(tmp_path, b, max_retries=3)
    with pytest.raises(LLMError):
        c.chat("m", [{"role": "user", "content": "hi"}])
    assert b.calls == 1
    assert not list((tmp_path / "llm").glob("*.json"))


def test_200_error_body_maps_to_llm_error():
    class Resp:  # what the SDK returns when the proxy answers 200 with {"error": ...}
        choices = None
        error = {"message": "litellm.BadRequestError: temperature may only be set to 1", "code": "400"}

    with pytest.raises(LLMError) as e:
        _content_or_raise(Resp())
    assert "temperature" in str(e.value)

    from types import SimpleNamespace as NS

    ok = NS(choices=[NS(message=NS(content="fine"))])
    assert _content_or_raise(ok) == "fine"


def test_is_cached_reflects_the_disk_cache(tmp_path):
    t = FakeTransport()
    c = _client(tmp_path, t)
    msgs = [{"role": "user", "content": "hi"}]
    assert c.is_cached("m", msgs, {"temperature": 0}) is False
    c.chat("m", msgs, temperature=0)
    assert c.is_cached("m", msgs, {"temperature": 0}) is True
    assert c.is_cached("m", msgs) is False  # params are part of the key
    assert _client(tmp_path, t, read_cache=False).is_cached("m", msgs, {"temperature": 0}) is False
