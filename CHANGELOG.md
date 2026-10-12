# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-12

### Added
- Initial release of triagekit-agent
- AI agent for support-ticket triage
- Basic triage functionality
- Step 0: Reproducible repo init (`uv sync && uv run pytest`, `ruff check .`)
- Step 1: First LLM call wrapper (`llm_client.py`) with env key, timeout, retry with backoff
- Step 1 demo script (`scripts/hello_llm.py`)

### Changed
- Added `src/triagekit/config.py` Settings class
- Added `tests/test_llm_client.py` with 8 unit tests