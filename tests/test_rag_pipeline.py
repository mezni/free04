"""Deterministic end-to-end tests for RAG pipeline using mocked clients."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import MagicMock, patch
import pytest

from domain import Document, Chunk, RetrievalResult, Answer
from retrieval.vector_store import VectorStore
from embeddings.embedder import Embedder
from retrieval.retriever import Retriever
from generation.prompt import build_prompt, make_prompt_from_results
from generation.llm import LLMClient
from rag.pipeline import RAGPipeline


def test_pipeline_abstention_no_chunks():
    """Test pipeline abstention when no chunks found."""
    store = VectorStore(dimension=384)
    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    pipeline = RAGPipeline(vector_store=store, embedder=embedder, top_k=4)

    result = pipeline.run("What is the procedure for satellite network handover?")

    assert result["used_context"] is False
    assert "I don't have enough information" in result["answer"]
    assert result["retrieved_documents"] == []
    assert result["retrieval_scores"] == []
    print("✓ Pipeline abstention no chunks")


def test_pipeline_with_mocked_llm():
    """Test pipeline with mocked LLM client."""
    store = VectorStore(dimension=384)

    chunk = Chunk(
        chunk_id="test#0001",
        content="5G packet loss troubleshooting steps",
        document_id="test",
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
    )
    store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    retriever = Retriever(vector_store=store, embedder=embedder, top_k=4)

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(
        text="Begin by checking the base station cell for RF interference",
        used_context=True,
    )

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=embedder,
        retriever=retriever,
        llm_client=mock_llm,
        top_k=4,
    )

    result = pipeline.run("How do I troubleshoot 5G packet loss?")

    assert result["used_context"] is True
    assert result["answer"] == "Begin by checking the base station cell for RF interference"
    assert "5g_packet_loss.md" in result["retrieved_documents"]
    print("✓ Pipeline with mocked LLM")


def test_pipeline_abstention_on_empty_answer():
    """Test pipeline uses abstention when LLM returns empty answer without context."""
    store = VectorStore(dimension=384)

    chunk = Chunk(
        chunk_id="test#0001",
        content="some content",
        document_id="test",
        document_name="test.md",
        source="data/documents/test.md",
    )
    store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(text="", used_context=False)

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=embedder,
        llm_client=mock_llm,
        top_k=4,
    )

    result = pipeline.run("Some question")

    assert result["used_context"] is False
    assert "I don't have enough information" in result["answer"]
    print("✓ Pipeline abstention on empty answer")


def test_pipeline_top_k_limit():
    """Test pipeline respects top-k limit."""
    store = VectorStore(dimension=384)

    for i in range(5):
        chunk = Chunk(
            chunk_id=f"doc{i}#0001",
            content=f"Content {i} about networking",
            document_id=f"doc{i}",
            document_name=f"doc{i}.md",
            source=f"data/documents/doc{i}.md",
        )
        store.add([chunk])

    embedder = Embedder(provider="local-sentence-transformers", model="all-MiniLM-L6-v2")
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(text="Answer", used_context=True)
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=embedder,
        llm_client=mock_llm,
        top_k=3,
    )

    result = pipeline.run("network question")

    assert len(result["retrieved_documents"]) <= 3
    print("✓ Pipeline top-k limit")


if __name__ == "__main__":
    test_pipeline_abstention_no_chunks()
    test_pipeline_with_mocked_llm()
    test_pipeline_abstention_on_empty_answer()
    test_pipeline_top_k_limit()
    print("✓ All pipeline tests passed")