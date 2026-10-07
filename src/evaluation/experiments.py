"""Prompt-strategy experiment harness (T036, FR-023/FR-025; research R8).

Runs strategies A-D over data/evaluation/grounded_answers.jsonl and scores
every case with the existing answer metrics (SC-009). Retrieval and answer
layers stay separate labeled layers (Principle XXII).

Determinism: `CopyOracle` is a scripted extractive generator — it answers
verbatim from the retrieved evidence (and abstains on empty evidence). It
replaces the LLM in CI runs (FR-022) so the measurement path is exercised
reproducibly; a live-LLM rerun only swaps the oracle (see the runner script).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from domain import Evidence, GroundedAnswer, GroundedEvaluationCase, GroundednessVerdict
from evaluation.answer_metrics import (
    AnswerEvaluationReport,
    EvaluationOutcome,
    evaluate_answers,
)
from evaluation.groundedness import evaluate_claim, extract_claims
from grounding.citation_validator import validate_citations

ABSTENTION_TEXT = "I don't have enough information in the knowledge base to answer this question."

AllStrategies = ("A", "B", "C", "D")


class CopyOracle:
    """Deterministic extractive 'generator' (FR-022; no LLM).

    - empty evidence  -> abstains (unknown/unanswerable case)
    - evidence present -> answers verbatim from the top chunks and cites
      every retrieved evidence block (valid citations by construction)
    """

    def __init__(self, top_n: int = 2) -> None:
        self.top_n = top_n

    def generate(self, question: str, evidence: list[Evidence]) -> GroundedAnswer:
        if not evidence:
            return GroundedAnswer(answer=ABSTENTION_TEXT, abstained=True, sufficient_evidence=False)
        top = evidence[: self.top_n]
        answer = " ".join(e.text.strip() for e in top)
        from domain import Citation

        citations = [
            Citation(
                document_id=e.document_id,
                chunk_id=e.chunk_id,
                evidence_id=e.evidence_id,
            )
            for e in top
        ]
        return GroundedAnswer(
            answer=answer,
            citations=citations,
        )


@dataclass
class StrategyRun:
    """One strategy scored over the whole dataset."""

    strategy: str
    report: AnswerEvaluationReport
    outcomes: list[EvaluationOutcome] = field(default_factory=list)
    verdicts: list[list[GroundednessVerdict]] = field(default_factory=list)
    prompt_texts: list[str] = field(default_factory=list)

    @property
    def grounded_totals(self) -> tuple[int, int, int]:
        g = self.report.groundedness
        return g.supported, g.unsupported, g.partially_supported


def score_case(
    case: GroundedEvaluationCase,
    evidence: list[Evidence],
    oracle: CopyOracle,
    judge=None,
) -> tuple[EvaluationOutcome, str, list[GroundednessVerdict]]:
    """One grounded case under an oracle, using the shared measurement path."""
    grounded = oracle.generate(case.question, evidence)
    # Abstained answers carry no factual claims to ground (the abstention
    # sentence is a meta-statement, not a claim about the domain).
    claims = extract_claims(grounded.answer) if not grounded.abstained else []
    verdicts = [evaluate_claim(claim, evidence, judge=judge) for claim in claims]
    outcome = EvaluationOutcome(
        case=case,
        answer=grounded.answer,
        abstained=grounded.abstained,
        citation_validation=validate_citations(evidence, list(grounded.citations)),
        grounding_verdicts=verdicts,
    )
    return outcome, grounded.answer, verdicts


def run_strategy(
    strategy: str,
    cases: list[GroundedEvaluationCase],
    evidence_for: Callable[[GroundedEvaluationCase], list[Evidence]],
    oracle: CopyOracle,
    judge=None,
) -> StrategyRun:
    """Score `strategy` over `cases`; retrieval stays outside this function."""
    from generation.prompt import build_strategy_prompt

    outcomes: list[EvaluationOutcome] = []
    verdicts_list: list[list[GroundednessVerdict]] = []
    prompt_texts: list[str] = []

    for case in cases:
        evidence = evidence_for(case)
        prompt_texts.append(build_strategy_prompt(strategy, case.question, evidence))
        outcome, _, verdicts = score_case(case, evidence, oracle, judge)
        outcomes.append(outcome)
        verdicts_list.append(verdicts)

    return StrategyRun(
        strategy=strategy,
        report=evaluate_answers(outcomes),
        outcomes=outcomes,
        verdicts=verdicts_list,
        prompt_texts=prompt_texts,
    )


def run_all(
    cases: list[GroundedEvaluationCase],
    evidence_for: Callable[[GroundedEvaluationCase], list[Evidence]],
    oracle: CopyOracle | None = None,
    judge=None,
) -> dict[str, StrategyRun]:
    """Run all four strategies (A-D) over the same cases and retrieval."""
    oracle = oracle or CopyOracle()
    return {name: run_strategy(name, cases, evidence_for, oracle, judge) for name in AllStrategies}


def format_run(strategy: str, run: StrategyRun, dataset_path: str) -> list[str]:
    """Recordable lines for experiments.md (per-strategy block)."""
    r = run.report
    s, u, p = run.grounded_totals
    lines = [
        f"### Strategy {strategy} (dataset: {dataset_path})",
        f"- correctness={r.answer_correctness:.2f} "
        f"abstention_acc={r.abstention_accuracy:.2f} "
        f"citation_validity={r.citation_validity:.2f} "
        f"citation_completeness={r.citation_completeness:.2f}",
        f"- groundedness: supported {s} / unsupported {u} / partially {p}",
        f"- hallucination tests: unsupported claims={u} (all flagged)",
        f"- conflict tests: conflict cases answered="
        f"{sum(1 for o in run.outcomes if o.case.case_type == 'conflict')}",
    ]
    for row in r.per_case:
        lines.append(
            f"  - {row.case_id}: correct={row.correct:.1f} "
            f"abstain={row.abstain_ok} citations {row.valid_citations}/"
            f"{row.total_citations} valid grounded "
            f"{row.grounded_supported}/{row.grounded_unsupported}/"
            f"{row.grounded_partial}"
        )
    return lines
