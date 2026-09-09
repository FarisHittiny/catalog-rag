#!/usr/bin/env bash
# Milestone 0 in one go: scrape, chunk, eval BM25.
set -euo pipefail
uv run python -m catalog_rag.scrape --depts ECEN --depts CSCE
uv run python -m catalog_rag.chunk
uv run python -m catalog_rag.eval.run --retrievers bm25
