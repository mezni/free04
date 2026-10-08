"""Cross-encoder reranking of the fused candidate pool (FR-012…FR-014).

- Lazy model load: the model is fetched on the first rerank() call, so
  strategies that never rerank never pay for it (research R5).
- The scorer is injectable for tests — no model download in CI.
- Only the candidates passed in are scored and returned: the pool bound
  is enforced by the controller (reranking.candidate_k) and this class
  never draws from anywhere else (FR-014).
- `reranker_score` records the raw cross-encoder output; the headline
  `score` becomes that value for hybrid_reranked results
  (contracts/retrieval-result-schema.md §3). Equal scores keep input
  order (stable sort, SC-004).
"""

from __future__ import annotations

from collections.abc import Callable

from domain import RetrievalResult

Scorer = Callable[[str, list[str]], list[float]]


class CrossEncoderReranker:
    """Re-scores a bounded candidate list with a cross-encoder model."""

    def __init__(self, *, model: str, scorer: Scorer | None = None):
        self.model = model
        self._scorer = scorer
        self._cross_encoder = None  # lazy: loaded on first real rerank

    def _load_model(self):
        if self._cross_encoder is None:
            from sentence_transformers import CrossEncoder

            self._cross_encoder = CrossEncoder(self.model)
        return self._cross_encoder

    def _score(self, query: str, texts: list[str]) -> list[float]:
        if self._scorer is not None:
            scores = self._scorer(query, texts)
        else:
            encoder = self._load_model()
            scores = encoder.predict([(query, t) for t in texts])
        if len(scores) != len(texts):
            raise ValueError(
                f"reranker scorer returned {len(scores)} scores for {len(texts)} candidates"
            )
        return [float(s) for s in scores]

    def rerank(self, query: str, candidates: list[RetrievalResult]) -> list[RetrievalResult]:
        """Re-score candidates, return them in descending reranker order."""
        if not candidates:
            return []

        scores = self._score(query, [c.chunk.content for c in candidates])
        rescored = [
            candidate.model_copy(update={"reranker_score": score, "score": score})
            for candidate, score in zip(candidates, scores, strict=True)
        ]
        # Stable sort: equal scores keep the fused input order (SC-004).
        rescored.sort(key=lambda r: -r.score)
        for rank, result in enumerate(rescored, start=1):
            result.rank = rank
        return rescored
