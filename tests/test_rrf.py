"""RRF rank fusion tests (FR-005/FR-006, US2, Principle XXV NON-NEGOTIABLE).

Rank-based combination only — never raw-score averaging. Deterministic,
duplicates merged once, single-system input still fused.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Chunk, RetrievalResult

try:
    from retrieval.fusion import rrf_fuse
except ImportError:  # TDD: module does not exist yet
    rrf_fuse = None


def _r(doc_id: str, rank: int, score: float = 0.0, **prov) -> RetrievalResult:
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
        **prov,
    )


def test_chunk_in_both_lists_appears_once_with_both_contributions():
    vec = [_r("a", 1, 0.9, vector_rank=1), _r("b", 2, 0.8, vector_rank=2)]
    bm25 = [_r("b", 1, 12.5, bm25_rank=1), _r("a", 2, 9.0, bm25_rank=2)]
    fused = rrf_fuse([vec, bm25], k=60)

    ids = [r.chunk.document_id for r in fused]
    assert sorted(ids) == ["a", "b"]  # once each
    merged = next(r for r in fused if r.chunk.document_id == "b")
    expected_b = 1 / (60 + 2) + 1 / (60 + 1)  # vector rank 2 + bm25 rank 1
    assert merged.rrf_score == pytest.approx(expected_b)
    assert merged.score == pytest.approx(expected_b)
    # Provenance from BOTH lists survives the merge.
    assert merged.vector_rank == 2
    assert merged.bm25_rank == 1
    # b contributed from both lists and outranks a (1/62+1/61 > 1/61+1/62? equal!)
    # a: 1/61 + 1/62; b: 1/62 + 1/61 — identical sums, so order = first-seen.
    assert fused[0].chunk.document_id == "a"  # first-seen stable tie-break
    print("✓ duplicate merged once with both rank contributions")


def test_scores_never_averaged():
    """Principle XXV: output score is the RRF sum, not a blend of inputs."""
    vec = [_r("a", 1, score=0.99)]
    bm25 = [_r("b", 1, score=500.0)]
    fused = rrf_fuse([vec, bm25], k=60)
    for r in fused:
        assert r.score == pytest.approx(1 / 61)
    print("✓ raw scores are never averaged (RRF only)")


def test_one_system_empty_preserves_other_order():
    vec = [_r("a", 1), _r("b", 2), _r("c", 3)]
    fused = rrf_fuse([vec, []], k=60)
    assert [r.chunk.document_id for r in fused] == ["a", "b", "c"]
    assert fused[1].rrf_score == pytest.approx(1 / 62)
    print("✓ single-system input fuses in rank order")


def test_both_systems_empty_returns_empty():
    assert rrf_fuse([[], []]) == []
    assert rrf_fuse([]) == []
    print("✓ empty input -> empty output")


def test_differing_ranks_favor_higher_contributions():
    vec = [_r("x", 1), _r("y", 3)]
    bm25 = [_r("y", 1), _r("x", 4)]
    fused = rrf_fuse([vec, bm25], k=60)
    # x: 1/61 + 1/64; y: 1/63 + 1/61  -> y > x
    scores = {r.chunk.document_id: r.rrf_score for r in fused}
    assert scores["y"] > scores["x"]
    assert fused[0].chunk.document_id == "y"
    print("✓ differing ranks produce RRF-weighted ordering")


def test_equal_scores_tie_broken_by_first_seen():
    # Genuine tie: each chunk contributes 1/(60+1) from a different list.
    fused = rrf_fuse([[_r("first", 1)], [_r("second", 1)]], k=60)
    assert fused[0].rrf_score == pytest.approx(fused[1].rrf_score)
    assert [r.chunk.document_id for r in fused] == ["first", "second"]
    print("✓ equal fusion scores keep first-seen order (stable, documented)")


def test_deterministic_across_runs():
    vec = [_r("a", 1), _r("b", 2), _r("c", 3)]
    bm25 = [_r("c", 1), _r("a", 2)]
    runs = [rrf_fuse([vec, bm25], k=60) for _ in range(5)]
    reference = [(r.chunk.document_id, r.rrf_score) for r in runs[0]]
    for run in runs[1:]:
        assert [(r.chunk.document_id, r.rrf_score) for r in run] == reference
    print("✓ repeated fusion is byte-identical (SC-004)")


def test_configurable_k():
    vec = [_r("a", 1)]
    fused = rrf_fuse([vec, []], k=1)
    assert fused[0].rrf_score == pytest.approx(1 / 2)
    print("✓ k is configurable")


def test_final_ranks_dense_and_ordered():
    vec = [_r("a", 1), _r("b", 2)]
    bm25 = [_r("b", 1), _r("c", 2)]
    fused = rrf_fuse([vec, bm25], k=60)
    assert [r.rank for r in fused] == list(range(1, len(fused) + 1))
    scores = [r.rrf_score for r in fused]
    assert scores == sorted(scores, reverse=True)
    print("✓ dense 1-based ranks in descending RRF order")


def test_inputs_not_mutated():
    vec = [_r("a", 1, vector_rank=1)]
    before = vec[0].rank, vec[0].score, vec[0].rrf_score
    rrf_fuse([vec, []], k=60)
    after = vec[0].rank, vec[0].score, vec[0].rrf_score
    assert before == after
    print("✓ fusion does not mutate its inputs")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
