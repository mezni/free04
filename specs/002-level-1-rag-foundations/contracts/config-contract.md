# Contract: Configuration

**Silent goal**: every tunable lives in one file so SC-004 (config-only
experiments) and FR-005/006/011 are met. Precedence: env var > YAML >
code default.

**Implementation**: `src/config.py` migrates to `pydantic-settings`
(model fields on `Settings(BaseSettings)`).
`PYDANTIC_SETTINGS` config sources: `config/settings.yaml` (via a
`settings_yaml` `BaseSettings` subclass or explicit YAML loader) as the
base, environment variables as overrides. `.env` support retained (current
behavior) but YAML is the primary artifact.

## Schema — `config/settings.yaml`

```yaml
corpus:
  document_dir: data/documents          # env: DOCUMENT_DIR

chunking:
  chunk_size: 500                       # env: CHUNK_SIZE  (> 0)
  chunk_overlap: 50                     # env: CHUNK_OVERLAP (0 <= overlap < chunk_size)

retrieval:
  top_k: 4                              # env: TOP_K  (>= 1)
  similarity_threshold: 0.0             # env: SIMILARITY_THRESHOLD ([-1,1]; 0.0 => no filtering)
  vector_db_path: data/chroma           # env: VECTOR_DB_PATH
  collection: telco_documents           # env: VECTOR_COLLECTION

embedding:
  provider: local-sentence-transformers # env: EMBEDDING_PROVIDER
  model: BAAI/bge-small-en-v1.5         # env: EMBEDDING_MODEL   (default; tests use all-MiniLM-L6-v2)

evaluation:
  dataset_path: data/evaluation/retrieval_questions.jsonl  # env: EVAL_DATASET_PATH
  default_k: 5                          # env: EVAL_K

llm:
  base_url: https://openrouter.ai/api/v1 # env: LLM_BASE_URL (required, current behavior)
  api_key: ""                            # env: LLM_API_KEY  (never committed; .env / env)
  model: ""                              # env: LLM_MODEL    (required)
  max_tokens: 512                        # env: LLM_MAX_TOKENS (>= 1)
  temperature: 0.0                       # env: LLM_TEMPERATURE (0..2)
```

## Validation Rules (fail fast, exit 1)

- `chunk_size > 0`
- `0 <= chunk_overlap < chunk_size` (spec Edge Case)
- `top_k >= 1`
- `-1 <= similarity_threshold <= 1`
- `0 <= llm.temperature <= 2`; `llm.max_tokens >= 1`
- `llm.base_url` and `llm.model` non-empty (Level 0 regression)

## Secrets

`api_key` MUST NOT be committed. `.env.example` documents it; `.env`
gitignored (constitution X). The settings file itself contains only the empty
default.

## Backward Compatibility

Existing env names (`DOCUMENT_DIR`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`,
`EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`) keep working unchanged —
Level 0 tests and CI env are unaffected (SC-005).