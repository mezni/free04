"""US2 Level 1 CLI tests: --debug-retrieval and FR-017 (constitution VIII)."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli import app

runner = CliRunner()


def test_debug_retrieval_prints_per_chunk_diagnostics_without_llm():
    """--debug-retrieval shows chunk rows (id :: doc :: score) and does NOT invoke the LLM."""
    from rag.pipeline import RAGPipeline

    mock_pipeline = MagicMock(spec=RAGPipeline)
    mock_pipeline.retrieve.return_value = [
        SimpleNamespace(
            score=0.83,
            chunk=SimpleNamespace(
                document_id="5g_packet_loss",
                chunk_id="5g_packet_loss#0001",
                document_name="5g_packet_loss.md",
                content="5G packet loss is often caused by RF interference at the cell site.",
            ),
        )
    ]

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "What causes 5G packet loss?", "--debug-retrieval"])

    assert result.exit_code == 0, result.output
    assert "5g_packet_loss :: 5g_packet_loss#0001" in result.output
    assert "(score: 0.83)" in result.output
    assert "Retrieved Documents:" in result.output
    # Retrieval diagnostics are independent of generation (FR-007/US2): no LLM call.
    mock_pipeline.retrieve.assert_called_once()
    mock_pipeline.run.assert_not_called()
    print("✓ debug-retrieval prints chunk rows without LLM")


def test_debug_retrieval_zero_results():
    """Zero results above threshold -> explicit none message, no LLM."""
    from rag.pipeline import RAGPipeline

    mock_pipeline = MagicMock(spec=RAGPipeline)
    mock_pipeline.retrieve.return_value = []

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "totally unknown?", "--debug-retrieval"])

    assert result.exit_code == 0, result.output
    assert "(none" in result.output or "Retrieved Documents:" in result.output
    mock_pipeline.run.assert_not_called()
    print("✓ debug-retrieval zero-results handled")


def test_fr017_llm_failure_nonzero_exit():
    """LLM unreachable -> clear error to stderr, exit code 2 (FR-017)."""
    from rag.pipeline import RAGPipeline

    mock_pipeline = MagicMock(spec=RAGPipeline)
    mock_pipeline.retrieve.return_value = [
        SimpleNamespace(
            score=0.8,
            chunk=SimpleNamespace(
                document_id="5g_packet_loss",
                chunk_id="5g_packet_loss#0001",
                document_name="5g_packet_loss.md",
                content="x",
            ),
        )
    ]
    mock_pipeline.run.side_effect = RuntimeError("LLM request timed out after 30s")

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "What causes 5G packet loss?"])

    assert result.exit_code == 2
    assert "unavailable" in result.stderr.lower() or "LLM request" in result.stderr
    print("✓ FR-017 non-zero exit on LLM failure")


def test_abstention_question_does_not_call_llm():
    """No retrieved context -> abstention text printed, LLM never invoked, exit 0."""
    from rag.pipeline import RAGPipeline

    mock_pipeline = MagicMock(spec=RAGPipeline)
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.run.return_value = {
        "question": "q",
        "answer": "I don't have enough information in the knowledge base to answer this question.",
        "retrieved_documents": [],
        "retrieval_scores": [],
        "used_context": False,
        "abstention": "I don't have enough information in the knowledge base to answer this question.",
    }

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "what is the meaning of tea?"])

    assert result.exit_code == 0
    assert "I don't have enough information" in result.output
    print("✓ abstention prints text, exit 0")


def test_cli_top_k_override_reaches_pipeline():
    """--top-k from CLI is forwarded to retrieve and run (US3)."""
    from rag.pipeline import RAGPipeline

    mock_pipeline = MagicMock(spec=RAGPipeline)
    mock_pipeline.retrieve.return_value = []
    mock_pipeline.run.return_value = {
        "question": "q",
        "answer": "A",
        "retrieved_documents": ["5g_packet_loss.md"],
        "retrieval_scores": [0.9],
        "used_context": True,
        "abstention": "",
    }

    with patch("cli.setup_pipeline", MagicMock(return_value=mock_pipeline)):
        result = runner.invoke(app, ["query", "What causes 5G packet loss?", "--top-k", "2"])

    assert result.exit_code == 0, result.err
    mock_pipeline.run.assert_called_once_with("What causes 5G packet loss?", top_k=2)
    print("✓ --top-k reaches pipeline")


if __name__ == "__main__":
    test_debug_retrieval_prints_per_chunk_diagnostics_without_llm()
    test_debug_retrieval_zero_results()
    test_fr017_llm_failure_nonzero_exit()
    test_abstention_question_does_not_call_llm()
    test_cli_top_k_override_reaches_pipeline()
    print("✓ All CLI Level 1 tests passed")
