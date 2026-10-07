"""ChromaDB-backed vector store (FR-002/015/016, constitution XV).

This repository owns all ChromaDB access — no Chroma-specific API leaks
outside src/retrieval/ (FR-015). Embeddings are supplied explicitly by the
Embedder (never ChromaDB's default embedding function).

ChromaDB returns *distances*; scores are converted here as
`score = 1 - distance` so every RetrievalResult.score is a cosine similarity
where higher = more similar (contracts/store-and-retriever.md).
"""

from pathlib import Path

import chromadb
import numpy as np

from domain import Chunk, RetrievalResult


class VectorStore:
    """Persistent local ChromaDB vector store with metadata filtering."""

    def __init__(
        self,
        *,
        persist_directory: str,
        collection_name: str,
        dimension: int | None = None,
        distance_metric: str = "cosine",
    ):
        if dimension is not None and dimension <= 0:
            raise ValueError(f"dimension must be > 0, got {dimension}")

        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.dimension = dimension
        self.distance_metric = distance_metric

        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection: chromadb.Collection | None = None
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        try:
            self._collection = self._client.get_collection(
                name=self.collection_name,
                # Vector DB isolates here (FR-015). Embeddings always supplied
                # explicitly, so we disable the default embedding function.
                embedding_function=None,
            )
        except Exception:
            # Collection does not exist yet — create on demand.
            self._collection = self._client.create_collection(
                name=self.collection_name,
                embedding_function=None,
                metadata={"hnsw:space": self.distance_metric},
            )

    def add(self, chunks: list[Chunk], embeddings: list[np.ndarray]) -> None:
        """Store chunks with their pre-computed embeddings and metadata."""
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must match"
            )

        assert self._collection is not None
        try:
            self._collection.add(
                ids=[c.chunk_id for c in chunks],
                embeddings=[vec.tolist() for vec in embeddings],
                documents=[c.content for c in chunks],
                metadatas=[
                    {
                        "document_id": c.document_id,
                        "document_name": c.document_name,
                        "source": c.source,
                        "chunk_id": c.chunk_id,
                        "chunk_index": c.chunk_index,
                    }
                    for c in chunks
                ],
            )
        except Exception as exc:
            raise RuntimeError(f"ChromaDB add failed: {exc}") from exc

    def reset(self) -> None:
        """Delete and recreate the collection (FR-016: fresh state per ingest)."""
        try:
            self._client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self._collection = self._client.create_collection(
            name=self.collection_name,
            embedding_function=None,
            metadata={"hnsw:space": self.distance_metric},
        )

    def count(self) -> int:
        """Number of stored vectors."""
        assert self._collection is not None
        try:
            return self._collection.count()
        except Exception:
            return 0

    def query(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        metadata_filter: dict | None = None,
    ) -> list[RetrievalResult]:
        """Cosine similarity search; returns results ordered by descending score."""
        assert self._collection is not None
        if self.count() == 0:
            return []

        # ChromaDB raises if n_results exceeds collection size — clamp it.
        k = min(max(top_k, 1), self.count())
        where = metadata_filter or None

        try:
            result = self._collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise RuntimeError(f"ChromaDB query failed: {exc}") from exc

        # Convert distances to scores (higher = more similar).
        results: list[RetrievalResult] = []
        ids: list[str] = list(result.get("ids") or [[]])[0]
        documents: list[str] = list(result.get("documents") or [[]])[0]
        raw_metadatas = list(result.get("metadatas") or [[]])[0]
        distances: list[float] = list(result.get("distances") or [[]])[0]

        for rank, chunk_id in enumerate(ids, start=1):
            meta = dict(raw_metadatas[rank - 1] or {})
            score = float(1.0 - float(distances[rank - 1]))
            content = documents[rank - 1] or ""
            chunk = Chunk(
                chunk_id=chunk_id,
                content=content,
                document_id=str(meta.get("document_id", "") or ""),
                document_name=str(meta.get("document_name", "") or ""),
                source=str(meta.get("source", "") or ""),
                chunk_index=int(str(meta.get("chunk_index", 0))),
                metadata={
                    k: v
                    for k, v in meta.items()
                    if k
                    not in ("document_id", "document_name", "source", "chunk_id", "chunk_index")
                },
            )
            results.append(RetrievalResult(chunk=chunk, score=score, rank=rank))

        return results
