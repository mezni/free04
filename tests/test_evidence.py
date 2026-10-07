"""Evidence builder tests (spec US1, FR-001/FR-002, data-model.md)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from pydantic import ValidationError

from domain import Chunk, Evidence, RetrievalResult


def _result(i: int = 0, doc_id: str = "5g_packet_loss") -> RetrievalResult:
    chunk = Chunk(
        chunk_id=f"{doc_id}-{i + 1:03d}",
        content=f"Packet loss evidence number {i}",
        document_id=doc_id,
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        chunk_index=i + 1,
        metadata={},
    )
    return RetrievalResult(chunk=chunk, score=0.87 - i * 0.1, rank=i + 1)


def test_evidence_builder_empty_input():
    from grounding.evidence_builder import build_evidence

    assert build_evidence([]) == []


def test_evidence_builder_preserves_identity_and_score():
    from grounding.evidence_builder import build_evidence

    results = [_result(0), _result(1)]
    evidence = build_evidence(results)

    assert len(evidence) == 2
    first = evidence[0]
    assert first.document_id == "5g_packet_loss"
    assert first.chunk_id == "5g_packet_loss-001"
    assert first.title == "5g_packet_loss.md"
    assert first.source == "data/documents/5g_packet_loss.md"
    assert first.text == "Packet loss evidence number 0"
    assert first.retrieval_score == pytest.approx(0.87)
    assert first.rank == 1


def test_evidence_ids_stable_and_ordered():
    from grounding.evidence_builder import build_evidence

    evidence = build_evidence([_result(0), _result(1), _result(2)])
    assert [e.evidence_id for e in evidence] == [
        "EVIDENCE-001",
        "EVIDENCE-002",
        "EVIDENCE-003",
    ]


def test_evidence_ids_unique_across_runs():
    from grounding.evidence_builder import build_evidence

    run_a = build_evidence([_result(0), _result(1)])
    run_b = build_evidence([_result(0), _result(1)])
    assert [e.evidence_id for e in run_a] == [e.evidence_id for e in run_b]
    assert len({e.evidence_id for e in run_a}) == 2


def test_evidence_metadata_preserved():
    from grounding.evidence_builder import build_evidence

    chunk = Chunk(
        chunk_id="c1",
        content="text",
        document_id="d1",
        document_name="d.md",
        source="data/documents/d.md",
        chunk_index=1,
        metadata={"tenant": "internal"},
    )
    evidence = build_evidence([RetrievalResult(chunk=chunk, score=0.5, rank=1)])
    assert evidence[0].metadata == {"tenant": "internal"}


def test_evidence_model_validators():
    with pytest.raises(ValidationError):
        Evidence(
            evidence_id="EVIDENCE-001",
            document_id="",
            chunk_id="c",
            title="t",
            source="s",
            text="x",
            retrieval_score=0.5,
        )
    with pytest.raises(ValidationError):
        Evidence(
            evidence_id="EVIDENCE-001",
            document_id="d",
            chunk_id="c",
            title="t",
            source="s",
            text="x",
            retrieval_score=1.5,
        )
    with pytest.raises(ValidationError):
        Evidence(
            evidence_id="EVIDENCE-001",
            document_id="d",
            chunk_id="c",
            title="t",
            source="s",
            text="   ",
            retrieval_score=0.5,
        )
