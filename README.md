# catalog-rag

[![eval](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml/badge.svg)](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml)

Eval-driven RAG over the Texas A&M course catalog. See `PLAN.md`.

Numbers go here at M3. Not before.

```bash
uv sync --extra dev
cp .env.example .env
uv run pytest
./scripts/m0.sh
```
