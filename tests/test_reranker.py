"""Cross-encoder reranker tests (FR-012…FR-014, US5).

Fake scorer injected — no model download. The reranker re-scores the
bounded candidate pool only; disabled reranking must fall through to
fusion order exactly (SC-005).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Chunk, RetrievalResult

try:
    from retrieval.reranker import CrossEncoderReranker
except ImportError:  # TDD: module does not exist yet
    CrossEncoderReranker = None

try:
    from retrieval.controller import RetrievalController
except ImportError:
    RetrievalController = None


def _r(doc_id: str, rank: int, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=f"{doc_id}#0001",
            content=f"content of {doc_id}",
            document_id=doc_id,
            document_name=f"{doc_id}.md",
            source=f"data/documents/{doc_id}.md",
            chunk_index=1,
        ),
        score=score,
        rank=rank,
    )


def _scorer_factory(record: list | None = None, scores_by_text: dict | None = None):
    def scorer(query: str, texts: list[str]) -> list[float]:
        if record is not None:
            record.append((query, list(texts)))
        if scores_by_text is not None:
            return [float(scores_by_text.get(t, 0.0)) for t in texts]
        return [float(len(t)) for t in texts]

    return scorer


# -- direct reranker behavior ----------------------------------------------


def test_results_ordered_by_reranker_score_descending():
    rr = CrossEncoderReranker(
        model="unused-in-tests",
        scorer=_scorer_factory(scores_by_text={"content of a": 1.0, "content of b": 7.5}),
    )
    out = rr.rerank("q", [_r("a", 1, 0.9), _r("b", 2, 0.8)])
    assert [r.chunk.document_id for r in out] == ["b", "a"]
    print("✓ reranker reorders by cross-encoder score")


def test_reranker_score_recorded_and_headline_score_updated():
    rr = CrossEncoderReranker(
        model="unused",
        scorer=_scorer_factory(scores_by_text={"content of a": 2.5, "content of b": -1.0}),
    )
    out = rr.rerank("q", [_r("a", 1, 0.9), _r("b", 2, 0.8)])
    by_id = {r.chunk.document_id: r for r in out}
    assert by_id["a"].reranker_score == pytest.approx(2.5)
    assert by_id["a"].score == pytest.approx(2.5)  # headline score = reranker score
    assert by_id["b"].reranker_score == pytest.approx(-1.0)
    assert [r.rank for r in out] == [1, 2]  # dense ranks after reorder
    print("✓ reranker_score recorded; score is the cross-encoder output")


def test_empty_candidate_pool_returns_empty_without_scorer_call():
    record: list = []
    rr = CrossEncoderReranker(model="unused", scorer=_scorer_factory(record=record))
    assert rr.rerank("q", []) == []
    assert record == []
    print("✓ empty pool -> empty output, scorer never called")


def test_scorer_receives_query_and_candidate_texts():
    record: list = []
    rr = CrossEncoderReranker(model="unused", scorer=_scorer_factory(record=record))
    rr.rerank("the query", [_r("a", 1, 0.9), _r("b", 2, 0.8)])
    query, texts = record[0]
    assert query == "the query"
    assert texts == ["content of a", "content of b"]
    print("✓ scorer receives (query, candidate contents)")


def test_equal_scores_keep_original_order_stable():
    rr = CrossEncoderReranker(
        model="unused",
        scorer=_scorer_factory(scores_by_text={"content of a": 5.0, "content of b": 5.0}),
    )
    out = rr.rerank("q", [_r("a", 1, 0.9), _r("b", 2, 0.8)])
    assert [r.chunk.document_id for r in out] == ["a", "b"]
    print("✓ equal reranker scores keep input order (stable, SC-004)")


# -- controller-level bounds (FR-012/FR-014, SC-005) ------------------------


class FakeRetriever:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def retrieve(self, query):
        self.calls.append(query)
        return list(self._results)


def _controller(reranker=None, **kwargs):
    kwargs.setdefault("vector_retriever", FakeRetriever([_r("a", 1, 0.9), _r("b", 2, 0.8)]))
    kwargs.setdefault("bm25_retriever", FakeRetriever([_r("b", 1, 5.0), _r("c", 2, 3.0)]))
    return RetrievalController(strategy="hybrid_reranked", reranker=reranker, **kwargs)


def test_candidate_pool_bounds_nothing_outside_pool():
    record: list = []
    rr = CrossEncoderReranker(
        model="unused",
        scorer=_scorer_factory(
            record=record,
            scores_by_text={
                "content of a": 9.0,
                "content of b": 8.0,
                "content of c": 7.0,
            },
        ),
    )
    c = _controller(reranker=rr, rerank_candidate_k=2, stage_top_k={"final": 2})
    dbg = c.retrieve("q")
    # Scorer only ever saw the top-2 fused candidates (never the full list).
    _, texts = record[0]
    assert len(texts) == 2
    ids = {r.chunk.document_id for r in dbg.results}
    assert len(ids) <= 2
    assert all(r.reranker_score is not None for r in dbg.results)
    print("✓ reranker draws only from the bounded candidate pool")


def test_final_k_slice_after_rerank():
    rr = CrossEncoderReranker(model="unused", scorer=_scorer_factory())
    c = _controller(reranker=rr, rerank_candidate_k=5, rerank_final_k=2)
    dbg = c.retrieve("q")
    assert len(dbg.results) == 2
    assert [r.rank for r in dbg.results] == [1, 2]
    print("✓ rerank_final_k bounds the returned results")


def test_top_k_override_beats_final_k():
    rr = CrossEncoderReranker(model="unused", scorer=_scorer_factory())
    c = _controller(reranker=rr, rerank_final_k=5, stage_top_k={"final": 5})
    dbg = c.retrieve("q", top_k=1)
    assert len(dbg.results) == 1
    print("✓ --top-k override still wins after rerank")


def test_pool_smaller_than_final_k_returns_all_without_error():
    rr = CrossEncoderReranker(model="unused", scorer=_scorer_factory())
    c = _controller(
        reranker=rr,
        vector_retriever=FakeRetriever([_r("a", 1, 0.9)]),
        bm25_retriever=FakeRetriever([_r("b", 1, 5.0)]),
        rerank_final_k=5,
    )
    dbg = c.retrieve("q")
    assert len(dbg.results) == 2  # pool (2) < final_k (5) -> all returned
    assert not any(r.reranker_score is None for r in dbg.results)
    print("✓ pool < final_k -> all results returned, no error")


def test_reranking_disabled_falls_through_to_fusion_order():
    rr = CrossEncoderReranker(
        model="unused",
        scorer=_scorer_factory(scores_by_text={"content of a": 99.0}),
    )
    disabled = _controller(reranker=rr, reranking_enabled=False)
    hybrid = RetrievalController(
        strategy="hybrid",
        vector_retriever=FakeRetriever([_r("a", 1, 0.9), _r("b", 2, 0.8)]),
        bm25_retriever=FakeRetriever([_r("b", 1, 5.0), _r("c", 2, 3.0)]),
    )
    dbg = disabled.retrieve("q")
    baseline = hybrid.retrieve("q")
    assert [r.chunk.chunk_id for r in dbg.results] == [r.chunk.chunk_id for r in baseline.results]
    assert all(r.reranker_score is None for r in dbg.results)
    assert "rerank" in dbg.stages_skipped
    print("✓ disabled reranking == hybrid baseline, rerank recorded as skipped")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
