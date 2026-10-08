"""Retrieval matrix: question × strategy × query mode (FR-020…FR-024).

Pure Python over the existing evaluation layer (research R8, Principle
XVI): metric formulas for document-level labels are REUSED from
evaluation/metrics.py — never reimplemented. Chunk-level labels
(`relevant_chunks`) are scored at chunk granularity; when they are empty,
document labels are the ground truth. Unanswerable questions are excluded
from answerable aggregates and reported as true negatives / false
positives.

Latency aggregation reports, per stage, p50/p95 over the entries that
MEASURED that stage — stages nobody measured are absent, never 0
(constitution "never fabricate").
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from domain import EvaluationQuestion, RetrievalResult
from evaluation import metrics as _metrics

DEFAULT_KS: tuple[int, ...] = (1, 3, 5, 10)
QUERY_MODES: tuple[str, ...] = ("original", "rewritten")
LATENCY_STAGES: tuple[str, ...] = (
    "rewrite",
    "embed",
    "vector",
    "bm25",
    "filter",
    "fuse",
    "rerank",
    "total",
)


class DebugLike(Protocol):
    """Structural type of RetrievalDebug (retrieval/controller.py)."""

    results: list[RetrievalResult]
    latency_ms: dict[str, float]
    rewritten_query: str | None


class SupportsRetrieve(Protocol):
    """Anything the matrix may call as a controller cell."""

    def retrieve(
        self,
        question: str,
        *,
        strategy: str | None = None,
        filters: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> DebugLike: ...


def score_results(
    results: Sequence[RetrievalResult],
    question: EvaluationQuestion,
    ks: Sequence[int] = DEFAULT_KS,
) -> dict:
    """Recall@K / Precision@K / MRR for one result list.

    Delegates to evaluation/metrics.py for document-level questions;
    scores at chunk granularity when `relevant_chunks` is non-empty.
    Unanswerable questions score 0.0 (never averaged silently upstream).
    """
    if question.is_unanswerable:
        return {
            "recall": {k: 0.0 for k in ks},
            "precision": {k: 0.0 for k in ks},
            "mrr": 0.0,
        }

    if not question.relevant_chunks:
        return {
            "recall": {k: _metrics.recall_at_k(results, question, k) for k in ks},
            "precision": {k: _metrics.precision_at_k(results, question, k) for k in ks},
            "mrr": _metrics.reciprocal_rank(results, question),
        }

    expected = set(question.relevant_chunks)
    ranked = sorted(results, key=lambda r: r.rank)

    def _hits_at(k: int) -> set[str]:
        return {r.chunk.chunk_id for r in ranked if r.rank <= k and r.chunk.chunk_id in expected}

    first_rank = next((r.rank for r in ranked if r.chunk.chunk_id in expected), None)
    return {
        "recall": {k: len(_hits_at(k)) / len(expected) for k in ks},
        "precision": {k: len(_hits_at(k)) / k for k in ks},
        "mrr": (1.0 / first_rank) if first_rank else 0.0,
    }


@dataclass
class MatrixEntry:
    """One scored cell: a question under one strategy and one query mode."""

    question_id: str
    strategy: str
    query_mode: str
    recall: dict[int, float]
    precision: dict[int, float]
    mrr: float
    latency_ms: dict[str, float]
    rewrite_applied: bool
    is_unanswerable: bool
    num_results: int
    filters: dict = field(default_factory=dict)


@dataclass
class MatrixReport:
    """All scored cells plus aggregate views (SC-001, SC-006)."""

    entries: list[MatrixEntry]

    def __post_init__(self) -> None:
        self._index = {(e.question_id, e.strategy, e.query_mode): e for e in self.entries}

    def entry(self, question_id: str, strategy: str, query_mode: str) -> MatrixEntry:
        return self._index[(question_id, strategy, query_mode)]

    def cell(self, strategy: str, query_mode: str) -> list[MatrixEntry]:
        return [e for e in self.entries if e.strategy == strategy and e.query_mode == query_mode]

    @property
    def strategies(self) -> list[str]:
        seen: dict[str, None] = {}
        for e in self.entries:
            seen.setdefault(e.strategy)
        return list(seen)

    @property
    def modes(self) -> list[str]:
        seen: dict[str, None] = {}
        for e in self.entries:
            seen.setdefault(e.query_mode)
        return list(seen)

    def aggregate(self, strategy: str, query_mode: str) -> dict:
        """Mean metrics over the ANSWERABLE questions of one cell (FR-021)."""
        entries = self.cell(strategy, query_mode)
        answerable = [e for e in entries if not e.is_unanswerable]
        unanswerable = [e for e in entries if e.is_unanswerable]
        ks = sorted({k for e in entries for k in e.recall}) or list(DEFAULT_KS)
        if answerable:
            recall = {k: sum(e.recall[k] for e in answerable) / len(answerable) for k in ks}
            precision = {k: sum(e.precision[k] for e in answerable) / len(answerable) for k in ks}
            mrr = sum(e.mrr for e in answerable) / len(answerable)
        else:
            recall = {k: 0.0 for k in ks}
            precision = {k: 0.0 for k in ks}
            mrr = 0.0
        return {
            "recall_at_k": recall,
            "precision_at_k": precision,
            "mrr": float(mrr),
            "n_answerable": len(answerable),
            "true_negatives": sum(1 for e in unanswerable if e.num_results == 0),
            "false_positives": sum(1 for e in unanswerable if e.num_results > 0),
        }

    def category_aggregate(
        self, strategy: str, query_mode: str, categories: Mapping[str, str]
    ) -> dict[str, dict]:
        """Per-category aggregates for the SC-010 winner table.

        `categories` maps question_id -> category name.
        """
        result: dict[str, dict] = {}
        for cat in sorted(set(categories.values())):
            ids = {qid for qid, c in categories.items() if c == cat}
            subset = [
                e
                for e in self.entries
                if e.question_id in ids and e.strategy == strategy and e.query_mode == query_mode
            ]
            if not subset:
                continue
            answerable = [e for e in subset if not e.is_unanswerable]
            ks = sorted({k for e in subset for k in e.recall})
            if answerable:
                result[cat] = {
                    "recall_at_k": {
                        k: sum(e.recall[k] for e in answerable) / len(answerable) for k in ks
                    },
                    "precision_at_k": {
                        k: sum(e.precision[k] for e in answerable) / len(answerable) for k in ks
                    },
                    "mrr": sum(e.mrr for e in answerable) / len(answerable),
                    "n": len(subset),
                }
            else:
                result[cat] = {
                    "recall_at_k": {k: 0.0 for k in ks},
                    "precision_at_k": {k: 0.0 for k in ks},
                    "mrr": 0.0,
                    "n": len(subset),
                }
        return result


def aggregate_latency(entries: Sequence[MatrixEntry]) -> dict[str, dict]:
    """p50/p95 per stage over entries that measured the stage (SC-007).

    A stage absent from every entry's latency map is absent here —
    never reported as 0 (constitution: never fabricate measurements).
    """
    buckets: dict[str, list[float]] = {}
    for e in entries:
        for stage, value in e.latency_ms.items():
            buckets.setdefault(stage, []).append(float(value))

    out: dict[str, dict] = {}
    for stage in LATENCY_STAGES:
        values = buckets.get(stage)
        if not values:
            continue
        ordered = sorted(values)
        p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
        out[stage] = {
            "p50": float(statistics.median(ordered)),
            "p95": float(ordered[p95_index]),
            "n": len(ordered),
        }
    # any stage key outside the known order still reported (no data dropped)
    for stage, values in buckets.items():
        if stage not in out:
            ordered = sorted(values)
            p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
            out[stage] = {
                "p50": float(statistics.median(ordered)),
                "p95": float(ordered[p95_index]),
                "n": len(ordered),
            }
    return out


def run_matrix(
    questions: Sequence[EvaluationQuestion],
    controllers: Mapping[str, Mapping[str, SupportsRetrieve]],
    ks: Sequence[int] = DEFAULT_KS,
    *,
    progress=None,
) -> MatrixReport:
    """Score every question under every provided (mode, strategy) cell.

    Args:
        questions: evaluation dataset entries (labels + per-question filters).
        controllers: query_mode -> strategy -> controller. Each controller is
            called as `retrieve(question, filters=..., top_k=...)` and returns
            a RetrievalDebug-like object (results, latency_ms,
            rewritten_query).
        progress: optional callable(mode, strategy) invoked after each cell.

    Returns a MatrixReport covering the full cross product (SC-001).
    """
    top_k = max(ks)
    entries: list[MatrixEntry] = []
    for mode, by_strategy in controllers.items():
        for strategy, controller in by_strategy.items():
            for q in questions:
                debug = controller.retrieve(q.question, filters=dict(q.filters), top_k=top_k)
                scores = score_results(debug.results, q, ks=ks)
                entries.append(
                    MatrixEntry(
                        question_id=q.id,
                        strategy=strategy,
                        query_mode=mode,
                        recall=scores["recall"],
                        precision=scores["precision"],
                        mrr=scores["mrr"],
                        latency_ms=dict(debug.latency_ms),
                        rewrite_applied=debug.rewritten_query is not None,
                        is_unanswerable=q.is_unanswerable,
                        num_results=len(debug.results),
                        filters=dict(q.filters),
                    )
                )
            if progress is not None:
                progress(mode, strategy)
    return MatrixReport(entries=entries)
