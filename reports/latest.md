> corpus: Course.text() no longer duplicates the Prerequisite line (re-chunked 2026-09-10); dense is expected to be flat until code-free questions land, since all 30 current questions name a course code

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr |
|---|---|---|---|---|---|---|---|
| bm25 | 148 | overall | 30 | 0.234 | 0.565 | 0.792 | 0.561 |
| bm25 | 148 | factual | 18 | 0.333 | 0.611 | 0.833 | 0.457 |
| bm25 | 148 | has_code | 30 | 0.234 | 0.565 | 0.792 | 0.561 |
| bm25 | 148 | prereq | 12 | 0.086 | 0.496 | 0.731 | 0.715 |
| bm25_codes | 148 | overall | 30 | 0.349 | 0.704 | 0.897 | 0.718 |
| bm25_codes | 148 | factual | 18 | 0.500 | 0.778 | 0.944 | 0.613 |
| bm25_codes | 148 | has_code | 30 | 0.349 | 0.704 | 0.897 | 0.718 |
| bm25_codes | 148 | prereq | 12 | 0.124 | 0.594 | 0.825 | 0.875 |
| bm25_codes_id | 148 | overall | 30 | 0.567 | 0.823 | 0.928 | 0.772 |
| bm25_codes_id | 148 | factual | 18 | 0.944 | 1.000 | 1.000 | 0.972 |
| bm25_codes_id | 148 | has_code | 30 | 0.567 | 0.823 | 0.928 | 0.772 |
| bm25_codes_id | 148 | prereq | 12 | 0.000 | 0.558 | 0.820 | 0.472 |
| dense | 148 | overall | 30 | 0.057 | 0.441 | 0.554 | 0.418 |
| dense | 148 | factual | 18 | 0.056 | 0.556 | 0.667 | 0.251 |
| dense | 148 | has_code | 30 | 0.057 | 0.441 | 0.554 | 0.418 |
| dense | 148 | prereq | 12 | 0.058 | 0.269 | 0.385 | 0.667 |
| hybrid | 148 | overall | 30 | 0.243 | 0.703 | 0.837 | 0.646 |
| hybrid | 148 | factual | 18 | 0.333 | 0.833 | 0.889 | 0.511 |
| hybrid | 148 | has_code | 30 | 0.243 | 0.703 | 0.837 | 0.646 |
| hybrid | 148 | prereq | 12 | 0.108 | 0.507 | 0.759 | 0.850 |
