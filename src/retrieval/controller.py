"""Retrieval controller: one entry point for every strategy (FR-007).

Orchestrates optional query rewriting → strategy retrieval (vector/bm25/
hybrid) → metadata filtering → RRF fusion → optional reranking, and
returns ranked results only — it never generates answers (Principle XXI).

Strategy selection is validated against a closed set: unknown values fail
loudly, never fall back (FR-008). Every returned result records which
strategy produced it; stage provenance fields stay `None` for stages that
did not run (Principle XXVI). The original query is always preserved
(Principle XXIX).
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from config import RETRIEVAL_STRATEGIES
from domain import RetrievalQuery, RetrievalResult
from retrieval.fusion import DEFAULT_K, rrf_fuse
from retrieval.hybrid import HybridRetriever

# Execution accounting (contracts/cli-retrieve.md §3): a stage either ran
# (latency key present) or appears in stages_skipped — never fabricated.
ALL_STAGES = ["rewrite", "embed", "vector", "bm25", "filter", "fuse", "rerank"]

DEFAULT_STAGE_TOP_K = {"vector": 20, "bm25": 20, "hybrid": 20, "final": 5}


class RetrievalDebug(BaseModel):
    """Diagnostics trail for one retrieve() call (data-model.md)."""

    model_config = ConfigDict(validate_assignment=False)

    query: str
    rewritten_query: str | None = None
    strategy: str
    filters: dict[str, Any] = Field(default_factory=dict)
    results: list[RetrievalResult] = Field(default_factory=list)
    latency_ms: dict[str, float] = Field(default_factory=dict)
    stages_skipped: list[str] = Field(default_factory=list)


class RetrievalController:
    """Strategy selection + orchestration. Returns results, never answers."""

    def __init__(
        self,
        *,
        vector_retriever=None,
        bm25_retriever=None,
        strategy: str = "vector",
        stage_top_k: dict[str, int] | None = None,
        fusion_k: int = DEFAULT_K,
        filters: dict[str, Any] | None = None,
        reranker=None,
        reranking_enabled: bool = True,
        rerank_candidate_k: int = 20,
        rerank_final_k: int = 5,
        rewriter=None,
        rewriting_enabled: bool = False,
    ):
        if strategy not in RETRIEVAL_STRATEGIES:
            raise ValueError(
                f"retrieval strategy must be one of "
                f"{', '.join(RETRIEVAL_STRATEGIES)}, got {strategy!r}"
            )

        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.strategy = strategy
        self.stage_top_k = dict(DEFAULT_STAGE_TOP_K)
        if stage_top_k:
            self.stage_top_k.update(stage_top_k)
        self.fusion_k = fusion_k
        self.filters = dict(filters or {})
        self.reranker = reranker
        self.reranking_enabled = reranking_enabled
        self.rerank_candidate_k = rerank_candidate_k
        self.rerank_final_k = rerank_final_k
        self.rewriter = rewriter
        self.rewriting_enabled = rewriting_enabled
        self.hybrid = HybridRetriever(
            vector_retriever=vector_retriever, bm25_retriever=bm25_retriever
        )

    # -- stage helpers ----------------------------------------------------

    def _valid_strategy(self, strategy: str | None) -> str:
        chosen = strategy or self.strategy
        if chosen not in RETRIEVAL_STRATEGIES:
            raise ValueError(
                f"retrieval strategy must be one of "
                f"{', '.join(RETRIEVAL_STRATEGIES)}, got {chosen!r}"
            )
        return chosen

    def _needs_vector(self, strategy: str) -> bool:
        return strategy in ("vector", "hybrid", "hybrid_reranked")

    def _needs_bm25(self, strategy: str) -> bool:
        return strategy in ("bm25", "hybrid", "hybrid_reranked")

    def _needs_fusion(self, strategy: str) -> bool:
        return strategy in ("hybrid", "hybrid_reranked")

    def _rerank_stage_runs(self, strategy: str) -> bool:
        return (
            strategy == "hybrid_reranked" and self.reranking_enabled and self.reranker is not None
        )

    def _rewrite_stage_runs(self) -> bool:
        return bool(self.rewriting_enabled and self.rewriter is not None)

    def _available_vector(self) -> None:
        if self.vector_retriever is None:
            raise RuntimeError(
                "vector retriever not available for this controller build "
                "(built for a bm25-only strategy)"
            )

    def _available_bm25(self) -> None:
        if self.bm25_retriever is None:
            raise RuntimeError("bm25 retriever not available for this controller build")

    @staticmethod
    def _ms(started: float) -> float:
        return round((time.perf_counter() - started) * 1000.0, 3)

    def _record_vector_timing(self, latency: dict[str, float], wall_ms: float) -> None:
        """embed/vector split from the instrumented Retriever when available.

        Without instrumentation only the wall time is recorded — no key is
        fabricated for a stage whose duration is unknown (Principle XXVI).
        """
        timings = getattr(self.vector_retriever, "last_timings", None)
        if timings and "embed" in timings and "search" in timings:
            latency["embed"] = round(float(timings["embed"]), 3)
            latency["vector"] = round(float(timings["search"]), 3)
        else:
            latency["vector"] = wall_ms

    # -- main entry -------------------------------------------------------

    def retrieve(
        self,
        question: str,
        *,
        strategy: str | None = None,
        filters: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RetrievalDebug:
        """Run one retrieval request and return results with a debug trail."""
        chosen = self._valid_strategy(strategy)
        active_filters = dict(self.filters if filters is None else filters)
        started = time.perf_counter()
        latency: dict[str, float] = {}

        run_stages: set[str] = set()
        query = question
        rewritten: str | None = None

        # Stage: optional query rewriting (Principle XXIX — original kept).
        if self._rewrite_stage_runs():
            run_stages.add("rewrite")
            stage_started = time.perf_counter()
            candidate = self.rewriter.rewrite(question)
            latency["rewrite"] = self._ms(stage_started)
            if candidate:  # non-empty validated rewrite; else fallback (FR-017)
                query = candidate
                rewritten = candidate

        # Stage: strategy retrieval.
        vector_results: list[RetrievalResult] = []
        bm25_results: list[RetrievalResult] = []
        if self._needs_fusion(chosen):
            self._available_vector()
            self._available_bm25()
            run_stages.update({"vector", "embed", "bm25", "fuse"})
            stage_started = time.perf_counter()
            vector_results, bm25_results = self.hybrid.pools(
                query,
                vector_top_k=self.stage_top_k["vector"],
                bm25_top_k=self.stage_top_k["bm25"],
            )
            pool_ms = self._ms(stage_started)
            latency["bm25"] = self.hybrid.last_timings.get("bm25", pool_ms)
            self._record_vector_timing(latency, self.hybrid.last_timings.get("vector", pool_ms))
        elif chosen == "vector":
            self._available_vector()
            run_stages.update({"vector", "embed"})
            stage_started = time.perf_counter()
            vector_results = self.vector_retriever.retrieve(
                RetrievalQuery(question=query, top_k=self.stage_top_k["vector"])
            )
            self._record_vector_timing(latency, self._ms(stage_started))
            vector_results = [r.model_copy(update={"vector_rank": r.rank}) for r in vector_results]
        else:  # bm25
            self._available_bm25()
            run_stages.add("bm25")
            stage_started = time.perf_counter()
            bm25_results = self.bm25_retriever.retrieve(
                RetrievalQuery(question=query, top_k=self.stage_top_k["bm25"])
            )
            latency["bm25"] = self._ms(stage_started)
            bm25_results = [r.model_copy(update={"bm25_rank": r.rank}) for r in bm25_results]

        # Stage: metadata filtering (restriction only, never reordering).
        # Application is generic over keys; wired in US4 (T027).
        run_stages.add("filter")
        stage_started = time.perf_counter()
        if active_filters:
            from retrieval.filters import apply_filters

            vector_results = apply_filters(vector_results, active_filters)
            bm25_results = apply_filters(bm25_results, active_filters)
        latency["filter"] = self._ms(stage_started)

        # Stage: fusion (rank-based only — Principle XXV), bounded by the
        # hybrid stage depth (fused candidate pool).
        if self._needs_fusion(chosen):
            stage_started = time.perf_counter()
            results = rrf_fuse([vector_results, bm25_results], k=self.fusion_k)
            results = results[: self.stage_top_k["hybrid"]]
            latency["fuse"] = self._ms(stage_started)
        else:
            results = vector_results if self._needs_vector(chosen) else bm25_results

        # Stage: optional reranking, bounded by the configured candidate pool
        # (FR-012/FR-014: nothing outside the pool can appear).
        if self._rerank_stage_runs(chosen):
            run_stages.add("rerank")
            stage_started = time.perf_counter()
            pool = results[: self.rerank_candidate_k]
            results = self.reranker.rerank(query, pool)
            latency["rerank"] = self._ms(stage_started)

        # Final slicing + uniform provenance (FR-009). When the rerank stage
        # ran, reranking.final_k is the output depth (config contract §1).
        if top_k is not None:
            final_k = top_k
        elif "rerank" in run_stages:
            final_k = self.rerank_final_k
        else:
            final_k = self.stage_top_k["final"]
        results = results[:final_k]
        for rank, result in enumerate(results, start=1):
            results[rank - 1] = result.model_copy(update={"rank": rank, "retrieval_method": chosen})

        stages_skipped = [s for s in ALL_STAGES if s not in run_stages]
        latency["total"] = self._ms(started)

        return RetrievalDebug(
            query=question,
            rewritten_query=rewritten,
            strategy=chosen,
            filters=active_filters,
            results=results,
            latency_ms=latency,
            stages_skipped=stages_skipped,
        )


def build_controller(
    *,
    strategy: str | None = None,
    filters: dict[str, Any] | None = None,
    reranking_enabled: bool | None = None,
    rewriting_enabled: bool | None = None,
) -> RetrievalController:
    """Wire a controller from configuration.

    The embedding model is only loaded when the strategy actually needs
    vector search — a bm25-only run stays ML-free.
    """
    from config import settings
    from retrieval.bm25 import BM25Retriever, build_bm25_index

    chosen = strategy or settings.retrieval_strategy
    if chosen not in RETRIEVAL_STRATEGIES:
        raise ValueError(
            f"retrieval strategy must be one of {', '.join(RETRIEVAL_STRATEGIES)}, got {chosen!r}"
        )

    bm25_retriever = BM25Retriever(build_bm25_index())

    vector_retriever = None
    if chosen != "bm25":
        from embeddings.embedder import Embedder
        from retrieval.retriever import Retriever
        from retrieval.vector_store import VectorStore

        embedder = Embedder(
            provider=settings.embedding_provider,
            model=settings.embedding_model,
        )
        store = VectorStore(
            persist_directory=settings.vector_db_path,
            collection_name=settings.collection,
            dimension=embedder.dimension(),
        )
        vector_retriever = Retriever(store, embedder)

    rerank_on = settings.rerank_enabled if reranking_enabled is None else reranking_enabled
    rewrite_on = settings.query_rewrite_enabled if rewriting_enabled is None else rewriting_enabled

    reranker = None
    if rerank_on and chosen == "hybrid_reranked":
        from retrieval.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker(model=settings.rerank_model)

    rewriter = None
    if rewrite_on:
        from retrieval.query_rewriter import QueryRewriter

        rewriter = QueryRewriter.from_settings(settings)

    return RetrievalController(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        strategy=chosen,
        stage_top_k={
            "vector": settings.stage_top_k_vector,
            "bm25": settings.stage_top_k_bm25,
            "hybrid": settings.stage_top_k_hybrid,
            "final": settings.stage_top_k_final,
        },
        fusion_k=settings.fusion_k,
        filters=dict(settings.retrieval_filters if filters is None else filters),
        reranker=reranker,
        reranking_enabled=rerank_on,
        rerank_candidate_k=settings.rerank_candidate_k,
        rerank_final_k=settings.rerank_final_k,
        rewriter=rewriter,
        rewriting_enabled=rewrite_on,
    )
