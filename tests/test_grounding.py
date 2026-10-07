"""Groundedness classification tests (spec US5, FR-016; research R4).

Lexical claim-support baseline is deterministic; the LLM judge interface
is tested with fixture judges only (no live calls, FR-022).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Evidence


def _evidence(eid: str, text: str) -> Evidence:
    return Evidence(
        evidence_id=eid,
        document_id="5g_packet_loss",
        chunk_id=f"5g_packet_loss-{eid[-3:]}",
        title="5g_packet_loss.md",
        source="data/documents/5g_packet_loss.md",
        text=text,
        retrieval_score=0.9,
        rank=1,
    )


EVIDENCE_TEXT = (
    "Radio signal interference causes intermittent packet loss on 5G "
    "networks. Check the signal strength and reference signal quality. "
    "Restart the affected base station and update the firmware to the "
    "latest version. Congestion in crowded areas can also cause loss."
)

NOISE_TEXT = "Satellite backhaul is used for remote antenna sites in rural areas."


def test_classify_supported_claim():
    from evaluation.groundedness import classify_claim

    verdict = classify_claim(
        "Radio signal interference causes packet loss.",
        [EVIDENCE_TEXT],
    )
    assert verdict.status == "SUPPORTED"
    assert verdict.supporting_evidence_ids == []  # ids only when provided
    assert verdict.claim


def test_classify_partially_supported_claim():
    from evaluation.groundedness import classify_claim

    verdict = classify_claim(
        "Packet loss indicates network congestion and solar flares.",
        [EVIDENCE_TEXT],
    )
    assert verdict.status == "PARTIALLY_SUPPORTED"


def test_classify_unsupported_claim():
    from evaluation.groundedness import classify_claim

    verdict = classify_claim(
        "Cows produce high quality optical fiber cable.",
        [EVIDENCE_TEXT],
    )
    assert verdict.status == "UNSUPPORTED"
    assert verdict.supporting_evidence_ids == []


def test_classify_supported_requires_passing_evidence_ids():
    from evaluation.groundedness import classify_claim

    verdict = classify_claim(
        "Check the signal strength and restart the base station.",
        [EVIDENCE_TEXT],
        evidence_ids=["EVIDENCE-001"],
    )
    assert verdict.status == "SUPPORTED"
    assert "EVIDENCE-001" in verdict.supporting_evidence_ids


def test_classify_empty_claim_rejected():
    from evaluation.groundedness import classify_claim

    with pytest.raises(ValueError):
        classify_claim("   ", [EVIDENCE_TEXT])


def test_supporting_ids_list_documents_that_contribute():
    from evaluation.groundedness import classify_claim

    verdict = classify_claim(
        "Packet loss is caused by solar flares.",
        [EVIDENCE_TEXT, NOISE_TEXT],
        evidence_ids=["EVIDENCE-001", "EVIDENCE-002"],
    )
    # Only token overlap with EVIDENCE-001 (interference... cause loss).
    assert set(verdict.supporting_evidence_ids) == {"EVIDENCE-001"}


def test_extract_claims_splits_sentences():
    from evaluation.groundedness import extract_claims

    claims = extract_claims("Radio interference causes packet loss. Check the base station!")
    assert len(claims) == 2
    assert "Check the base station" in claims[1]


def test_evaluate_claim_uses_judge_when_provided():
    from domain import GroundednessVerdict
    from evaluation.groundedness import evaluate_claim

    evidence = [_evidence("EVIDENCE-001", EVIDENCE_TEXT)]

    class FakeJudge:
        def judge(self, claim, ev):
            assert ev == evidence
            return GroundednessVerdict(
                claim=claim, status="SUPPORTED", supporting_evidence_ids=["EVIDENCE-001"]
            )

    verdict = evaluate_claim("nonsense claim no evidence", evidence, judge=FakeJudge())
    assert verdict.status == "SUPPORTED"


def test_evaluate_claim_lexical_default_without_judge():
    from evaluation.groundedness import evaluate_claim

    evidence = [_evidence("EVIDENCE-001", EVIDENCE_TEXT)]
    verdict = evaluate_claim("Cows produce optical fiber.", evidence)
    assert verdict.status == "UNSUPPORTED"


def test_groundedness_verdict_model_validation():
    from pydantic import ValidationError

    from domain import GroundednessVerdict

    with pytest.raises(ValidationError):
        GroundednessVerdict(claim="", status="SUPPORTED", supporting_evidence_ids=[])
