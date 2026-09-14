> gold set 100 questions, all verified (21 code-free). Generation: top-5 course records per question, generator LLM_MODEL (gpt-5.4-mini via TAMU chat API), judge JUDGE_MODEL (Claude Sonnet 4.6, a different model). Prereq answers are capped by the top-5 context: 12 of 25 prereq rows have more than 5 gold courses, so prereq correctness is bounded above. The graph retriever returns only the courses a code unlocks, not the queried course itself, and the generator sometimes abstains on such a context even when the answer is in it; that is why routed prereq correctness can trail bm25_codes_id despite perfect retrieval. Judge agreement reads 'unlabeled' until data/gold/human_labels.jsonl is filled in by hand. Prereq gold ids derive from the same graph the graph retriever queries, so graph recall on that split is by construction. Router accuracy is in-sample. Corpus: Course.text() no longer duplicates the Prerequisite line (re-chunked 2026-09-10)

> router accuracy: 1.000 (100/100)

> generator: protected.gpt-5.4-mini; judge: protected.Claude Sonnet 4.6; top-5 records per question

> judge agreement (bm25_codes_id: unlabeled (0/30 labeled, 22/30 answers current), routed: unlabeled (0/30 labeled, 30/30 answers current))

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr | n_gen | correctness | citation_prec | abstain_acc | judge_agr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bm25_codes_id | 148 | overall | 85 | 0.549 | 0.887 | 0.955 | 0.816 | 100 | 0.740 | 0.945 | 0.950 | unlabeled (0/30 labeled, 22/30 answers current) |
| bm25_codes_id | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 | 40 | 0.825 | 0.972 | 0.900 | - |
| bm25_codes_id | 148 | has_code | 65 | 0.449 | 0.853 | 0.941 | 0.777 | 79 | 0.671 | 0.926 | 0.937 | - |
| bm25_codes_id | 148 | prereq | 25 | 0.000 | 0.637 | 0.847 | 0.480 | 25 | 0.400 | 0.907 | 1.000 | - |
| bm25_codes_id | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 | 21 | 1.000 | 1.000 | 1.000 | - |
| bm25_codes_id | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | 20 | 0.850 | 0.942 | 1.000 | - |
| bm25_codes_id | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |
| routed | 148 | overall | 85 | 0.635 | 0.915 | 0.974 | 0.969 | 100 | 0.720 | 0.967 | 0.930 | unlabeled (0/30 labeled, 30/30 answers current) |
| routed | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 | 40 | 0.825 | 0.972 | 0.900 | - |
| routed | 148 | has_code | 65 | 0.561 | 0.889 | 0.966 | 0.977 | 79 | 0.646 | 0.955 | 0.911 | - |
| routed | 148 | prereq | 25 | 0.293 | 0.731 | 0.913 | 1.000 | 25 | 0.320 | 0.978 | 0.920 | - |
| routed | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 | 21 | 1.000 | 1.000 | 1.000 | - |
| routed | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 | 20 | 0.850 | 0.942 | 1.000 | - |
| routed | 148 | not_in_catalog | 0 | - | - | - | - | 15 | 0.933 | - | 0.933 | - |

```
token usage (this run; cache hits cost nothing):
  protected.gpt-5.4-mini: 125 api calls, 75 cache hits, 86003 prompt + 6007 completion tokens
  protected.Claude Sonnet 4.6: 88 api calls, 112 cache hits, 40153 prompt + 10718 completion tokens
  total: 213 api calls, 187 cache hits, 126156 prompt + 16725 completion tokens
```
