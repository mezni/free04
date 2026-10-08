"""RetrievalController tests (FR-004/FR-007/FR-008/FR-009, US2).

Strategy selection is explicit and validated: no silent fallback, results
record their strategy, and disabled stages are skipped (recorded, not
guessed) per Principle XXVI.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Chunk, RetrievalQuery, RetrievalResult

try:
    from retrieval.controller import RetrievalController
except ImportError:  # TDD: module does not exist yet
    RetrievalController = None


def _r(doc_id: str, rank: int, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=f"{doc_id}#0001",
            content=f"content {doc_id}",
            document_id=doc_id,
            document_name=f"{doc_id}.md",
            source=f"data/documents/{doc_id}.md",
            chunk_index=1,
        ),
        score=score,
        rank=rank,
    )


class FakeRetriever:
    """Records RetrievalQuery calls; returns a fixed candidate list."""

    def __init__(self, results):
        self._results = list(results)
        self.calls: list[RetrievalQuery] = []

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        self.calls.append(query)
        return list(self._results)


def _controller(strategy="vector", **kwargs):
    kwargs.setdefault("vector_retriever", FakeRetriever([_r("a", 1, 0.9), _r("b", 2, 0.8)]))
    kwargs.setdefault("bm25_retriever", FakeRetriever([_r("b", 1, 5.0), _r("c", 2, 3.0)]))
    return RetrievalController(strategy=strategy, **kwargs)


def test_default_strategy_is_used_when_not_overridden():
    c = _controller(strategy="hybrid")
    dbg = c.retrieve("what is latency?")
    assert dbg.strategy == "hybrid"
    print("✓ strategy resolves from configuration default")


def test_explicit_strategy_overrides_default():
    c = _controller(strategy="vector")
    dbg = c.retrieve("q", strategy="bm25")
    assert dbg.strategy == "bm25"
    print("✓ explicit strategy overrides the default")


def test_unknown_strategy_fails_loudly():
    """FR-008: no silent fallback to another strategy."""
    with pytest.raises(ValueError, match="strategy"):
        _controller(strategy="souped")
    c = _controller()
    with pytest.raises(ValueError, match="strategy"):
        c.retrieve("q", strategy="souped")
    print("✓ unknown strategy rejected at config AND invocation time")


def test_only_selected_path_executes():
    vector = FakeRetriever([_r("a", 1, 0.9)])
    bm25 = FakeRetriever([_r("a", 1, 5.0)])
    c = _controller(strategy="vector", vector_retriever=vector, bm25_retriever=bm25)
    c.retrieve("q")
    assert len(vector.calls) == 1 and not bm25.calls

    vector2 = FakeRetriever([_r("a", 1, 0.9)])
    bm252 = FakeRetriever([_r("a", 1, 5.0)])
    c2 = _controller(strategy="bm25", vector_retriever=vector2, bm25_retriever=bm252)
    c2.retrieve("q")
    assert len(bm252.calls) == 1 and not vector2.calls
    print("✓ each strategy executes only its own retrieval path")


def test_results_record_their_strategy_and_provenance():
    c = _controller(strategy="vector")
    results = c.retrieve("q").results
    assert all(r.retrieval_method == "vector" for r in results)
    assert all(r.vector_rank == r.rank for r in results)
    assert all(r.bm25_rank is None and r.rrf_score is None for r in results)

    c2 = _controller(strategy="hybrid")
    results2 = c2.retrieve("q").results
    assert all(r.retrieval_method == "hybrid" for r in results2)
    assert all(r.rrf_score is not None for r in results2)
    print("✓ results carry strategy + stage provenance (absent = not run)")


def test_hybrid_fuses_both_retrievers():
    c = _controller(strategy="hybrid")
    ids = sorted(r.chunk.document_id for r in c.retrieve("q").results)
    assert ids == ["a", "b", "c"]  # union of both lists, deduped
    print("✓ hybrid combines both retrievers")


def test_hybrid_reranked_without_reranker_falls_through_to_fusion():
    """US2 baseline: reranker absent => fusion order, rerank recorded as skipped."""
    c = _controller(strategy="hybrid_reranked")
    hybrid = _controller(strategy="hybrid").retrieve("q")
    dbg = c.retrieve("q")
    assert [r.chunk.chunk_id for r in dbg.results] == [r.chunk.chunk_id for r in hybrid.results]
    assert all(r.reranker_score is None for r in dbg.results)
    assert "rerank" in dbg.stages_skipped
    print("✓ hybrid_reranked falls through to fusion when reranker absent")


def test_empty_results_are_not_an_error():
    c = _controller(
        strategy="vector",
        vector_retriever=FakeRetriever([]),
        bm25_retriever=FakeRetriever([]),
    )
    dbg = c.retrieve("q")
    assert dbg.results == []
    print("✓ empty result set -> empty results, no error")


def test_rewrite_disabled_keeps_original_query():
    c = _controller(strategy="vector", rewriting_enabled=False)
    dbg = c.retrieve("the original question?")
    assert dbg.query == "the original question?"
    assert dbg.rewritten_query is None
    assert "rewrite" in dbg.stages_skipped
    # Retrievers received the untouched original (Principle XXIX).
    assert c.vector_retriever.calls[0].question == "the original question?"
    print("✓ rewriting off: original preserved and used (XXIX)")


def test_top_k_override_respected():
    c = _controller(strategy="vector")
    dbg = c.retrieve("q", top_k=1)
    assert len(dbg.results) == 1
    assert c.vector_retriever.calls[-1].top_k == 20  # stage depth, not final slice
    print("✓ --top-k controls the final result count")


def test_stage_depths_used_for_pool_retrieval():
    c = _controller(
        strategy="hybrid", stage_top_k={"vector": 7, "bm25": 3, "hybrid": 9, "final": 2}
    )
    c.retrieve("q")
    assert c.vector_retriever.calls[-1].top_k == 7
    assert c.bm25_retriever.calls[-1].top_k == 3
    print("✓ per-stage top_k from configuration")


def test_debug_object_shape():
    c = _controller(strategy="hybrid")
    dbg = c.retrieve("q", filters={})
    assert dbg.query == "q"
    assert dbg.rewritten_query is None
    assert dbg.strategy == "hybrid"
    assert isinstance(dbg.latency_ms, dict) and "total" in dbg.latency_ms
    assert isinstance(dbg.stages_skipped, list)
    print("✓ RetrievalDebug carries query/strategy/latency/skipped")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
