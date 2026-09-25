# Hugging Face Docker Space image for the catalog-rag demo API (src/catalog_rag/api.py).
# Build:  docker build -t catalog-rag-demo .
# Run:    docker run --rm -p 7860:7860 --env-file .env catalog-rag-demo
# Embeddings and the bge-small weights are computed at build time, so the first request is fast
# and the container never needs network access to Hugging Face.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Spaces run the container as uid 1000; own everything under $HOME so the app can write its caches.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_COMPILE_BYTECODE=1
WORKDIR $HOME/app

# Dependencies first (cached layer): CPU-only torch on Linux via [tool.uv.sources] in pyproject.
COPY --chown=user pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Code and the two corpus files the API reads; then bake the model weights + embeddings.npy.
COPY --chown=user src ./src
COPY --chown=user data/processed/chunks.jsonl data/processed/courses.jsonl ./data/processed/
RUN uv sync --frozen --no-dev \
 && uv run python -m catalog_rag.api --build-embeddings

# Everything the model needs is now in the image; never call out to the Hub at runtime.
# DEMO_PROXY_HOPS=1: the Space proxy appends the caller's address to X-Forwarded-For; the rate
# limiter keys on that last entry (api.client_key) instead of uvicorn's forgeable leftmost one.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    DEMO_PROXY_HOPS=1

EXPOSE 7860
CMD ["uv", "run", "--no-sync", "uvicorn", "catalog_rag.api:app", "--host", "0.0.0.0", "--port", "7860"]
