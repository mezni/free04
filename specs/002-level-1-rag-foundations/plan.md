# Implementation Plan: Level 1 RAG Foundations

**Branch**: `002-level-1-rag-foundations` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-level-1-rag-foundations/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Upgrade the Level 0 simulated RAG system to Level 1 by replacing the fake
embedding/vector-store infrastructure with real components while keeping the
RAG orchestration code in plain Python. Primary deliverables:

- Real local embeddings via `sentence-transformers` (default
  `BAAI/bge-small-en-v1.5`, 384-dim).
- Persistent vector storage and similarity search via `ChromaDB`.
- Structured Pydantic v2 models (Document, Chunk, RetrievalResult,
  RetrievalQuery) with metadata preserved end-to-end.
- Configurable chunking (chunk_size, chunk_overlap), retrieval (top_k,
  similarity_threshold) via YAML + environment configuration.
- Retrieval diagnostics CLI flag (`--debug-retrieval`) independent of LLM
  generation.
- Retrieval evaluation dataset (20–30 questions, incl. unanswerable cases)
  and in-house Recall@K / Precision@K / MRR metrics.
- Level 0 regression: all existing tests and CLI behavior preserved.

Tech stack (user-required): Python 3.12+, uv, Pydantic v2, Sentence
Transformers (BAAI/bge-small-en-v1.5), ChromaDB, OpenRouter + OpenAI SDK,
YAML + Pydantic Settings, Typer, pytest, Ruff, mypy. No Docker.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**:
- `pydantic>=2`, `pydantic-settings`
- `sentence-transformers` (embedding model: `BAAI/bge-small-en-v1.5`)
- `chromadb` (local persistent vector store)
- `openai` (OpenRouter-compatible generation client)
- `pyyaml`
- `typer`

**Storage**: Local persistent ChromaDB (path configurable, default
`./data/chroma`); Markdown corpus under `data/documents/`; evaluation data
under `data/evaluation/retrieval_questions.jsonl`.

**Testing**: pytest (unit + retrieval regression); deterministic tests
isolated from live LLM/embedding calls.

**Target Platform**: Linux developer workstation CLI (no web UI, no Docker).

**Project Type**: Python CLI application (flat `src/` package, installed via
uv with `telco-rag` console script).

**Performance Goals**: Ingestion of full corpus < 60s; query-to-retrieval
< 3s (spec SC-008, SC-009).

**Constraints**: Real infrastructure only (constitution XV); own Python RAG
logic (no LangChain/LlamaIndex); own metric implementation (XVI); no secrets
committed (X); collection reset on re-ingest (FR-016).

**Scale/Scope**: 8 markdown documents; ~20–30 evaluation questions; single
local collection `telco_documents`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Plan |
|------------------------|-----------------|
| I. Learn From the Level (NON-NEGOTIABLE) | Every new component answers "what Level 1 problem": real embeddings, real vector store, config, diagnostics, evaluation. No hidden abstractions. |
| II. Simple Before Sophisticated (NON-NEGOTIABLE) | No LangChain/LlamaIndex/agents/distributed infra. ChromaDB local persistent mode only. |
| V. Explicit RAG Pipeline | Keep distinct stages: Loader → Chunker → Embedder → VectorStore → Retriever → Prompt → LLM → Answer; add Evaluation path. |
| VIII. Make Retrieval Inspectable | `--debug-retrieval` prints document_id, chunk_id, score independent of LLM. |
| IX. Minimal Metadata | Metadata survives ingestion → retrieval (deterministic ids, document_name, source, chunk_index). |
| X. Configuration Over Hardcoding | Centralized settings (YAML `config/settings.yaml` + pydantic-settings, env overrides). `.env` gitignored; `.env.example` provided. |
| XI. Tests From the Beginning | Unit/regression tests for models, chunking, store, retriever, evaluation; Level 0 suite keeps passing. |
| XII. CLI First | Typer CLI; querying + `--debug-retrieval`; no web UI. |
| XIII. No Premature Enterprise Architecture | No auth/RBAC/lifecycle/HA/CI features added. |
| XIV. Every Level Must Expose the Next Problem | Documented retrieval failures feed Level 2 (citations, grounded answers). |
| XV. Real Before Sophisticated (NON-NEGOTIABLE) | Sentence-transformers embeddings + ChromaDB replace fake hash-embedding and numpy store. |
| XVI. Metrics Written, Not Hidden (NON-NEGOTIABLE) | Recall@K, Precision@K, MRR implemented in `src/evaluation/metrics.py` from formulas. |

**Gate result**: PASS — no unjustified violations; no Complexity Tracking
table needed.

**Post-Phase 1 re-check (2026-10-06)**: PASS. All design artifacts
(`data-model.md`, `contracts/`, `quickstart.md`) satisfy the target-level
constitution:

| Constitution Principle | Post-Phase 1 Evidence |
|------------------------|----------------------|
| I. Learn From the Level | data-model.md: each entity maps to an explicit Level 1 problem; no enterprise fields implemented (reserved only). |
| II. Simple Before Sophisticated | contracts/store-and-retriever.md: ChromaDB local persistent only; no server/deploy; metadata filter internal-only (FR-008). |
| V. Explicit RAG Pipeline | data-model.md relationship diagram keeps Loader → Chunker → Embedder → VectorStore → Retriever → Prompt → LLM; evaluate path separate. |
| VIII. Make Retrieval Inspectable | contracts/CLI.md + generation-and-diagnostics.md: debug block expanded, printed before generation; store-and-retriever.md score rule (higher=better). |
| IX. Minimal Metadata | data-model.md: chunk carries document_id/name/source/chunk_id/chunk_index; survives ingestion → retrieval (contracts/store-and-retriever.md storage contract). |
| X. Configuration Over Hardcoding | contracts/config-contract.md: full YAML schema + env overrides; `.env` gitignored, `.env.example` provided; all Level 0 env names preserved. |
| XI. Tests From the Beginning | plan.md project structure lists test_models/embeddings/evaluation/vector_store/retriever/chunker + Level 0 regression; quickstart §1 gates on `uv run pytest`. |
| XII. CLI First | contracts/CLI.md: Typer `query`/`ingest`/`evaluate` + `--debug-retrieval`; no web UI. |
| XIII. No Premature Enterprise Architecture | YAML/eval dataset only; no auth/RBAC/lifecycle/HA/CI added; enterprices fields documented as reserved in data-model.md. |
| XV. Real Before Sophisticated (NON-NEGOTIABLE) | research.md: sentence-transformers + ChromaDB replace hash embedding and numpy store; explicit embeddings owned by Embedder (not Chroma default). |
| XVI. Metrics Written, Not Hidden (NON-NEGOTIABLE) | contracts/evaluation-contract.md: Recall@K/Precision@K/MRR formulas implemented in `src/evaluation/metrics.py`; FR-009a true-negative split. |

## Project Structure

### Documentation (this feature)

```text
specs/002-level-1-rag-foundations/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── __main__.py
├── cli.py               # Typer CLI: ask query, --debug-retrieval, ingest, evaluate
├── config.py            # pydantic-settings: env + config/settings.yaml
├── domain.py            # Pydantic v2 models (Document, Chunk, RetrievalResult, Answer)
├── embeddings/
│   ├── __init__.py
│   └── embedder.py      # sentence-transformers; embed()/embed_batch()/dimension()
├── generation/
│   ├── __init__.py
│   ├── llm.py           # OpenRouter via OpenAI-compatible client
│   └── prompt.py        # grounded prompt builder (unchanged from Level 0)
├── ingestion/
│   ├── __init__.py
│   ├── loader.py        # Markdown -> Document objects
│   └── chunker.py       # configurable chunk_size/chunk_overlap -> Chunk objects
├── rag/
│   ├── __init__.py
│   └── pipeline.py      # retrieve -> prompt -> generate -> answer
├── retrieval/
│   ├── __init__.py
│   ├── vector_store.py  # ChromaDB-backed repository; reset-on-ingest
│   └── retriever.py     # top_k + similarity_threshold + metadata filter arg
└── evaluation/
    ├── __init__.py
    ├── dataset.py       # load data/evaluation/retrieval_questions.jsonl
    └── metrics.py       # Recall@K, Precision@K, MRR, true-negative count

config/
└── settings.yaml        # chunking, retrieval, embeddings, vector_store, llm

data/
├── documents/           # existing 8 Telco markdown files
└── evaluation/
    └── retrieval_questions.jsonl   # 20-30 questions w/ expected docs

tests/
├── conftest.py
├── test_chunker.py      # Level 0 (regression)
├── test_loader.py       # Level 0 (regression)
├── test_vector_store.py # rewritten for ChromaDB-backed store
├── test_retriever.py    # rewritten for real retriever
├── test_prompt.py       # Level 0 (regression)
├── test_rag_pipeline.py # Level 0 + FR-017 LLM-failure handling
├── test_cli_output.py   # + ingestion/evaluation/evaluation commands
├── test_models.py       # Pydantic models validation
├── test_embeddings.py   # deterministic model (all-MiniLM) sanity
└── test_evaluation.py   # metrics formulas + dataset + true-negative
```

**Structure Decision**: Keep the existing flat `src/` package (already
flattened from `src/telco_rag/`). Add `src/evaluation/` for metrics + dataset
and `src/models/` models stay consolidated in `src/domain.py` until the
Pydantic refactor necessitates a split (minimal churn). ChromaDB access
isolated in `src/retrieval/vector_store.py` (constitution FR-015).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

None — all gates pass. Intentionally omitted.

## Reference: Level 1 Source Documents

- Constitution: `docs/levels/level-01-rag-foundations/constitution.md`
- Level 1 plan: `docs/levels/level-01-rag-foundations/plan.md`
- Project constitution: `.specify/memory/constitution.md`