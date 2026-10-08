"""Reciprocal Rank Fusion — the only way hybrid results are combined.

FR-005/FR-006, research R2, Principle XXV (NON-NEGOTIABLE):
rank-based only (never raw-score averaging), deterministic (stable
first-seen tie-break), duplicates merged once with every contributing
rank preserved as provenance.
"""

from __future__ import annotations

from collections.abc import Sequence

from domain import RetrievalResult

DEFAULT_K = 60


def rrf_fuse(
    result_lists: Sequence[Sequence[RetrievalResult]],
    k: int = DEFAULT_K,
) -> list[RetrievalResult]:
    """Fuse ranked result lists by RRF(d) = Σ 1/(k + rank_i(d)).

    Args:
        result_lists: ranked lists; each result's own `rank` field is its
            contribution rank (after filtering, ranks keep their original
            stage meaning); an empty list means that system found nothing.
        k: RRF constant (config `retrieval.fusion.k`, default 60).

    Returns:
        New RetrievalResults sorted by descending RRF score with dense
        1-based ranks; `score == rrf_score`. Inputs are never mutated.
    """
    if k < 1:
        raise ValueError(f"RRF k must be >= 1, got {k}")

    winners: dict[str, RetrievalResult] = {}
    scores: dict[str, float] = {}
    first_seen: list[str] = []

    for results in result_lists:
        for result in results:
            chunk_id = result.chunk.chunk_id
            if chunk_id not in winners:
                winners[chunk_id] = result
                first_seen.append(chunk_id)
            else:
                # Merge provenance from the losing copy into the winner
                # (FR-006: duplicates appear once, both ranks visible).
                winner = winners[chunk_id]
                updates = {}
                if winner.vector_rank is None and result.vector_rank is not None:
                    updates["vector_rank"] = result.vector_rank
                if winner.bm25_rank is None and result.bm25_rank is not None:
                    updates["bm25_rank"] = result.bm25_rank
                if updates:
                    winner = winner.model_copy(update=updates)
                winners[chunk_id] = winner
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + result.rank)

    fused = [
        winners[cid].model_copy(update={"score": scores[cid], "rrf_score": scores[cid]})
        for cid in first_seen
    ]
    # Stable sort: equal RRF scores keep first-seen order (documented rule).
    fused.sort(key=lambda r: -(r.rrf_score or 0.0))
    for rank, result in enumerate(fused, start=1):
        result.rank = rank
    return fused
