"""Deterministic tests for retriever - must pass before implementation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_retriever_basic():
    """Test basic retrieval operation."""
    from domain import Chunk, RetrievalResult
    from embeddings.embedder import Embedder
    from retrieval.retriever import Retriever
    from retrieval.vector_store import VectorStore

    store = VectorStore(dimension=384)
    chunk = Chunk(
        chunk_id="test#0001",
        content="5G packet loss troubleshooting/5G network issues",
        document_id="test",
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
    )
    store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    retriever = Retriever(vector_store=store, embedder=embedder, top_k=3)

    results = retriever.retrieve("How do I troubleshoot 5G packet loss?")

    assert len(results) > 0, "Expected at least one result"
    assert results[0].chunk.document_name == "5g_packet_loss.md"
    assert results[0].rank == 1
    print("✓ Retriever basic")


def test_retriever_top_k():
    """Test top-k limitation."""
    from domain import Chunk
    from embeddings.embedder import Embedder
    from retrieval.retriever import Retriever
    from retrieval.vector_store import VectorStore

    store = VectorStore(dimension=384)

    for i in range(5):
        chunk = Chunk(
            chunk_id=f"doc{i}#0001",
            content=f"Content about topic {i}",
            document_id=f"doc{i}",
            document_name=f"doc{i}.md",
            source=f"data/documents/doc{i}.md",
        )
        store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    retriever = Retriever(vector_store=store, embedder=embedder, top_k=3)

    results = retriever.retrieve("some question")

    assert len(results) <= 3, f"Expected at most 3 results, got {len(results)}"
    print("✓ Retriever top-k")


def test_retriever_result_types():
    """Test that results are RetrievalResult objects."""
    from domain import Chunk, RetrievalResult
    from embeddings.embedder import Embedder
    from retrieval.retriever import Retriever
    from retrieval.vector_store import VectorStore

    store = VectorStore(dimension=384)
    chunk = Chunk(
        chunk_id="test#0001",
        content="test content",
        document_id="test",
        document_name="test.md",
        source="data/documents/test.md",
    )
    store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    retriever = Retriever(vector_store=store, embedder=embedder, top_k=1)

    results = retriever.retrieve("question")

    assert len(results) == 1
    result = results[0]
    assert hasattr(result, "chunk")
    assert hasattr(result, "score")
    assert hasattr(result, "rank")
    assert isinstance(result.score, float)
    assert result.rank == 1
    print("✓ Retriever result types")


def test_retriever_descending_scores():
    """Test that results are sorted by descending score."""
    from domain import Chunk
    from embeddings.embedder import Embedder
    from retrieval.retriever import Retriever
    from retrieval.vector_store import VectorStore

    store = VectorStore(dimension=384)

    for i in range(3):
        chunk = Chunk(
            chunk_id=f"doc{i}#0001",
            content=f" topic {i} related content here",
            document_id=f"doc{i}",
            document_name=f"doc{i}.md",
            source=f"data/documents/doc{i}.md",
        )
        store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    retriever = Retriever(vector_store=store, embedder=embedder, top_k=3)

    results = retriever.retrieve("question")

    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score, \
            f"Scores should be descending: {results[i].score} < {results[i+1].score}"
    print("✓ Retriever descending scores")


def test_retriever_rank_assignment():
    """Test that ranks are assigned starting from 1."""
    from domain import Chunk
    from embeddings.embedder import Embedder
    from retrieval.retriever import Retriever
    from retrieval.vector_store import VectorStore

    store = VectorStore(dimension=384)

    for i in range(3):
        chunk = Chunk(
            chunk_id=f"doc{i}#0001",
            content=f"content {i}",
            document_id=f"doc{i}",
            document_name=f"doc{i}.md",
            source=f"data/documents/doc{i}.md",
        )
        store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    retriever = Retriever(vector_store=store, embedder=embedder, top_k=3)

    results = retriever.retrieve("question")

    for i, result in enumerate(results):
        assert result.rank == i + 1, f"Expected rank {i+1}, got {result.rank}"
    print("✓ Retriever rank assignment")


if __name__ == "__main__":
    test_retriever_basic()
    test_retriever_top_k()
    test_retriever_result_types()
    test_retriever_descending_scores()
    test_retriever_rank_assignment()
    print("✓ All retriever tests passed")