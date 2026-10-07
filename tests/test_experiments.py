"""Deterministic tests for the prompt-strategy experiment harness (T036).

CopyOracle never calls an LLM (FR-022); retrieval is a scripted
ground-truth `evidence_for` so the whole measurement path is reproducible.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain import Evidence, GroundedEvaluationCase


def _evidence(text: str, evidence_id: str, doc: str, chunk: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        document_id=doc,
        chunk_id=chunk,
        title=f"{doc}.md",
        source=f"data/documents/{doc}.md",
        text=text,
        retrieval_score=0.9,
        rank=1,
    )


def _case(case_type: str, id_: str, expected: str, docs: list[str]) -> GroundedEvaluationCase:
    return GroundedEvaluationCase(
        id=id_,
        question=f"question about {id_}",
        case_type=case_type,
        answerable=case_type != "unanswerable",
        expected_answer=expected,
        relevant_documents=docs,
    )


def _oracle():
    from evaluation.experiments import CopyOracle

    return CopyOracle(top_n=2)


def _cases():
    return [
        _case("answerable", "qa", "Radio interference causes packet loss.", ["5g_packet_loss"]),
        _case("unanswerable", "qu", "", []),
        _case(
            "conflict",
            "qc",
            "Speeds vary by network load and location.",
            ["5g_speed", "5g_speed_reporting"],
        ),
    ]


def _evidence_for(case):
    mapping = {
        "qa": [
            _evidence(
                "Radio interference causes packet loss.",
                "EVIDENCE-001",
                "5g_packet_loss",
                "5g_packet_loss#0001",
            )
        ],
        "qu": [],
        "qc": [
            _evidence(
                "Speeds vary by network load and location.",
                "EVIDENCE-002",
                "5g_speed_reporting",
                "5g_speed_reporting#0001",
            ),
            _evidence(
                "Ideal speeds reach up to 1 Gbps.", "EVIDENCE-003", "5g_speed", "5g_speed#0001"
            ),
        ],
    }
    return mapping[case.id]


def test_run_all_strategies_produces_four_complete_reports():
    from evaluation.experiments import AllStrategies, run_all

    results = run_all(_cases(), _evidence_for, judge=None)

    assert tuple(results) == AllStrategies
    for _, run in results.items():
        assert run.report.case_count == 3
        assert run.report.answerable == 1
        assert run.report.unanswerable == 1
        assert run.report.conflict == 1
        assert run.prompt_texts
        assert 0.0 <= run.report.answer_correctness <= 1.0


def test_copy_oracle_abstains_on_no_evidence():
    from evaluation.experiments import CopyOracle

    oracle = CopyOracle()
    grounded = oracle.generate("unknown", [])

    assert grounded.abstained is True
    assert grounded.sufficient_evidence is False
    assert "don't have enough information" in grounded.answer


def test_copy_oracle_answers_verbatim_and_cites_retrieved_chunks():
    from evaluation.experiments import CopyOracle

    oracle = CopyOracle()
    evidence = [
        _evidence(
            "Radio interference causes packet loss.",
            "EVIDENCE-001",
            "5g_packet_loss",
            "5g_packet_loss#0001",
        )
    ]

    grounded = oracle.generate("question", evidence)

    assert grounded.abstained is False
    assert grounded.answer.startswith("Radio interference")
    assert [c.chunk_id for c in grounded.citations] == ["5g_packet_loss#0001"]
    assert grounded.citations[0].evidence_id == "EVIDENCE-001"


def test_run_strategy_maps_conflict_case_with_valid_citations():
    from evaluation.experiments import run_strategy

    run = run_strategy("D", _cases(), _evidence_for, _oracle())

    conflict = [o for o in run.outcomes if o.case.case_type == "conflict"][0]
    assert conflict.citation_validation
    assert all(v.is_valid for v in conflict.citation_validation)
    assert not conflict.abstained


def test_format_run_includes_all_five_measures():
    from evaluation.experiments import format_run, run_strategy

    run = run_strategy("A", _cases(), _evidence_for, _oracle())
    lines = format_run("A", run, "data/evaluation/grounded_answers.jsonl")

    joined = "\n".join(lines)
    assert "### Strategy A" in joined
    assert "correctness=" in joined
    assert "abstention_acc=" in joined
    assert "citation_validity=" in joined
    assert "citation_completeness=" in joined
    assert "groundedness: supported" in joined
    assert "qa:" in joined
    assert "qu:" in joined
    assert "qc:" in joined
