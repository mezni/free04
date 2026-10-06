"""Deterministic tests for ingestion chunker - must pass before implementation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Document
from ingestion.chunker import chunk_document


def test_chunk_document_basic():
    """Test basic chunking produces chunks with correct properties."""
    doc = Document(
        document_id="testdoc",
        document_name="test.md",
        source="test.md",
        content="This is a test content for chunking purposes with enough text "
                "to be split into multiple chunks across the chunk size boundary.",
    )
    chunks = chunk_document(doc, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"
    # Verify chunk properties
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_id.startswith("testdoc#")
        assert chunk.document_id == "testdoc"
        assert chunk.document_name == "test.md"
        assert chunk.source == "test.md"
        # chunk_index is 1-based and matches chunk_id position
        assert chunk.chunk_index == i + 1
        assert chunk.chunk_id == f"testdoc#{i + 1:04d}"
    print(f"✓ Basic chunking: {len(chunks)} chunks produced")
    print(f"✓ chunk_index preserved: {[c.chunk_index for c in chunks]}")


def test_chunk_document_undersized():
    """Test that undersized documents produce exactly one chunk."""
    doc = Document(
        document_id="short",
        document_name="short.md",
        source="short.md",
        content="Short content",
    )
    chunks = chunk_document(doc, chunk_size=1000, chunk_overlap=100)
    assert len(chunks) == 1, f"Expected 1 chunk for undersized doc, got {len(chunks)}"
    assert chunks[0].content == "Short content"
    print("✓ Undersized document: 1 chunk produced")


def test_chunk_document_chunk_size_overlap_validation():
    """Test that invalid chunk_size/overlap raises ValueError."""
    doc = Document(
        document_id="test",
        document_name="test.md",
        source="test.md",
        content="Some content here",
    )
    # overlap >= chunk_size should fail
    with pytest.raises(ValueError):
        chunk_document(doc, chunk_size=50, chunk_overlap=50)

    # negative chunk_size should fail
    with pytest.raises(ValueError):
        chunk_document(doc, chunk_size=0, chunk_overlap=10)

    # negative overlap should fail
    with pytest.raises(ValueError):
        chunk_document(doc, chunk_size=100, chunk_overlap=-1)
print("✓ Chunker tests passed")