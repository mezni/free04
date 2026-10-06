from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except ImportError:
    _HAS_ST = False


class Embedder:
    """Embedding protocol: embed_documents, embed_query, dimension.

    Level 0 default uses `sentence-transformers` with `all-MiniLM-L6-v2`
    (384-dim). The protocol is provider-agnostic so Level 1+ can swap in
    API-backed providers without touching retrieval code.
    """

    def __init__(self, provider: str = "local-sentence-transformers",
                 model: str = "all-MiniLM-L6-v2"):
        self.provider = provider
        self.model_name = model
        self._dimension = 384 if model == "all-MiniLM-L6-v2" else 384
        self._model = None

        if _HAS_ST and provider == "local-sentence-transformers":
            self._model = SentenceTransformer(model)

    def embed_documents(self, documents: List[str]) -> List[np.ndarray]:
        """Embed a list of document strings."""
        if self._model is not None:
            return self._model.encode(documents).tolist()
        # Fallback: deterministic hash-based embeddings
        return [self._hash_embed(text) for text in documents]

    def embed_query(self, question: str) -> np.ndarray:
        """Embed a single query string."""
        if self._model is not None:
            return self._model.encode([question])[0]
        return self._hash_embed(question)

    def dimension(self) -> int:
        """Return the embedding vector dimension."""
        return self._dimension

    def _hash_embed(self, text: str) -> np.ndarray:
        """Fallback hash-based embedding when sentence-transformers is unavailable."""
        hash_val = hash(text) & 0xFFFFFFFF
        np.random.seed(hash_val % (2 ** 32))
        vec = np.random.rand(self._dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec