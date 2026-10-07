"""Answer-metric tests (spec US5, FR-015/FR-016; contracts/cli-grounded-output.md §4).

Deterministic scoring: correctness via expected-token coverage; abstention
accuracy; citation validity/completeness; groundedness aggregation.
Never invokes an LLM (FR-022).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dataclasses import dataclass

import pytest

from domain import Citation, CitationVerdict, GroundedEvaluationCase, GroundednessVerdict


@dataclass
class Outcome:
    case: GroundedEvaluationCase
    answer: str
    abstained: bool
    citation_validation: list
    grounding_verdicts: list


def _case(case_id: str, case_type: str, answerable: bool, expected: str) -> GroundedEvaluationCase:
    return GroundedEvaluationCase(
        id=case_id,
        question=f"question for {case_id}",
        case_type=case_type,
        answerable=answerable,
        expected_answer=expected,
        relevant_documents=["5g_packet_loss"],
    )


def _verdict(status: str) -> CitationVerdict:
    return CitationVerdict(
        citation=Citation(document_id="5g_packet_loss", chunk_id="c"),
        status=status,
    )


def _gverdict(status: str) -> GroundednessVerdict:
    return GroundednessVerdict(claim="claim", status=status, supporting_evidence_ids=[])


def test_answer_correctness_full_coverage():
    from evaluation.answer_metrics import answer_correctness

    case = _case("a1", "answerable", True, "Check the base station for radio interference")
    assert (
        answer_correctness(
            case, answer="Check the base station for radio interference.", abstained=False
        )
        == 1.0
    )


def test_answer_correctness_missing_expected_tokens():
    from evaluation.answer_metrics import answer_correctness

    case = _case("a2", "answerable", True, "update the modem firmware to the latest version")
    assert answer_correctness(case, answer="restart the modem", abstained=False) < 0.5


def test_answer_correctness_partial_coverage():
    from evaluation.answer_metrics import answer_correctness

    case = _case("a3", "partial", True, "check signal strength and update firmware")
    score = answer_correctness(case, answer="Check the signal strength first.", abstained=False)
    assert 0.0 < score < 1.0


def test_answer_correctness_unanswerable_scores_abstention_exactly():
    from evaluation.answer_metrics import answer_correctness

    case = _case("u1", "unanswerable", False, "")
    assert (
        answer_correctness(case, answer="I don't have enough information.", abstained=True) == 1.0
    )
    assert answer_correctness(case, answer="It is 300 Mbps.", abstained=False) == 0.0


def test_abstention_correctness():
    from evaluation.answer_metrics import abstention_correct

    un = _case("u1", "unanswerable", False, "")
    an = _case("a1", "answerable", True, "x")
    assert abstention_correct(un, abstained=True) == 1
    assert abstention_correct(un, abstained=False) == 0
    assert abstention_correct(an, abstained=False) == 1
    assert abstention_correct(an, abstained=True) == 0


def test_citation_validity_fraction():
    from evaluation.answer_metrics import citation_validity_fraction

    verdicts = [_verdict("VALID"), _verdict("VALID"), _verdict("NOT_RETRIEVED")]
    assert citation_validity_fraction(verdicts) == pytest.approx(2 / 3)


def test_citation_validity_no_citations():
    from evaluation.answer_metrics import citation_validity_fraction

    assert citation_validity_fraction([], abstained=True) == 1.0
    assert citation_validity_fraction([], abstained=False) == 0.0


def test_citation_completeness_requires_valid_citation_on_factual_answer():
    from evaluation.answer_metrics import citation_completeness

    case = _case("a1", "answerable", True, "x")
    assert citation_completeness(case, abstained=False, verdicts=[_verdict("VALID")]) == 1.0
    assert citation_completeness(case, abstained=False, verdicts=[_verdict("NOT_RETRIEVED")]) == 0.0
    assert citation_completeness(case, abstained=False, verdicts=[]) == 0.0
    assert citation_completeness(case, abstained=True, verdicts=[]) == 1.0


def test_evaluate_answers_aggregates_all_five_metrics():
    from evaluation.answer_metrics import evaluate_answers

    cases = [
        Outcome(
            _case("ans", "answerable", True, "check the network"),
            answer="Check the network for congestion.",
            abstained=False,
            citation_validation=[_verdict("VALID")],
            grounding_verdicts=[_gverdict("SUPPORTED")],
        ),
        Outcome(
            _case("uns", "unanswerable", False, ""),
            answer="I don't have enough information.",
            abstained=True,
            citation_validation=[],
            grounding_verdicts=[],
        ),
        Outcome(
            _case("par", "partial", True, "check signal strength and update firmware"),
            answer="Check signal strength.",
            abstained=False,
            citation_validation=[_verdict("VALID"), _verdict("UNKNOWN_DOCUMENT")],
            grounding_verdicts=[_gverdict("PARTIALLY_SUPPORTED")],
        ),
        Outcome(
            _case("con", "conflict", True, "speeds vary by network load"),
            answer="Expected speed varies by network load.",
            abstained=False,
            citation_validation=[_verdict("VALID"), _verdict("VALID")],
            grounding_verdicts=[_gverdict("SUPPORTED"), _gverdict("UNSUPPORTED")],
        ),
    ]

    report = evaluate_answers(cases)

    assert report.case_count == 4
    assert report.answerable == 1
    assert report.unanswerable == 1
    assert report.partial == 1
    assert report.conflict == 1
    assert 0.0 <= report.answer_correctness <= 1.0
    assert 0.0 <= report.abstention_accuracy <= 1.0
    assert 0.0 <= report.citation_validity <= 1.0
    assert 0.0 <= report.citation_completeness <= 1.0
    assert report.groundedness.supported == 2
    assert report.groundedness.partially_supported == 1
    assert report.groundedness.unsupported == 1


def test_report_per_case_matrix_complete():
    from evaluation.answer_metrics import evaluate_answers

    outcomes = [
        Outcome(
            _case("ans", "answerable", True, "check the network"),
            answer="Check the network.",
            abstained=False,
            citation_validation=[_verdict("VALID")],
            grounding_verdicts=[_gverdict("SUPPORTED")],
        ),
        Outcome(
            _case("uns", "unanswerable", False, ""),
            answer="I don't have enough information.",
            abstained=True,
            citation_validation=[],
            grounding_verdicts=[],
        ),
    ]
    report = evaluate_answers(outcomes)

    assert [row.case_id for row in report.per_case] == ["ans", "uns"]
    for row in report.per_case:
        assert row.case_id
        assert row.correct in (0, 1) or 0.0 <= row.correct <= 1.0
        assert row.abstain_ok in (0, 1)
        assert 0 <= row.valid_citations <= row.total_citations or row.total_citations == 0
        assert row.grounded_supported + row.grounded_unsupported + row.grounded_partial == len(
            row.grounding_verdicts
        )


def test_report_lines_partition_retrieval_and_answer():
    from evaluation.answer_metrics import evaluate_answers

    outcomes = [
        Outcome(
            _case("ans", "answerable", True, "check the network"),
            answer="Check the network.",
            abstained=False,
            citation_validation=[_verdict("VALID")],
            grounding_verdicts=[_gverdict("SUPPORTED")],
        ),
    ]
    report = evaluate_answers(outcomes)
    lines = report.lines()

    joined = "\n".join(lines)
    assert (
        "Answer Evaluation: 1 cases (answerable 1 / unanswerable 0 / partial 0 / conflict 0)"
        in joined
    )
    assert "Answer correctness:" in joined
    assert "Abstention accuracy:" in joined
    assert "Citation validity:" in joined
    assert "Citation completeness:" in joined
    assert "Groundedness:" in joined
    assert "Per-case: ans" in joined
    print("✓ two-layer report lines present")
