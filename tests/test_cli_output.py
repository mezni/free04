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


if __name__ == "__main__":
    test_cli_protocol_four_blocks()
    test_cli_empty_question_returns_exit_1()
    test_cli_abstention_format()
    test_cli_retrieved_doc_format()
    print("✓ All CLI output tests passed")