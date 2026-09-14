> router accuracy: 1.000 (100/100)

> generator: protected.gpt-5.4-mini {'temperature': 0, 'seed': 0}; judge: protected.Claude Sonnet 4.6 {'seed': 0}; top-5 records per question

> judge agreement (routed: 0.900 (30/30))

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr | n_gen | correctness | citation_prec | abstain_acc | judge_agr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| routed | 148 | overall | 85 | 0.635 | 0.915 | 0.974 | 0.969 | 100 | 0.840 | 0.939 | 0.960 | 0.900 (30/30) |
| routed | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 | 40 | 0.825 | 0.948 | 0.925 | - |
| routed | 148 | has_code | 65 | 0.561 | 0.889 | 0.966 | 0.977 | 79 | 0.797 | 0.931 | 0.949 | - |
| routed | 148 | prereq | 25 | 0.293 | 0.731 | 0.913 | 1.000 | 25 | 0.840 | 0.900 | 1.000 | - |
| routed | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 | 21 | 1.000 | 0.963 | 1.000 | - |
| routed | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | 20 | 0.800 | 0.970 | 1.000 | - |
| routed | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |

```
token usage (this run; cache hits cost nothing):
  protected.gpt-5.4-mini: 0 api calls, 100 cache hits, 0 prompt + 0 completion tokens
  protected.Claude Sonnet 4.6: 0 api calls, 100 cache hits, 0 prompt + 0 completion tokens
  total: 0 api calls, 200 cache hits, 0 prompt + 0 completion tokens
```
