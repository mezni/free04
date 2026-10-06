"""Retriever tests using RetrievalQuery (FR-004/006/008, US1, constitution XI)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from domain import Chunk, RetrievalQuery
from retrieval.retriever import Retriever
from retrieval.vector_store import VectorStore

DIM = 4


class _FakeEmbedder:
    """Deterministic embedder: embed returns its argument positions as vector."""

    def embed_query(self, question: str) -> np.ndarray:
        # Simple baggy feature vector so retrieval is deterministic.
        vec = np.zeros(DIM, dtype=np.float32)
        for i, ch in enumerate(question):
            vec[i % DIM] += ord(ch)
        return vec

    def embed(self, question: str) -> np.ndarray:
        return self.embed_query(question)


def _chunk(doc_id: str, content: str) -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}#0001",
        content=content,
        document_id=doc_id,
        document_name=f"{doc_id}.md",
        source=f"data/documents/{doc_id}.md",
        chunk_index=1,
    )


def _setup(tmp_path, chunks, dim=DIM):
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma"), collection_name="test_c", dimension=dim
    )
    store.add(
        chunks,
        [np.eye(dim, dtype=np.float32)[i % dim] for i in range(len(chunks))],
    )
    return Retriever(store, _FakeEmbedder())  # top_k/threshold come from query


class _FakeEmbedder2:
    """Embeds query token to a basis vector of the same dimension."""

    def embed_query(self, question: str) -> np.ndarray:
        return np.eye(DIM, dtype=np.float32)[len(question) % DIM]


def _setup_ortho(tmp_path):
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma"), collection_name="test_c", dimension=DIM
    )
    store.add(
        [_chunk("a", "a"), _chunk("b", "b")],
        [np.eye(DIM, dtype=np.float32)[0], np.eye(DIM, dtype=np.float32)[1]],
    )
    return Retriever(store, _FakeEmbedder2())


def test_retrieve_returns_descending_scores(tmp_path):
    r = _setup(tmp_path, [_chunk("a", "a"), _chunk("b", "b")])
    results = r.retrieve(RetrievalQuery(question="aaaa", top_k=2))
    assert len(results) == 2
    assert [res.score for res in results] == sorted(
        (res.score for res in results), reverse=True
    )
    assert [res.rank for res in results] == [1, 2]


def test_top_k_limits_results(tmp_path):
    chunks = [_chunk(f"d{i}", f"content {i}") for i in range(5)]
    r = _setup(tmp_path, chunks)
    results = r.retrieve(RetrievalQuery(question="zzz", top_k=3))
    assert len(results) == 3


def test_similarity_threshold_filters_low_scores(tmp_path):
    r = _setup_ortho(tmp_path)
    # query "aaaa" embeds to e0: chunk a score = 1.0, chunk b score = 0.0.
    # threshold 0.5 should drop the low-score (chunk b) result entirely.
    results = r.retrieve(RetrievalQuery(question="aaaa", top_k=2, similarity_threshold=0.5))
    assert len(results) == 1
    assert results[0].chunk.document_id == "a"
    assert results[0].score >= 0.5


def test_rank_is_1_based(tmp_path):
    chunks = [_chunk(f"d{i}", f"content {i}") for i in range(4)]
    r = _setup(tmp_path, chunks)
    results = r.retrieve(RetrievalQuery(question="zzz", top_k=2))
    assert [res.rank for res in results] == [1, 2]


def test_empty_store_returns_empty(tmp_path):
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma"), collection_name="test_c", dimension=DIM
    )
    r = Retriever(store, _FakeEmbedder())
    assert r.retrieve(RetrievalQuery(question="zzz", top_k=2)) == []


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_retrieve_returns_descending_scores(Path(td))
        test_top_k_limits_results(Path(td))
        test_similarity_threshold_filters_low_scores(Path(td))
        test_rank_is_1_based(Path(td))
        test_empty_store_returns_empty(Path(td))
    print("✓ Retriever tests passed")