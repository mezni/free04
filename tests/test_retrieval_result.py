"""RetrievalResult provenance contract (contracts/retrieval-result-schema.md).

Level 3 (FR-009/FR-027): provenance fields are optional, `None` means the
stage did not run, and the Level 2 fields (chunk/score/rank) keep their
exact Level 1 meaning so the evidence builder is untouched.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain import Chunk, RetrievalResult


def _chunk() -> Chunk:
    return Chunk(
        chunk_id="doc_a#0001",
        content="X2 interface timeout raises error 504 during handover.",
        document_id="doc_a",
        document_name="doc_a.md",
        source="data/documents/doc_a.md",
        chunk_index=1,
    )


def test_level2_fields_construct_unchanged():
    """Level 2 construction path (chunk, score, rank) still works (FR-027)."""
    r = RetrievalResult(chunk=_chunk(), score=0.87, rank=1)
    assert r.chunk.chunk_id == "doc_a#0001"
    assert r.score == 0.87
    assert r.rank == 1
    print("✓ Level 2 fields unchanged")


def test_provenance_defaults_are_none():
    """Absent provenance = stage not run; never fabricated zeros (Principle XXVI)."""
    r = RetrievalResult(chunk=_chunk(), score=0.5, rank=2)
    assert r.retrieval_method is None
    assert r.vector_rank is None
    assert r.bm25_rank is None
    assert r.rrf_score is None
    assert r.reranker_score is None
    print("✓ provenance defaults are None")


def test_provenance_fields_populate_when_stage_ran():
    r = RetrievalResult(
        chunk=_chunk(),
        score=0.031,
        rank=1,
        retrieval_method="hybrid",
        vector_rank=2,
        bm25_rank=1,
        rrf_score=0.031,
    )
    assert r.retrieval_method == "hybrid"
    assert (r.vector_rank, r.bm25_rank, r.rrf_score) == (2, 1, 0.031)
    assert r.reranker_score is None  # rerank stage did not run
    print("✓ provenance populates per stage that ran")


def test_evidence_builder_consumes_extended_results():
    """FR-027: evidence builder reads only chunk/score/rank — untouched."""
    from grounding.evidence_builder import build_evidence

    results = [RetrievalResult(chunk=_chunk(), score=0.5, rank=1)]
    evidence = build_evidence(results)
    assert len(evidence) == 1
    assert evidence[0].chunk_id == "doc_a#0001"
    assert evidence[0].retrieval_score == 0.5
    print("✓ evidence builder compatible with extended RetrievalResult")


if __name__ == "__main__":
    test_level2_fields_construct_unchanged()
    test_provenance_defaults_are_none()
    test_provenance_fields_populate_when_stage_ran()
    test_evidence_builder_consumes_extended_results()
    print("✓ RetrievalResult provenance contract tests passed")
