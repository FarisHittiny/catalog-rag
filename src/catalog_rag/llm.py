"""OpenAI-compatible chat client with a disk cache and retry/backoff.

Configured from the environment (loaded from .env):
    LLM_BASE_URL   OpenAI-compatible endpoint (the TAMU chat API)
    LLM_API_KEY    bearer key; falls back to TAMU_CHAT_API_KEY
    LLM_MODEL      generator model (read by eval.run)
    JUDGE_MODEL    judge model, must differ from LLM_MODEL (read by eval.run)

Cache: data/cache/llm/<sha256(model + messages + params)>.json. A hit never touches the API,
so a re-run of an unchanged eval costs zero tokens and is byte-for-byte reproducible.
`read_cache=False` bypasses reads (every call goes to the API) but still writes, which is
how run-to-run drift is measured.
Retries: the transport raises `Retryable` on 429 / 5xx / connection / timeout; `chat`
backs off exponentially (base_delay * 2**attempt, plus jitter) up to `max_retries`.
The transport is injectable so tests never import openai or touch the network.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

Transport = Callable[[str, list[dict], dict], tuple[str, dict]]  # (model, messages, params) -> (content, usage)


class Retryable(Exception):
    """Transient API failure (rate limit, server error, connection problem)."""


class LLMError(Exception):
    """Non-retryable API failure (bad request, unsupported parameter). Never cached."""


def _content_or_raise(resp) -> str:
    """The TAMU proxy answers some bad requests with HTTP 200 and an {"error": ...} body; the
    SDK then returns a ChatCompletion with choices=None. Surface that as LLMError."""
    choices = getattr(resp, "choices", None)
    if not choices:
        raise LLMError(str(getattr(resp, "error", None) or "no choices in response"))
    return choices[0].message.content or ""


@dataclass
class ChatResult:
    content: str
    usage: dict = field(default_factory=dict)
    cached: bool = False


def _openai_transport(base_url: str, api_key: str) -> Transport:
    from openai import (  # lazy: keeps import cheap and tests free of the SDK
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        OpenAI,
        RateLimitError,
    )

    client = OpenAI(base_url=base_url, api_key=api_key, max_retries=0)  # retries are ours

    def call(model: str, messages: list[dict], params: dict) -> tuple[str, dict]:
        try:
            # stream=False must be explicit: the TAMU proxy streams SSE when the key is absent
            resp = client.chat.completions.create(model=model, messages=messages, stream=False, **params)
        except RateLimitError as e:
            raise Retryable(f"429: {e}") from e
        except APIStatusError as e:
            if e.status_code >= 500:
                raise Retryable(f"{e.status_code}: {e}") from e
            raise
        except (APIConnectionError, APITimeoutError) as e:
            raise Retryable(str(e)) from e
        content = _content_or_raise(resp)
        if not content.strip():
            raise Retryable("empty completion")  # never cache an empty answer
        u = resp.usage
        usage = {"prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
                 "completion_tokens": getattr(u, "completion_tokens", 0) or 0} if u else {}
        return content, usage

    return call


class LLMClient:
    def __init__(
        self,
        transport: Transport,
        cache_dir: Path = Path("data/cache/llm"),
        max_retries: int = 5,
        base_delay: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        read_cache: bool = True,
    ) -> None:
        self.transport = transport
        self.cache_dir = Path(cache_dir)
        self.read_cache = read_cache
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.sleep = sleep
        self.usage: dict[str, dict[str, int]] = defaultdict(
            lambda: {"calls": 0, "cache_hits": 0, "prompt_tokens": 0, "completion_tokens": 0}
        )

    @classmethod
    def from_env(cls, cache_dir: Path = Path("data/cache/llm"), env_file: Path = Path(".env"), **kw) -> LLMClient:
        from dotenv import load_dotenv

        load_dotenv(env_file)  # relative to the working directory; the eval runs from the repo root
        base_url = os.environ.get("LLM_BASE_URL", "")
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("TAMU_CHAT_API_KEY", "")
        missing = [n for n, v in (("LLM_BASE_URL", base_url), ("LLM_API_KEY (or TAMU_CHAT_API_KEY)", api_key)) if not v]
        if missing:
            raise SystemExit("generation needs these in .env or the environment: " + ", ".join(missing))
        return cls(_openai_transport(base_url, api_key), cache_dir=cache_dir, **kw)

    # -- cache -------------------------------------------------------------------------
    @staticmethod
    def cache_key(model: str, messages: list[dict], params: dict | None = None) -> str:
        blob = json.dumps({"model": model, "messages": messages, "params": params or {}},
                          sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    # -- calls -------------------------------------------------------------------------
    def chat(self, model: str, messages: list[dict], **params) -> ChatResult:
        key = self.cache_key(model, messages, params)
        path = self._cache_path(key)
        if self.read_cache and path.exists():
            try:
                hit = json.loads(path.read_text(encoding="utf-8"))
                content = hit["content"]
            except (json.JSONDecodeError, KeyError, TypeError):
                path.unlink()  # malformed cache file: refetch instead of aborting the run
            else:
                self.usage[model]["cache_hits"] += 1
                return ChatResult(content=content, usage=hit.get("usage", {}), cached=True)

        content, usage = self._call_with_retry(model, messages, params)
        self.usage[model]["calls"] += 1
        self.usage[model]["prompt_tokens"] += int(usage.get("prompt_tokens", 0))
        self.usage[model]["completion_tokens"] += int(usage.get("completion_tokens", 0))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"model": model, "messages": messages, "params": params, "content": content,
                        "usage": usage}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return ChatResult(content=content, usage=usage, cached=False)

    def _call_with_retry(self, model: str, messages: list[dict], params: dict) -> tuple[str, dict]:
        for attempt in range(self.max_retries + 1):
            try:
                return self.transport(model, messages, params)
            except Retryable:
                if attempt == self.max_retries:
                    raise
                self.sleep(self.base_delay * 2**attempt + random.uniform(0, 0.25))
        raise AssertionError("unreachable")

    # -- reporting ---------------------------------------------------------------------
    def usage_report(self) -> str:
        lines = ["token usage (this run; cache hits cost nothing):"]
        tot = {"calls": 0, "cache_hits": 0, "prompt_tokens": 0, "completion_tokens": 0}
        for model, u in self.usage.items():
            lines.append(f"  {model}: {u['calls']} api calls, {u['cache_hits']} cache hits, "
                         f"{u['prompt_tokens']} prompt + {u['completion_tokens']} completion tokens")
            for k in tot:
                tot[k] += u[k]
        lines.append(f"  total: {tot['calls']} api calls, {tot['cache_hits']} cache hits, "
                     f"{tot['prompt_tokens']} prompt + {tot['completion_tokens']} completion tokens")
        return "\n".join(lines)
