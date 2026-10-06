# Contract: Generation & Diagnostics (FR-007 / FR-017 / FR-014)

**Silent goal**: retrieval diagnostics independent of LLM; generation failure
never masquerades as retrieval failure; LLM provider stays separate from
embedding provider.

## Separation (FR-014)

- Embeddings: `src/embeddings/embedder.py` (Sentence Transformers, local).
- Generation: `src/generation/llm.py` → OpenRouter via OpenAI-compatible
  client (`openai` SDK per stack; HTTP base behavior retained).
- Independent config sections (see config contract): `embedding.*` vs `llm.*`.
- `evaluate` never touches the LLM; `--debug-retrieval` queries never touch
  the LLM (US-2 / SC-003).

## Diagnostics Output (`--debug-retrieval`)

Before any generation, print one line per retrieved chunk (SC-003):

```text
Retrieved Documents:
1. 5g_packet_loss :: 5g_packet_loss#0008 :: 5g_packet_loss.md (score: 0.84)
   <first 120 chars of chunk text, stripped>
```

Include chunk text preview so a developer can explain *why* a chunk was
retrieved from the output alone (SC-007). If zero results above threshold,
print `Retrieved Documents: (none — nothing above similarity_threshold=0.0)`.

## LLM Failure Handling (FR-017)

On a normal `query` where the generation backend is unreachable or returns an
error:

1. If `--debug-retrieval` was requested, diagnostics are printed FIRST
   (retrieval results and scores shown normally, per US-2).
2. Then print a clear error to stderr:
   `Error: generation backend unavailable (<provider>): <detail>`.
3. Exit with non-zero code **2** (runtime failure).

Abstention path (no context) does NOT call the LLM — it returns the Level 0
abstention text with exit 0; this is not a failure.

## Embedding Failure

Model fails to download/load on ingest or first query ⇒ clear actionable
error (spec Edge Case: check network, model name) ⇒ exit 2.