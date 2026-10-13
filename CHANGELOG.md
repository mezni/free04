# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Step 2: Pydantic domain models (`Category`, `TriageResult`) in `src/triagekit/models.py`
- Structured output via forced tool use (`LLMClient.complete_structured`), with validation-error feedback and bounded retries
- Step 3: versioned prompt module `src/triagekit/prompts.py` with category definitions, precedence rules, a 0–1 confidence scale, 9 import-validated few-shot examples, and a `wrap_ticket()` data-delimiter helper
- `classify_with_llm` wrapper (`src/triagekit/llm_classifier.py`) and `scripts/classify_llm.py` demo
- Tests: `tests/test_prompts.py`, `tests/test_llm_structured.py`

### Changed
- `Settings` now reads `ANTHROPIC_API_KEY` and `TRIAGEKIT_MODEL` from the environment; explicit `api_key=None` still disables the key
- `docs/steps.md`: documented Step 3

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