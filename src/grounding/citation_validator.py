"""Pure-function citation validator (FR-007/FR-008, research R2).

Validates generated citations against the current question's Evidence[]
only — no I/O, no retrieval, no LLM (Principle XVIII/XX, spec US2).

Status mapping (data-model.md):
- empty/whitespace ids -> MALFORMED (also: evidence_id that does not
  reference an Evidence of the current question)
- document absent from the evidence documents -> UNKNOWN_DOCUMENT
- document present, chunk_id exists in evidence under a different
  document -> UNKNOWN_CHUNK (misattributed chunk)
- document present, chunk_id not retrieved for this question at all
  -> NOT_RETRIEVED
- pair present -> VALID

Identical (document_id, chunk_id) pairs are deduplicated deterministically
(first occurrence wins); duplicates never inflate verdict counts.
"""

from domain import Citation, CitationStatus, CitationVerdict, Evidence

VALID: CitationStatus = "VALID"
UNKNOWN_DOCUMENT: CitationStatus = "UNKNOWN_DOCUMENT"
UNKNOWN_CHUNK: CitationStatus = "UNKNOWN_CHUNK"
NOT_RETRIEVED: CitationStatus = "NOT_RETRIEVED"
MALFORMED: CitationStatus = "MALFORMED"


def validate_citations(
    evidence: list[Evidence], citations: list[Citation]
) -> list[CitationVerdict]:
    """Validate citations against retrieved evidence.

    Args:
        evidence: Evidence objects retrieved for this question.
        citations: citations from the structured answer.

    Returns:
        One CitationVerdict per unique citation, in input order.
    """
    pairs = {(e.document_id, e.chunk_id) for e in evidence}
    documents = {e.document_id for e in evidence}
    chunks = {e.chunk_id for e in evidence}
    evidence_ids = {e.evidence_id for e in evidence}

    verdicts: list[CitationVerdict] = []
    seen: set[tuple[str, str]] = set()

    for citation in citations:
        doc = citation.document_id
        chunk = citation.chunk_id

        if citation.key in seen:
            continue
        seen.add(citation.key)

        if (
            not isinstance(doc, str)
            or not isinstance(chunk, str)
            or not doc.strip()
            or not chunk.strip()
        ):
            verdicts.append(
                CitationVerdict(
                    citation=citation,
                    status=MALFORMED,
                    detail="document_id and chunk_id must be non-empty",
                )
            )
            continue

        if citation.evidence_id is not None and citation.evidence_id not in evidence_ids:
            verdicts.append(
                CitationVerdict(
                    citation=citation,
                    status=MALFORMED,
                    detail=f"unknown evidence_id {citation.evidence_id!r} for this question",
                )
            )
            continue

        if (doc, chunk) in pairs:
            verdicts.append(CitationVerdict(citation=citation, status=VALID, detail=""))
        elif doc not in documents:
            verdicts.append(
                CitationVerdict(
                    citation=citation,
                    status=UNKNOWN_DOCUMENT,
                    detail=f"document {doc!r} was not retrieved for this question",
                )
            )
        elif chunk in chunks:
            verdicts.append(
                CitationVerdict(
                    citation=citation,
                    status=UNKNOWN_CHUNK,
                    detail=f"chunk {chunk!r} belongs to a different retrieved document",
                )
            )
        else:
            verdicts.append(
                CitationVerdict(
                    citation=citation,
                    status=NOT_RETRIEVED,
                    detail=f"chunk {chunk!r} was not retrieved for this question",
                )
            )

    return verdicts
