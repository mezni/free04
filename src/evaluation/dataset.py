"""Evaluation dataset loader (contracts/evaluation-contract.md).

Reads `data/evaluation/retrieval_questions.jsonl` line by line, validating
each line as an `EvaluationQuestion`. An invalid line => clear error (exit 1),
never a silent skip (contract). A referenced document missing from the corpus
is reported as a miss for that question, never a crash (Edge Case).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from domain import EvaluationQuestion

KNOWN_DOC_IDS = frozenset(
    {
        "5g_latency",
        "5g_packet_loss",
        "broadband_connectivity",
        "enterprise_sla",
        "lte_troubleshooting",
        "network_escalation",
        "noc_incident_procedure",
        "sim_activation",
    }
)


def load_questions(path: str | Path) -> list[EvaluationQuestion]:
    """Load and validate the evaluation dataset from a JSONL file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {p}")

    questions: list[EvaluationQuestion] = []
    with p.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                questions.append(EvaluationQuestion.model_validate(payload))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{p}:{lineno}: invalid evaluation question: {exc}") from exc

    if not questions:
        raise ValueError(f"Evaluation dataset is empty: {p}")

    return questions


def missing_docs(questions: Sequence[EvaluationQuestion]) -> list[str]:
    """Document ids referenced by the dataset but absent from the corpus."""
    referenced = {doc for q in questions for doc in q.relevant_documents}
    return sorted(referenced - KNOWN_DOC_IDS)