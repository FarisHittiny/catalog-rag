> gold set 100 questions, all verified (21 code-free). Generation: routed prereq questions get the queried course's own record first, then every graph result (no cap); everything else gets the retriever's top-5 records. System prompt rule 4 asks for every applicable course on require/unlock/follow-from questions. Generator LLM_MODEL (gpt-5.4-mini via TAMU chat API), judge JUDGE_MODEL (Claude Sonnet 4.6, a different model). Judge agreement reads 'unlabeled' until data/gold/human_labels.jsonl is filled in by hand. Prereq gold ids derive from the same graph the graph retriever queries, so graph recall on that split is by construction. Router accuracy is in-sample. Corpus: Course.text() no longer duplicates the Prerequisite line (re-chunked 2026-09-10)

> router accuracy: 1.000 (100/100)

> generator: protected.gpt-5.4-mini; judge: protected.Claude Sonnet 4.6; top-5 records per question

> judge agreement (routed: unlabeled (0/30 labeled, 30/30 answers current))

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr | n_gen | correctness | citation_prec | abstain_acc | judge_agr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| routed | 148 | overall | 85 | 0.635 | 0.915 | 0.974 | 0.969 | 100 | 0.850 | 0.906 | 0.960 | unlabeled (0/30 labeled, 30/30 answers current) |
| routed | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 | 40 | 0.900 | 0.876 | 0.925 | - |
| routed | 148 | has_code | 65 | 0.561 | 0.889 | 0.966 | 0.977 | 79 | 0.823 | 0.930 | 0.949 | - |
| routed | 148 | prereq | 25 | 0.293 | 0.731 | 0.913 | 1.000 | 25 | 0.760 | 0.949 | 1.000 | - |
| routed | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 | 21 | 0.952 | 0.831 | 1.000 | - |
| routed | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | 20 | 0.800 | 0.906 | 1.000 | - |
| routed | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |

```
token usage (this run; cache hits cost nothing):
  protected.gpt-5.4-mini: 100 api calls, 0 cache hits, 83400 prompt + 5532 completion tokens
  protected.Claude Sonnet 4.6: 64 api calls, 36 cache hits, 30112 prompt + 6514 completion tokens
  total: 164 api calls, 36 cache hits, 113512 prompt + 12046 completion tokens
```
