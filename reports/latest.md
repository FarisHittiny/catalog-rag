> gold set 100 questions, all verified (21 code-free). Generation: routed prereq questions get the queried course's own record first, then every graph result (no cap); everything else gets the retriever's top-5 records. Generator LLM_MODEL (gpt-5.4-mini via TAMU chat API) pinned to temperature 0, seed 0; judge JUDGE_MODEL (Claude Sonnet 4.6, a different model) cannot be pinned on this endpoint (extended thinking is on, temperature must be 1), seed is sent but likely ignored. Request params are part of the LLM cache key. Drift check: two back-to-back --fresh runs of routed agreed on 100/100 answers and 100/100 verdicts. Rubric now scores any answer that omits a gold course as 0. A 'list every applicable course' prompt rule was tried in 8d9dea8: citation precision fell 0.962 to 0.906 with no correctness gain, so it was reverted in 2088cbe. Judge agreement counts only rows whose stored generated_answer matches the current answer and reads 'unlabeled' until all 30 are filled in. Prereq gold ids derive from the same graph the graph retriever queries, so graph recall on that split is by construction. Router accuracy is in-sample. Corpus: Course.text() no longer duplicates the Prerequisite line (re-chunked 2026-09-10)

> router accuracy: 1.000 (100/100)

> generator: protected.gpt-5.4-mini {'temperature': 0, 'seed': 0}; judge: protected.Claude Sonnet 4.6 {'seed': 0}; top-5 records per question

> judge agreement (routed: unlabeled (13/30 labeled, 30/30 answers current))

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr | n_gen | correctness | citation_prec | abstain_acc | judge_agr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| routed | 148 | overall | 85 | 0.635 | 0.915 | 0.974 | 0.969 | 100 | 0.830 | 0.940 | 0.960 | unlabeled (13/30 labeled, 30/30 answers current) |
| routed | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 | 40 | 0.825 | 0.948 | 0.925 | - |
| routed | 148 | has_code | 65 | 0.561 | 0.889 | 0.966 | 0.977 | 79 | 0.785 | 0.932 | 0.949 | - |
| routed | 148 | prereq | 25 | 0.293 | 0.731 | 0.913 | 1.000 | 25 | 0.800 | 0.903 | 1.000 | - |
| routed | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 | 21 | 1.000 | 0.963 | 1.000 | - |
| routed | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | 20 | 0.800 | 0.970 | 1.000 | - |
| routed | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |

```
token usage (this run; cache hits cost nothing):
  protected.gpt-5.4-mini: 0 api calls, 100 cache hits, 0 prompt + 0 completion tokens
  protected.Claude Sonnet 4.6: 100 api calls, 0 cache hits, 45922 prompt + 10074 completion tokens
  total: 100 api calls, 100 cache hits, 45922 prompt + 10074 completion tokens
```
