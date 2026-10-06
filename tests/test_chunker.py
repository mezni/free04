"""Deterministic tests for ingestion chunker - must pass before implementation."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain import Document, Chunk
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
    print(f"✓ Basic chunking: {len(chunks)} chunks produced")


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
    try:
        chunk_document(doc, chunk_size=50, chunk_overlap=50)
        assert False, "Should have raised ValueError for overlap >= chunk_size"
    except ValueError:
        pass

    # negative chunk_size should fail
    try:
        chunk_document(doc, chunk_size=0, chunk_overlap=10)
        assert False, "Should have raised ValueError for chunk_size <= 0"
    except ValueError:
        pass

    # negative overlap should fail
    try:
        chunk_document(doc, chunk_size=100, chunk_overlap=-1)
        assert False, "Should have raised ValueError for negative overlap"
    except ValueError:
        pass
print("✓ Chunker tests passed")