import numpy as np
from typing import List, Tuple

from telco_rag.domain import Chunk, RetrievalResult


class VectorStore:
    """In-memory numpy vector store with L2-normalized embeddings.

    Stores chunks and provides exact brute-force search via cosine similarity
    (computed as dot product of L2-normalized vectors).
    """

    def __init__(self, dimension: int):
        if dimension <= 0:
            raise ValueError(f"dimension must be > 0, got {dimension}")
        self.dimension = dimension
        self._matrix: np.ndarray | None = None
        self._chunks: List[Chunk] = []
        self._added = False

    def add(self, chunks: List[Chunk]) -> None:
        """Add chunks to the vector store.

        Chunks are L2-normalized and stored in a single (N, dim) float32 matrix.
        """
        if not chunks:
            return

        # Extract embeddings from chunks (we'll use chunk content as proxy
        # for embeddings in this baseline; actual embeddings come from the embedder)
        vectors = np.array([self._hash_to_vector(chunk.content) for chunk in chunks],
                          dtype=np.float32)

        # L2-normalize the vectors
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # avoid div by zero
        vectors = vectors / norms

        if self._matrix is None:
            self._matrix = vectors
            self._chunks = chunks
        else:
            self._matrix = np.vstack([self._matrix, vectors])
            self._chunks.extend(chunks)
        self._added = True

    def search(self, query_vector: np.ndarray, top_k: int) -> List[RetrievalResult]:
        """Search for the top-k most similar chunks to the query vector.

        Uses cosine similarity via dot product (vectors are L2-normalized).
        Returns results ordered by descending score.
        """
        if self._matrix is None:
            return []

        # Normalize query vector
        query = query_vector.astype(np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm > 0:
            query = query / query_norm

        # Compute cosine similarities via dot product
        scores = self._matrix @ query

        # Get top-k indices in descending order
        k = min(top_k, len(self._matrix))
        top_indices = np.argsort(-scores)[:k]

        # Build retrieval results
        results: List[RetrievalResult] = []
        for rank, idx in enumerate(top_indices, start=1):
            chunk = self._chunks[idx]
            score = float(scores[idx])
            results.append(RetrievalResult(chunk=chunk, score=score, rank=rank))

        return results

    def _hash_to_vector(self, text: str) -> np.ndarray:
        """Convert text to a deterministic vector using a simple hash.

        In a real system, this would be the actual embedding from the embedder.
        For the baseline, we use a hash-based approach to produce a deterministic
        vector of the expected dimension.
        """
        # Use a simple hash to generate a deterministic vector
        hash_val = hash(text) & 0xFFFFFFFF
        np.random.seed(hash_val % (2 ** 32))
        vec = np.random.rand(self.dimension).astype(np.float32)

        # L2-normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec