"""Retrieval policy layer (FR-004/006/008, contracts/store-and-retriever.md).

Takes a typed RetrievalQuery (question, top_k, similarity_threshold,
metadata_filter), embeds the question, searches the store, drops results
below the threshold, and assigns 1-based ranks.
"""

import time

from domain import RetrievalQuery, RetrievalResult
from embeddings.embedder import Embedder
from retrieval.vector_store import VectorStore


class Retriever:
    """Question → query embedding → vector search → ranked RetrievalResults."""

    def __init__(self, vector_store: VectorStore, embedder: Embedder):
        self.vector_store = vector_store
        self.embedder = embedder
        # Last retrieval timings in ms ({"embed", "search"}) — additive
        # diagnostics for the Level 3 controller (US3, FR-019); behavior
        # of retrieve() is unchanged.
        self.last_timings: dict[str, float] = {}

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        """Search for top-K chunks relevant to the question."""
        started = time.perf_counter()
        query_vector = self.embedder.embed_query(query.question)
        embed_ms = (time.perf_counter() - started) * 1000.0

        metadata_filter = dict(query.metadata_filter) if query.metadata_filter is not None else None

        started = time.perf_counter()
        results = self.vector_store.query(
            query_vector,
            top_k=query.top_k,
            metadata_filter=metadata_filter,
        )
        search_ms = (time.perf_counter() - started) * 1000.0
        self.last_timings = {
            "embed": round(embed_ms, 3),
            "search": round(search_ms, 3),
        }

        # Drop results below the similarity threshold (already stored as cosine
        # similarity where higher = more similar).
        results = [r for r in results if r.score >= query.similarity_threshold]

        # Ordered by descending score and re-ranked from 1.
        results.sort(key=lambda r: r.score, reverse=True)
        for i, result in enumerate(results, start=1):
            result.rank = i

        return results
