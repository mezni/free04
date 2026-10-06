# Changelog

All notable changes to `project` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec.php#pec-2.0.0).

## Version History

| Version | Feature Domain | Key Objectives |
|---------|---------------|----------------|
| 0.2-pre | Level 0 — Naive RAG Baseline | First working RAG pipeline with deterministic tests |
| 0.0.1   | Project          | Scaffold|
| 0.1-pre | Repo       | Cleanup|


## [0.2-pre] - 2026-10-06

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

