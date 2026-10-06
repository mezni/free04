"""Retrieval evaluation package (US4)."""

from evaluation.dataset import KNOWN_DOC_IDS, load_questions, missing_docs
from evaluation.metrics import (
    evaluate_retrieval,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

__all__ = [
    "KNOWN_DOC_IDS",
    "evaluate_retrieval",
    "load_questions",
    "missing_docs",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
]