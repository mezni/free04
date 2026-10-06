"""Pydantic model validation (data-model.md, constitution XI)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from pydantic import ValidationError

from domain import Chunk, Document, RetrievalQuery, RetrievalResult


def make_chunk(**overrides):
    fields = dict(
        chunk_id="doc1#0001",
        content="5G packet loss basics",
        document_id="doc1",
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        chunk_index=1,
    )
    fields.update(overrides)
    return Chunk(**fields)


def test_document_requires_non_empty_content():
    with pytest.raises(ValidationError):
        Document(document_id="d", document_name="d.md", source="d.md", content="  \n")
    doc = Document(document_id="d", document_name="d.md", source="d.md", content="ok")
    assert doc.metadata == {}


def test_chunk_preserves_required_init_fields():
    chunk = make_chunk()
    assert chunk.chunk_id == "doc1#0001"
    assert chunk.document_id == "doc1"
    assert chunk.document_name == "5g_packet_loss.md"
    assert chunk.source == "data/documents/5g_packet_loss.md"
    assert chunk.chunk_index == 1
    assert chunk.metadata == {}


def test_chunk_index_defaults_to_zero_for_level0_compat():
    chunk = Chunk(
        chunk_id="doc1#0001",
        content="text",
        document_id="doc1",
        document_name="d.md",
        source="s.md",
    )
    assert chunk.chunk_index == 0


def test_retrieval_query_validation():
    q = RetrievalQuery(question="What causes 5G packet loss?")
    assert q.top_k == 4
    assert q.similarity_threshold == 0.0
    assert q.metadata_filter is None

    with pytest.raises(ValidationError):
        RetrievalQuery(question="   ")
    with pytest.raises(ValidationError):
        RetrievalQuery(question="q", top_k=0)
    with pytest.raises(ValidationError):
        RetrievalQuery(question="q", similarity_threshold=1.5)

    filtered = RetrievalQuery(
        question="q", top_k=3, similarity_threshold=0.1, metadata_filter={"document_id": "doc1"}
    )
    assert filtered.metadata_filter == {"document_id": "doc1"}


def test_retrieval_result_holds_typed_chunk_and_score():
    chunk = make_chunk()
    result = RetrievalResult(chunk=chunk, score=0.85, rank=1)
    assert result.chunk.chunk_id == "doc1#0001"
    assert result.score == 0.85
    assert result.rank == 1
    rank_updated = result.model_copy(update={"rank": 2})
    assert rank_updated.rank == 2


if __name__ == "__main__":
    test_document_requires_non_empty_content()
    test_chunk_preserves_required_init_fields()
    test_chunk_index_defaults_to_zero_for_level0_compat()
    test_retrieval_query_validation()
    test_retrieval_result_holds_typed_chunk_and_score()
    print("✓ Model tests passed")