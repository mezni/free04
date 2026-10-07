"""GroundedAnswer structured-output schema tests (spec US1, FR-004;

contracts/grounded-answer-schema.md rules 1-7, data-model.md).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from pydantic import ValidationError

from domain import (
    Citation,
    ConflictNote,
    GroundedAnswer,
    StructuredOutputError,
)


def test_valid_answer_parses():
    answer = GroundedAnswer.model_validate(
        {
            "answer": "Packet loss can occur because of radio interference.",
            "citations": [{"document_id": "5g_packet_loss", "chunk_id": "c-001"}],
            "abstained": False,
            "sufficient_evidence": True,
            "conflicts": [],
        }
    )
    assert answer.answer.startswith("Packet loss")
    assert answer.citations[0].document_id == "5g_packet_loss"
    assert answer.abstained is False
    assert answer.inconsistent_abstention is False
    assert answer.missing_citations is False


def test_defaults_apply_for_optional_fields():
    answer = GroundedAnswer.model_validate({"answer": "text"})
    assert answer.citations == []
    assert answer.abstained is False
    assert answer.sufficient_evidence is True
    assert answer.conflicts == []
    assert answer.missing_citations is True


def test_missing_answer_field_rejected():
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate({"citations": []})


def test_empty_answer_rejected():
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate({"answer": "   "})


def test_extra_field_rejected():
    """Contract rule 7: unknown fields are rejected."""
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate({"answer": "text", "hallucinated_field": 1})


def test_citation_requires_non_empty_ids():
    with pytest.raises(ValidationError):
        GroundedAnswer.model_validate(
            {"answer": "text", "citations": [{"document_id": "", "chunk_id": "c"}]}
        )


def test_abstained_with_citations_is_flagged_not_rejected():
    """Contract rule 4: inconsistent abstention is flagged, not a parse error."""
    answer = GroundedAnswer.model_validate(
        {
            "answer": "Not enough information.",
            "abstained": True,
            "citations": [{"document_id": "d", "chunk_id": "c"}],
        }
    )
    assert answer.inconsistent_abstention is True


def test_conflict_requires_at_least_two_positions():
    with pytest.raises(ValidationError):
        ConflictNote(
            description="docs disagree",
            positions=[Citation(document_id="a", chunk_id="c1")],
        )
    note = ConflictNote(
        description="docs disagree",
        positions=[
            Citation(document_id="a", chunk_id="c1"),
            Citation(document_id="b", chunk_id="c2"),
        ],
    )
    assert len(note.positions) == 2


def test_malformed_provider_json_raises_structured_output_error():
    """Contract rule 1: malformed output detected, never silently accepted."""
    from generation.generator import parse_grounded_answer

    with pytest.raises(StructuredOutputError):
        parse_grounded_answer("Sorry, here is what I think: 5G is fast.")


def test_structurally_invalid_json_raises_structured_output_error():
    from generation.generator import parse_grounded_answer

    with pytest.raises(StructuredOutputError):
        parse_grounded_answer('{"result": "answer without schema"}')


def test_valid_json_string_parses_to_grounded_answer():
    from generation.generator import parse_grounded_answer

    payload = (
        '{"answer": "Radio interference causes packet loss.",'
        ' "citations": [{"document_id": "d", "chunk_id": "c"}],'
        ' "abstained": false, "sufficient_evidence": true, "conflicts": []}'
    )
    answer = parse_grounded_answer(payload)
    assert isinstance(answer, GroundedAnswer)
    assert answer.answer == "Radio interference causes packet loss."
