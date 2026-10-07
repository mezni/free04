# Implementation Plan: Level 2 Grounded RAG

**Branch**: `003-level-2-grounded-rag` | **Date**: 2026-10-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-level-2-grounded-rag/spec.md`

## Summary

Upgrade the existing Level 1 retrieval system into a grounded RAG system:
every retrieved result becomes an explicit **Evidence** object, the LLM
returns a **structured answer** (text + citations + abstention flag), every
citation is **validated against the actual retrieval result** before
display, the system **abstains** when evidence is insufficient, and
answer-level evaluation (correctness, groundedness, citation validity,
citation completeness, abstention) is added as a second layer alongside the
preserved Level 1 retrieval metrics. Technical approach: extend the
existing flat `src/` package with a `grounding/` layer, extend
`domain.py` with Evidence/Citation/answer models, replace the free-text
prompt with an evidence-aware prompt returning JSON parsed by Pydantic, add
a deterministic pure-function citation validator, and implement answer
evaluation directly in Python (no evaluation framework), with LLM-judge
steps isolated behind interfaces and mocked in unit tests.

## Technical Context

**Language/Version**: Python 3.12+ (existing `pyproject.toml`, `requires-python = ">=3.12"`)

**Primary Dependencies**: unchanged from Level 1 — Pydantic v2,
pydantic-settings, PyYAML, Typer, httpx (OpenAI-compatible chat-completions
client against OpenRouter), sentence-transformers
(BAAI/bge-small-en-v1.5), ChromaDB. No new runtime dependencies.

**Storage**: ChromaDB persistent store (`data/chroma/`), JSONL evaluation
datasets (`data/evaluation/`), Markdown corpus (`data/documents/`).

**Testing**: pytest + pytest-cov, Ruff, mypy; deterministic tests use
mocked LLM clients (existing pattern in `tests/test_rag_pipeline.py`);
live-model behavior isolated to documented experiments.

**Target Platform**: local Linux, CLI-only (`telco-rag` console script /
`python -m src.__main__`).

**Project Type**: CLI (single project, `src/` layout — no services, no
frontend).

**Performance Goals**: interactive CLI use; answer latency is
LLM-bound (existing 30 s client timeout); evaluation runs offline over
~20–40 dataset cases.

**Constraints**: no new frameworks (constitution II/XXI); prompt
instructions alone do not count as grounding (Principle XX) — validation
logic and evaluation must exist; deterministic tests MUST NOT call the
live LLM; Level 0/1 tests must keep passing (FR-022).

**Scale/Scope**: 8 corpus documents; evaluation dataset extended from the
Level 1 retrieval set to also cover answerable / unanswerable /
partial-evidence / conflict cases; ~7 new test modules; CLI gains one
debug mode and source display.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against `.specify/memory/constitution.md` v1.2.0 (Level 2 active).

| Gate | Status | Evidence |
|------|--------|----------|
| I. Learn From the Level | PASS | Every new component (evidence builder, validator, abstention, answer metrics) maps to a Level 2 requirement in the spec. |
| II. Simple Before Sophisticated | PASS | Pure functions + Pydantic models; no orchestration/agent/evaluation framework introduced. |
| III. Telco Domain From Day One | PASS | Existing synthetic Telco corpus reused; conflict/partial cases added synthetically. |
| IV. Reproducibility | PASS | No dependency changes; `uv.lock` untouched; documented run/eval steps in quickstart.md. |
| V. Explicit RAG Pipeline | PASS | Pipeline extends with distinct stages: Retriever → Evidence Builder → Grounded Prompt → LLM → Structured Answer → Citation Validator → Final Response; each a separate unit. |
| VI. Retrieval Before Generation | PASS | Generation consumes only evidence built from retrieval; no direct question→LLM path. |
| VII. No Knowledge Outside the Corpus | PASS | Grounded prompt + structured output + citation validation + evaluation (Principle XX combination). |
| VIII. Make Retrieval Inspectable | PASS | Existing `--debug-retrieval` retained; new grounding debug mode exposes evidence, answer, citations, validation result (FR-014). |
| IX. Minimal Metadata | PASS | Evidence preserves document_id, chunk_id, title/source, score end to end (FR-001/FR-002). |
| X. Configuration Over Hardcoding | PASS | Sufficiency threshold / min-evidence and existing retrieval settings live in `config/settings.yaml` + Pydantic Settings; no secrets added. |
| XI. Tests From the Beginning | PASS | New suites for evidence, answer schema, citations, abstention, grounding, answer evaluation, pipeline; Level 0/1 regression preserved (FR-020/FR-022). |
| XII. CLI First | PASS | Normal output shows Sources; grounding debug mode shows full path; no web UI. |
| XIII. No Premature Enterprise Architecture | PASS | No auth, RBAC, lifecycle, monitoring introduced. |
| XIV. Every Level Must Expose the Next Problem | PASS | plan.md/docs step retains Level 3 motivation (retrieval reliability). |
| XV. Real Before Sophisticated | PASS | Citations validated against real retrieval results; real structured output parsed by Pydantic — no simulated grounding signals. |
| XVI. Metrics Written, Not Hidden | PASS | Answer-level metrics implemented in-repo in Python; no evaluation framework dependency (FR-016). |
| XVII. Evidence Is a First-Class Object (NON-NEGOTIABLE) | PASS | `Evidence` model with evidence_id/document_id/chunk_id/title/source/text/retrieval_score (FR-001). |
| XVIII. Validated Citations Only (NON-NEGOTIABLE) | PASS | Validator rejects nonexistent/unretrieved citations before display; LLM cannot invent identifiers (FR-007). |
| XIX. Abstention Is a Valid Result (NON-NEGOTIABLE) | PASS | Abstention modeled, flagged in structured answer, tested (FR-010/FR-012). |
| XX. Prompt Constraints Alone Are Insufficient (NON-NEGOTIABLE) | PASS | Grounding = prompt + structured output + validation + evaluation; validation is deterministic code, not prompt wording. |
| XXI. Separation of Retrieval, Generation, Validation | PASS | Generator receives evidence only; validator is a pure function over evidence + citations, performs no retrieval (FR-005/FR-008). |
| XXII. Two-Layer Evaluation (NON-NEGOTIABLE) | PASS | Recall@K/Precision@K/MRR preserved and reported separately from answer metrics (FR-017). |
| XXIII. Surface Conflicts, Never Merge Them | PASS | Conflict behavior specified (FR-019), tested via conflict dataset cases. |
| Technology Constitution (stack) | PASS | Python 3.12+, uv, Pydantic v2, PyYAML, Typer, sentence-transformers, ChromaDB, OpenRouter/httpx, pytest/Ruff/mypy — unchanged; evaluation in Python/Pydantic/pytest. |
| Out of Scope / Framework Constitution | PASS | No BM25, hybrid, reranking, agents, LangChain/LlamaIndex/LangGraph, RAG eval frameworks, CI/CD, K8s. |

**Gate result: PASS — no violations, Complexity Tracking table stays empty.**

Post-Phase-1 re-check: PASS (design artifacts below introduce no new
technology and no new top-level components beyond `src/grounding/` and
evaluation modules required by the spec).

## Project Structure

### Documentation (this feature)

```text
specs/003-level-2-grounded-rag/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── grounded-answer-schema.md
│   └── cli-grounded-output.md
├── checklists/
│   └── requirements.md  # from /speckit.specify
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
├── domain.py                    # + Evidence, Citation, GroundedAnswer,
│                                #   EvidenceSufficiency, GroundednessVerdict
├── config.py                    # + grounding settings (sufficiency, judge)
├── cli.py                       # + Sources block, --debug-grounding
├── grounding/                   # NEW package
│   ├── __init__.py
│   ├── evidence_builder.py      # RetrievalResult[] -> Evidence[]
│   ├── citation_validator.py    # pure function: evidence + citations -> verdicts
│   ├── abstention.py            # evidence-sufficiency decision
│   └── grounding_checker.py     # claim/evidence support classification helper
├── generation/
│   ├── prompt.py                # + evidence-aware grounded prompt
│   ├── llm.py                   # + structured JSON response mode
│   └── generator.py             # NEW: prompt -> LLM -> Pydantic GroundedAnswer
├── evaluation/
│   ├── dataset.py               # + grounded-answer dataset loader
│   ├── answer_metrics.py        # NEW: correctness, abstention, citation metrics
│   └── groundedness.py          # NEW: claim support classification
├── rag/
│   └── pipeline.py              # orchestrates evidence -> generate -> validate
└── (ingestion/, retrieval/, embeddings/ unchanged)

tests/
├── test_evidence.py             # NEW
├── test_answer_schema.py        # NEW
├── test_citations.py            # NEW
├── test_abstention.py           # NEW
├── test_grounding.py            # NEW
├── test_answer_evaluation.py    # NEW
├── test_rag_pipeline.py         # extended (grounded path)
└── (existing Level 0/1 tests unchanged and passing)

data/
├── documents/                   # + conflict/partial source docs as needed
└── evaluation/
    ├── retrieval_questions.jsonl        # preserved (Level 1)
    └── grounded_answers.jsonl           # NEW: answerable/unanswerable/
                                        #   partial/conflict cases

docs/levels/level-02-grounded-rag/
├── constitution.md              # exists
├── plan.md                      # exists
├── experiments.md               # NEW: prompt-strategy + hallucination results
└── lessons-learned.md           # NEW
```

**Structure Decision**: extend the existing single-project `src/` layout
(flat modules under `src/`, `sys.path`-based imports). The conceptual
`src/telco_rag/...` tree in `docs/levels/level-02-grounded-rag/plan.md` is
realized with the repository's actual package layout — a rename to
`telco_rag` would be a Level 1/2-wide refactor with no grounding benefit
(Principle I). New code lands in a new `src/grounding/` package plus two
new evaluation modules; existing packages are touched only where the spec
requires it (prompt, llm, pipeline, cli, domain, config).

## Complexity Tracking

No constitution violations to justify — table intentionally empty.
