"""ChromaDB-backed VectorStore tests (FR-002/015/016, US1, constitution XI).

Uses a tmp_path Chroma persistent client so tests do not touch real data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pytest

from domain import Chunk
from retrieval.vector_store import VectorStore

DIM = 4

CHUNK_META = [
    ("doc1", "5g_packet_loss.md", "data/documents/5g_packet_loss.md"),
    ("doc2", "sim_activation.md", "data/documents/sim_activation.md"),
]


def _chunk(i: int) -> Chunk:
    doc_id, name, source = CHUNK_META[i % len(CHUNK_META)]
    return Chunk(
        chunk_id=f"{doc_id}#000{i + 1}",
        content=f"content {i}",
        document_id=doc_id,
        document_name=name,
        source=source,
        chunk_index=i + 1,
    )


def _vectors(chunks):
    # Orthogonal basis vectors so cosine similarities are distinct.
    return [np.eye(DIM, dtype=np.float32)[i % DIM] for i, _ in enumerate(chunks)]


def _ortho_query(dim_index: int) -> np.ndarray:
    return np.eye(DIM, dtype=np.float32)[dim_index]


def _store(tmp_path):
    return VectorStore(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_collection",
        dimension=DIM,
    )


def test_add_and_count(tmp_path):
    store = _store(tmp_path)
    assert store.count() == 0
    store.add([_chunk(0), _chunk(1)], _vectors([_chunk(0), _chunk(1)]))
    assert store.count() == 2


def test_add_then_reopen_persists(tmp_path):
    path = tmp_path / "chroma"
    store = VectorStore(persist_directory=str(path), collection_name="test_c", dimension=DIM)
    store.add([_chunk(0)], _vectors([_chunk(0)]))

    reopened = VectorStore(persist_directory=str(path), collection_name="test_c", dimension=DIM)
    assert reopened.count() == 1  # persistence across restarts (FR-002)


def test_reset_recreates_collection(tmp_path):
    store = _store(tmp_path)
    store.add([_chunk(0)], _vectors([_chunk(0)]))
    assert store.count() == 1
    store.reset()
    assert store.count() == 0
    store.add([_chunk(1)], _vectors([_chunk(1)]))
    assert store.count() == 1  # no stale vectors (FR-016)


def test_query_returns_ranked_results_with_metadata(tmp_path):
    store = _store(tmp_path)
    chunks = [_chunk(0), _chunk(1)]
    store.add(chunks, _vectors(chunks))
    results = store.query(np.eye(DIM, dtype=np.float32)[1], top_k=2)
    assert len(results) == 2
    assert all(r.score >= 0.0 for r in results)
    # chunk1 embeds e1=[0,1,0,0]; query e1 -> score 1.0 (top), chunk0 -> 0.0
    assert results[0].chunk.document_name == "sim_activation.md"
    assert results[0].chunk.document_id == "doc2"
    assert results[1].score < results[0].score  # distance converted to score (higher=better)


def test_query_clamps_top_k_to_collection_size(tmp_path):
    store = _store(tmp_path)
    store.add([_chunk(0)], _vectors([_chunk(0)]))
    results = store.query(np.full(DIM, 1.0, dtype=np.float32), top_k=10)
    assert len(results) == 1  # clamps to collection size, no Chroma error


def test_query_empty_store_returns_empty(tmp_path):
    store = _store(tmp_path)
    assert store.query(np.full(DIM, 1.0, dtype=np.float32), top_k=4) == []


def test_query_metadata_filter(tmp_path):
    store = _store(tmp_path)
    chunks = [_chunk(0), _chunk(1)]
    store.add(chunks, _vectors(chunks))
    results = store.query(
        np.full(DIM, 2.0, dtype=np.float32),
        top_k=2,
        metadata_filter={"document_id": "doc1"},
    )
    assert len(results) == 1
    assert results[0].chunk.document_id == "doc1"


def test_dimension_must_be_positive(tmp_path):
    with pytest.raises(ValueError):
        VectorStore(persist_directory=str(tmp_path), collection_name="test_c", dimension=0)
    with pytest.raises(ValueError):
        VectorStore(persist_directory=str(tmp_path), collection_name="test_c", dimension=-3)


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_add_and_count(Path(td))
        test_query_returns_ranked_results_with_metadata(Path(td))
        test_query_clamps_top_k_to_collection_size(Path(td))
        test_query_empty_store_returns_empty(Path(td))
        test_query_metadata_filter(Path(td))
    print("✓ Vector store (ChromaDB) tests passed")