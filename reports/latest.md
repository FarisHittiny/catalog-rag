> gold set 100 questions, all verified (21 code-free); corpus: Course.text() no longer duplicates the Prerequisite line (re-chunked 2026-09-10)

| retriever | corpus | split | n | recall@1 | recall@5 | recall@10 | mrr |
|---|---|---|---|---|---|---|---|
| bm25 | 148 | overall | 85 | 0.400 | 0.734 | 0.874 | 0.719 |
| bm25 | 148 | factual | 40 | 0.625 | 0.800 | 0.925 | 0.695 |
| bm25 | 148 | has_code | 65 | 0.254 | 0.652 | 0.835 | 0.651 |
| bm25 | 148 | prereq | 25 | 0.094 | 0.508 | 0.764 | 0.677 |
| bm25 | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 |
| bm25 | 148 | multi_hop | 20 | 0.333 | 0.883 | 0.908 | 0.821 |
| bm25_codes | 148 | overall | 85 | 0.481 | 0.833 | 0.922 | 0.830 |
| bm25_codes | 148 | factual | 40 | 0.750 | 0.900 | 0.975 | 0.806 |
| bm25_codes | 148 | has_code | 65 | 0.360 | 0.782 | 0.899 | 0.796 |
| bm25_codes | 148 | prereq | 25 | 0.129 | 0.666 | 0.850 | 0.820 |
| bm25_codes | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 |
| bm25_codes | 148 | multi_hop | 20 | 0.383 | 0.908 | 0.908 | 0.892 |
| bm25_codes_id | 148 | overall | 85 | 0.549 | 0.887 | 0.955 | 0.816 |
| bm25_codes_id | 148 | factual | 40 | 0.975 | 1.000 | 1.000 | 0.988 |
| bm25_codes_id | 148 | has_code | 65 | 0.449 | 0.853 | 0.941 | 0.777 |
| bm25_codes_id | 148 | prereq | 25 | 0.000 | 0.637 | 0.847 | 0.480 |
| bm25_codes_id | 148 | no_code | 20 | 0.875 | 1.000 | 1.000 | 0.942 |
| bm25_codes_id | 148 | multi_hop | 20 | 0.383 | 0.975 | 1.000 | 0.892 |
| dense | 148 | overall | 85 | 0.269 | 0.542 | 0.661 | 0.566 |
| dense | 148 | factual | 40 | 0.400 | 0.725 | 0.825 | 0.534 |
| dense | 148 | has_code | 65 | 0.113 | 0.409 | 0.557 | 0.458 |
| dense | 148 | prereq | 25 | 0.081 | 0.223 | 0.342 | 0.551 |
| dense | 148 | no_code | 20 | 0.775 | 0.975 | 1.000 | 0.917 |
| dense | 148 | multi_hop | 20 | 0.242 | 0.575 | 0.733 | 0.650 |
| hybrid | 148 | overall | 85 | 0.416 | 0.762 | 0.869 | 0.753 |
| hybrid | 148 | factual | 40 | 0.650 | 0.875 | 0.950 | 0.736 |
| hybrid | 148 | has_code | 65 | 0.266 | 0.689 | 0.828 | 0.685 |
| hybrid | 148 | prereq | 25 | 0.106 | 0.525 | 0.726 | 0.728 |
| hybrid | 148 | no_code | 20 | 0.900 | 1.000 | 1.000 | 0.975 |
| hybrid | 148 | multi_hop | 20 | 0.333 | 0.833 | 0.883 | 0.818 |
