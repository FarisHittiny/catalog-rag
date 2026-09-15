"""One command: index, run every retriever over the gold set, write the table.

    python -m catalog_rag.eval.run --retrievers bm25                       # retrieval only, no API key
    python -m catalog_rag.eval.run --retrievers routed --generate           # + generation and LLM judge

Writes reports/<timestamp>.json and prints Markdown. Retrieval-only is the default so CI
never needs a key. `--generate` needs LLM_BASE_URL, an API key, LLM_MODEL and JUDGE_MODEL
in .env (see llm.py); every call is disk-cached, so re-runs cost zero tokens.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import typer
from rich import print

from ..generate import GEN_PARAMS, generate
from ..models import Chunk, GoldQuestion
from ..prereq_graph import load_courses
from ..retrievers import (
    BM25CodesIdRetriever,
    BM25CodesRetriever,
    BM25Retriever,
    DenseRetriever,
    GraphRetriever,
    HybridRetriever,
    RoutedRetriever,
)
from ..retrievers.tokenize import CODE_RE
from ..router import route
from .human_subset import load_human_labels, write_human_subset
from .judge import JUDGE_PARAMS, judge
from .metrics import aggregate, judge_agreement, nan_to_none, to_markdown

REGISTRY = {  # name -> zero-arg factory
    "bm25": BM25Retriever,
    "bm25_codes": BM25CodesRetriever,
    "bm25_codes_id": BM25CodesIdRetriever,
    "dense": DenseRetriever,
    "hybrid": lambda: HybridRetriever([BM25CodesRetriever(), DenseRetriever()]),
    "graph": GraphRetriever,
    "routed": lambda: RoutedRetriever(GraphRetriever(), BM25CodesIdRetriever()),
}  # M2: "hybrid+rerank"

HUMAN_SUBSET_RETRIEVER = "routed"  # the human labels are written against this retriever's answers


def router_accuracy(gold: list[GoldQuestion]) -> tuple[float, list[str]]:
    """Fraction of gold questions where route(question) agrees with (type == "prereq")."""
    bad = [q.id for q in gold if route(q.question) != ("prereq" if q.type == "prereq" else "other")]
    return (1 - len(bad) / len(gold)) if gold else float("nan"), bad


def load_jsonl(path: Path, model):
    return [model.model_validate_json(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def validate_gold(gold: list[GoldQuestion], corpus_ids: set[str]) -> None:
    """Fail loudly on placeholders and unverified rows; warn on gold ids the corpus doesn't contain.

    A placeholder silently scores as a miss and drags recall down, which is worse than a crash.
    """
    problems = []
    for q in gold:
        if any("FILL" in cid for cid in q.gold_course_ids) or "FILL" in q.gold_answer:
            problems.append(f"{q.id}: placeholder still present")
        if q.answerable and not q.gold_course_ids:
            problems.append(f"{q.id}: answerable but no gold_course_ids")
        if not q.verified:
            problems.append(f"{q.id}: not verified")
        if q.has_code != bool(CODE_RE.search(q.question)):
            problems.append(f"{q.id}: has_code={q.has_code} disagrees with question text")
        if not q.answerable and q.gold_course_ids:
            problems.append(f"{q.id}: not answerable but has gold_course_ids")
    if problems:
        raise SystemExit("gold set invalid:\n  " + "\n  ".join(problems))
    missing = sorted({cid for q in gold for cid in q.gold_course_ids if cid not in corpus_ids})
    if missing:
        print(f"[yellow]warning:[/] {len(missing)} gold course ids not in corpus (recall capped): {missing[:10]}")


def agreement_label(rows: list[dict], human: list[dict]) -> str:
    """Judge agreement for one retriever. A human label counts only while the answer it was
    written against is still this retriever's answer, so stale labels read as unlabeled."""
    if not human:
        return "unlabeled"
    by_id = {r["id"]: r for r in rows}
    live = [h for h in human if h["id"] in by_id and by_id[h["id"]]["answer"] == h["generated_answer"]]
    labeled = [h for h in human if h.get("human_correct") is not None]
    agr = judge_agreement({r["id"]: r["correct"] for r in rows}, human) if len(live) == len(human) else None
    if agr is None:
        return f"unlabeled ({len(labeled)}/{len(human)} labeled, {len(live)}/{len(human)} answers current)"
    return f"{agr:.3f} ({len(human)}/{len(human)})"


def main(
    retrievers: list[str] = typer.Option(["bm25"]),
    chunks_path: Path = Path("data/processed/chunks.jsonl"),
    gold_path: Path = Path("data/gold/gold_set.jsonl"),
    k: int = 10,
    reports: Path = Path("reports"),
    note: str = typer.Option("", help="one-line provenance note written above the table"),
    generate_: bool = typer.Option(False, "--generate", help="run generation + LLM judge (needs .env)"),
    gen_retrievers: list[str] = typer.Option([], "--gen-retriever", help="with --generate, only these retrievers generate (default: all)"),
    fresh: bool = typer.Option(False, "--fresh", help="bypass LLM cache reads (still writes) to measure drift"),
    gen_k: int = typer.Option(5, help="course records handed to the generator"),
    courses_path: Path = Path("data/processed/courses.jsonl"),
    human_labels: Path = Path("data/gold/human_labels.jsonl"),
):
    chunks = load_jsonl(chunks_path, Chunk)
    gold = load_jsonl(gold_path, GoldQuestion)
    corpus_ids = {c.course_id for c in chunks}
    corpus_size = len(corpus_ids)
    validate_gold(gold, corpus_ids)
    acc, misrouted = router_accuracy(gold)
    router_line = (f"router accuracy: {acc:.3f} ({len(gold) - len(misrouted)}/{len(gold)})"
                   + (f"; misrouted: {', '.join(misrouted)}" if misrouted else ""))
    para = [q for q in gold if q.paraphrase]  # out-of-sample phrasings, reported on their own
    para_acc, para_bad = router_accuracy(para) if para else (float("nan"), [])
    if para:
        router_line += f"; paraphrase: {para_acc:.3f} ({len(para) - len(para_bad)}/{len(para)})"

    client = gen_model = judge_model = courses = None
    if generate_:
        from ..llm import LLMClient

        client = LLMClient.from_env(read_cache=not fresh)
        gen_model, judge_model = os.environ.get("LLM_MODEL", ""), os.environ.get("JUDGE_MODEL", "")
        if not gen_model or not judge_model:
            raise SystemExit("generation needs LLM_MODEL and JUDGE_MODEL in .env")
        if gen_model == judge_model:
            print(f"[yellow]warning:[/] LLM_MODEL == JUDGE_MODEL ({gen_model}); the judge should differ")
        courses = {c.course_id: c for c in load_courses(courses_path)}

    results, generations, agreement = {}, {}, {}
    for name in retrievers:
        r = REGISTRY[name]()
        r.index(chunks)
        do_gen = generate_ and (not gen_retrievers or name in gen_retrievers)
        rows = []
        for q in gold:
            ranked = [x.course_id for x in r.retrieve(q.question, k=k)]
            row = {"id": q.id, "type": q.type, "has_code": q.has_code, "paraphrase": q.paraphrase,
                   "ranked": ranked, "gold": q.gold_course_ids}
            if do_gen:
                ids = r.context(q.question, gen_k) if hasattr(r, "context") else ranked[:gen_k]
                top = [courses[cid] for cid in ids if cid in courses]
                g = generate(q.question, top, client, gen_model)
                v = judge(q.question, q.gold_answer, g.answer, client, judge_model)
                row.update({"answerable": q.answerable, "question": q.question, "gold_answer": q.gold_answer,
                            "answer": g.answer, "cited": g.cited_course_ids, "abstained": g.abstained,
                            "correct": v.correct, "reason": v.reason})
            rows.append(row)
        results[r.name] = aggregate(rows)
        misses = [row["id"] for row in rows if row["gold"] and not set(row["gold"]) & set(row["ranked"][:5])]
        if misses:
            print(f"[dim]{r.name} recall@5 misses:[/] {', '.join(misses)}")
        if do_gen:
            generations[r.name] = rows
            wrong = [row["id"] for row in rows if not row["correct"]]
            print(f"[dim]{r.name} judged incorrect ({len(wrong)}):[/] {', '.join(wrong)}")
            if r.name == HUMAN_SUBSET_RETRIEVER and not Path(human_labels).exists():
                n = write_human_subset(rows, human_labels)
                print(f"wrote {n} rows to {human_labels} for hand labeling (human_correct: null)")
    if generate_:
        human = load_human_labels(human_labels)  # after the loop: same labels for every retriever
        agreement = {name: agreement_label(rows, human) for name, rows in generations.items()}

    md = to_markdown(results, corpus_size, agreement or None)
    head = [f"> {router_line}"]
    if generate_:
        head.append(f"> generator: {gen_model} {GEN_PARAMS}; judge: {judge_model} {JUDGE_PARAMS}; "
                    f"top-{gen_k} records per question" + ("; --fresh (cache reads bypassed)" if fresh else ""))
        head.append("> judge agreement (" + ", ".join(f"{n}: {a}" for n, a in agreement.items()) + ")")
    md = "\n\n".join(head) + "\n\n" + md
    if note:
        md = f"> {note}\n\n" + md
    if client is not None:
        md += "\n\n```\n" + client.usage_report() + "\n```"
    print(md)
    reports.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    payload = {"note": note, "router": {"accuracy": acc, "misrouted": misrouted,
                                        "paraphrase": {"accuracy": para_acc, "misrouted": para_bad}},
               "results": results,
               "generation": {"generator": gen_model, "judge": judge_model, "gen_k": gen_k, "fresh": fresh,
                              "gen_params": GEN_PARAMS, "judge_params": JUDGE_PARAMS,
                              "agreement": agreement, "rows": generations} if generate_ else None}
    (reports / f"{stamp}.json").write_text(
        json.dumps(nan_to_none(payload), indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    (reports / "latest.md").write_text(md + "\n", encoding="utf-8")


if __name__ == "__main__":
    typer.run(main)
