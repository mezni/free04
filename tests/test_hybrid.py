"""HybridRetriever tests (FR-005/FR-006, US2).

Pool retrieval annotates per-list provenance before fusion; fused output
contains the union of both retrievers with duplicates merged once.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Chunk, RetrievalQuery, RetrievalResult

try:
    from retrieval.hybrid import HybridRetriever
except ImportError:  # TDD: module does not exist yet
    HybridRetriever = None


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
    def __init__(self, results):
        self._results = list(results)
        self.calls: list[RetrievalQuery] = []

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        self.calls.append(query)
        return list(self._results)


def _hybrid(vector_results, bm25_results):
    return HybridRetriever(
        vector_retriever=FakeRetriever(vector_results),
        bm25_retriever=FakeRetriever(bm25_results),
    )


def test_pools_annotate_per_list_provenance():
    h = _hybrid([_r("a", 1, 0.9)], [_r("b", 1, 4.0)])
    vec_pool, bm25_pool = h.pools("q", vector_top_k=10, bm25_top_k=10)
    assert vec_pool[0].vector_rank == 1
    assert vec_pool[0].bm25_rank is None
    assert bm25_pool[0].bm25_rank == 1
    assert bm25_pool[0].vector_rank is None
    print("✓ pools carry their own rank provenance")


def test_pools_respect_stage_depths():
    h = _hybrid([_r("a", 1, 0.9)], [_r("b", 1, 4.0)])
    h.pools("q", vector_top_k=5, bm25_top_k=2)
    assert h.vector_retriever.calls[-1].top_k == 5
    assert h.bm25_retriever.calls[-1].top_k == 2
    print("✓ per-stage depths forwarded to each retriever")


def test_retrieve_returns_union_with_merged_duplicates():
    h = _hybrid([_r("a", 1, 0.9), _r("b", 2, 0.8)], [_r("b", 1, 5.0), _r("c", 2, 2.0)])
    results = h.retrieve("q", vector_top_k=10, bm25_top_k=10, final_k=5)
    ids = sorted(r.chunk.document_id for r in results)
    assert ids == ["a", "b", "c"]
    merged = next(r for r in results if r.chunk.document_id == "b")
    assert merged.vector_rank == 2
    assert merged.bm25_rank == 1
    assert merged.rrf_score is not None
    print("✓ union with duplicates merged once, both ranks kept")


def test_one_retriever_empty_preserves_other_order():
    h = _hybrid([_r("a", 1, 0.9), _r("b", 2, 0.7)], [])
    results = h.retrieve("q", vector_top_k=10, bm25_top_k=10, final_k=5)
    assert [r.chunk.document_id for r in results] == ["a", "b"]
    h2 = _hybrid([], [_r("c", 1, 3.0), _r("d", 2, 1.0)])
    results2 = h2.retrieve("q", vector_top_k=10, bm25_top_k=10, final_k=5)
    assert [r.chunk.document_id for r in results2] == ["c", "d"]
    print("✓ one empty retriever -> other's rank order preserved")


def test_both_empty_returns_empty():
    h = _hybrid([], [])
    assert h.retrieve("q", vector_top_k=5, bm25_top_k=5, final_k=5) == []
    print("✓ both empty -> empty output, no error")


def test_final_k_slices_fused_pool():
    h = _hybrid(
        [_r("a", 1, 0.9), _r("b", 2, 0.8), _r("c", 3, 0.7)],
        [_r("d", 1, 5.0), _r("e", 2, 4.0)],
    )
    results = h.retrieve("q", vector_top_k=10, bm25_top_k=10, final_k=2)
    assert len(results) == 2
    assert [r.rank for r in results] == [1, 2]
    print("✓ final_k bounds the returned results")


def test_deterministic_across_calls():
    h = _hybrid([_r("a", 1, 0.9), _r("b", 2, 0.8)], [_r("b", 1, 5.0), _r("c", 2, 2.0)])
    first = [(r.chunk.chunk_id, r.rrf_score) for r in h.retrieve("q", 10, 10, 5)]
    second = [(r.chunk.chunk_id, r.rrf_score) for r in h.retrieve("q", 10, 10, 5)]
    assert first == second
    print("✓ repeated hybrid runs are identical (SC-004)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
