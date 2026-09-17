# catalog-rag

[![eval](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml/badge.svg)](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml)

Eval-driven retrieval-augmented question answering over the ECEN and CSCE course records on catalog.tamu.edu. The product is the eval harness, not the chatbot: a 115-question gold set written by hand and checked against the catalog page, deterministic retrieval metrics, an LLM judge anchored to 30 human labels, and one command that runs every retriever and writes the table. Seven retrievers were built in sequence, from plain BM25 to a rule-routed system that sends "what can I take after X" questions to a prerequisite graph and everything else to BM25 with fused course-code tokens and id pinning. Each change was measured before it was kept, and the ones that did not pay were reverted.

## Results

| retriever | recall@5 | MRR | correctness | judge agreement |
|---|---|---|---|---|
| bm25 (baseline) | 0.671 | 0.635 | - | - |
| routed | 0.822 | 0.848 | 0.757 | 0.900 |

Corpus of 148 courses. Retrieval metrics over the 100 answerable questions; correctness over all 115, judged by Claude Sonnet 4.6 against hand-written gold answers, with the generator (gpt-5.4-mini) pinned at temperature 0. Judge agreement is on the 30 human-labeled rows. Correctness was not run for the baseline.

The one place the system fails is paraphrases: on the 15 questions that share no vocabulary with the record, dense retrieval reaches recall@5 0.711 and every lexical retriever, routed included, stays at or below 0.363, because a student who describes a course without naming it or quoting its title gets nothing from BM25.

The full report, with all seven retrievers, per-type splits, findings and caveats, is in [reports/eval_report.md](reports/eval_report.md).

## Reproduce

```bash
uv run python -m catalog_rag.scrape --depts ECEN --depts CSCE
uv run python -m catalog_rag.chunk
uv run python -m catalog_rag.eval.run --retrievers bm25 --retrievers routed
```

Retrieval needs no API key. Add `--generate` for correctness and the judge; that needs `LLM_BASE_URL`, an API key, `LLM_MODEL` and `JUDGE_MODEL` in `.env` (see `.env.example`). Every LLM call is disk-cached, so re-running an unchanged eval costs nothing.
