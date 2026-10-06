"""Real sentence-transformers embedding provider (FR-001, constitution XV).

Primary API (plan.md / research.md):
    embed(text) -> np.ndarray            # single string
    embed_batch(texts) -> list[np.ndarray]
    dimension() -> int

Backward-compat aliases (Level 0 regression): embed_query == embed,
embed_documents == embed_batch. The hash-based fallback is gone from the
production path (constitution XV): if the model is unavailable we raise a
clear, actionable error (spec Edge Case).
"""


import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


class EmbedderError(RuntimeError):
    """Embedding model failed to load or embed (spec Edge Case)."""


class Embedder:
    """Embedding protocol isolated behind an application interface."""

    def __init__(
        self,
        provider: str = "local-sentence-transformers",
        model: str = DEFAULT_MODEL,
    ):
        self.provider = provider
        self.model_name = model
        self._dimension: int | None = None
        self._model: SentenceTransformer | None = None

        if provider == "local-sentence-transformers":
            try:
                self._model = SentenceTransformer(model)
            except Exception as exc:  # network / offline / bad name
                raise EmbedderError(
                    f"Failed to load embedding model '{model}'. Check the model "
                    f"name and network access (HuggingFace). Detail: {exc}"
                ) from exc
        else:
            raise EmbedderError(f"Unsupported embedding provider: {provider}")

    def embed(self, text: str) -> np.ndarray:
        """Embed a single string into a float vector (higher=closer)."""
        if self._model is None:
            raise EmbedderError("Embedding model is not loaded")
        return self._model.encode(text).astype(np.float32)

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        """Embed a batch of strings in one model call."""
        if self._model is None:
            raise EmbedderError("Embedding model is not loaded")
        if not texts:
            return []
        encoded = self._model.encode(texts)
        return [vec.astype(np.float32) for vec in encoded]

    def dimension(self) -> int:
        """Return the embedding vector dimension."""
        if self._dimension is None:
            if self._model is None:
                raise EmbedderError("Embedding model is not loaded")
            getter = getattr(self._model, "get_embedding_dimension", None)
            if getter is None:
                getter = self._model.get_sentence_embedding_dimension
            self._dimension = int(getter() or 0)
        return self._dimension

    # -- Level 0 backward-compatible aliases ---------------------------------
    def embed_documents(self, documents: list[str]) -> list[np.ndarray]:
        return self.embed_batch(documents)

    def embed_query(self, question: str) -> np.ndarray:
        return self.embed(question)