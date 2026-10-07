"""Citation validator tests (spec US2, FR-007; research R2;

data-model.md CitationVerdict status mapping).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain import Citation, Evidence


def _ev(
    doc: str = "5g_packet_loss",
    chunk: str | None = None,
    eid: str | None = None,
    rank: int = 1,
    score: float = 0.9,
) -> Evidence:
    return Evidence(
        evidence_id=eid or f"EVIDENCE-{rank:03d}",
        document_id=doc,
        chunk_id=chunk or f"{doc}-001",
        title=f"{doc}.md",
        source=f"data/documents/{doc}.md",
        text="evidence text",
        retrieval_score=score,
        rank=rank,
    )


def test_valid_citation_passes():
    from grounding.citation_validator import validate_citations

    evidence = [_ev()]
    verdicts = validate_citations(
        evidence, [Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001")]
    )
    assert len(verdicts) == 1
    assert verdicts[0].status == "VALID"
    assert verdicts[0].detail == ""
    assert verdicts[0].is_valid is True


def test_unknown_document_rejected():
    from grounding.citation_validator import validate_citations

    verdicts = validate_citations(
        [_ev()], [Citation(document_id="ghost_doc", chunk_id="ghost_doc-001")]
    )
    assert verdicts[0].status == "UNKNOWN_DOCUMENT"
    assert verdicts[0].detail


def test_unknown_chunk_rejected():
    """Chunk exists in evidence but under a different document."""
    from grounding.citation_validator import validate_citations

    evidence = [
        _ev(doc="5g_packet_loss", chunk="5g_packet_loss-001"),
        _ev(doc="handover", chunk="handover-007", rank=2),
    ]
    verdicts = validate_citations(
        evidence, [Citation(document_id="5g_packet_loss", chunk_id="handover-007")]
    )
    assert verdicts[0].status == "UNKNOWN_CHUNK"
    assert verdicts[0].detail


def test_not_retrieved_rejected():
    """Document retrieved, but this chunk was not retrieved for this question."""
    from grounding.citation_validator import validate_citations

    verdicts = validate_citations(
        [_ev(doc="5g_packet_loss", chunk="5g_packet_loss-001")],
        [Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-999")],
    )
    assert verdicts[0].status == "NOT_RETRIEVED"
    assert verdicts[0].detail


def test_not_retrieved_when_no_evidence_at_all():
    from grounding.citation_validator import validate_citations

    verdicts = validate_citations(
        [], [Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001")]
    )
    assert verdicts[0].status == "UNKNOWN_DOCUMENT"


def test_malformed_empty_ids():
    from grounding.citation_validator import validate_citations

    bad = Citation.model_construct(document_id="", chunk_id="  ")
    verdicts = validate_citations([_ev()], [bad])
    assert verdicts[0].status == "MALFORMED"
    assert verdicts[0].detail


def test_malformed_unknown_evidence_id():
    from grounding.citation_validator import validate_citations

    c = Citation(
        document_id="5g_packet_loss", chunk_id="5g_packet_loss-001", evidence_id="EVIDENCE-099"
    )
    verdicts = validate_citations([_ev()], [c])
    assert verdicts[0].status == "MALFORMED"


def test_duplicate_citations_deduplicated():
    from grounding.citation_validator import validate_citations

    c1 = Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001")
    c2 = Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001")
    verdicts = validate_citations([_ev()], [c1, c2])
    assert len(verdicts) == 1
    assert verdicts[0].status == "VALID"


def test_duplicate_invalid_citations_counted_once():
    from grounding.citation_validator import validate_citations

    c = Citation(document_id="ghost", chunk_id="ghost-001")
    verdicts = validate_citations([_ev()], [c, c, c])
    assert len(verdicts) == 1
    assert verdicts[0].status == "UNKNOWN_DOCUMENT"


def test_empty_citation_list_returns_empty():
    from grounding.citation_validator import validate_citations

    assert validate_citations([_ev()], []) == []


def test_mixed_verdicts_preserve_order():
    from grounding.citation_validator import validate_citations

    evidence = [_ev(doc="a", chunk="a-001"), _ev(doc="b", chunk="b-001", rank=2)]
    citations = [
        Citation(document_id="a", chunk_id="a-001"),
        Citation(document_id="ghost", chunk_id="g-001"),
        Citation(document_id="b", chunk_id="b-999"),
    ]
    verdicts = validate_citations(evidence, citations)
    assert [v.status for v in verdicts] == ["VALID", "UNKNOWN_DOCUMENT", "NOT_RETRIEVED"]
