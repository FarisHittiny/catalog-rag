> gold set 100 questions, all verified (21 code-free). Prereq gold ids were derived from prereq_graph.unlocked_by, the same graph the graph retriever queries, so graph recall on the prereq split is by construction; the real claim rests on the prereq-string parser matching the catalog. 12 of 25 prereq rows have more than 5 gold ids and 7 have more than 10, so the prereq split's recall@5 ceiling is 0.731 and recall@10 ceiling is 0.913 for any retriever. Router patterns were written against this set, so router accuracy is in-sample. Corpus: Course.text() no longer duplicates the Prerequisite line (re-chunked 2026-09-10); chunks now carry prereqs so the graph is built from the indexed corpus

> router accuracy: 1.000 (100/100)

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr |
|---|---|---|---|---|---|---|---|
| bm25_codes_id | 148 | overall | 85 | 0.549 | 0.887 | 0.955 | 0.816 |
| bm25_codes_id | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 |
| bm25_codes_id | 148 | has_code | 65 | 0.449 | 0.853 | 0.941 | 0.777 |
| bm25_codes_id | 148 | prereq | 25 | 0.000 | 0.637 | 0.847 | 0.480 |
| bm25_codes_id | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 |
| bm25_codes_id | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 |
| graph | 148 | overall | 85 | 0.092 | 0.252 | 0.341 | 0.326 |
| graph | 148 | factual | 40 | 0.000 | 0.000 | 0.025 | 0.003 |
| graph | 148 | has_code | 65 | 0.120 | 0.330 | 0.446 | 0.427 |
| graph | 148 | prereq | 25 | 0.293 | 0.731 | 0.913 | 1.000 |
| graph | 148 | no_code | 20 | 0.000 | 0.000 | 0.000 | 0.000 |
| graph | 148 | multi_hop | 20 | 0.025 | 0.158 | 0.258 | 0.131 |
| routed | 148 | overall | 85 | 0.635 | 0.915 | 0.974 | 0.969 |
| routed | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 |
| routed | 148 | has_code | 65 | 0.561 | 0.889 | 0.966 | 0.977 |
| routed | 148 | prereq | 25 | 0.293 | 0.731 | 0.913 | 1.000 |
| routed | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 |
| routed | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 |
