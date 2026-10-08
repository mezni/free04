"""CLI --debug-grounding tests (spec US4, FR-013/FR-014; contracts §3).

Mocks pipeline/LLM only — deterministic, no live calls (FR-022).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli import app

runner = CliRunner()


def _evidence():
    from domain import Evidence

    return Evidence(
        evidence_id="EVIDENCE-001",
        document_id="5g_packet_loss",
        chunk_id="5g_packet_loss-001",
        title="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        text="Radio interference is a leading cause of packet loss.",
        retrieval_score=0.87,
        rank=1,
    )


def _grounding_result(**over):
    from domain import (
        Citation,
        CitationVerdict,
        EvidenceSufficiencyDecision,
        GroundedAnswer,
    )

    evidence = [_evidence()]
    grounded = GroundedAnswer(
        answer="Check the base station cell for RF interference.",
        citations=[Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001")],
    )
    base = {
        "question": "How do I troubleshoot 5G packet loss?",
        "answer": grounded.answer,
        "retrieved_documents": ["5g_packet_loss.md"],
        "retrieval_scores": [0.87],
        "used_context": True,
        "abstention": "",
        "abstained": False,
        "sufficient_evidence": True,
        "evidence_sufficiency": EvidenceSufficiencyDecision(
            sufficient=True, reason="SUFFICIENT", evidence_count=1, mean_score=0.87
        ),
        "evidence": evidence,
        "grounded_answer": grounded,
        "citation_validation": [CitationVerdict(citation=grounded.citations[0], status="VALID")],
        "conflicts": [],
    }
    base.update(over)
    return base


def _retrieval_result():
    from domain import Chunk, RetrievalResult

    chunk = Chunk(
        chunk_id="5g_packet_loss-001",
        content="Radio interference is a leading cause of packet loss.",
        document_id="5g_packet_loss",
        document_name="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        chunk_index=1,
    )
    return RetrievalResult(chunk=chunk, score=0.87, rank=1)


def _run(args, mock):
    with patch("cli.setup_pipeline", MagicMock(return_value=mock)):
        return runner.invoke(app, args)


def test_debug_grounding_prints_full_path():
    """Contract §3: evidence, sufficiency, answer, citations, validation, final."""
    mock = MagicMock()
    mock.retrieve.return_value = [_retrieval_result()]
    mock.run_grounded.return_value = _grounding_result()

    result = _run(["query", "How do I troubleshoot 5G packet loss?", "--debug-grounding"], mock)

    assert result.exit_code == 0, result.output
    assert "Question:" in result.output
    assert "Retrieved Evidence:" in result.output
    assert "EVIDENCE-001 | 5g_packet_loss | 5g_packet_loss-001 | score 0.87" in result.output
    assert "Evidence sufficiency: SUFFICIENT (count=1, mean_score=0.87)" in result.output
    assert "Generated Answer:" in result.output
    assert "Citations:" in result.output
    assert "[5g_packet_loss:5g_packet_loss-001]  (evidence EVIDENCE-001)" in result.output
    assert "Citation Validation:" in result.output
    assert "PASS" in result.output
    assert "Groundedness:" in result.output
    assert "Final Response:" in result.output
    print("✓ --debug-grounding prints the full path")


def test_debug_grounding_insufficient_shows_reason():
    from domain import EvidenceSufficiencyDecision

    mock = MagicMock()
    mock.retrieve.return_value = []
    result_add = _grounding_result()
    result_add["evidence_sufficiency"] = EvidenceSufficiencyDecision(
        sufficient=False, reason="NO_EVIDENCE", evidence_count=0, mean_score=None
    )
    result_add["abstained"] = True
    result_add["answer"] = (
        "I don't have enough information in the knowledge base to answer this question."
    )
    mock.run_grounded.return_value = result_add

    result = _run(["query", "what is the meaning of tea?", "--debug-grounding"], mock)

    assert result.exit_code == 0, result.output
    assert "Evidence sufficiency: INSUFFICIENT (NO_EVIDENCE)" in result.output
    assert "Final Response:" in result.output
    print("✓ insufficient evidence reason shown in debug mode")


def test_debug_grounding_generation_failure_prints_evidence_then_exit_2():
    """Contract §3: on generation failure print Retrieved Evidence, then error, exit 2."""
    mock = MagicMock()
    mock.retrieve.return_value = [_retrieval_result()]
    mock.run_grounded.side_effect = RuntimeError("LLM request timed out after 30s")

    result = _run(["query", "How do I troubleshoot 5G packet loss?", "--debug-grounding"], mock)

    assert result.exit_code == 2
    assert "Retrieved Evidence:" in result.output
    assert "EVIDENCE-001 | 5g_packet_loss" in result.output
    assert "generation backend unavailable" in result.stderr.lower()
    print("✓ generation failure still exposes evidence, exit 2")


def test_debug_grounding_structured_output_error_message():
    from domain import StructuredOutputError

    mock = MagicMock()
    mock.retrieve.return_value = [_retrieval_result()]
    mock.run_grounded.side_effect = StructuredOutputError("output is not valid JSON")

    result = _run(["query", "How do I troubleshoot 5G packet loss?", "--debug-grounding"], mock)

    assert result.exit_code == 2
    assert "structured output invalid" in result.stderr.lower()
    print("✓ structured output error surfaces with distinct message")


def test_debug_retrieval_never_invokes_llm():
    """US4 scenario: --debug-retrieval output is diagnostics-only (FR-007)."""
    mock = MagicMock()
    mock.retrieve.return_value = [_retrieval_result()]
    mock.run.side_effect = AssertionError("debug-retrieval must not call generation")
    mock.run_grounded.side_effect = AssertionError("debug-retrieval must not call generation")

    result = _run(["query", "How do I troubleshoot 5G packet loss?", "--debug-retrieval"], mock)

    assert result.exit_code == 0, result.output
    assert "diagnostics only" in result.output
    mock.run.assert_not_called()
    mock.run_grounded.assert_not_called()
    print("✓ --debug-retrieval never invokes the LLM")


def test_debug_grounding_conflicts_block_renders():
    """Conflicts rendered as a block, never merged (FR-019, Principle XXIII)."""
    from domain import Citation, ConflictNote

    note = ConflictNote(
        description="One guide says reboot the modem; another requires a technician visit.",
        positions=[
            Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss-001"),
            Citation(document_id="handover", chunk_id="handover-007"),
        ],
    )
    mock = MagicMock()
    mock.retrieve.return_value = [_retrieval_result()]
    mock.run_grounded.return_value = _grounding_result(conflicts=[note])

    result = _run(["query", "How do I troubleshoot 5G packet loss?", "--debug-grounding"], mock)

    assert result.exit_code == 0, result.output
    assert "Conflicts:" in result.output
    assert "(none)" not in result.output.split("Conflicts:")[1].split("\n\n")[0]
    assert "reboot the modem" in result.output
    print("✓ conflicts block rendered in debug output")


def _grounded_outcome_case():
    from domain import GroundedEvaluationCase

    return GroundedEvaluationCase(
        id="packet_loss_steps",
        question="How do I fix packet loss on my 5G connection?",
        answerable=True,
        case_type="answerable",
        expected_answer="Restart the affected base station and check for radio interference.",
        relevant_documents=["5g_packet_loss"],
        relevant_chunks=["5g_packet_loss#0001"],
    )


def _fake_pipeline_outcome():
    """Duck-typed pipeline returning a grounded result without any LLM."""
    from domain import Citation, CitationVerdict

    pipeline = MagicMock()
    validation = [
        CitationVerdict(
            citation=Citation(document_id="5g_packet_loss", chunk_id="5g_packet_loss#0001"),
            status="VALID",
        )
    ]
    result = _grounding_result()
    result["citation_validation"] = validation
    result["answer"] = "Restart the affected base station."
    result["evidence"] = [
        _evidence(),
    ]
    pipeline.run_grounded.return_value = result
    return pipeline


def test_evaluate_answers_cli_prints_answer_layer():
    """evaluate_answers_cli prints §4 without retrieval merge (Principle XXII)."""
    import io
    from contextlib import redirect_stdout
    from unittest.mock import patch

    from cli import evaluate_answers_cli

    buf = io.StringIO()
    with redirect_stdout(buf), patch("cli.setup_pipeline"):
        rc = evaluate_answers_cli(
            [_grounded_outcome_case()],
            _fake_pipeline_outcome(),
            judge=None,
            top_k=4,
            path="data/evaluation/grounded_answers.jsonl",
        )
    assert rc == 0, buf.getvalue()
    out = buf.getvalue()
    assert "(dataset: data/evaluation/grounded_answers.jsonl)" in out
    assert (
        "Answer Evaluation: 1 cases (answerable 1 / unanswerable 0 / partial 0 / conflict 0)" in out
    )
    assert "Answer correctness:" in out
    assert "Groundedness:" in out
    assert "Per-case: packet_loss_steps" in out
    assert "Retrieval" not in out
    print("✓ answer layer CLI prints §4 report without mixing retrieval metrics")


def _runner_invoke(args, patched_pipeline):
    with patch("cli.setup_pipeline", MagicMock(return_value=patched_pipeline)):
        return runner.invoke(app, args)


def test_evaluate_routes_grounded_dataset_to_answer_layer():
    """`evaluate --dataset data/evaluation/grounded_answers.jsonl` runs the answer layer."""
    from pathlib import Path

    pipeline = _fake_pipeline_outcome()
    pipeline.llm_client.generate_json.return_value = (
        '{"claim": "stub", "status": "SUPPORTED", "supporting_evidence_ids": []}'
    )
    dataset_path = str(
        Path(__file__).parent.parent / "data" / "evaluation" / "grounded_answers.jsonl"
    )
    result = _runner_invoke(["evaluate", "--dataset", dataset_path, "--k", "2"], pipeline)
    assert result.exit_code == 0, result.output
    assert "Answer Evaluation: 4 cases" in result.output
    assert "(answerable 1 / unanswerable 1 / partial 1 / conflict 1)" in result.output
    assert "Groundedness:" in result.output


def test_evaluate_answers_flag_defaults_to_grounded_dataset():
    """`evaluate --answers` with no path loads grounded_answers.jsonl (V13 quickstart).

    Regression: the bare --answers route once resolved to
    settings.eval_dataset_path (the retrieval dataset) and crashed
    GroundedEvaluationCase validation.
    """
    pipeline = _fake_pipeline_outcome()
    pipeline.llm_client.generate_json.return_value = (
        '{"claim": "stub", "status": "SUPPORTED", "supporting_evidence_ids": []}'
    )
    result = _runner_invoke(["evaluate", "--answers", "--k", "2"], pipeline)
    assert result.exit_code == 0, result.output
    assert "Answer Evaluation: 4 cases" in result.output
    assert "Retrieval Evaluation" not in result.output
    print("✓ evaluate --answers defaults to the grounded dataset")
