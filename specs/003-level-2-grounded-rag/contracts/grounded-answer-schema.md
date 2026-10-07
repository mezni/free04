# Contract: Structured Answer (GroundedAnswer)

**Feature**: specs/003-level-2-grounded-rag
**Consumer**: `src/generation/generator.py` (producer: LLM via
chat-completions), `src/rag/pipeline.py`, `src/evaluation/*`
**Type**: JSON object returned as the chat message content, parsed with
Pydantic (source of truth = schema below, not provider wording).

## Request side

The grounded prompt (contractual sections, in order):

```text
QUESTION:  <user question>

EVIDENCE:  <EVIDENCE-001 | document_id | chunk_id | score>
           <text>
           ...

INSTRUCTIONS:
  Answer using only the EVIDENCE above.
  Do not introduce unsupported facts.
  Do not invent citations — cite only evidence IDs given above.
  If the evidence is insufficient, set abstained=true and sufficient_evidence=false.
  If evidence contradicts itself, set conflicts[] with both positions.
  Respond with a JSON object matching the schema exactly.
```

Transport: `response_format={"type":"json_object"}` attempted; on
provider rejection, fall back to prompt-enforced JSON (research R1).

## Response schema

```json
{
  "answer": "string (required, non-empty)",
  "citations": [
    {
      "document_id": "string (required)",
      "chunk_id": "string (required)",
      "evidence_id": "string or null (optional)"
    }
  ],
  "abstained": false,
  "sufficient_evidence": true,
  "conflicts": [
    {
      "description": "string (required)",
      "positions": [
        {"document_id": "string", "chunk_id": "string"}
      ]
    }
  ]
}
```

## Rules

| # | Rule | Violation handling |
|---|------|--------------------|
| 1 | Response MUST parse as JSON and validate against the schema | `StructuredOutputError` → CLI exit 2, message `structured output invalid` (never silently accepted) |
| 2 | `citations[]` entries MUST have non-empty `document_id` and `chunk_id` | validator returns `MALFORMED` |
| 3 | Model MUST NOT introduce `(document_id, chunk_id)` pairs absent from the evidence | validator returns `UNKNOWN_DOCUMENT` / `UNKNOWN_CHUNK` / `NOT_RETRIEVED` |
| 4 | `abstained=true` with non-empty `citations` | flagged `INCONSISTENT_ABSTENTION`; abstention takes precedence in display |
| 5 | `abstained=false`, factual answer, `citations=[]` | evaluation flags `INCOMPLETE_CITATIONS` (not a parse error) |
| 6 | `conflicts[].positions` MUST contain ≥ 2 entries | schema validation error |
| 7 | Extra unknown fields | rejected (Pydantic `extra="forbid"`) — keeps the contract tight |

## Validation flow (post-generation, deterministic)

```text
GroundedAnswer
  → citation_validator(evidence, answer.citations) → CitationVerdict[]
  → abstention.decide(evidence, answer)            → EvidenceSufficiencyDecision
  → final display / evaluation
```

The validator and abstention modules perform no I/O and no retrieval.
