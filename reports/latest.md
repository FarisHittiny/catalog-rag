> corpus: Course.text() no longer duplicates the Prerequisite line (148 chunks re-chunked 2026-09-10)

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr |
|---|---|---|---|---|---|---|---|
| bm25 | 148 | overall | 30 | 0.234 | 0.565 | 0.792 | 0.561 |
| bm25 | 148 | factual | 18 | 0.333 | 0.611 | 0.833 | 0.457 |
| bm25 | 148 | prereq | 12 | 0.086 | 0.496 | 0.731 | 0.715 |
| bm25_codes | 148 | overall | 30 | 0.349 | 0.704 | 0.897 | 0.718 |
| bm25_codes | 148 | factual | 18 | 0.500 | 0.778 | 0.944 | 0.613 |
| bm25_codes | 148 | prereq | 12 | 0.124 | 0.594 | 0.825 | 0.875 |
