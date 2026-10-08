"""Retrieval matrix tests (FR-020…FR-024, US7).

Every question × strategy × query mode is scored; metric formulas are
REUSED from evaluation/metrics.py (Principle XVI — no reimplementation);
chunk-level labels take precedence when present, document-level labels
are the fallback; unanswerable questions are excluded from answerable
aggregates and reported as TN/FP; latency aggregation reports only
measured stages (never fabricated zeros).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Chunk, EvaluationQuestion, RetrievalResult
from evaluation import metrics as M

try:
    from evaluation.retrieval_matrix import (
        DEFAULT_KS,
        MatrixReport,
        aggregate_latency,
        run_matrix,
        score_results,
    )
except ImportError:  # TDD: module does not exist yet
    MatrixReport = aggregate_latency = run_matrix = score_results = None
    DEFAULT_KS = (1, 3, 5, 10)

STRATEGIES = ("vector", "bm25", "hybrid", "hybrid_reranked")


def _r(chunk_id: str, rank: int, score: float = 1.0) -> RetrievalResult:
    doc_id = chunk_id.split("#")[0]
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=chunk_id,
            content=f"content of {chunk_id}",
            document_id=doc_id,
            document_name=f"{doc_id}.md",
            source=f"data/documents/{doc_id}.md",
            chunk_index=int(chunk_id.split("#")[1]),
        ),
        score=score,
        rank=rank,
    )


def _q(qid, question="q?", docs=(), chunks=(), category="semantic"):
    return EvaluationQuestion(
        id=qid,
        question=question,
        relevant_documents=list(docs),
        relevant_chunks=list(chunks),
        category=category,
    )


class FakeController:
    """Stands in for RetrievalController: canned results + fixed latency."""

    def __init__(self, results_by_question: dict, latency_ms: dict, rewritten_query=None):
        self.results_by_question = results_by_question
        self.latency_ms = latency_ms
        self.rewritten_query = rewritten_query
        self.calls: list[tuple[str, dict | None, int | None]] = []

    def retrieve(self, question, *, strategy=None, filters=None, top_k=None):
        from retrieval.controller import RetrievalDebug

        self.calls.append((question, filters, top_k))
        return RetrievalDebug(
            query=question,
            rewritten_query=self.rewritten_query,
            strategy=strategy or "vector",
            filters=dict(filters or {}),
            results=self.results_by_question.get(question, []),
            latency_ms=dict(self.latency_ms),
        )


def _controllers_for(results_by_question, latency_by_strategy):
    """mode -> strategy -> FakeController (original mode never rewrote)."""
    return {
        "original": {
            s: FakeController(results_by_question, latency_by_strategy[s]) for s in STRATEGIES
        },
        "rewritten": {
            s: FakeController(
                results_by_question, latency_by_strategy[s], rewritten_query="rewritten q"
            )
            for s in STRATEGIES
        },
    }


def _latencies():
    return {
        "vector": {"embed": 10.0, "vector": 5.0, "filter": 0.1, "total": 15.1},
        "bm25": {"bm25": 1.0, "filter": 0.1, "total": 1.1},
        "hybrid": {
            "embed": 10.0,
            "vector": 5.0,
            "bm25": 1.0,
            "filter": 0.1,
            "fuse": 0.2,
            "total": 16.3,
        },
        "hybrid_reranked": {
            "embed": 10.0,
            "vector": 5.0,
            "bm25": 1.0,
            "filter": 0.1,
            "fuse": 0.2,
            "rerank": 40.0,
            "total": 56.3,
        },
    }


QUESTIONS = [
    _q("q1", "what is latency?", docs=["d1"], chunks=[], category="semantic"),
    _q("q2", "which code?", docs=["d2"], chunks=["d2#0002"], category="error_code"),
    _q("q3", "who knows?", docs=[], chunks=[], category="unanswerable"),
]

RESULTS = {
    "what is latency?": [_r("d1#0001", 1, 0.9), _r("d3#0001", 2, 0.5), _r("d4#0001", 3, 0.4)],
    "which code?": [_r("d5#0001", 1, 0.9), _r("d2#0002", 2, 0.8), _r("d2#0001", 3, 0.7)],
    "who knows?": [_r("d6#0001", 1, 0.9)],
}


# -- coverage (SC-001) -------------------------------------------------------


def test_every_question_scored_under_all_four_strategies_both_modes():
    report = run_matrix(QUESTIONS, _controllers_for(RESULTS, _latencies()))
    cells = {(e.query_mode, e.strategy, e.question_id) for e in report.entries}
    expected = {
        (m, s, q.id) for m in ("original", "rewritten") for s in STRATEGIES for q in QUESTIONS
    }
    assert cells == expected, f"missing cells: {expected - cells}"
    assert len(report.entries) == len(expected)
    print(f"✓ {len(report.entries)} cells = {len(QUESTIONS)}q × 4 strategies × 2 modes")


def test_aggregate_reports_ks_and_mrr_for_every_cell():
    report = run_matrix(QUESTIONS, _controllers_for(RESULTS, _latencies()))
    for s in STRATEGIES:
        for m in ("original", "rewritten"):
            agg = report.aggregate(strategy=s, query_mode=m)
            assert set(agg["recall_at_k"]) == set(DEFAULT_KS) == {1, 3, 5, 10}
            assert set(agg["precision_at_k"]) == {1, 3, 5, 10}
            assert isinstance(agg["mrr"], float)
            assert agg["n_answerable"] == 2  # q3 unanswerable excluded
    print("✓ every cell reports Recall@1/3/5/10, Precision@1/3/5/10, MRR")


# -- metric reuse (Principle XVI) --------------------------------------------


def test_doc_level_scores_match_evaluation_metrics_module():
    q = QUESTIONS[0]
    results = RESULTS["what is latency?"]
    for k in DEFAULT_KS:
        assert M.recall_at_k(results, q, k) <= 1.0
    report = run_matrix(
        [q], {"original": {"vector": FakeController(RESULTS, _latencies()["vector"])}}
    )
    entry = report.entries[0]
    for k in DEFAULT_KS:
        assert entry.recall[k] == pytest.approx(M.recall_at_k(results, q, k))
        assert entry.precision[k] == pytest.approx(M.precision_at_k(results, q, k))
    assert entry.mrr == pytest.approx(M.reciprocal_rank(results, q))
    print("✓ doc-level scores identical to evaluation/metrics.py values")


def test_score_results_chunk_labels_take_precedence():
    q = QUESTIONS[1]  # relevant_chunks = ["d2#0002"]
    results = RESULTS["which code?"]  # d2#0002 at rank 2
    scores = score_results(results, q, ks=(1, 2, 3))
    assert scores["recall"][1] == 0.0  # chunk not in top-1
    assert scores["recall"][2] == 1.0  # chunk at rank 2
    assert scores["recall"][3] == 1.0
    assert scores["precision"][1] == 0.0
    assert scores["precision"][2] == 0.5
    assert scores["mrr"] == pytest.approx(0.5)
    print("✓ relevant_chunks scored at chunk granularity")


def test_missing_labels_fall_back_to_document_level():
    q_no_chunks = QUESTIONS[0]
    results = RESULTS["what is latency?"]
    scores = score_results(results, q_no_chunks, ks=DEFAULT_KS)
    for k in DEFAULT_KS:
        assert scores["recall"][k] == pytest.approx(M.recall_at_k(results, q_no_chunks, k))
    # a relevant_chunks label that retrieval never returns -> clean zeros
    q_ghost = _q("qg", docs=["d1"], chunks=["d1#0099"])
    scores_ghost = score_results(results, q_ghost, ks=DEFAULT_KS)
    assert all(scores_ghost["recall"][k] == 0.0 for k in DEFAULT_KS)
    assert scores_ghost["mrr"] == 0.0
    print("✓ empty labels -> document metrics; unretrieved chunk -> 0, no crash")


# -- unanswerable handling (FR-009a) -----------------------------------------


def test_unanswerable_excluded_from_aggregates_but_counted():
    report = run_matrix(
        QUESTIONS, {"original": {"vector": FakeController(RESULTS, _latencies()["vector"])}}
    )
    agg = report.aggregate(strategy="vector", query_mode="original")
    assert agg["n_answerable"] == 2
    assert agg["false_positives"] == 1  # q3 retrieved results
    assert agg["true_negatives"] == 0
    # aggregate recall equals mean over answerable questions only
    q1_entry = report.entry("q1", "vector", "original")
    q2_entry = report.entry("q2", "vector", "original")
    assert agg["recall_at_k"][5] == pytest.approx((q1_entry.recall[5] + q2_entry.recall[5]) / 2)
    print("✓ unanswerable never averaged into Recall; FP/TN counted")


# -- latency aggregation (SC-007, FR-023) ------------------------------------


def test_latency_aggregation_reports_only_measured_stages():
    report = run_matrix(QUESTIONS, _controllers_for(RESULTS, _latencies()))
    stages = aggregate_latency(report.entries)
    # per-strategy runs are recorded distinctly: a bm25 run has no embed/fuse
    assert "total" in stages
    assert set(stages) <= {
        "rewrite",
        "embed",
        "vector",
        "bm25",
        "filter",
        "fuse",
        "rerank",
        "total",
    }
    assert "rewrite" not in stages  # no entry measured a rewrite -> absent, never 0
    assert all("p50" in v and "p95" in v and v["n"] >= 1 for v in stages.values())
    # entries exist whose latency lacks 'rerank' -> rerank stage still present
    # because hybrid_reranked entries measured it
    assert "rerank" in stages
    print("✓ latency aggregate = measured stages only (no fabricated zeros)")


def test_latency_aggregation_omits_stages_no_entry_measured():
    report = run_matrix(
        [QUESTIONS[0]],
        {"original": {"bm25": FakeController(RESULTS, {"bm25": 1.0, "total": 1.1})}},
    )
    stages = aggregate_latency(report.entries)
    assert set(stages) == {"bm25", "total"}  # embed/fuse/rerank/rewrite absent
    print("✓ stages nobody measured are absent from the aggregate")


def test_query_mode_axis_kept_separate():
    report = run_matrix(QUESTIONS, _controllers_for(RESULTS, _latencies()))
    orig = report.entry("q1", "vector", "original")
    rew = report.entry("q1", "vector", "rewritten")
    assert orig.query_mode == "original" and rew.query_mode == "rewritten"
    assert rew.rewrite_applied is True
    assert orig.rewrite_applied is False
    print("✓ original vs rewritten measured as separate cells (SC-006)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
