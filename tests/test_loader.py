"""Deterministic tests for ingestion loader - must pass before implementation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ingestion.loader import discover_documents


def test_discover_documents_with_existing_dir():
    """Test that discover_documents finds the 10 synthetic Telco documents."""
    doc_dir = Path(__file__).parent.parent / "data" / "documents"
    docs = discover_documents(str(doc_dir))
    assert len(docs) == 10, f"Expected 10 documents, got {len(docs)}"
    doc_ids = [d.document_id for d in docs]
    assert "5g_packet_loss" in doc_ids, f"5g_packet_loss not found in {doc_ids}"
    packet_loss = next(d for d in docs if d.document_id == "5g_packet_loss")
    assert packet_loss.document_name == "5g_packet_loss.md"
    assert "5g_packet_loss.md" in packet_loss.source
    assert doc_ids == sorted(doc_ids), "Documents should be sorted alphabetically"
    print(f"✓ Found {len(docs)} documents")


def test_discover_documents_missing_dir():
    """Test that discover_documents fails with clear error for missing directory."""
    with pytest.raises(FileNotFoundError, match="not found"):
        discover_documents("/tmp/nonexistent_directory_xyz")


def test_discover_documents_empty_dir():
    """Test that discover_documents fails with clear error for empty directory."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            discover_documents(tmpdir)


def test_front_matter_parsed_into_document_metadata():
    """US4/T029: YAML front matter becomes Document.metadata, stripped from content."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "doc.md"
        path.write_text(
            "---\ncategory: 5g\ndepartment: network-operations\ncode: 504\n---\n"
            "# Title\n\nBody text.\n",
            encoding="utf-8",
        )
        docs = discover_documents(tmpdir)
        assert len(docs) == 1
        doc = docs[0]
        assert doc.metadata == {"category": "5g", "department": "network-operations", "code": 504}
        assert doc.content.startswith("# Title")
        assert not doc.content.startswith("---")
        print("✓ front matter parsed into metadata and stripped from content")


def test_documents_without_front_matter_keep_metadata_empty():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "plain.md"
        path.write_text("# Just a heading\n\nBody.\n", encoding="utf-8")
        docs = discover_documents(tmpdir)
        assert docs[0].metadata == {}
        assert docs[0].content.startswith("# Just a heading")
        print("✓ no front matter -> empty metadata, content untouched")


print("✓ Loader tests passed")
