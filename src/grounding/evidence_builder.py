"""Evidence builder: RetrievalResult[] -> Evidence[] (FR-002, research R2).

Assigns stable, ordered evidence identifiers (EVIDENCE-001, ...) and
preserves document/chunk identity, metadata, and retrieval scores — the
boundary between retrieval and generation (Principle XVII).
"""

from domain import Evidence, RetrievalResult

EVIDENCE_ID_PREFIX = "EVIDENCE-"


def build_evidence(results: list[RetrievalResult]) -> list[Evidence]:
    """Project retrieval results into first-class evidence objects.

    Identifiers are assigned in rank order starting at EVIDENCE-001 and are
    stable across runs for the same result order (data-model.md).
    """
    evidence: list[Evidence] = []
    for position, result in enumerate(results, start=1):
        chunk = result.chunk
        evidence.append(
            Evidence(
                evidence_id=f"{EVIDENCE_ID_PREFIX}{position:03d}",
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                title=chunk.document_name,
                source=chunk.source,
                text=chunk.content,
                retrieval_score=result.score,
                rank=result.rank,
                metadata=dict(chunk.metadata),
            )
        )
    return evidence
