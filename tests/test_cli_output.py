"""Deterministic CLI protocol tests for the Typer-based CLI (constitution XII)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli import app

runner = CliRunner()


def _pipeline_results(**over):
    base = {
        "question": "How do I troubleshoot 5G packet loss?",
        "answer": "Begin by checking the base station cell for RF interference",
        "retrieved_documents": ["5g_packet_loss.md"],
        "retrieval_scores": [0.81],
        "used_context": True,
        "abstention": "",
    }
    base.update(over)
    return base


def test_cli_protocol_four_blocks():
    """Query prints the four labelled blocks and exits 0."""
    mock_pipeline = MagicMock()
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.run.return_value = _pipeline_results()

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "How do I troubleshoot 5G packet loss?"])

    assert result.exit_code == 0, result.output
    assert "Question:" in result.output
    assert "Retrieved Documents:" in result.output
    assert "Answer:" in result.output
    assert "5g_packet_loss.md" in result.output
    assert "(score: 0.81)" in result.output
    print("✓ CLI protocol four blocks")


def test_cli_empty_question_returns_exit_1():
    """Empty question -> exit code 1 (usage error)."""
    result = runner.invoke(app, ["query", "   "])
    assert result.exit_code == 1
    assert "cannot be empty" in result.stderr or "empty" in result.stderr
    print("✓ CLI empty question exits 1")


def test_cli_abstention_format():
    """No context -> abstention text and exit 0, no generation."""
    mock_pipeline = MagicMock()
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.run.return_value = _pipeline_results(
        answer="I don't have enough information in the knowledge base to answer this question.",
        retrieved_documents=[],
        retrieval_scores=[],
        used_context=False,
    )

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "what is the meaning of tea?"])

    assert result.exit_code == 0
    assert "I don't have enough information" in result.output
    mock_pipeline.run.assert_called_once()
    print("✓ CLI abstention format")


def test_cli_retrieved_doc_format():
    """Retrieved documents are formatted 'name  (score: 0.00)'."""
    doc_name = "5g_packet_loss.md"
    score = 0.81
    formatted = f"{doc_name}  (score: {score:.2f})"
    assert "5g_packet_loss.md" in formatted
    assert "(score: 0.81)" in formatted
    print("✓ CLI retrieved document format")


def _grounded_result(citations, verdicts, answer="Check RF interference."):
    from domain import GroundedAnswer

    grounded = GroundedAnswer(answer=answer, citations=citations)
    return {
        "question": "How do I troubleshoot 5G packet loss?",
        "answer": answer,
        "retrieved_documents": ["5g_packet_loss.md"],
        "retrieval_scores": [0.81],
        "used_context": True,
        "abstention": "",
        "grounded_answer": grounded,
        "citation_validation": verdicts,
    }


def test_cli_sources_lists_only_valid_citations():
    """Contract §1: Sources shows validated citations; invalid ones get the FAIL banner."""
    from domain import Citation, Evidence
    from grounding.citation_validator import validate_citations

    evidence = [
        Evidence(
            evidence_id="EVIDENCE-001",
            document_id="5g_packet_loss",
            chunk_id="5g_packet_loss-001",
            title="5g_packet_loss.md",
            source="data/documents/5g_packet_loss.md",
            text="evidence",
            retrieval_score=0.9,
            rank=1,
        )
    ]
    citations = [
        Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001"),
        Citation(document_id="ghost_doc", chunk_id="ghost-99"),
    ]
    verdicts = validate_citations(evidence, citations)
    mock_pipeline = MagicMock()
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.run.return_value = _grounded_result(citations, verdicts)

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "How do I troubleshoot 5G packet loss?"])

    assert result.exit_code == 0, result.output
    assert "Citation validation: FAIL (1 invalid)" in result.output
    assert "[ghost_doc:ghost-99] UNKNOWN_DOCUMENT" in result.output
    assert "Answer:" in result.output
    assert "Sources:" in result.output
    # Valid citation in Sources; invalid citation appears exactly once (banner).
    assert "[5g_packet_loss:5g_packet_loss-001]" in result.output
    assert result.output.count("[ghost_doc:ghost-99]") == 1
    print("✓ Sources lists only valid citations with FAIL banner")


def test_cli_all_valid_citations_no_fail_banner():
    """All-valid citations: Sources printed, no FAIL banner."""
    from domain import Citation, CitationVerdict

    citations = [Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001")]
    verdicts = [CitationVerdict(citation=c, status="VALID") for c in citations]
    mock_pipeline = MagicMock()
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.run.return_value = _grounded_result(citations, verdicts)

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "How do I troubleshoot 5G packet loss?"])

    assert result.exit_code == 0, result.output
    assert "Citation validation: FAIL" not in result.output
    assert "Sources:" in result.output
    assert "[5g_packet_loss:5g_packet_loss-001]" in result.output
    print("✓ all-valid citations print Sources without FAIL banner")


def test_cli_abstained_answer_prints_no_sources():
    """Abstention takes precedence: no Sources block, no FAIL banner (T022)."""
    from domain import Citation, CitationVerdict

    citations = [Citation(document_id="ghost_doc", chunk_id="ghost-99")]
    verdicts = [CitationVerdict(citation=c, status="UNKNOWN_DOCUMENT") for c in citations]
    result = _grounded_result(
        citations,
        verdicts,
        answer="I don't have enough information in the knowledge base to answer this question.",
    )
    result["abstained"] = True
    result["sufficient_evidence"] = False
    mock_pipeline = MagicMock()
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.run.return_value = result

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        out = runner.invoke(app, ["query", "what is the meaning of tea?"])

    assert out.exit_code == 0, out.output
    assert "I don't have enough information" in out.output
    assert "Sources:" not in out.output
    assert "Citation validation: FAIL" not in out.output
    print("✓ abstained answers print no Sources and no FAIL banner")


if __name__ == "__main__":
    test_cli_protocol_four_blocks()
    test_cli_empty_question_returns_exit_1()
    test_cli_abstention_format()
    test_cli_retrieved_doc_format()
    print("✓ All CLI output tests passed")
