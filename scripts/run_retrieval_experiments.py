"""Level 3 retrieval experiments: strategy matrix + ablation study (FR-021…FR-024).

Runs every evaluation question under all four strategies (original query
mode; + rewritten mode with --rewrite) via the real RetrievalController,
scores with evaluation/metrics.py (reused), and writes measured Markdown
tables into docs/levels/level-03-advanced-retrieval/experiments.md.

Ablation configurations (FR-022):
    A  vector only                      (semantic only)
    B  bm25 only                        (lexical only)
    C  vector + bm25, no fusion         (semantic + lexical, unfused concat)
    D  vector + bm25 + RRF fusion       (hybrid)
    E  hybrid + reranker                (hybrid_reranked, rerank ON)
    F  hybrid + query rewriting         (requires --rewrite)
    G  hybrid + rewriting + reranker    (requires --rewrite)

Unmeasured cells are written as TBD — never estimated (FR-024).
Rewritten-mode cells and F/G require --rewrite (LLM gateway); without it
they stay TBD.

Usage:
    LLM_MODEL=... uv run python scripts/run_retrieval_experiments.py [--rewrite]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import settings  # noqa: E402
from domain import EvaluationQuestion  # noqa: E402
from evaluation.dataset import load_questions  # noqa: E402
from evaluation.retrieval_matrix import (  # noqa: E402
    MatrixEntry,
    MatrixReport,
    aggregate_latency,
    run_matrix,
    score_results,
)

STRATEGY_ORDER = ("vector", "bm25", "hybrid", "hybrid_reranked")
LABELS = {
    "vector": "Vector",
    "bm25": "BM25",
    "hybrid": "Hybrid (RRF)",
    "hybrid_reranked": "Hybrid + Reranker",
}
ABLATION_ROWS = [
    ("A", "Vector only"),
    ("B", "BM25 only"),
    ("C", "Vector + BM25 (round-robin, no fusion)"),
    ("D", "Vector + BM25 + RRF"),
    ("E", "Hybrid + Reranker"),
    ("F", "Hybrid + Query Rewriting"),
    ("G", "Hybrid + Query Rewriting + Reranker"),
]
CATEGORY_ORDER = (
    "semantic",
    "exact_terminology",
    "error_code",
    "acronym",
    "multi_concept",
    "ambiguous",
    "metadata_filtered",
    "unanswerable",
)
CATEGORY_LABELS = {
    "semantic": "semantic",
    "exact_terminology": "exact terminology",
    "error_code": "error code",
    "acronym": "acronym",
    "multi_concept": "multi-concept",
    "ambiguous": "ambiguous",
    "metadata_filtered": "metadata-filtered",
    "unanswerable": "unanswerable",
}
EXPERIMENTS_PATH = Path("docs/levels/level-03-advanced-retrieval/experiments.md")


def fmt(value) -> str:
    return "TBD" if value is None else f"{value:.4f}"


def _p50(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def cell_total_p50(report: MatrixReport, strategy: str, mode: str) -> float | None:
    totals = [e.latency_ms["total"] for e in report.cell(strategy, mode) if "total" in e.latency_ms]
    return _p50(totals)


# -- controller wiring -------------------------------------------------------


def build_controllers(rewrite: bool) -> dict[str, dict[str, object]]:
    from retrieval.controller import build_controller

    original = {}
    for s in STRATEGY_ORDER:
        original[s] = build_controller(
            strategy=s,
            reranking_enabled=(s == "hybrid_reranked"),
            rewriting_enabled=False,
        )
    controllers: dict[str, dict[str, object]] = {"original": original}
    if rewrite:
        controllers["rewritten"] = {
            s: build_controller(
                strategy=s,
                reranking_enabled=(s == "hybrid_reranked"),
                rewriting_enabled=True,
            )
            for s in STRATEGY_ORDER
        }
    return controllers


def run_concat(
    questions: list[EvaluationQuestion],
    vector_controller,
    bm25_controller,
) -> list[MatrixEntry]:
    """Ablation C: semantic + lexical WITHOUT fusion — strict round-robin.

    v0, b0, v1, b1, ... deduped by chunk_id: both systems contribute
    inside every top-k, so C→D isolates rank fusion itself.
    """
    entries: list[MatrixEntry] = []
    for q in questions:
        v = vector_controller.retrieve(q.question, filters=dict(q.filters), top_k=10)
        b = bm25_controller.retrieve(q.question, filters=dict(q.filters), top_k=10)
        combined: list = []
        seen: set[str] = set()
        for i in range(max(len(v.results), len(b.results))):
            for pool in (v.results, b.results):
                if i < len(pool):
                    r = pool[i]
                    if r.chunk.chunk_id not in seen:
                        seen.add(r.chunk.chunk_id)
                        combined.append(r)
        for pos, r in enumerate(combined, start=1):
            r.rank = pos
        scores = score_results(combined, q)
        entries.append(
            MatrixEntry(
                question_id=q.id,
                strategy="concat",
                query_mode="original",
                recall=scores["recall"],
                precision=scores["precision"],
                mrr=scores["mrr"],
                latency_ms={
                    "total": v.latency_ms.get("total", 0.0) + b.latency_ms.get("total", 0.0)
                },
                rewrite_applied=False,
                is_unanswerable=q.is_unanswerable,
                num_results=len(combined),
                filters=dict(q.filters),
            )
        )
    return entries


# -- markdown sections -------------------------------------------------------


def matrix_section(report: MatrixReport) -> str:
    lines = []
    for s in STRATEGY_ORDER:
        agg = report.aggregate(s, "original")
        cells = [fmt(agg["recall_at_k"][k]) for k in sorted(agg["recall_at_k"])]
        cells += [fmt(agg["precision_at_k"][k]) for k in sorted(agg["precision_at_k"])]
        cells.append(fmt(agg["mrr"]))
        lines.append(f"| {LABELS[s]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def rewrite_section(report: MatrixReport) -> str:
    lines = []
    for s in ("hybrid", "hybrid_reranked"):
        for mode in ("original", "rewritten"):
            if mode in report.modes:
                agg = report.aggregate(s, mode)
                r5 = fmt(agg["recall_at_k"].get(5))
                mrr = fmt(agg["mrr"])
                lat = fmt(cell_total_p50(report, s, mode))
            else:
                r5 = mrr = lat = "TBD"
            lines.append(f"| {LABELS[s]} | {mode} | {r5} | {mrr} | {lat} |")
    return "\n".join(lines)


def ablation_section(report: MatrixReport, concat_entries: list[MatrixEntry], rewrite: bool) -> str:
    concat_report = MatrixReport(entries=concat_entries)
    cells_by_key: dict[str, tuple] = {}
    for key, s, mode in (
        ("A", "vector", "original"),
        ("B", "bm25", "original"),
        ("D", "hybrid", "original"),
        ("E", "hybrid_reranked", "original"),
    ):
        agg = report.aggregate(s, mode)
        cells_by_key[key] = (
            fmt(agg["recall_at_k"].get(5)),
            fmt(agg["precision_at_k"].get(5)),
            fmt(agg["mrr"]),
            fmt(cell_total_p50(report, s, mode)),
        )
    c_agg = concat_report.aggregate("concat", "original")
    cells_by_key["C"] = (
        fmt(c_agg["recall_at_k"].get(5)),
        fmt(c_agg["precision_at_k"].get(5)),
        fmt(c_agg["mrr"]),
        fmt(_p50([e.latency_ms["total"] for e in concat_entries if "total" in e.latency_ms])),
    )
    for key, s in (("F", "hybrid"), ("G", "hybrid_reranked")):
        if rewrite and "rewritten" in report.modes:
            agg = report.aggregate(s, "rewritten")
            cells_by_key[key] = (
                fmt(agg["recall_at_k"].get(5)),
                fmt(agg["precision_at_k"].get(5)),
                fmt(agg["mrr"]),
                fmt(cell_total_p50(report, s, "rewritten")),
            )
        else:
            cells_by_key[key] = ("TBD", "TBD", "TBD", "TBD")

    lines = []
    for key, config in ABLATION_ROWS:
        r5, p5, mrr, lat = cells_by_key[key]
        lines.append(f"| {key} | {config} | {r5} | {p5} | {mrr} | {lat} |")
    return "\n".join(lines)


def latency_section(report: MatrixReport) -> str:
    entries = [e for s in STRATEGY_ORDER for e in report.cell(s, "original")]
    stages = aggregate_latency(entries)
    notes = {
        "embed": "bge-small-en-v1.5",
        "rerank": "candidate_k = 20",
        "rewrite": "network call",
        "total": "across strategies; per-config totals in §4",
    }
    row_labels = {
        "embed": "Embedding",
        "vector": "Vector retrieval",
        "bm25": "BM25 retrieval",
        "filter": "Metadata filter",
        "fuse": "Fusion (RRF)",
        "rerank": "Reranking",
        "rewrite": "Query rewriting",
        "total": "**Total**",
    }
    order = ["embed", "vector", "bm25", "filter", "fuse", "rerank", "rewrite", "total"]
    lines = []
    for stage in order:
        if stage not in stages:
            lines.append(f"| {row_labels[stage]} | TBD | TBD | not measured in this run |")
            continue
        v = stages[stage]
        lines.append(
            f"| {row_labels[stage]} | {v['p50']:.1f} | {v['p95']:.1f} | {notes.get(stage, '')} |"
        )
    return "\n".join(lines)


def category_section(report: MatrixReport, questions: list[EvaluationQuestion]) -> str:
    categories = {q.id: q.category for q in questions}
    per_strategy = {s: report.category_aggregate(s, "original", categories) for s in STRATEGY_ORDER}
    lines = []
    for cat in CATEGORY_ORDER:
        scored = [(s, per_strategy[s][cat]) for s in STRATEGY_ORDER if cat in per_strategy[s]]
        if not scored:
            lines.append(f"| {CATEGORY_LABELS[cat]} | TBD | TBD |")
            continue
        n = scored[0][1]["n"]
        if cat == "unanswerable":
            # excluded from Recall by design; report the honest observable:
            agg_fp = {s: report.aggregate(s, "original")["false_positives"] for s in STRATEGY_ORDER}
            fp = ", ".join(f"{s} {agg_fp[s]}" for s in STRATEGY_ORDER)
            lines.append(
                f"| {CATEGORY_LABELS[cat]} | n/a (unanswerable excluded from Recall) "
                f"| false positives: {fp} |"
            )
            continue
        ranked = sorted(
            scored,
            key=lambda t: (
                -t[1]["recall_at_k"].get(5, 0.0),
                -t[1]["mrr"],
                STRATEGY_ORDER.index(t[0]),
            ),
        )
        best_s, best = ranked[0]
        ties = [
            s
            for s, a in scored[1:]
            if a["recall_at_k"].get(5, 0.0) == best["recall_at_k"].get(5, 0.0)
            and a["mrr"] == best["mrr"]
            and s != best_s
        ]
        tie_note = f" (tie with {', '.join(LABELS[t] for t in ties)})" if ties else ""
        evidence = (
            f"Recall@5 = {best['recall_at_k'].get(5, 0.0):.4f} "
            f"(MRR = {best['mrr']:.4f}, n={n}){tie_note}"
        )
        lines.append(f"| {CATEGORY_LABELS[cat]} | {LABELS[best_s]} | {evidence} |")
    return "\n".join(lines)


def corpus_chunk_count() -> int:
    from ingestion.chunker import chunk_document
    from ingestion.loader import discover_documents

    return sum(len(chunk_document(d)) for d in discover_documents())


def run_meta(questions: list[EvaluationQuestion], rewrite: bool, n_chunks: int) -> str:
    modes = "original + rewritten" if rewrite else "original (rewritten: TBD — no gateway run)"
    return (
        f"**Status: MEASURED — {date.today().isoformat()}**\n\n"
        f"Command: `LLM_MODEL=<model> uv run python scripts/run_retrieval_experiments.py"
        f"{' --rewrite' if rewrite else ''}`\n\n"
        f"- Corpus: data/documents (10 documents, {n_chunks} chunks) | "
        f"questions: {len(questions)} across 8 categories\n"
        f"- Query modes measured: {modes}\n"
        f"- Fusion: RRF k={settings.fusion_k} | rerank candidate_k={settings.rerank_candidate_k}, "
        f"final_k={settings.rerank_final_k} | evaluation top_k=10\n"
        f"- Per-question metadata filters applied where the dataset defines them "
        f"(metadata_filtered category)\n"
        f"- TBD = not measured; never replaced with an estimate (FR-024)"
    )


# -- file writer -------------------------------------------------------------


def replace_block(text: str, name: str, body: str) -> str:
    begin, end = f"<!-- BEGIN:{name} -->", f"<!-- END:{name} -->"
    if begin not in text or end not in text:
        raise SystemExit(f"experiments.md is missing markers {begin} / {end} — restore them first")
    i = text.index(begin) + len(begin)
    j = text.index(end)
    return text[:i] + "\n" + body.strip("\n") + "\n" + text[j:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rewrite",
        action="store_true",
        help="also run the rewritten-query mode (hits the LLM gateway)",
    )
    parser.add_argument(
        "--questions", default=settings.eval_dataset_path, help="evaluation dataset path"
    )
    args = parser.parse_args()

    questions = load_questions(args.questions)
    print(f"loaded {len(questions)} questions from {args.questions}")

    controllers = build_controllers(rewrite=args.rewrite)
    print(
        f"running matrix: {len(controllers)} mode(s) × {len(STRATEGY_ORDER)} strategies × {len(questions)} questions"
    )
    report = run_matrix(
        questions,
        controllers,
        progress=lambda m, s: print(f"  scored cell {m}/{s}", flush=True),
    )

    print("running ablation C (vector+bm25 round-robin, no fusion)")
    concat_entries = run_concat(
        questions, controllers["original"]["vector"], controllers["original"]["bm25"]
    )

    n_chunks = corpus_chunk_count()
    text = EXPERIMENTS_PATH.read_text(encoding="utf-8")
    text = replace_block(text, "run-meta", run_meta(questions, args.rewrite, n_chunks))
    text = replace_block(text, "matrix-rows", matrix_section(report))
    text = replace_block(text, "rewrite-rows", rewrite_section(report))
    text = replace_block(
        text, "ablation-rows", ablation_section(report, concat_entries, args.rewrite)
    )
    text = replace_block(text, "latency-rows", latency_section(report))
    text = replace_block(text, "category-rows", category_section(report, questions))
    EXPERIMENTS_PATH.write_text(text, encoding="utf-8")
    print(f"wrote measured tables to {EXPERIMENTS_PATH}")

    for s in STRATEGY_ORDER:
        agg = report.aggregate(s, "original")
        print(f"  {LABELS[s]:20s} Recall@5={agg['recall_at_k'].get(5):.4f} MRR={agg['mrr']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
