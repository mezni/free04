"""Answer/groundedness metrics (spec US5, FR-015/FR-016; contracts §4).

Deterministic, in-repo scoring with no frameworks (Principle XVI):
- correctness: expected-token coverage for answerable/partial/conflict;
  unanswerable cases score abstention exactly (SC-003).
- abstention accuracy
- citation validity fraction
- citation completeness (factual answers must carry >= 1 valid citation;
  flagged INCOMPLETE_CITATIONS otherwise)
- groundedness aggregation (SUPPORTED / UNSUPPORTED / PARTIALLY_SUPPORTED)

Retrieval and answer metrics MUST stay as separate labeled layers
(Principle XXII) — this module only ever produces the answer layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domain import (
    CitationVerdict,
    GroundedEvaluationCase,
    GroundednessVerdict,
)
from evaluation.groundedness import tokenize

ANSWERABLE_TYPES = ("answerable", "partial", "conflict")


@dataclass
class GroundednessCounts:
    """Aggregated claim verdicts across evaluated cases."""

    supported: int = 0
    unsupported: int = 0
    partially_supported: int = 0

    def add(self, verdict: GroundednessVerdict) -> None:
        if verdict.status == "SUPPORTED":
            self.supported += 1
        elif verdict.status == "UNSUPPORTED":
            self.unsupported += 1
        else:
            self.partially_supported += 1


@dataclass
class PerCaseResult:
    """One row of the per-case answer matrix (contract §4)."""

    case_id: str
    correct: float
    abstain_ok: int
    valid_citations: int
    total_citations: int
    grounding_verdicts: list[GroundednessVerdict] = field(default_factory=list)

    @property
    def grounded_supported(self) -> int:
        return sum(1 for v in self.grounding_verdicts if v.status == "SUPPORTED")

    @property
    def grounded_unsupported(self) -> int:
        return sum(1 for v in self.grounding_verdicts if v.status == "UNSUPPORTED")

    @property
    def grounded_partial(self) -> int:
        return sum(1 for v in self.grounding_verdicts if v.status == "PARTIALLY_SUPPORTED")


@dataclass
class EvaluationOutcome:
    """One case evaluated end-to-end (case + pipeline result-ish projection)."""

    case: GroundedEvaluationCase
    answer: str
    abstained: bool
    citation_validation: list[CitationVerdict]
    grounding_verdicts: list[GroundednessVerdict] = field(default_factory=list)


@dataclass
class AnswerEvaluationReport:
    """The answer evaluation layer (contracts/cli-grounded-output.md §4)."""

    case_count: int
    answerable: int
    unanswerable: int
    partial: int
    conflict: int
    answer_correctness: float
    abstention_accuracy: float
    citation_validity: float
    citation_completeness: float
    groundedness: GroundednessCounts
    per_case: list[PerCaseResult]

    def lines(self) -> list[str]:
        g = self.groundedness
        out = [
            f"Answer Evaluation: {self.case_count} cases "
            f"(answerable {self.answerable} / unanswerable {self.unanswerable} "
            f"/ partial {self.partial} / conflict {self.conflict})",
            f"Answer correctness:   {self.answer_correctness:.2f}",
            f"Abstention accuracy:  {self.abstention_accuracy:.2f}",
            f"Citation validity:    {self.citation_validity:.2f}",
            f"Citation completeness:{self.citation_completeness:.2f}",
            f"Groundedness:         supported {g.supported} / unsupported "
            f"{g.unsupported} / partially {g.partially_supported}",
        ]
        for row in self.per_case:
            out.append(
                f"Per-case: {row.case_id} (correct={row.correct:.1f}, "
                f"abstain={row.abstain_ok}, citations {row.valid_citations}/"
                f"{row.total_citations} valid, grounded "
                f"{row.grounded_supported}/{row.grounded_unsupported}/"
                f"{row.grounded_partial})"
            )
        return out


def answer_correctness(case: GroundedEvaluationCase, answer: str, abstained: bool) -> float:
    """Deterministic answer correctness (0.0-1.0; R4 keyword coverage).

    Unanswerable cases score abstention exactly (SC-003): abstaining is the
    only correct behavior.
    """
    if case.case_type == "unanswerable":
        return 1.0 if abstained else 0.0

    expected = tokenize(case.expected_answer)
    if not expected:
        return 0.0
    got = tokenize(answer)
    return len(expected & got) / len(expected)


def abstention_correct(case: GroundedEvaluationCase, abstained: bool) -> int:
    """1 when abstention matches the case (unanswerable -> abstain)."""
    should_abstain = case.case_type == "unanswerable"
    return 1 if abstained == should_abstain else 0


def citation_validity_fraction(verdicts: list[CitationVerdict], abstained: bool = False) -> float:
    """Fraction of VALID verdicts; vacuous for abstained answers."""
    if not verdicts:
        return 1.0 if abstained else 0.0
    valid = sum(1 for v in verdicts if v.is_valid)
    return valid / len(verdicts)


def citation_completeness(
    case: GroundedEvaluationCase,
    abstained: bool,
    verdicts: list[CitationVerdict],
) -> float:
    """1.0 when abstained or >= 1 VALID citation; else 0.0 (INCOMPLETE)."""
    if abstained:
        return 1.0
    return 1.0 if any(v.is_valid for v in verdicts) else 0.0


def evaluate_answers(outcomes: list[Any]) -> AnswerEvaluationReport:
    """Aggregate per-case answer metrics into the answer-layer report.

    Args:
        outcomes: evaluation outcomes with case / answer / abstained /
            citation_validation / grounding_verdicts attributes.

    Returns:
        An AnswerEvaluationReport (deterministic; no LLM).
    """
    per_case: list[PerCaseResult] = []
    counts = GroundednessCounts()

    for outcome in outcomes:
        case = outcome.case
        verdicts = outcome.citation_validation

        correct = answer_correctness(case, outcome.answer, outcome.abstained)
        abstain_ok = abstention_correct(case, outcome.abstained)
        valid = sum(1 for v in verdicts if v.is_valid)

        row = PerCaseResult(
            case_id=case.id,
            correct=correct,
            abstain_ok=abstain_ok,
            valid_citations=valid,
            total_citations=len(verdicts),
            grounding_verdicts=list(outcome.grounding_verdicts),
        )
        per_case.append(row)
        for verdict in outcome.grounding_verdicts:
            counts.add(verdict)

    n = len(outcomes)
    if n:
        answer_correctness_mean = sum(r.correct for r in per_case) / n
        abstention_mean = sum(r.abstain_ok for r in per_case) / n
        validity_sum = sum(
            citation_validity_fraction(o.citation_validation, abstained=o.abstained)
            for o in outcomes
        )
        completeness_sum = sum(
            citation_completeness(o.case, o.abstained, o.citation_validation) for o in outcomes
        )
    else:
        answer_correctness_mean = 0.0
        abstention_mean = 0.0
        validity_sum = 0.0
        completeness_sum = 0.0

    return AnswerEvaluationReport(
        case_count=n,
        answerable=sum(1 for o in outcomes if o.case.case_type == "answerable"),
        unanswerable=sum(1 for o in outcomes if o.case.case_type == "unanswerable"),
        partial=sum(1 for o in outcomes if o.case.case_type == "partial"),
        conflict=sum(1 for o in outcomes if o.case.case_type == "conflict"),
        answer_correctness=answer_correctness_mean,
        abstention_accuracy=abstention_mean,
        citation_validity=validity_sum / n if n else 0.0,
        citation_completeness=completeness_sum / n if n else 0.0,
        groundedness=counts,
        per_case=per_case,
    )
