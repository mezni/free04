"""BM25 lexical retrieval tests (FR-001/FR-002, US1, Phase 3).

Covers FR-026 lexical items: exact terms, error codes, acronyms,
no-result queries, top-K, descending order, metadata preservation,
and rebuild reproducibility (documents are the source of truth).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Chunk, RetrievalQuery

try:
    from retrieval.bm25 import BM25Index, BM25Retriever, build_bm25_index, tokenize
except ImportError:  # TDD: module does not exist yet
    BM25Index = BM25Retriever = build_bm25_index = tokenize = None


def _chunk(
    doc_id: str,
    text: str,
    *,
    index: int = 1,
    metadata: dict | None = None,
) -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}#{index:04d}",
        content=text,
        document_id=doc_id,
        document_name=f"{doc_id}.md",
        source=f"data/documents/{doc_id}.md",
        chunk_index=index,
        metadata=dict(metadata or {}),
    )


CORPUS = [
    _chunk(
        "lte_guide",
        "Error 504 (gateway timeout) on the X2 interface during handover. "
        "Restart the eNodeB X2 link and verify SCTP association.",
        metadata={"department": "network", "product": "lte"},
    ),
    _chunk(
        "noc_runbook",
        "NOC runbook: escalate P1 incidents to L2 within 15 minutes. "
        "SLA acknowledgement window is 4 hours for critical issues.",
        metadata={"department": "operations", "product": "noc"},
    ),
    _chunk(
        "broadband_faq",
        "Broadband disconnections are often caused by router firmware. "
        "Reboot the CPE and check the DSL sync rate.",
        metadata={"department": "support", "product": "broadband"},
    ),
]


@pytest.fixture
def index():
    return BM25Index.build_from_chunks(CORPUS)


def test_exact_error_code_query_finds_chunk(index):
    """US1 independent test: exact identifiers find the right chunk."""
    results = index.search("X2 timeout 504", top_k=3)
    assert results, "expected results for an exact-identifier query"
    top = results[0]
    assert top.chunk.document_id == "lte_guide"
    assert top.chunk.chunk_id == "lte_guide#0001"
    assert top.chunk.metadata["department"] == "network"  # metadata intact
    print("✓ exact error-code query finds the chunk")


def test_acronym_ranks_above_non_matching(index):
    # "NOC"/"SLA" live in noc_runbook; "timeout" only matches lte_guide.
    results = index.search("NOC timeout SLA", top_k=3)
    assert results[0].chunk.document_id == "noc_runbook"
    non_matching = [r for r in results if r.chunk.document_id != "noc_runbook"]
    assert non_matching, "sanity: other chunks also returned"
    assert results[0].score > non_matching[0].score
    print("✓ acronym/terminology chunk ranks above non-matching")


def test_no_match_returns_empty_without_error(index):
    assert index.search("quantum blockchain zebra", top_k=5) == []
    print("✓ no-match query -> empty list, no error")


def test_empty_corpus_returns_empty():
    empty = BM25Index.build_from_chunks([])
    assert empty.search("anything", top_k=5) == []
    print("✓ empty corpus -> empty results, no error")


def test_top_k_bound_and_descending_order(index):
    results = index.search("LTE NOC broadband router timeout", top_k=2)
    assert len(results) <= 2
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert [r.rank for r in results] == list(range(1, len(results) + 1))
    print("✓ top-K bound + descending score order + dense ranks")


def test_provenance_populated(index):
    results = index.search("NOC runbook", top_k=1)
    r = results[0]
    assert r.retrieval_method == "bm25"
    assert r.bm25_rank == r.rank
    assert r.vector_rank is None and r.rrf_score is None
    print("✓ bm25 provenance set; vector/rrf absent (not fabricated)")


def test_rebuild_is_reproducible():
    """FR-002: rebuilding from source documents yields an identical index."""
    repo_root = Path(__file__).parent.parent
    first = build_bm25_index(str(repo_root / "data" / "documents"))
    second = build_bm25_index(str(repo_root / "data" / "documents"))
    assert len(first.chunks) == len(second.chunks) > 0
    assert [c.chunk_id for c in first.chunks] == [c.chunk_id for c in second.chunks]
    assert first._tokens == second._tokens
    probe = "LTE latency SLA"
    s1 = [float(r.score) for r in first.search(probe, top_k=10)]
    s2 = [float(r.score) for r in second.search(probe, top_k=10)]
    assert s1 == s2
    print("✓ rebuild from documents reproduces the index byte-identically")


def test_retriever_interface_matches_vector_retriever(index):
    """BM25Retriever consumes RetrievalQuery like Retriever.retrieve does."""
    retriever = BM25Retriever(index)
    results = retriever.retrieve(RetrievalQuery(question="X2 timeout 504", top_k=2))
    assert results and results[0].chunk.document_id == "lte_guide"
    assert len(results) <= 2
    print("✓ RetrievalQuery interface parity")


def test_tokenize_lowercases_and_splits_identifiers():
    assert tokenize("Error 504 on X2-interface") == ["error", "504", "on", "x2", "interface"]
    print("✓ identifier-friendly tokenization")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
