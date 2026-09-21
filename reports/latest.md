> M3 final: 129 questions (115 + 14 holdout B, g128 excluded as unverified); generation + judge for bm25, routed, routed_v2

> router accuracy: 0.930 (120/129); misrouted: g111, g112, g113, g114, g115, g126, g127, g129, g130; paraphrase: 0.690 (20/29); holdout_b: 0.714 (10/14)

> generator: protected.gpt-5.4-mini {'temperature': 0, 'seed': 0}; judge: protected.Claude Sonnet 4.6 {'seed': 0}; top-5 records per question

> judge agreement (bm25: unlabeled (26/30 labeled, 11/30 answers current), routed: unlabeled (26/30 labeled, 26/30 answers current), routed_v2: unlabeled (26/30 labeled, 30/30 answers current))

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr | n_gen | correctness | citation_prec | abstain_acc | judge_agr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bm25 | 148 | overall | 114 | 0.299 | 0.610 | 0.751 | 0.569 | 129 | 0.512 | 0.901 | 0.721 | unlabeled (26/30 labeled, 11/30 answers current) |
| bm25 | 148 | factual | 60 | 0.417 | 0.533 | 0.650 | 0.468 | 60 | 0.467 | 0.890 | 0.567 | - |
| bm25 | 148 | has_code | 74 | 0.225 | 0.670 | 0.859 | 0.618 | 88 | 0.523 | 0.911 | 0.795 | - |
| bm25 | 148 | prereq | 34 | 0.072 | 0.586 | 0.835 | 0.599 | 34 | 0.324 | 0.866 | 0.824 | - |
| bm25 | 148 | no_code | 40 | 0.438 | 0.500 | 0.550 | 0.478 | 41 | 0.488 | 0.875 | 0.561 | - |
| bm25 | 148 | multi_hop | 20 | 0.333 | 0.883 | 0.908 | 0.821 | 20 | 0.600 | 0.984 | 0.800 | - |
| bm25 | 148 | paraphrase | 29 | 0.004 | 0.243 | 0.375 | 0.128 | 29 | 0.207 | 0.575 | 0.345 | - |
| bm25 | 148 | holdout_b | 14 | 0.000 | 0.179 | 0.429 | 0.097 | 14 | 0.143 | 0.500 | 0.286 | - |
| bm25 | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 1.000 | - | 1.000 | - |
| bm25_codes | 148 | overall | 114 | 0.368 | 0.696 | 0.787 | 0.683 | - | - | - | - | - |
| bm25_codes | 148 | factual | 60 | 0.500 | 0.600 | 0.683 | 0.542 | - | - | - | - | - |
| bm25_codes | 148 | has_code | 74 | 0.330 | 0.802 | 0.915 | 0.794 | - | - | - | - | - |
| bm25_codes | 148 | prereq | 34 | 0.125 | 0.741 | 0.898 | 0.809 | - | - | - | - | - |
| bm25_codes | 148 | no_code | 40 | 0.438 | 0.500 | 0.550 | 0.478 | - | - | - | - | - |
| bm25_codes | 148 | multi_hop | 20 | 0.383 | 0.908 | 0.908 | 0.892 | - | - | - | - | - |
| bm25_codes | 148 | paraphrase | 29 | 0.033 | 0.286 | 0.375 | 0.233 | - | - | - | - | - |
| bm25_codes | 148 | holdout_b | 14 | 0.036 | 0.268 | 0.429 | 0.233 | - | - | - | - | - |
| bm25_codes_id | 148 | overall | 114 | 0.409 | 0.736 | 0.811 | 0.651 | - | - | - | - | - |
| bm25_codes_id | 148 | factual | 60 | 0.650 | 0.667 | 0.700 | 0.663 | - | - | - | - | - |
| bm25_codes_id | 148 | has_code | 74 | 0.394 | 0.863 | 0.953 | 0.745 | - | - | - | - | - |
| bm25_codes_id | 148 | prereq | 34 | 0.000 | 0.717 | 0.897 | 0.490 | - | - | - | - | - |
| bm25_codes_id | 148 | no_code | 40 | 0.438 | 0.500 | 0.550 | 0.478 | - | - | - | - | - |
| bm25_codes_id | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | - | - | - | - | - |
| bm25_codes_id | 148 | paraphrase | 29 | 0.000 | 0.283 | 0.375 | 0.164 | - | - | - | - | - |
| bm25_codes_id | 148 | holdout_b | 14 | 0.000 | 0.268 | 0.429 | 0.162 | - | - | - | - | - |
| dense | 148 | overall | 114 | 0.323 | 0.587 | 0.713 | 0.574 | - | - | - | - | - |
| dense | 148 | factual | 60 | 0.467 | 0.767 | 0.867 | 0.587 | - | - | - | - | - |
| dense | 148 | has_code | 74 | 0.126 | 0.411 | 0.571 | 0.448 | - | - | - | - | - |
| dense | 148 | prereq | 34 | 0.118 | 0.277 | 0.429 | 0.505 | - | - | - | - | - |
| dense | 148 | no_code | 40 | 0.688 | 0.912 | 0.975 | 0.805 | - | - | - | - | - |
| dense | 148 | multi_hop | 20 | 0.242 | 0.575 | 0.733 | 0.650 | - | - | - | - | - |
| dense | 148 | paraphrase | 29 | 0.483 | 0.721 | 0.864 | 0.596 | - | - | - | - | - |
| dense | 148 | holdout_b | 14 | 0.500 | 0.732 | 0.821 | 0.590 | - | - | - | - | - |
| hybrid | 148 | overall | 114 | 0.342 | 0.660 | 0.764 | 0.637 | - | - | - | - | - |
| hybrid | 148 | factual | 60 | 0.450 | 0.633 | 0.717 | 0.526 | - | - | - | - | - |
| hybrid | 148 | has_code | 74 | 0.270 | 0.706 | 0.839 | 0.690 | - | - | - | - | - |
| hybrid | 148 | prereq | 34 | 0.157 | 0.605 | 0.777 | 0.727 | - | - | - | - | - |
| hybrid | 148 | no_code | 40 | 0.475 | 0.575 | 0.625 | 0.540 | - | - | - | - | - |
| hybrid | 148 | multi_hop | 20 | 0.333 | 0.833 | 0.883 | 0.818 | - | - | - | - | - |
| hybrid | 148 | paraphrase | 29 | 0.127 | 0.360 | 0.454 | 0.297 | - | - | - | - | - |
| hybrid | 148 | holdout_b | 14 | 0.089 | 0.357 | 0.464 | 0.260 | - | - | - | - | - |
| graph | 148 | overall | 114 | 0.121 | 0.263 | 0.333 | 0.322 | - | - | - | - | - |
| graph | 148 | factual | 60 | 0.000 | 0.000 | 0.017 | 0.002 | - | - | - | - | - |
| graph | 148 | has_code | 74 | 0.186 | 0.405 | 0.513 | 0.497 | - | - | - | - | - |
| graph | 148 | prereq | 34 | 0.390 | 0.789 | 0.936 | 1.000 | - | - | - | - | - |
| graph | 148 | no_code | 40 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | - | - | - |
| graph | 148 | multi_hop | 20 | 0.025 | 0.158 | 0.258 | 0.131 | - | - | - | - | - |
| graph | 148 | paraphrase | 29 | 0.205 | 0.295 | 0.310 | 0.310 | - | - | - | - | - |
| graph | 148 | holdout_b | 14 | 0.179 | 0.286 | 0.286 | 0.286 | - | - | - | - | - |
| routed | 148 | overall | 114 | 0.474 | 0.754 | 0.822 | 0.764 | 129 | 0.698 | 0.914 | 0.829 | unlabeled (26/30 labeled, 26/30 answers current) |
| routed | 148 | factual | 60 | 0.650 | 0.667 | 0.700 | 0.663 | 60 | 0.550 | 0.900 | 0.650 | - |
| routed | 148 | has_code | 74 | 0.493 | 0.891 | 0.969 | 0.919 | 88 | 0.784 | 0.926 | 0.955 | - |
| routed | 148 | prereq | 34 | 0.215 | 0.778 | 0.932 | 0.868 | 34 | 0.794 | 0.897 | 1.000 | - |
| routed | 148 | no_code | 40 | 0.438 | 0.500 | 0.550 | 0.478 | 41 | 0.512 | 0.875 | 0.561 | - |
| routed | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | 20 | 0.800 | 0.970 | 1.000 | - |
| routed | 148 | paraphrase | 29 | 0.000 | 0.283 | 0.375 | 0.164 | 29 | 0.207 | 0.727 | 0.379 | - |
| routed | 148 | holdout_b | 14 | 0.000 | 0.268 | 0.429 | 0.162 | 14 | 0.214 | 0.800 | 0.357 | - |
| routed | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |
| routed_v2 | 148 | overall | 114 | 0.561 | 0.899 | 0.971 | 0.879 | 129 | 0.791 | 0.932 | 0.907 | unlabeled (26/30 labeled, 30/30 answers current) |
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
  protected.gpt-5.4-mini: 6 api calls, 381 cache hits, 3937 prompt + 204 completion tokens
  protected.Claude Sonnet 4.6: 4 api calls, 383 cache hits, 1832 prompt + 411 completion tokens
  total: 10 api calls, 764 cache hits, 5769 prompt + 615 completion tokens
```
