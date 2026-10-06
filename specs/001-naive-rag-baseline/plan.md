# Implementation Plan: Level 0 — Naive RAG Baseline

**Branch**: `001-naive-rag-baseline` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-naive-rag-baseline/spec.md`

## Summary

Build the smallest working retrieval-augmented question/answer system for a
local synthetic Telco knowledge base (Per spec FR-001..FR-016). A developer
asks a question via a command-line interface; the system ingests ~8 local
Markdown documents, chunks them, embeds them, retrieves the top-K most
similar chunks, composes a grounded prompt, and returns an answer plus an
inspection record (sources + scores), abstaining when the corpus has no
answer. Approach (from research.md): Python 3.12, sentence-transformers
embedding via a provider-agnostic embedder contract, an in-memory numpy
vector store, fixed-size chunking with overlap, a plain-HTTP
OpenAI-compatible chat-completions client, argparse CLI, pytest tests.

## Technical Context

**Language/Version**: Python 3.12+ (locked by existing `pyproject.toml`)

**Primary Dependencies**: sentence-transformers, numpy, httpx, pytest
(dev); embedding and answer providers are decoupled behind small client
classes so no vendor is hard-bound

**Storage**: In-memory numpy matrix built from the corpus at startup;
persistent-file storage deliberately out of scope for Level 0

**Testing**: pytest — deterministic components (loader, chunker, retriever,
prompt builder) tested directly; embedding and LLM clients mocked in
end-to-end pipeline and CLI tests

**Target Platform**: Local Linux/macOS developer machine (CLI)

**Project Type**: CLI application (src-layout package `telco-rag`)

**Performance Goals**: Single user; a question is answered in under 10
seconds end to end (spec SC-001), including embedding + retrieval + model
call; retrieval only <1s

**Constraints**: No external infrastructure (no DB server, no daemon, no
queue); secrets only via environment; deterministic logic testable without
network; prompt context kept small (top-K=4 × ~500 chars)

**Scale/Scope**: ~8 Markdown documents (~20–40 chunks); single user;
educational reproducibility baseline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Constitution: `.specify/memory/constitution.md` v1.0.0 (Level 0 — Naive RAG).

- **P I Learn From the Baseline**: every component has an explicit Level 0
  problem to solve (loader, chunker, embedder, store, retriever, prompt,
  LLM client) — PASS.
- **P II Simple Before Sophisticated**: no frameworks/orchestration/
  microservices/queues/K8s/complex DB; vector store is ~30 lines of numpy,
  no ANN index — PASS.
- **P III Telco Domain**: synthetic corpus with 5G/LTE/broadband/SIM/SLA/NOC
  topics; no real customer data — PASS.
- **P IV Reproducibility**: pyproject + `.env.example` + README setup/run/
  test steps; deterministic embedder (local model) — PASS.
- **P V Explicit RAG Pipeline**: distinct, nameable stages, no opaque
  mega-function — PASS.
- **P VI Retrieval Before Generation**: every question goes through
  retrieval → prompt → generation; no direct-to-LLM path — PASS.
- **P VII No Knowledge Outside the Corpus**: system prompt mandates
  context-only answers and explicit "not enough information" abstention —
  PASS.
- **P VIII Make Retrieval Inspectable**: output includes question,
  retrieved chunks, sources, scores, answer — PASS.
- **P IX Minimal Metadata**: `document_id`, `document_name`, `chunk_id`,
  `source` preserved on every chunk — PASS.
- **P X Configuration Over Hardcoding**: settings externalized, `.env`
  ignored, `.env.example` provided, secrets never committed — PASS.
- **P XI Tests From the Beginning**: loader/chunker/retriever/prompt tests
  plus mocked end-to-end test; deterministic logic isolated from live model
  — PASS.
- **P XII CLI First**: argparse CLI with example command documented; no web
  UI — PASS.
- **P XIII No Premature Enterprise Architecture**: known limitations
  documented in `docs/levels/level-00-naive-rag/baseline.md`; nothing faked
  production-grade — PASS.
- **P XIV Every Level Exposes the Next Problem**: baseline experiments
  record failures (irrelevant retrieval, hallucination, chunk splitting)
  as justification for Level 1 — PASS.

**Gate result**: No violations. Complexity Tracking section intentionally
left empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-naive-rag-baseline/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (cli.md, config.md)
├── checklists/
│   └── requirements.md  # Spec quality checklist (/speckit.specify output)
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
telco-rag/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── data/
│   └── documents/
│       ├── 5g_packet_loss.md
│       ├── 5g_latency.md
│       ├── lte_troubleshooting.md
│       ├── broadband_connectivity.md
│       ├── sim_activation.md
│       ├── enterprise_sla.md
│       ├── noc_incident_procedure.md
│       └── network_escalation.md
├── src/
│   └── telco_rag/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── cli.py
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── chunker.py
│       ├── embeddings/
│       │   ├── __init__.py
│       │   └── embedder.py
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── vector_store.py
│       │   └── retriever.py
│       ├── generation/
│       │   ├── __init__.py
│       │   ├── prompt.py
│       │   └── llm.py
│       └── rag/
│           ├── __init__.py
│           └── pipeline.py
├── tests/
│   ├── conftest.py
│   ├── test_loader.py
│   ├── test_chunker.py
│   ├── test_vector_store.py
│   ├── test_retriever.py
│   ├── test_prompt.py
│   └── test_rag_pipeline.py
└── docs/
    └── levels/
        └── level-00-naive-rag/     # already exists; baseline.md filled in
            ├── constitution.md
            ├── plan.md
            └── baseline.md
```

**Structure Decision**: Single src-layout package (`src/telco_rag`), matching
the empty `src/` and `tests/` directories already scaffolded in the repo.
This is Option 1 (Single project). Stage packages mirror the constitution's
explicit pipeline (P V) so a developer can read the pipeline as a file tree.
`data/documents/` holds the synthetic corpus; the Level 0 docs already live
at `docs/levels/level-00-naive-rag/` and `baseline.md` receives the recorded
experiment results. No frontend/backend or mobile split applies.

## Complexity Tracking

> Intentionally empty — no Constitution Check violations to justify.