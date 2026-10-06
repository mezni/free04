"""Deterministic tests for ingestion loader - must pass before implementation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.loader import discover_documents


def test_discover_documents_with_existing_dir():
    """Test that discover_documents finds the 8 synthetic Telco documents."""
    doc_dir = Path(__file__).parent.parent / "data" / "documents"
    docs = discover_documents(str(doc_dir))
    assert len(docs) == 8, f"Expected 8 documents, got {len(docs)}"
    doc_ids = [d.document_id for d in docs]
    assert "5g_packet_loss" in doc_ids, f"5g_packet_loss not found in {doc_ids}"
    packet_loss = next(d for d in docs if d.document_id == "5g_packet_loss")
    assert packet_loss.document_name == "5g_packet_loss.md"
    assert "5g_packet_loss.md" in packet_loss.source
    assert doc_ids == sorted(doc_ids), "Documents should be sorted alphabetically"
    print(f"✓ Found {len(docs)} documents")


def test_discover_documents_missing_dir():
    """Test that discover_documents fails with clear error for missing directory."""
    try:
        discover_documents("/tmp/nonexistent_directory_xyz")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        assert "not found" in str(e).lower() or "nonexistent" in str(e).lower()


def test_discover_documents_empty_dir():
    """Test that discover_documents fails with clear error for empty directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            discover_documents(tmpdir)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected
print("✓ Loader tests passed")