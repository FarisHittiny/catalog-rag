# catalog-rag

[![eval](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml/badge.svg)](https://github.com/FarisHittiny/catalog-rag/actions/workflows/eval.yml)

Eval-driven retrieval-augmented question answering over the ECEN and CSCE course records on catalog.tamu.edu. The product is the eval harness, not the chatbot: a 115-question gold set written by hand and checked against the catalog page, deterministic retrieval metrics, an LLM judge anchored to 30 human labels, and one command that runs every retriever and writes the table. Seven retrievers were built in sequence, from plain BM25 to a rule-routed system that sends "what can I take after X" questions to a prerequisite graph and everything else to BM25 with fused course-code tokens and id pinning. Each change was measured before it was kept, and the ones that did not pay were reverted.

## Results

| retriever | recall@5 | MRR | correctness | judge agreement |
|---|---|---|---|---|
| bm25 (baseline) | 0.610 | 0.569 | 0.512 | - |
| routed | 0.754 | 0.764 | 0.698 | 0.900 (30 labels, before rebind) |
| routed_v2 | 0.899 | 0.879 | 0.791 | pending (26/30 relabeled) |

Corpus of 148 courses, 129 questions (114 answerable). Retrieval metrics over the answerable questions; correctness over all 129, judged by Claude Sonnet 4.6 against hand-written gold answers, with the generator (gpt-5.4-mini) pinned at temperature 0. routed_v2 (headline) is routed with one change: a question that names no course code goes to dense retrieval instead of BM25. It was designed post-hoc, after the first 15 paraphrase questions exposed the gap, and then validated on a 14-question held-out set written afterwards and never retrieved before that run: held-out recall@5 0.911 and correctness 0.643 against routed's 0.268 and 0.214. Judge agreement is on 30 human-labeled rows. The labels were taken against routed's answers (0.900); they have been rebound to routed_v2's answers, 26 of which are identical, and the remaining 4 await relabeling. bm25 generation hands the generator its plain top-5 with no context construction; routed and routed_v2 hand prereq questions the queried course plus every graph result.

The failure that shaped the last change is paraphrases: on the 29 questions that share no vocabulary with the record, every lexical retriever stays at or below recall@5 0.363 on the first batch, because a student who describes a course without naming it or quoting its title gets nothing from BM25; routing those questions to dense takes the paraphrase split to 0.869 (routed 0.283). The open problem now is generation, not retrieval: on three held-out paraphrases (g116, g118, g119) the gold record is in the generator's context and it still answers that the catalog does not cover the question.

The full report, with all eight retrievers, per-type splits, findings and caveats, is in [reports/eval_report.md](reports/eval_report.md).

## Reproduce

```bash
uv run python -m catalog_rag.scrape --depts ECEN --depts CSCE
uv run python -m catalog_rag.chunk
uv run python -m catalog_rag.eval.run --retrievers bm25 --retrievers routed
```

Retrieval needs no API key. Add `--generate` for correctness and the judge; that needs `LLM_BASE_URL`, an API key, `LLM_MODEL` and `JUDGE_MODEL` in `.env` (see `.env.example`). Every LLM call is disk-cached, so re-running an unchanged eval costs nothing.
