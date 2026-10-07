"""Evidence-sufficiency decision (FR-010/FR-011, research R3).

Layered, explainable, first-match-wins (data-model.md decision order):
NO_EVIDENCE -> BELOW_MIN_COUNT -> BELOW_THRESHOLD ->
MODEL_REPORTS_INSUFFICIENT -> SUFFICIENT

Layers 1-2 are deterministic config checks with zero LLM involvement;
layer 3 lets the model's structured sufficient_evidence flag override.
No semantic-entailment model (plan Section 11 defers it).
"""

from config import settings
from domain import Evidence, EvidenceSufficiencyDecision, GroundedAnswer


def decide(
    evidence: list[Evidence],
    model_answer: GroundedAnswer | None = None,
) -> EvidenceSufficiencyDecision:
    """Decide whether the retrieved evidence is sufficient to answer.

    Args:
        evidence: Evidence retrieved for this question.
        model_answer: the structured answer, if generation ran; its
            sufficient_evidence flag is layer 3 of the decision.

    Returns:
        An explainable EvidenceSufficiencyDecision.
    """
    count = len(evidence)
    mean_score = sum(e.retrieval_score for e in evidence) / count if count else None

    if count == 0:
        return EvidenceSufficiencyDecision(
            sufficient=False,
            reason="NO_EVIDENCE",
            evidence_count=0,
            mean_score=None,
        )

    if count < settings.min_evidence:
        return EvidenceSufficiencyDecision(
            sufficient=False,
            reason="BELOW_MIN_COUNT",
            evidence_count=count,
            mean_score=mean_score,
        )

    if mean_score is not None and mean_score < settings.sufficiency_threshold:
        return EvidenceSufficiencyDecision(
            sufficient=False,
            reason="BELOW_THRESHOLD",
            evidence_count=count,
            mean_score=mean_score,
        )

    if model_answer is not None and not model_answer.sufficient_evidence:
        return EvidenceSufficiencyDecision(
            sufficient=False,
            reason="MODEL_REPORTS_INSUFFICIENT",
            evidence_count=count,
            mean_score=mean_score,
        )

    return EvidenceSufficiencyDecision(
        sufficient=True,
        reason="SUFFICIENT",
        evidence_count=count,
        mean_score=mean_score,
    )
