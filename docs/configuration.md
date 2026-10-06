# Configuration Architecture

## 1. Purpose

Configuration is a first-class architectural concern of the `telco-rag` platform.

The configuration system must provide:

* Strongly typed configuration.
* Environment-specific configuration.
* Secure secret handling.
* Deterministic configuration precedence.
* Validation at application startup.
* Separation between configuration and business logic.
* Easy testing.
* Safe production defaults.
* Provider-independent configuration.
* Runtime visibility without exposing secrets.

The configuration system must prevent application code from directly reading environment variables or configuration files.

The application should receive validated configuration objects through dependency injection.

---

# 2. Configuration Principles

## 2.1 Strongly Typed Configuration

All application configuration must be represented by typed Pydantic models.

Example:

```python
from pydantic import BaseModel


class DatabaseSettings(BaseModel):
    url: str
    pool_size: int = 10
    max_overflow: int = 20
```

Configuration errors must fail fast.

---

## 2.2 Configuration Is Not Domain Data

Configuration belongs outside the domain model.

The domain must not know about:

* Environment variables.
* YAML files.
* Docker.
* PostgreSQL URLs.
* OpenRouter API keys.
* FastAPI settings.
* Deployment profiles.

The domain receives values through application services or domain value objects.

---

## 2.3 Secrets Are Not Stored in YAML

Secrets must never be committed to Git.

Examples:

* API keys.
* Database passwords.
* Authentication secrets.
* Encryption keys.
* Provider credentials.

Development secrets may be supplied through `.env`.

Production secrets must come from the deployment environment or a dedicated secret-management system.

---

# 3. Configuration Layers

The configuration architecture consists of:

```text
Environment Variables
        │
        ▼
Secret Configuration
        │
        ▼
YAML Configuration
        │
        ▼
Environment Profile
        │
        ▼
Pydantic Validation
        │
        ▼
Application Settings
        │
        ▼
Application Components
```

The application must consume only the final validated configuration object.

---

# 4. Configuration Categories

The system should organize configuration into the following categories:

```text
Application
Database
LLM
Embeddings
Retrieval
Ingestion
Generation
Security
Evaluation
Observability
API
Performance
Feature Flags
```

---

# 5. Configuration Files

The project uses:

```text
config/
├── settings.yaml
├── ingestion.yaml
├── retrieval.yaml
├── evaluation.yaml
├── security.yaml
├── observability.yaml
└── profiles/
    ├── dev.yaml
    ├── test.yaml
    └── prod.yaml
```

The files contain non-secret configuration.

Secrets are supplied separately.

---

# 6. Base Configuration

`settings.yaml` defines configuration shared across environments.

Example:

```yaml
application:
  name: telco-rag
  environment: dev
  debug: false

api:
  prefix: /api/v1

database:
  pool_size: 10
  max_overflow: 20

llm:
  provider: openrouter

embeddings:
  provider: openrouter

retrieval:
  top_k: 10
```

---

# 7. Environment Profiles

Environment-specific differences belong in:

```text
config/profiles/
```

Example:

```yaml
# dev.yaml

application:
  debug: true

observability:
  log_level: DEBUG

retrieval:
  top_k: 5
```

Production:

```yaml
# prod.yaml

application:
  debug: false

observability:
  log_level: INFO

retrieval:
  top_k: 10
```

Production configuration must prioritize safety over convenience.

---

# 8. Configuration Precedence

Configuration precedence must be deterministic.

The recommended order is:

```text
Lowest Priority
    │
    ▼
Default Values
    │
    ▼
Base YAML
    │
    ▼
Environment Profile
    │
    ▼
Environment Variables
    │
    ▼
Runtime Overrides
    │
    ▼
Highest Priority
```

Runtime overrides should be restricted to explicitly supported configuration.

---

# 9. Environment Variables

Environment variables are primarily used for:

* Secrets.
* Deployment-specific values.
* Infrastructure endpoints.
* Configuration that must vary outside source control.

Example:

```text
DATABASE_URL
OPENROUTER_API_KEY
ENVIRONMENT
LOG_LEVEL
```

Application code must not repeatedly call:

```python
os.getenv(...)
```

throughout the codebase.

Instead:

```text
Environment
    ↓
Settings Loader
    ↓
Validated Settings
    ↓
Dependency Injection
```

---

# 10. Pydantic Settings

The configuration implementation should use Pydantic Settings.

Example:

```python
from pydantic_settings import BaseSettings


class EnvironmentSettings(BaseSettings):
    environment: str = "dev"
    debug: bool = False

    class Config:
        env_file = ".env"
```

Nested settings should be modeled separately.

Example:

```python
class LLMSettings(BaseModel):
    provider: str
    model: str
    temperature: float = 0.0
    timeout_seconds: int = 30
```

The complete application settings object can then compose these models.

---

# 11. Application Settings Model

The root configuration should provide one application settings object.

Conceptually:

```python
class Settings(BaseModel):
    application: ApplicationSettings
    api: APISettings
    database: DatabaseSettings
    llm: LLMSettings
    embeddings: EmbeddingSettings
    retrieval: RetrievalSettings
    ingestion: IngestionSettings
    security: SecuritySettings
    evaluation: EvaluationSettings
    observability: ObservabilitySettings
```

Components should receive only the configuration they need where practical.

---

# 12. Database Configuration

Database configuration includes:

```yaml
database:
  url: ...
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 1800
  echo: false
```

The database URL should normally be supplied through an environment variable.

Example:

```text
DATABASE_URL=postgresql+psycopg://...
```

Credentials must never be committed.

---

# 13. LLM Configuration

LLM configuration must remain provider-independent.

Example:

```yaml
llm:
  provider: openrouter
  model: <configured-model>
  temperature: 0.0
  timeout_seconds: 30
  max_retries: 2
```

Application code should depend on:

```python
LLMProvider
```

rather than:

```python
OpenRouterClient
```

This allows the provider to change without changing application or domain code.

---

# 14. Embedding Configuration

Example:

```yaml
embeddings:
  provider: openrouter
  model: <configured-embedding-model>
  batch_size: 32
  timeout_seconds: 30
```

Embedding dimensions must be validated against the database schema.

A change to embedding model or dimensions must trigger an explicit migration/reindex strategy.

---

# 15. Retrieval Configuration

Retrieval configuration controls:

* Candidate count.
* Top K.
* Vector search.
* Keyword search.
* Hybrid search.
* Reranking.
* Filtering.

Example:

```yaml
retrieval:
  top_k: 10

  candidate_k:
    vector: 20
    keyword: 20

  vector:
    enabled: true

  keyword:
    enabled: true

  hybrid:
    enabled: true
    method: rrf

  reranking:
    enabled: false
    top_n: 20
    final_k: 8

  filters:
    require_active_document: true
    require_authorization: true
```

Security-related retrieval configuration must not be user-overridable.

---

# 16. Ingestion Configuration

Ingestion configuration includes:

```yaml
ingestion:
  supported_extensions:
    - .pdf
    - .docx
    - .md
    - .txt

  max_file_size_mb: 50

  chunking:
    target_size: 800
    overlap: 100

  classification:
    require_classification: true

  quarantine:
    enabled: true
```

Unsafe or unsupported documents must not silently enter the searchable corpus.

---

# 17. Security Configuration

Security configuration includes:

* Authentication.
* Authorization.
* Classification enforcement.
* Access policy enforcement.
* Request limits.
* File upload limits.
* Security headers.
* Token configuration.

Example:

```yaml
security:
  require_authentication: true

  document_access:
    enforce: true

  ingestion:
    quarantine_unknown_classification: true

  uploads:
    max_size_mb: 50
```

Security must fail closed.

---

# 18. Observability Configuration

Example:

```yaml
observability:
  log_level: INFO

  logging:
    format: json

  tracing:
    enabled: true
    sample_rate: 0.1

  metrics:
    enabled: true
```

Production telemetry must not expose:

* API keys.
* Authorization headers.
* Passwords.
* Secrets.
* Unnecessary document contents.
* Sensitive user information.

---

# 19. Evaluation Configuration

Evaluation configuration controls:

* Dataset location.
* Retrieval K values.
* Generation evaluation.
* Evaluation thresholds.
* Judge configuration.

Example:

```yaml
evaluation:
  dataset_path: data/eval/questions.jsonl

  retrieval:
    k_values:
      - 1
      - 5
      - 10

  thresholds:
    recall_at_10: 0.80
```

Evaluation thresholds should be version controlled.

---

# 20. Configuration Validation

Configuration must be validated during startup.

Invalid configuration must prevent the application from starting.

Examples:

```text
Missing database URL
Invalid embedding dimension
Unknown LLM provider
Invalid retrieval top_k
Invalid environment name
Invalid timeout
Missing production secret
```

Configuration validation errors should identify the invalid field without exposing secret values.

---

# 21. Feature Flags

Feature flags may control experimental capabilities.

Examples:

```yaml
features:
  hybrid_retrieval: true
  reranking: false
  query_rewriting: false
  agentic_rag: false
```

Feature flags must not bypass security controls.

Security cannot be disabled through ordinary feature flags in production.

---

# 22. Configuration and Testing

Tests must be able to construct deterministic configuration.

Example:

```python
settings = Settings(
    application=...,
    database=...,
    retrieval=...,
)
```

Tests must not depend on developer machine configuration.

Test profiles should use:

* Local database.
* Fake providers.
* Deterministic settings.
* Disabled external telemetry where appropriate.

---

# 23. Configuration and Dependency Injection

The composition root loads configuration once.

Conceptually:

```text
main.py
   │
   ├── load_settings()
   │
   ├── create_database()
   │
   ├── create_llm_provider()
   │
   ├── create_embedding_provider()
   │
   ├── create_retriever()
   │
   └── create_application_services()
```

Business logic must not create global configuration objects.

---

# 24. Configuration Immutability

Once loaded, configuration should be treated as immutable.

Components should not mutate global configuration during execution.

Dynamic state belongs in:

* Database.
* Cache.
* Application state.
* Domain state.

It does not belong in static configuration.

---

# 25. Configuration Security

The following rules are mandatory:

1. Secrets must never be committed.
2. Secrets must never be logged.
3. Secrets must never appear in error messages.
4. Production must not rely on development `.env` files.
5. Security defaults must fail closed.
6. Unknown configuration must be rejected where possible.
7. Configuration changes must be reviewable.
8. Provider credentials must remain outside domain logic.

---

# 26. Configuration Package

Recommended implementation:

```text
src/telco_rag/config/
├── __init__.py
├── settings.py
├── loader.py
├── models.py
└── validation.py
```

Responsibilities:

### `models.py`

Pydantic configuration models.

### `loader.py`

Loads YAML, profiles, and environment variables.

### `settings.py`

Exposes the final application settings.

### `validation.py`

Performs cross-field and environment-specific validation.

---

# 27. Configuration Testing

Tests must verify:

* Default values.
* YAML loading.
* Profile overrides.
* Environment overrides.
* Secret loading.
* Invalid configuration.
* Production validation.
* Provider selection.
* Retrieval configuration.
* Security configuration.
* Feature flags.

---

# 28. Operational Requirements

The application should expose safe configuration metadata through diagnostics.

Example:

```json
{
  "environment": "prod",
  "llm_provider": "openrouter",
  "retrieval_hybrid": true,
  "reranking": false,
  "embedding_model": "<redacted>"
}
```

Secrets and sensitive values must be redacted.

---

# 29. Definition of Done

Configuration is complete when:

* All configuration is strongly typed.
* Pydantic validation is implemented.
* YAML configuration is supported.
* Environment profiles are supported.
* Environment variables can override configuration.
* Secrets are separated from source-controlled configuration.
* Startup validation exists.
* Production validation exists.
* Configuration can be replaced in tests.
* Provider selection is configurable.
* Retrieval configuration is configurable.
* Security configuration is fail-closed.
* Configuration is observable without exposing secrets.
* Tests cover configuration behavior.

---

# 30. Final Rule

The configuration system must provide **one validated, deterministic source of application configuration** while keeping secrets secure and preventing infrastructure configuration from leaking into the domain.

