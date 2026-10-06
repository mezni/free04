# Contract: Configuration & Providers

**Feature**: Level 0 — Naive RAG Baseline
**Date**: 2026-10-06
**Constitution**: v1.0.0 (P X Configuration Over Hardcoding)

All environment-specific settings are externalized. The system reads them
from environment variables (optionally loaded from a `.env` file via
`--config`). A committed `.env.example` documents every variable; the real
`.env` is git-ignored and secrets never appear in the repository (P X,
FR-011).

## Configuration Surface

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `DOCUMENT_DIR` | no | `data/documents` | Corpus directory with `.md` files |
| `CHUNK_SIZE` | no | 500 | Fixed chunk length in characters |
| `CHUNK_OVERLAP` | no | 50 | Overlap between adjacent chunks |
| `TOP_K` | no | 4 | Number of chunks retrieved per question |
| `EMBEDDING_PROVIDER` | no | `local-sentence-transformers` | Provider name; resolved by the embedder |
| `EMBEDDING_MODEL` | no | `all-MiniLM-L6-v2` | Local model; other providers may ignore |
| `LLM_BASE_URL` | yes* | — | Base URL of an OpenAI-compatible chat-completions server |
| `LLM_API_KEY` | no | — | Bearer token for the server (empty allowed for local servers) |
| `LLM_MODEL` | yes* | — | Model identifier for the answer provider |
| `LLM_MAX_TOKENS` | no | 512 | Answer length cap |
| `LLM_TEMPERATURE` | no | 0.0 | Sampling temperature (0 = deterministic-style grounded answers) |

\* `LLM_BASE_URL` and `LLM_MODEL` are required to run a query. Missing
required settings produce a clear configuration error (exit 1 per
`contracts/cli.md`), listing the missing variable(s).

## Validation Rules

- `CHUNK_SIZE` > 0, `CHUNK_OVERLAP` >= 0, `CHUNK_OVERLAP` < `CHUNK_SIZE`.
- `TOP_K` >= 1.
- `LLM_TEMPERATURE` in `[0., 2.]`.
- `LLM_MAX_TOKENS` >= 1.
- `DOCUMENT_DIR` must exist and contain at least one `.md` file at ingest
  time; otherwise ingestion fails with a clear error naming the directory.
- Unknown variables are ignored; malformed numeric values fail fast with the
  variable name.

## Embedder Contract

The pipeline depends on an abstract embedding capability, not a provider
(FR-003, FR-008):

```text
embed_documents(documents: list[str]) -> vectors
embed_query(question: str) -> vector
dimension() -> int
```

`local-sentence-transformers` is the Level 0 default; an
OpenAI-compatible API provider may be added later without touching
retrieval code (research.md §1).

## Answer Provider Contract

The pipeline sends a single non-streaming request to
`POST {LLM_BASE_URL}/chat/completions` with an OpenAI-compatible JSON body
(`{model, messages, max_tokens, temperature}`) and `Accept: application/json`
(research.md §4). The response text is taken from
`choices[0].message.content`.

Provider failures (timeout, connection refused, HTTP 4xx/5xx, empty
`choices`, `finish_reason == "length"`) are reported as readable errors per
the CLI exit-code table.

## Prompt Grounding Rules (P VII)

The system instruction composing every prompt MUST state:

1. Answer using only the supplied retrieved context.
2. Do not invent facts not present in the context.
3. If the context is insufficient, say so explicitly — do not guess.
4. Answer clearly and directly in the language of the question.

The context section contains the retrieved chunk content only; the question
section contains the user question. Abstention wording used by the CLI when
no context exists (per `contracts/cli.md`):

```text
I don't have enough information in the knowledge base to answer this question.
```

## Notes

- This contract covers exactly what `/speckit.tasks` needs to implement;
  concrete parsing/loading mechanics are deferred there.
- Environment variables are the interface; whether they are loaded from
  `.env` or shell export is an implementation detail.