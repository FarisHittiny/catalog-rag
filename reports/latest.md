> M3: 129 questions (115 + 14 holdout B, g128 excluded as unverified); routed vs routed_v2, held-out validation

> router accuracy: 0.930 (120/129); misrouted: g111, g112, g113, g114, g115, g126, g127, g129, g130; paraphrase: 0.690 (20/29); holdout_b: 0.714 (10/14)

> generator: protected.gpt-5.4-mini {'temperature': 0, 'seed': 0}; judge: protected.Claude Sonnet 4.6 {'seed': 0}; top-5 records per question

> judge agreement (routed: 0.900 (30/30), routed_v2: unlabeled (30/30 labeled, 26/30 answers current))

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr | n_gen | correctness | citation_prec | abstain_acc | judge_agr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| routed | 148 | overall | 114 | 0.474 | 0.754 | 0.822 | 0.764 | 129 | 0.698 | 0.914 | 0.829 | 0.900 (30/30) |
| routed | 148 | factual | 60 | 0.650 | 0.667 | 0.700 | 0.663 | 60 | 0.550 | 0.900 | 0.650 | - |
| routed | 148 | has_code | 74 | 0.493 | 0.891 | 0.969 | 0.919 | 88 | 0.784 | 0.926 | 0.955 | - |
| routed | 148 | prereq | 34 | 0.215 | 0.778 | 0.932 | 0.868 | 34 | 0.794 | 0.897 | 1.000 | - |
| routed | 148 | no_code | 40 | 0.438 | 0.500 | 0.550 | 0.478 | 41 | 0.512 | 0.875 | 0.561 | - |
| routed | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | 20 | 0.800 | 0.970 | 1.000 | - |
| routed | 148 | paraphrase | 29 | 0.000 | 0.283 | 0.375 | 0.164 | 29 | 0.207 | 0.727 | 0.379 | - |
| routed | 148 | holdout_b | 14 | 0.000 | 0.268 | 0.429 | 0.162 | 14 | 0.214 | 0.800 | 0.357 | - |
| routed | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |
| routed_v2 | 148 | overall | 114 | 0.561 | 0.899 | 0.971 | 0.879 | 129 | 0.791 | 0.932 | 0.907 | unlabeled (30/30 labeled, 26/30 answers current) |
| routed_v2 | 148 | factual | 60 | 0.800 | 0.950 | 0.983 | 0.862 | 60 | 0.767 | 0.942 | 0.833 | - |
| routed_v2 | 148 | has_code | 74 | 0.493 | 0.891 | 0.969 | 0.919 | 88 | 0.784 | 0.926 | 0.955 | - |
| routed_v2 | 148 | prereq | 34 | 0.215 | 0.778 | 0.932 | 0.868 | 34 | 0.794 | 0.897 | 1.000 | - |
| routed_v2 | 148 | no_code | 40 | 0.688 | 0.912 | 0.975 | 0.805 | 41 | 0.805 | 0.945 | 0.805 | - |
| routed_v2 | 148 | multi_hop | 20 | 0.433 | 0.950 | 1.000 | 0.950 | 20 | 0.750 | 0.968 | 0.950 | - |
| routed_v2 | 148 | paraphrase | 29 | 0.414 | 0.869 | 0.962 | 0.633 | 29 | 0.655 | 0.909 | 0.759 | - |
| routed_v2 | 148 | holdout_b | 14 | 0.500 | 0.911 | 1.000 | 0.701 | 14 | 0.643 | 0.950 | 0.714 | - |
| routed_v2 | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |

```
token usage (this run; cache hits cost nothing):
  protected.gpt-5.4-mini: 24 api calls, 234 cache hits, 16080 prompt + 644 completion tokens
  protected.Claude Sonnet 4.6: 20 api calls, 238 cache hits, 8565 prompt + 1462 completion tokens
  total: 44 api calls, 472 cache hits, 24645 prompt + 2106 completion tokens
```
