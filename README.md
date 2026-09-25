# catalog-rag

[![eval](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml/badge.svg)](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml)

Eval-driven retrieval-augmented question answering over the ECEN and CSCE course records on catalog.tamu.edu. The product is the eval harness, not the chatbot: a 115-question gold set written by hand and checked against the catalog page, deterministic retrieval metrics, an LLM judge anchored to 30 human labels, and one command that runs every retriever and writes the table. Seven retrievers were built in sequence, from plain BM25 to a rule-routed system that sends "what can I take after X" questions to a prerequisite graph and everything else to BM25 with fused course-code tokens and id pinning. Each change was measured before it was kept, and the ones that did not pay were reverted.

## Results

| retriever | recall@5 | MRR | correctness | judge agreement |
|---|---|---|---|---|
| bm25 (baseline) | 0.610 | 0.569 | 0.512 | - |
| routed | 0.754 | 0.764 | 0.698 | 0.900 (30 labels, before rebind) |
| routed_v2 | 0.899 | 0.879 | 0.791 | 0.900 (30 labels) |

Corpus of 148 courses, 129 questions (114 answerable). Retrieval metrics over the answerable questions; correctness over all 129, judged by Claude Sonnet 4.6 against hand-written gold answers, with the generator (gpt-5.4-mini) pinned at temperature 0. routed_v2 (headline) is routed with one change: a question that names no course code goes to dense retrieval instead of BM25. It was designed post-hoc, after the first 15 paraphrase questions exposed the gap, and then validated on a 14-question held-out set written afterwards and never retrieved before that run: held-out recall@5 0.911 and correctness 0.643 against routed's 0.268 and 0.214. Judge agreement is on 30 human-labeled rows. The labels were taken against routed's answers (0.900); they were rebound to routed_v2's answers and the four changed rows relabeled; agreement is 0.900 (27/30). bm25 generation hands the generator its plain top-5 with no context construction; routed and routed_v2 hand prereq questions the queried course plus every graph result.

The failure that shaped the last change is paraphrases: on the 29 questions that share no vocabulary with the record, every lexical retriever stays at or below recall@5 0.363 on the first batch, because a student who describes a course without naming it or quoting its title gets nothing from BM25; routing those questions to dense takes the paraphrase split to 0.869 (routed 0.283). The open problem now is generation, not retrieval: on three held-out paraphrases (g116, g118, g119) the gold record is in the generator's context and it still answers that the catalog does not cover the question.

The full report, with all eight retrievers, per-type splits, findings and caveats, is in [reports/eval_report.md](reports/eval_report.md).

## Demo

`src/catalog_rag/api.py` serves the headline retriever behind two endpoints. `POST /ask` runs routed_v2 on every request and returns the route, which retriever answered, the top-10 courses, and the course ids the generator would see; it only calls the LLM when the body sets `"generate": true`, using the same prompt, model and disk cache as the eval, so the demo answers what the table measures. `GET /health` is the probe.

```bash
uv sync
uv run uvicorn catalog_rag.api:app --port 7860
curl -s localhost:7860/ask -H "content-type: application/json"   -d "{\"question\": \"what do I need before ECEN 350\", \"generate\": false}"
```

| variable | purpose |
|---|---|
| `TAMU_CHAT_API_KEY` (or `LLM_API_KEY`) | key for the OpenAI-compatible endpoint; without it `/ask` still retrieves and `generate=true` returns 503 |
| `LLM_BASE_URL` | that endpoint |
| `LLM_MODEL` | generator model, e.g. `protected.gpt-5.4-mini` |
| `DEMO_ORIGINS` | comma-separated CORS allow-list for the page that calls the API; unset means no cross-origin access |
| `DEMO_GENERATE_PER_HOUR` | generated answers per client IP per hour (default 20) |
| `DEMO_DAILY_TOKENS` | uncached generator tokens per UTC day before fresh answers stop (default 200000) |
| `DEMO_PROXY_HOPS` | reverse proxies in front of the API (default 0). The rate limit keys on the socket peer, or with N>0 on the Nth-from-last `X-Forwarded-For` entry, the one the proxy wrote; the Dockerfile sets 1 for the Space proxy |

Questions are capped at 300 characters. Over the rate limit or the daily budget the API answers 429 with a plain message; cached answers and retrieval-only calls keep working.

The `Dockerfile` targets a Hugging Face Docker Space: python 3.12 slim, uv, port 7860, bge-small weights and the chunk embeddings baked in at build time so the first request is fast. `docker build -t catalog-rag-demo .` then `docker run --rm -p 7860:7860 --env-file .env catalog-rag-demo`. On the Space, set `sdk: docker` and `app_port: 7860` in the Space README front matter and add the variables above as Space secrets.

## Reproduce

```bash
uv run python -m catalog_rag.scrape --depts ECEN --depts CSCE
uv run python -m catalog_rag.chunk
uv run python -m catalog_rag.eval.run --retrievers bm25 --retrievers routed
```

Retrieval needs no API key. Add `--generate` for correctness and the judge; that needs `LLM_BASE_URL`, an API key, `LLM_MODEL` and `JUDGE_MODEL` in `.env` (see `.env.example`). Every LLM call is disk-cached, so re-running an unchanged eval costs nothing.
