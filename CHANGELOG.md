# Changelog

All notable changes to `project` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec.php#pec-2.0.0).

## Version History

| Version | Feature Domain | Key Objectives |
|---------|---------------|----------------|
| 0.5.0 | Level 3 — Advanced Retrieval | BM25 lexical index, metadata filtering, hybrid RRF fusion, cross-encoder reranking, query rewriting, retrieval controller + provenance, evaluation matrix/ablation, failure attribution |
| 0.4.0 | Level 2 — Grounded RAG | Evidence objects, structured grounded answers, citation validation, abstention, conflict reporting, two-layer (retrieval + answer) evaluation |
| 0.3.0 | Level 1 — RAG Foundations | Real embeddings + ChromaDB, typed metadata, Typer CLI, retrieval evaluation, config polish |
| 0.2.0 | Level 0 — Naive RAG Baseline | First working RAG pipeline with deterministic tests |
| 0.0.1   | Project          | Scaffold|
| 0.0.1-pre | Repo       | Cleanup|


## [0.5.0] - 2026-10-08

### Added
- **BM25 lexical retrieval (FR-001/002):** `src/retrieval/bm25.py` — pure-Python index over loader+chunker output, rebuilt from documents at ingest (indexes derived, never truth); `rank-bm25` scoring, zero-score matches excluded
- **Metadata filtering (FR-009…011):** YAML front matter → `Document.metadata` (additive, stripped from content), generic `--filter key=value` applied identically to every strategy at stage-pool level
- **Hybrid retrieval + RRF (FR-004…007):** `src/retrieval/hybrid.py`/`fusion.py` — vector and BM25 branch lists fused by Reciprocal Rank Fusion (k=60, deterministic, no raw-score averaging per Principle XXV); duplicate chunks deduped, provenance keeps both branch ranks
- **Cross-encoder reranking (FR-012…014):** `src/retrieval/reranker.py` — `BAAI/bge-reranker-base` over fusion candidates (candidate_k=20, final_k=5), lazy-loaded, injectable scorer for hermetic tests, disable path verified (stages skipped, never fabricated scores)
- **Query rewriting (FR-015…018):** `src/retrieval/query_rewriter.py` — LLM-assisted rewrite, **off by default** (Principle XXIX), original query always preserved and shown, failure → warning + fallback to original, exit 0
- **Retrieval controller (FR-003/005/008/019…021):** `src/retrieval/controller.py` — strategy selection (vector/bm25/hybrid/hybrid_reranked configurable without code changes), per-stage latency block, provenance fields (`vector_rank`/`bm25_rank`/`rrf_score`/`reranker_score`; skipped stages absent, never 0), `telco-rag retrieve --strategy --debug --filter`
- **Evaluation matrix + ablation (FR-020…024):** `src/evaluation/retrieval_matrix.py` + `scripts/run_retrieval_experiments.py` — question × strategy × query mode (original/rewritten), Recall/Precision@1/3/5/10, MRR, chunk- and document-level labels, per-stage p50/p95 latency, per-category winners; 28-question dataset across 8 categories (`data/evaluation/retrieval_questions.jsonl`)
- **Failure attribution (FR-025…029):** runnable decision-tree procedure (lessons-learned §10); three significant failures logged (F-001…F-003, all first-stage vector semantic misses) with named hermetic regressions in `tests/test_regressions_level3.py`
- **Experiments + lessons:** `docs/levels/level-03-advanced-retrieval/{experiments,lessons-learned}.md` — measured matrix/ablation/latency/per-category tables; SC-003 refuted on this corpus (hybrid R@10 0.94 < vector 0.98); reranker measured not to pay on CPU (×154 ms for −0.04 R@5, +0.026 MRR); rewritten-query axis recorded TBD (no gateway) per FR-024

### Fixed
- **`evaluate --answers` default dataset (latent Level 2 CLI bug):** bare `--answers` resolved its path from `settings.eval_dataset_path` (the retrieval dataset) and crashed grounded-case validation; now defaults to `settings.grounded_dataset_path`, pinned by `test_evaluate_answers_flag_defaults_to_grounded_dataset`

### Notes
- Levels 0/1/2 behavior preserved (FR-027/SC-008): Level 2 suites pass unchanged; only additive Level 0 tests (front matter); full suite 270 green
- Measured winners (28 questions): vector = default (R@5 0.90, R@10 0.98); hybrid wins multi-concept only; BM25 guarantees exact-term anchors + filtered coverage at 1.6 ms; all conclusions from measurements, not assumptions

## [0.4.0] - 2026-10-07

### Added
- **Evidence objects (FR-001/002):** `src/grounding/evidence_builder.py` projects retrieval results into stable `EVIDENCE-nnn` objects (id, document_id, chunk_id, title, source, text, retrieval_score, rank)
- **Structured grounded answers (FR-003/004):** `GroundedAnswer` schema (answer + citations + abstained/sufficient_evidence/conflicts) with `extra="forbid"`; `generate_json` in `src/generation/llm.py` (400/422 retry); `parse_grounded_answer` raises `StructuredOutputError` on malformed output (contract rule 1)
- **Citation validation (FR-007/008):** `src/grounding/citation_validator.py` — MALFORMED/UNKNOWN_DOCUMENT/UNKNOWN_CHUNK/NOT_RETRIEVED/VALID verdicts, duplicate-invariant (SC-002); invalid citations never displayed
- **Abstention (FR-011/012):** `src/grounding/abstention.py` `decide()` layered over evidence count/threshold/model report; pipeline abstains instead of fabricating; legacy `used_context/abstention` keys preserved
- **Conflict reporting (FR-019):** contradictory evidence surfaced as `Conflicts:` blocks (named sources), never merged
- **Debug grounding (FR-013/014):** `--debug-grounding` prints the full grounding path (Retrieved Evidence / sufficiency / Generated Answer / Citations / Validation / Conflicts / Final Response)
- **Two-layer evaluation (FR-015/016):** `evaluate --answers` (or `--dataset data/evaluation/grounded_answers.jsonl`) reports a separately-labeled answer layer — correctness, abstention accuracy, citation validity, citation completeness, groundedness counts (Principle XXII); `data/evaluation/grounded_answers.jsonl` with answerable/unanswerable/partial/conflict cases
- **Groundedness (research R4):** `src/evaluation/groundedness.py` deterministic lexical claim/evidence support baseline + `GroundednessJudge` Protocol/`StructuredJudge` for isolated live judging
- **Prompt-strategy experiments (FR-023/SC-009):** strategies A-D over the grounded dataset, recorded in `docs/levels/level-02-grounded-rag/experiments.md`; `scripts/run_grounded_experiments.py` (deterministic `CopyOracle` by default, live via `--oracle llm`)
- **Lessons learned (FR-024):** `docs/levels/level-02-grounded-rag/lessons-learned.md` incl. the FR-018 failure-attribution procedure (retrieval vs generation/grounding)
- **Corpus:** `data/documents/5g_speed.md` + `data/documents/5g_speed_reporting.md` (marketing-vs-reality conflict/partial sources), 10 docs → 20 chunks
- **Test suite (155 tests):** evidence, answer schema, citation validator, abstention, grounding, answer evaluation, experiment harness, six hallucination scenarios, six named Level 2 regressions (FR-021); ruff + mypy clean; Suite hermetic (FR-022)

### Changed
- **CLI `query`:** grounded path by default (evidence → sufficiency → generation → citation validation); `Sources:` lists only VALID citations; FAIL banner + exit code when validation fails; conflict lines under normal mode
- **CLI `evaluate`:** retrieval layer unchanged; `--answers`/`--answers-dataset` and grounded-dataset auto-detection route to the answer layer
- **`RAGPipeline.run()`** delegates to `run_grounded()` (research R7), preserving every legacy key; grounded extras are additive (`evidence`, `grounded_answer`, `citation_validation`, `evidence_sufficiency`, `abstained`, `sufficient_evidence`, `conflicts`)
- **Config:** `grounded_dataset_path`, grounding `sufficiency_threshold` / `min_evidence` / `structured_output` settings

### Fixed
- Groundedness verdicts never score abstention text as a claim (US6/T036)
- Citation validation deduplicates identical `(document_id, chunk_id)` pairs (first wins)

## [0.3.0] - 2026-10-06

### Added
- **Real embeddings (FR-001/002):** `sentence-transformers` `BAAI/bge-small-en-v1.5` (384-d) replaces the fake hash embedder; explicit dimension getter for backward compat
- **Persistent ChromaDB store (FR-003/015/016):** metadata-preserving vector store with cosine space, `score = 1 - distance` in `src/retrieval/vector_store.py`, collection reset on re-ingest (FR-016)
- **Typer CLI (FR-007/017):** `ingest`, `query`, `evaluate` commands; `--debug-retrieval` (document_id :: chunk_id :: filename + score); `--top-k`/`--threshold`; non-zero exit with clear error when the LLM is unavailable
- **Config polish:** Pydantic-settings YAML + env overrides (`settings.yaml`, `LLM_*`, `CHUNK_*`, `TOP_K`, `SIMILARITY_THRESHOLD`), validation of chunk size/overlap/top-k/threshold
- **Retrieval evaluation (constitution XVI, US4):** `evaluate` command, `data/evaluation/retrieval_questions.jsonl` (27 questions, 3 unanswerable), Recall@K/Precision@K/MRR metrics, true-negative/false-positive reporting for unanswerable questions
- **Docs:** updated quickstart (§1–§7 scenarios with SC-001…SC-009 evidence), `README.md` uv setup, `CHANGELOG.md` feature entry
- **Test suite (61 tests):** rewritten Level 0 CLI/tests for Typer + ChromaDB, config tests, evaluation tests; ruff + mypy clean

### Changed
- **CLI output:** four-block protocol preserved (Question / Retrieved Documents / Answer); debug diagnostics added under `--debug-retrieval`
- **Packaging:** `[tool.setuptools.packages.find]` `include=["src*"]`, `src/__init__.py` sys.path bootstrap for the `telco-rag` console script

### Fixed
- **Embedder deprecation:** prefer `get_embedding_dimension`, fall back to `get_sentence_embedding_dimension`
- **mypy module mapping:** `explicit_package_bases` + exclude `src/__main__.py` resolves the `src.evaluation` vs `evaluation` duplicate-module error


## [0.2.0] - 2026-10-06

### Added
- **Base project scaffolding:** `src/telco_rag/` package (config, domain, CLI, embeddings, generation, ingestion, retrieval, RAG pipeline), `data/documents/` with 8 synthetic Telco markdown documents, `tests/conftest.py`, loader and chunker tests
- **Deterministic test suite (22 tests, spec FR-012):** `test_vector_store.py` (6), `test_retriever.py` (5), `test_prompt.py` (4), `test_rag_pipeline.py` (4), `test_cli_output.py` (3)
- **CLI:** four-block stdout protocol (Question / Retrieved Documents / Answer), exit codes 0/1/2
- **Configuration:** validated environment variables (`LLM_BASE_URL`, `LLM_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`)

### Fixed
- **Vector store:** L2-normalization `np.linalg.norm(..., axis)` → `axis=1` bug in `src/telco_rag/retrieval/vector_store.py`

### Changed
- **pyproject.toml:** added `sentence-transformers`, `numpy`, `httpx` dependencies, `telco-rag` console script, pytest configuration


## [0.0.1] - 2026-08-16

### Added
- **Project scaffold:** `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, test directory structure


## [0.0.1-pre] - 2026-08-16

### Added
- **Cleanup repo:**

