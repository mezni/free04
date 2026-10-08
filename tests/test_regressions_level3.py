"""Named Level 3 regression tests (FR-028, US8).

One test per failure logged in experiments.md §7 (F-001…F-003). Each
test pins the recorded stage outcome of the failure-analysis procedure
(lessons-learned.md §10) so a future change that alters a documented
fact surfaces immediately.

Hermetic by constitution (research R9): the recorded claims for these
failures live in the BM25 index and the loader/chunker output — pure
Python over data/documents, no embedder, no reranker, no network.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain import RetrievalQuery
from evaluation.dataset import load_questions
from ingestion.chunker import chunk_document
from ingestion.loader import discover_documents
from retrieval.bm25 import BM25Retriever, build_bm25_index

QUESTIONS = {q.id: q for q in load_questions("data/evaluation/retrieval_questions.jsonl")}


def _bm25(question: str, top_k: int = 20) -> list:
    return BM25Retriever(build_bm25_index()).retrieve(
        RetrievalQuery(question=question, top_k=top_k)
    )


def test_f001_lexical_gap_cannot_rescue_speed_reporting_tail():
    """F-001 (eval-004): BM25 anchors #0001 at rank 1 but never matches
    the KPI-tail chunk #0002 — the lexical system cannot rescue the
    vector rank-9 miss recorded in the log."""
    q = QUESTIONS["eval-004"]
    results = _bm25(q.question, top_k=10)
    ids = [r.chunk.chunk_id for r in results]

    assert "5g_speed_reporting#0001" in ids, "lexical anchor chunk must be retrieved"
    assert ids[0] == "5g_speed_reporting#0001", "exact-term match must rank first"
    assert "5g_speed_reporting#0002" not in ids, (
        "F-001 pins the lexical gap: the tail chunk has no query-token overlap "
        "(corpus 'P95 throughput' vs query 'real-world download rates')"
    )

    # corpus step of the tree: the labelled tail chunk exists in ingestion
    noc_like = [
        c
        for d in discover_documents()
        if d.document_id == "5g_speed_reporting"
        for c in chunk_document(d)
    ]
    tail = next(c for c in noc_like if c.chunk_id == "5g_speed_reporting#0002")
    assert "P95 throughput figures" in tail.content
    print("✓ F-001: lexical anchor ranks first; tail chunk unmatched but in corpus")


def test_f002_bm25_miss_on_operations_center_paraphrase():
    """F-002 (eval-005): BM25 finds both NOC chunks only deep in the pool
    (ranks > 10) — the 'operations center' paraphrase has almost no
    lexical overlap with 'NOC'/'Acknowledge alert'."""
    q = QUESTIONS["eval-005"]
    results = _bm25(q.question, top_k=20)
    ranks = {r.chunk.chunk_id: r.rank for r in results if r.chunk.chunk_id in q.relevant_chunks}

    assert set(ranks) == set(q.relevant_chunks), "both NOC chunks must be in the BM25 pool"
    assert all(rank > 10 for rank in ranks.values()), (
        f"F-002 pins deep-only BM25 ranks (expected >10): {ranks}"
    )
    top10 = [r.chunk.chunk_id for r in results if r.rank <= 10]
    assert not (set(top10) & set(q.relevant_chunks)), "no NOC chunk inside the BM25 top 10"

    # corpus step: both labelled chunks exist in ingestion
    present = {
        c.chunk_id
        for d in discover_documents()
        if d.document_id == "noc_incident_procedure"
        for c in chunk_document(d)
    }
    assert set(q.relevant_chunks) <= present
    print(f"✓ F-002: NOC chunks in pool only at ranks {sorted(ranks.values())} (>10)")


def test_f003_exact_anchor_ranks_first_and_tail_chunk_in_corpus():
    """F-003 (eval-016): the exact-term anchor chunk ranks first under
    BM25, while the heading-less continuation chunk #0002 is never a
    lexical match — and exists in the corpus (tree step 1 = YES)."""
    q = QUESTIONS["eval-016"]
    results = _bm25(q.question, top_k=20)
    ranks = {r.chunk.chunk_id: r.rank for r in results if r.chunk.chunk_id in q.relevant_chunks}

    assert ranks.get("noc_incident_procedure#0001") == 1, "exact anchor must rank first"
    assert "noc_incident_procedure#0002" not in ranks, (
        "F-003 pins the tail chunk as a non-match for the anomaly query"
    )

    chunks = {
        c.chunk_id: c
        for d in discover_documents()
        if d.document_id == "noc_incident_procedure"
        for c in chunk_document(d)
    }
    tail = chunks["noc_incident_procedure#0002"]
    assert "Assign incident to appropriate team" in tail.content, (
        "tree step 1: the lost chunk IS in the corpus (presence verified)"
    )
    print("✓ F-003: anchor@1, tail chunk unmatched by BM25 but present in corpus")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
