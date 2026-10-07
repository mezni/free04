"""In-house retrieval metrics (constitution XVI, contracts/evaluation-contract.md).

Recall@K = |Y ∩ R| / |Y|
Precision@K = |Y ∩ R| / K
MRR = mean( 1 / rank_first_relevant )   (0 contribution when not retrieved)

FR-009a: unanswerable questions (|Y| == 0) are EXCLUDED from the aggregates
and reported separately as true negatives / false positives.
"""

from __future__ import annotations

from collections.abc import Sequence

from domain import EvaluationQuestion, RetrievalResult


def _hits(results: Sequence[RetrievalResult], expected: Sequence[str]) -> list[str]:
    """Document ids among the retrieved results that match expected ids."""
    retrieved = {r.chunk.document_id for r in results}
    return [doc_id for doc_id in expected if doc_id in retrieved]


def recall_at_k(results: Sequence[RetrievalResult], question: EvaluationQuestion, k: int) -> float:
    """Recall@K for a single question; 1.0 if the expected doc is in top-K."""
    if question.is_unanswerable:
        return 0.0
    hits = _hits(results, question.relevant_documents)
    return len(hits) / len(question.relevant_documents)


def precision_at_k(
    results: Sequence[RetrievalResult], question: EvaluationQuestion, k: int
) -> float:
    """Precision@K; denominator is always K (misses yield 0)."""
    if question.is_unanswerable:
        return 0.0
    hits = _hits(results, question.relevant_documents)
    return len(hits) / k


def reciprocal_rank(results: Sequence[RetrievalResult], question: EvaluationQuestion) -> float:
    """1/rank of the first retrieved result whose document_id is relevant (or 0)."""
    if question.is_unanswerable:
        return 0.0
    for r in results:
        if r.chunk.document_id in question.relevant_documents:
            return 1.0 / r.rank
    return 0.0


def evaluate_retrieval(
    questions: Sequence[EvaluationQuestion],
    retriever,
    k: int,
    similarity_threshold: float = 0.0,
) -> dict:
    """Run retrieval for every question and compute the aggregate report.

    Args:
        questions: evaluation dataset entries.
        retriever: object with `retrieve(RetrievalQuery) -> list[RetrievalResult]`.
        k: evaluation depth (Recall@K / Precision@K).
        similarity_threshold: applied to every RetrievalQuery (FR-006) so the
            evaluation reflects the pipeline's real abstention boundary — an
            unanswerable question whose top hit falls below the threshold stays
            empty and counts as a true negative (FR-009a).

    Returns a report dict compatible with `telco-rag evaluate`:
        recall_at_k, precision_at_k, mrr, true_negatives, false_positives,
        per_question {id: {recall, precision, rr}}.
    """
    from domain import RetrievalQuery

    answerable: list[EvaluationQuestion] = [q for q in questions if not q.is_unanswerable]

    per_question: dict[str, dict] = {}
    true_negatives = 0
    false_positives = 0
    for q in questions:
        query = RetrievalQuery(
            question=q.question,
            top_k=k,
            similarity_threshold=similarity_threshold,
        )
        results = retriever.retrieve(query)
        per_question[q.id] = {
            "recall": recall_at_k(results, q, k),
            "precision": precision_at_k(results, q, k),
            "rr": reciprocal_rank(results, q),
        }
        if q.is_unanswerable:
            if results:
                false_positives += 1
            else:
                true_negatives += 1

    if answerable:
        recall = sum(per_question[q.id]["recall"] for q in answerable) / len(answerable)
        precision = sum(per_question[q.id]["precision"] for q in answerable) / len(answerable)
        mrr = sum(per_question[q.id]["rr"] for q in answerable) / len(answerable)
    else:
        recall = precision = mrr = 0.0

    return {
        "recall_at_k": recall,
        "precision_at_k": precision,
        "mrr": mrr,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "per_question": per_question,
    }
