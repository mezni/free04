"""Deterministic end-to-end tests for RAG pipeline using mocked clients."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import MagicMock

import numpy as np

from domain import Answer, Chunk
from generation.llm import LLMClient
from rag.pipeline import RAGPipeline
from retrieval.retriever import Retriever
from retrieval.vector_store import VectorStore

DIM = 4


class FakeEmbedder:
    """Deterministic fake embedder for pipeline tests."""

    def __init__(self, dim=DIM):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        return np.zeros(self.dim, dtype=np.float32)

    def embed_batch(self, texts) -> list:
        return [np.zeros(self.dim, dtype=np.float32) for _ in texts]

    def embed_query(self, question: str) -> np.ndarray:
        return np.zeros(self.dim, dtype=np.float32)

    def embed_documents(self, documents):
        return self.embed_batch(documents)

    def dimension(self) -> int:
        return self.dim


def _chunk(i: int = 0, doc_id: str = "test") -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}#000{i + 1}",
        content=f"5G packet loss troubleshooting steps number {i}",
        document_id=doc_id,
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        chunk_index=i + 1,
    )


def _empty_store(tmp_path):
    return VectorStore(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_pipeline",
        dimension=DIM,
    )


def test_pipeline_abstention_no_chunks(tmp_path):
    """Test pipeline abstention when no chunks found."""
    store = _empty_store(tmp_path)
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        top_k=4,
        llm_client=MagicMock(spec=LLMClient),
    )

    result = pipeline.run("What is the procedure for satellite network handover?")

    assert result["used_context"] is False
    assert "I don't have enough information" in result["answer"]
    assert result["retrieved_documents"] == []
    assert result["retrieval_scores"] == []
    print("✓ Pipeline abstention no chunks")


def test_pipeline_with_mocked_llm(tmp_path):
    """Test pipeline with mocked LLM client."""
    store = _empty_store(tmp_path)
    chunk = _chunk()
    store.add([chunk], [np.ones(DIM, dtype=np.float32)])

    retriever = Retriever(vector_store=store, embedder=FakeEmbedder())

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(
        text="Begin by checking the base station cell for RF interference",
        used_context=True,
    )

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        retriever=retriever,
        llm_client=mock_llm,
        top_k=4,
    )

    result = pipeline.run("How do I troubleshoot 5G packet loss?")

    assert result["used_context"] is True
    assert result["answer"] == "Begin by checking the base station cell for RF interference"
    assert "5g_packet_loss.md" in result["retrieved_documents"]
    print("✓ Pipeline with mocked LLM")


def test_pipeline_abstention_on_empty_answer(tmp_path):
    """Test pipeline uses abstention when LLM returns empty answer without context."""
    store = _empty_store(tmp_path)
    chunk = _chunk()
    store.add([chunk], [np.ones(DIM, dtype=np.float32)])

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(text="", used_context=False)

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=mock_llm,
        top_k=4,
    )

    result = pipeline.run("Some question")

    assert result["used_context"] is False
    assert "I don't have enough information" in result["answer"]
    print("✓ Pipeline abstention on empty answer")


def test_pipeline_top_k_limit(tmp_path):
    """Test pipeline respects top-k limit."""
    store = _empty_store(tmp_path)
    chunks = [_chunk(i=i, doc_id=f"doc{i}") for i in range(5)]
    store.add(chunks, [np.ones(DIM, dtype=np.float32) for _ in chunks])

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = Answer(text="Answer", used_context=True)
    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=mock_llm,
        top_k=3,
    )

    result = pipeline.run("network question")

    assert len(result["retrieved_documents"]) <= 3
    print("✓ Pipeline top-k limit")


def test_pipeline_runtime_error_on_llm_failure_propagates(tmp_path):
    """LLM failures propagate as RuntimeError for FR-017 handling."""
    store = _empty_store(tmp_path)
    chunk = _chunk()
    store.add([chunk], [np.ones(DIM, dtype=np.float32)])

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.side_effect = RuntimeError("LLM request timed out after 30s")

    pipeline = RAGPipeline(
        vector_store=store,
        embedder=FakeEmbedder(),
        llm_client=mock_llm,
        top_k=4,
    )

    import pytest

    with pytest.raises(RuntimeError, match="LLM request"):
        pipeline.run("How do I troubleshoot 5G packet loss?")
    print("✓ Pipeline propagates LLM failure")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_pipeline_abstention_no_chunks(Path(td))
        test_pipeline_with_mocked_llm(Path(td))
        test_pipeline_abstention_on_empty_answer(Path(td))
        test_pipeline_top_k_limit(Path(td))
        test_pipeline_runtime_error_on_llm_failure_propagates(Path(td))
    print("✓ All pipeline tests passed")