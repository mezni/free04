"""Generic metadata filtering tests (FR-010/FR-011, US4).

Filters are generic over keys (all-equality), restriction-only — they
never reorder or rescore — and behave identically under every strategy.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Chunk, RetrievalResult

try:
    from retrieval.filters import apply_filters, matches_filters
except ImportError:  # TDD: module does not exist yet
    matches_filters = None
    apply_filters = None

try:
    from retrieval.controller import RetrievalController
except ImportError:  # TDD: module does not exist yet
    RetrievalController = None


def _r(doc_id: str, rank: int, score: float, **meta) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=f"{doc_id}#0001",
            content=f"content {doc_id}",
            document_id=doc_id,
            document_name=f"{doc_id}.md",
            source=f"data/documents/{doc_id}.md",
            chunk_index=1,
            metadata=dict(meta),
        ),
        score=score,
        rank=rank,
    )


# -- T024: matches_filters unit semantics ----------------------------------


def test_all_keys_must_match():
    assert matches_filters(
        {"category": "5g", "department": "noc"}, {"category": "5g", "department": "noc"}
    )
    print("✓ all filter keys matching -> chunk kept")


def test_partial_mismatch_excluded():
    assert not matches_filters(
        {"category": "5g", "department": "noc"}, {"category": "5g", "department": "rf"}
    )
    print("✓ partial mismatch -> chunk excluded (AND semantics)")


def test_unknown_key_on_chunk_excluded():
    # Filter key exists on no chunk -> match fails, never an error (US4 S2).
    assert not matches_filters({"category": "5g"}, {"department": "noc"})
    results = [_r("a", 1, 0.9, category="5g"), _r("b", 2, 0.8, category="lte")]
    assert apply_filters(results, {"tier": "gold"}) == []
    print("✓ unknown key -> empty result set, no error")


def test_empty_filters_are_baseline_identity():
    results = [_r("a", 1, 0.9, category="5g"), _r("b", 2, 0.8, category="lte")]
    assert matches_filters({}, {})
    assert matches_filters({"anything": 1}, {})
    assert apply_filters(results, {}) == results
    print("✓ empty filters -> identical to unfiltered baseline")


def test_filter_never_reorders_or_rescores():
    results = [
        _r("a", 1, 0.9, category="5g"),
        _r("b", 2, 0.8, category="5g"),
        _r("c", 3, 0.7, category="lte"),
        _r("d", 4, 0.6, category="5g"),
    ]
    filtered = apply_filters(results, {"category": "5g"})
    assert [r.chunk.document_id for r in filtered] == ["a", "b", "d"]  # original order
    assert [r.score for r in filtered] == [0.9, 0.8, 0.6]  # scores untouched
    assert [r.rank for r in filtered] == [1, 2, 4]  # ranks untouched
    print("✓ filtering restricts only — no reorder, no rescore")


def test_new_metadata_key_works_without_code_changes():
    # A key that never existed in today's code (US4 scenario 5).
    assert matches_filters({"tier": "gold", "category": "5g"}, {"tier": "gold"})
    assert not matches_filters({"tier": "silver"}, {"tier": "gold"})
    print("✓ novel metadata keys work generically (FR-011)")


# -- T025: controller-level uniform behavior --------------------------------


class FakeRetriever:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def retrieve(self, query):
        self.calls.append(query)
        return list(self._results)


def _controller(strategy: str, results: list[RetrievalResult], filters=None):
    return RetrievalController(
        strategy=strategy,
        vector_retriever=FakeRetriever(results),
        bm25_retriever=FakeRetriever(results),
        filters=filters or {},
    )


def _pool():
    return [
        _r("nokia5g", 1, 0.9, category="5g", department="noc"),
        _r("lte_doc", 2, 0.8, category="lte", department="noc"),
        _r("sla_doc", 3, 0.7, category="enterprise", department="sales"),
    ]


@pytest.mark.parametrize("strategy", ["vector", "bm25", "hybrid", "hybrid_reranked"])
def test_filter_applied_uniformly_across_strategies(strategy):
    c = _controller(strategy, _pool(), filters={"category": "5g"})
    dbg = c.retrieve("anything")
    assert [r.chunk.document_id for r in dbg.results] == ["nokia5g"]
    assert dbg.filters == {"category": "5g"}
    print(f"✓ {strategy}: only matching metadata rows returned")


@pytest.mark.parametrize("strategy", ["vector", "bm25", "hybrid", "hybrid_reranked"])
def test_empty_filter_returns_full_baseline_across_strategies(strategy):
    c = _controller(strategy, _pool(), filters={})
    dbg = c.retrieve("anything")
    assert len(dbg.results) == 3
    assert [r.chunk.document_id for r in dbg.results] == ["nokia5g", "lte_doc", "sla_doc"]
    print(f"✓ {strategy}: no filters -> full baseline")


def test_multi_key_filter_and_unknown_key_empty():
    c = _controller("hybrid", _pool(), filters={"category": "5g", "department": "noc"})
    assert [r.chunk.document_id for r in c.retrieve("q").results] == ["nokia5g"]

    c2 = _controller("vector", _pool(), filters={"nonexistent_key": "x"})
    assert c2.retrieve("q").results == []
    print("✓ multi-key AND + unknown key -> empty, no error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
