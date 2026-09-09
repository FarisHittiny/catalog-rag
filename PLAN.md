# catalog-rag: plan

Eval-driven RAG over the Texas A&M course catalog. The product is the **eval harness and the numbers**, not the chatbot. Every retrieval and generation change gets measured against a human-written gold set before it's kept.

Start narrow (CE degree plan + ECEN + CSCE), expand later by adding department prefixes. Numbers are always reported with corpus size.

---

## What this is for

- A résumé bullet with real numbers by end of September, before applications peak.
- A public repo and eval report, then a demo on farishittiny.com.
- A talking point for the Sep 8–10 booths: "I'm building an eval harness for a RAG system; baseline recall@5 is X on N courses, hybrid retrieval is next."

**Rule:** nothing goes on the résumé until the eval produces the number.

---

## MVP scope

**In**
- Scrape course descriptions and the CE degree plan from catalog.tamu.edu (static public site; no Howdy, no section data, no login).
- Three retrievers with one interface: BM25, dense embeddings, hybrid (RRF) + cross-encoder rerank.
- Prereq graph (networkx) built from the parsed prerequisite strings. Used to answer "what can I take after X" questions and as an eval case where pure text retrieval fails.
- Gold set of 100 questions across four types, tagged by department.
- Generation with cited course codes. Must abstain on questions the catalog can't answer.
- Eval harness: retrieval metrics (deterministic), answer metrics (LLM judge with a human-verified subset), one command, one Markdown table.
- GitHub Actions runs the eval on every PR and posts the table.

**Out (for now)**
- Live section availability, professors, RateMyProfessor, grade distributions.
- Multi-turn chat. Every question is standalone.
- Fine-tuning anything.
- Auth, accounts, saved plans.

---

## Milestones

| # | Target | Done when |
|---|--------|-----------|
| M0 | Sep 8 | ECEN + CSCE + CE degree plan scraped to JSONL. 30 gold questions. BM25 recall@5 number exists. |
| M1 | Sep 15 | Dense + hybrid retrievers. 100 gold questions. `make eval` prints the comparison table. CI runs it. |
| M2 | Sep 22 | Generation + judge. 30-question human-verified subset with judge agreement reported. Prereq graph answering prereq-type questions. Abstention on `not_in_catalog`. |
| M3 | Sep 30 | Eval report in `reports/`, README with the table, résumé bullet drafted, demo stack chosen. |
| M4 | Oct | Demo live. Expand to all Engineering if it's cheap. |

M0 is the one that matters this week. Everything you need for the booth talking point is in M0.

---

## Stack

### Decided: Python core

| Concern | Choice | Why |
|---------|--------|-----|
| Runtime | Python 3.12, `uv` | Same language for scraper, retrievers, eval. Fast installs. |
| Scraper | `httpx` + `beautifulsoup4` | Catalog is CourseLeaf static HTML. No JS rendering needed. |
| Sparse retrieval | `rank_bm25` | Baseline. Zero dependencies, runs in CI. |
| Dense retrieval | `sentence-transformers`, `BAAI/bge-small-en-v1.5` | Local, free, 384-dim, fast on CPU. Good enough for ~2k chunks. |
| Vector search | `numpy` dot product | A few thousand chunks doesn't need a vector DB. Swap in FAISS if corpus > 50k. |
| Rerank | `BAAI/bge-reranker-base` cross-encoder | Standard hybrid setup. Local. |
| Prereq graph | `networkx` | Directed graph, course code → prereq codes. Handles "and/or" via parsed groups. |
| Config/CLI | `pydantic`, `typer` | Typed configs, one `catalog-rag` CLI. |
| Tests | `pytest` | Metrics are unit-tested before any number gets reported. |
| CI | GitHub Actions | Eval on every PR. Same story as Verilator CI on the RISC-V repo. |

### Decide by M2: generation and judge provider

Any of these work. Pick on cost and what you want on the résumé.

| Option | Cost | Note |
|--------|------|------|
| Anthropic API | ~$1–3 for full eval runs | Sonnet for gen, a different model for judge. |
| OpenAI API | Similar | Familiar from Azure OpenAI work. |
| TAMU Chat API (`chat-api.tamu.ai/openai`) | Free for Aggies | OpenAI-compatible endpoint. Check ToS allows a public demo. |

The judge should be a **different model** from the generator to reduce self-preference bias. Report judge agreement with your human labels on the 30-question subset.

### Decide by M3: demo stack

| Option | Pros | Cons |
|--------|------|------|
| **A. FastAPI on Fly.io/Railway + page on farishittiny.com** | One Python codebase. Demo calls the same code the eval measures. | Small monthly cost or free-tier cold starts. |
| B. Cloudflare Workers + Vectorize + Workers AI | Stays on your existing Cloudflare account. No server. | TypeScript rewrite of retrieval; two codebases; demo may not match eval numbers. |
| C. Gradio/Streamlit on Hugging Face Spaces, iframed | Fastest to ship. | Looks like a class project. |

Leaning A. Decide after M2 when you know the eval cost per query.

---

## Repo layout

```
catalog-rag/
  PLAN.md                   this file
  README.md                 stays short until M3; then holds the eval table
  pyproject.toml
  .env.example
  data/
    raw/                    scraped HTML (gitignored)
    processed/              courses.jsonl, chunks.jsonl, embeddings (gitignored)
    gold/
      gold_set.jsonl        the eval set. Committed. Hand-written.
      README.md             how to write a gold question
  src/catalog_rag/
    scrape.py               catalog.tamu.edu → courses.jsonl
    chunk.py                courses.jsonl → chunks.jsonl
    prereq_graph.py         parse prereq strings → networkx DiGraph
    retrievers/
      base.py               Retriever protocol
      bm25.py
      dense.py
      hybrid.py             RRF + rerank
    generate.py             prompt, citations, abstention
    eval/
      metrics.py            recall@k, MRR, per-type breakdown. Pure functions. Tested.
      judge.py              LLM-as-judge with rubric
      run.py                one command → reports/<timestamp>.json + Markdown table
  scripts/
    scrape.sh               convenience wrappers
  tests/
    test_metrics.py
  reports/                  eval outputs (JSON gitignored, .md committed)
  .github/workflows/eval.yml
```

---

## Data schemas

### `data/processed/courses.jsonl` (one per course)

```json
{
  "course_id": "ECEN 350",
  "dept": "ECEN",
  "number": "350",
  "title": "Computer Architecture and Design",
  "credits": "4",
  "description": "...",
  "prereq_raw": "Grade of C or better in ECEN 248 and ECEN 350 ...",
  "prereqs": [["ECEN 248"], ["CSCE 312", "ECEN 250"]],
  "coreqs": [],
  "crosslisted": ["CSCE 350"],
  "catalog_year": "2026-2027",
  "source_url": "https://catalog.tamu.edu/undergraduate/course-descriptions/ecen/"
}
```

`prereqs` is a list of AND-groups; each inner list is an OR-group. `[["A"], ["B", "C"]]` means A and (B or C).

### `data/gold/gold_set.jsonl` (one per question)

```json
{
  "id": "g001",
  "question": "What is the prerequisite for ECEN 350?",
  "dept": "ECEN",
  "type": "factual",
  "gold_course_ids": ["ECEN 350"],
  "gold_answer": "ECEN 248 and either CSCE 312 or ECEN 250, with a grade of C or better.",
  "answerable": true,
  "notes": "Straight lookup."
}
```

Question types (aim for roughly this mix in 100):

| type | count | what it tests |
|------|-------|---------------|
| `factual` | 40 | Single-course lookup: prereqs, credits, description, cross-listing. |
| `prereq` | 25 | "What can I take after X", "what do I need before Y". Needs the graph. |
| `multi_hop` | 20 | Compares or combines two or more courses. "Which of ECEN 449 or ECEN 454 requires ECEN 350?" |
| `not_in_catalog` | 15 | Should abstain. "Who teaches ECEN 350 this fall?" "What's the average grade?" |

`gold_course_ids` = the course records a correct answer must draw from. Retrieval metrics are computed against these.

---

## Metrics

### Retrieval (deterministic, no LLM)

- **recall@k** for k in {1, 5, 10}: fraction of `gold_course_ids` appearing in the top-k retrieved courses. Averaged over questions.
- **MRR**: reciprocal rank of the first gold course.
- **Per-type breakdown**: the prereq and multi_hop rows are where BM25 and dense will diverge. That's the story.

### Answer (LLM judge + human subset)

- **Correctness** (0/1): judge compares generated answer to `gold_answer` with a rubric. Rubric is in `judge.py` and committed.
- **Citation precision**: fraction of cited course codes that are in `gold_course_ids`.
- **Abstention accuracy**: on `not_in_catalog` questions, did it refuse. On answerable questions, did it not refuse.
- **Judge agreement**: on 30 questions you label by hand, percent agreement with the judge. Report this number next to every correctness number. Without it, correctness is unverified.

### What the final table looks like

```
| retriever        | corpus | recall@5 | MRR  | correctness | judge agr. | abstain acc |
|------------------|--------|----------|------|-------------|------------|-------------|
| bm25             | 412    | 0.xx     | 0.xx | 0.xx        | 0.xx       | 0.xx        |
| dense            | 412    | 0.xx     | 0.xx | 0.xx        | 0.xx       | 0.xx        |
| hybrid+rerank    | 412    | 0.xx     | 0.xx | 0.xx        | 0.xx       | 0.xx        |
| hybrid+graph     | 412    | 0.xx     | 0.xx | 0.xx        | 0.xx       | 0.xx        |
```

That table is the project.

---

## Expanding later

Built in from day one so it costs nothing:

- `scrape.py` takes `--depts ECEN CSCE`. Expanding = longer list.
- Every gold question is tagged `dept`. Eval reports per-dept and overall.
- Every chunk carries `course_id`, `dept`, `catalog_year` metadata. Adding docs = re-run chunk + embed, no schema change.

The one real consequence: recall drops when the corpus grows (more distractors). So every reported number states corpus size, and a résumé bullet says "over N courses."

---

## Résumé bullet target (fill in at M3)

> Built an eval-driven RAG system over N Texas A&M catalog courses with a 100-question human-labeled gold set; hybrid retrieval + prereq graph raised recall@5 from X to Y over BM25 and answer correctness to Z (judge agreement W%), with the eval running in CI on every PR.

Don't write it until X, Y, Z, W exist.

---

## Open questions (your call)

1. LLM provider (see Stack). TAMU Chat API is free but check whether a public demo is allowed.
2. Demo stack A/B/C. Not blocking until M3.
3. Whether to include the CE degree plan page as a document, or only use it to seed gold questions. Recommend: both.
4. Repo name. `catalog-rag`, `aggie-catalog-rag`, or something less literal.
