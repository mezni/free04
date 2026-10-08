"""Hybrid retrieval: vector + BM25 pools fused by RRF (FR-005/FR-006).

`HybridRetriever` owns the two-system pool retrieval and annotates each
pool with its own provenance (`vector_rank` / `bm25_rank`) before fusion —
the controller applies metadata filtering between these two steps.
"""

from __future__ import annotations

import time

from domain import RetrievalQuery, RetrievalResult
from retrieval.fusion import DEFAULT_K, rrf_fuse


class HybridRetriever:
    """Runs both retrievers independently and fuses their ranked lists."""

    def __init__(self, *, vector_retriever, bm25_retriever):
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        # Wall timings (ms) of the last pools() call — additive diagnostics
        # for the controller (US3, FR-019).
        self.last_timings: dict[str, float] = {}

    def pools(
        self,
        question: str,
        *,
        vector_top_k: int,
        bm25_top_k: int,
    ) -> tuple[list[RetrievalResult], list[RetrievalResult]]:
        """Fetch both ranked pools, each annotated with its list provenance."""
        started = time.perf_counter()
        vector_results = self.vector_retriever.retrieve(
            RetrievalQuery(question=question, top_k=vector_top_k)
        )
        vector_ms = (time.perf_counter() - started) * 1000.0

        started = time.perf_counter()
        bm25_results = self.bm25_retriever.retrieve(
            RetrievalQuery(question=question, top_k=bm25_top_k)
        )
        bm25_ms = (time.perf_counter() - started) * 1000.0
        self.last_timings = {
            "vector": round(vector_ms, 3),
            "bm25": round(bm25_ms, 3),
        }

        annotated_vector = [r.model_copy(update={"vector_rank": r.rank}) for r in vector_results]
        annotated_bm25 = [r.model_copy(update={"bm25_rank": r.rank}) for r in bm25_results]
        return annotated_vector, annotated_bm25

    def retrieve(
        self,
        question: str,
        vector_top_k: int,
        bm25_top_k: int,
        final_k: int,
        k: int = DEFAULT_K,
    ) -> list[RetrievalResult]:
        """Pools → RRF fusion → top final_k (no filtering — that's the controller)."""
        vector_results, bm25_results = self.pools(
            question, vector_top_k=vector_top_k, bm25_top_k=bm25_top_k
        )
        return rrf_fuse([vector_results, bm25_results], k=k)[:final_k]
