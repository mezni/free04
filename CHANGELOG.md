# Changelog

All notable changes to `project` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec.php#pec-2.0.0).

## Version History

| Version | Feature Domain | Key Objectives |
|---------|---------------|----------------|
| 0.3.0 | Level 1 — RAG Foundations | Real embeddings + ChromaDB, typed metadata, Typer CLI, retrieval evaluation, config polish |
| 0.2.0 | Level 0 — Naive RAG Baseline | First working RAG pipeline with deterministic tests |
| 0.0.1   | Project          | Scaffold|
| 0.1-pre | Repo       | Cleanup|


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


## [0.1-pre] - 2026-08-16

### Added
- **Cleanup repo:**

