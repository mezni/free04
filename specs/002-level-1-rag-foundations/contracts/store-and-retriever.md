# Contract: Vector Store & Retriever Interfaces (FR-015)

**Silent goal**: ChromaDB stays behind a repository (`vector_store.py`), and
retrieval policy (top_k, threshold, metadata filter, scoring) stays in the
retriever — no Chroma-specific API leaks outside `src/retrieval/`.

## `VectorStore` (ChromaDB-backed, replaces numpy store)

```py
class VectorStore:
    def __init__(self, *, persist_directory: str, collection_name: str,
                 dimension: int | None = None, distance_metric: str = "cosine"): ...

    def add(self, chunks: list[Chunk], embeddings: list[np.ndarray]) -> None:
        """Store chunks + their pre-computed embeddings (explicit embeddings:
        embedding model is owned by the Embedder, NOT ChromaDB default)."""

    def reset(self) -> None:
        """Delete and recreate the collection (FR-016: fresh state per ingest)."""

    def count(self) -> int:
        """Number of stored vectors (0 if collection absent/empty)."""

    def query(self, query_embedding: np.ndarray, top_k: int,
              metadata_filter: dict | None = None) -> list[RetrievalResult]:
        """Cosine similarity search. Converts Chroma distances to scores
        (`score = 1 - distance`) so `RetrievalResult.score` is higher=better.
        Clamps `top_k` to the current collection size (ChromaDB raises
        otherwise). Applied `metadata_filter` becomes the `where` clause."""
```

**Ownership**: `PersistentClient(path=persist_directory)`; collection created
lazily on first `add`/`reset`. `count() == 0` ⇒ `query` returns `[]` without
error (abstention path). ChromaDB exceptions are caught and re-raised as
`RuntimeError` (exit 2) with the failing operation named.

## `Retriever` (policy layer)

```py
class Retriever:
    def __init__(self, vector_store: VectorStore, embedder: Embedder,
                 top_k: int, similarity_threshold: float): ...

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        """1) embed query 2) vector_store.query(...) 3) sort by score desc
        4) drop results < query.similarity_threshold 5) assign 1-based ranks."""
```

`RetrievalQuery` carries `top_k`/`similarity_threshold`/`metadata_filter`
(see data-model). Default policy values are read from config in `cli.py` /
`pipeline.py`; a concrete `RetrievalQuery` always carries resolved values.

## Storage Contract

- Path: `data/chroma/` (config `retrieval.vector_db_path`) — created on first
  ingestion (spec Edge Case: missing dir is auto-created).
- Collection: `telco_documents` (default).
- Stored metadata per vector (FR-003, constitution IX): `document_id`,
  `document_name`, `source`, `chunk_id`, `chunk_index`.
- Embeddings: float vector per chunk as produced by `Embedder.embed_batch`.

## Conversion Rule

Everywhere a `RetrievalResult.score` is consumed, it MUST be a cosine
similarity in `[-1, 1]` where **higher = more similar**. The single distance→
score conversion lives in `VectorStore.query`. No other layer interprets
Chroma distances (SC-007 explainability).