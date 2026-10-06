"""Deterministic tests for vector store - must pass before implementation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from domain import Chunk
from retrieval.vector_store import VectorStore


def test_vector_store_add_and_search():
    """Test basic add and search operations."""
    store = VectorStore(dimension=384)

    chunk1 = Chunk(
        chunk_id="doc1#0001",
        content="5G packet loss troubleshooting basics",
        document_id="doc1",
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
    )
    chunk2 = Chunk(
        chunk_id="doc2#0001",
        content="SIM activation procedure",
        document_id="doc2",
        document_name="sim_activation.md",
        source="data/documents/sim_activation.md",
    )

    store.add([chunk1, chunk2])

    # Search with a query vector similar to chunk1's content
    query = np.ones(384, dtype=np.float32)
    results = store.search(query, top_k=2)

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert results[0].chunk.document_name == "5g_packet_loss.md"
    assert results[1].chunk.document_name == "sim_activation.md"
    print("✓ Vector store add and search")


def test_vector_store_top_k_limit():
    """Test that top_k limits the number of results."""
    store = VectorStore(dimension=384)

    for i in range(5):
        chunk = Chunk(
            chunk_id=f"doc#{i:04d}",
            content=f"Content {i}",
            document_id=f"doc{i}",
            document_name=f"doc{i}.md",
            source=f"data/documents/doc{i}.md",
        )
        store.add([chunk])

    query = np.ones(384, dtype=np.float32)
    results = store.search(query, top_k=3)

    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    print("✓ Vector store top-k limit")


def test_vector_store_empty():
    """Test searching in empty store."""
    store = VectorStore(dimension=384)
    results = store.search(np.ones(384, dtype=np.float32), top_k=4)
    assert len(results) == 0
    print("✓ Vector store empty search")


def test_vector_store_descending_order():
    """Test that results are ordered by descending score."""
    store = VectorStore(dimension=384)

    # Add chunks with distinct content so hashes produce different vectors
    chunk_long = Chunk(
        chunk_id="doclong#0001",
        content="a" * 1000,
        document_id="doclong",
        document_name="long.md",
        source="data/documents/long.md",
    )
    chunk_short = Chunk(
        chunk_id="docshort#0001",
        content="short",
        document_id="docshort",
        document_name="short.md",
        source="data/documents/short.md",
    )

    store.add([chunk_long, chunk_short])

    query = np.ones(384, dtype=np.float32)
    results = store.search(query, top_k=2)

    assert results[0].score >= results[1].score, "Results should be descending by score"
    print("✓ Vector store descending order")


def test_vector_store_dimension_required():
    """Test that dimension must be > 0."""
    try:
        store = VectorStore(dimension=0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("✓ Vector store dimension validation")


def test_vector_store_single_chunk():
    """Test storing and searching with a single chunk."""
    store = VectorStore(dimension=384)

    chunk = Chunk(
        chunk_id="single#0001",
        content="only chunk",
        document_id="single",
        document_name="single.md",
        source="data/documents/single.md",
    )

    store.add([chunk])

    query = np.ones(384, dtype=np.float32)
    results = store.search(query, top_k=1)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "single#0001"
    print("✓ Vector store single chunk")


if __name__ == "__main__":
    test_vector_store_add_and_search()
    test_vector_store_top_k_limit()
    test_vector_store_empty()
    test_vector_store_descending_order()
    test_vector_store_dimension_required()
    test_vector_store_single_chunk()
    print("✓ All vector store tests passed")