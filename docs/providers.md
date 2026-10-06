# Provider Architecture

## 1. Purpose

The `telco-rag` platform must remain independent from specific external AI providers.

The system will initially use OpenRouter, but OpenRouter must be an infrastructure adapter rather than a dependency throughout the application.

Provider abstraction applies primarily to:

* LLMs.
* Embedding models.
* Rerankers.
* Future AI services.

The architecture must allow providers or models to change without rewriting the domain or application layers.

---

# 2. Provider Independence Principle

The dependency direction is:

```text
Domain
   ↑
Application
   ↑
Provider Interfaces
   ↑
Infrastructure Adapters
   ├── OpenRouter
   ├── Future Provider A
   └── Future Provider B
```

The application must depend on provider interfaces.

Infrastructure implements those interfaces.

---

# 3. Initial Provider

The initial AI provider is:

```text
OpenRouter
```

OpenRouter provides access to supported LLM and embedding models through a common API.

The application should not import OpenRouter-specific SDK types outside the infrastructure provider adapter.

---

# 4. Provider Categories

The platform defines these provider abstractions:

```text
LLMProvider
EmbeddingProvider
RerankerProvider
```

Future abstractions may include:

```text
SpeechProvider
VisionProvider
ModerationProvider
OCRProvider
```

These should only be introduced when required by the product.

---

# 5. LLM Provider

The LLM provider is responsible for text generation.

Conceptual interface:

```python
class LLMProvider(Protocol):
    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        ...
```

The interface should hide:

* HTTP implementation.
* Authentication.
* Provider-specific request format.
* Provider-specific response format.
* Retry behavior.
* Timeout handling.
* Provider errors.

---

# 6. LLM Request

The application should construct a provider-independent request.

Example:

```python
class LLMRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float = 0.0
    max_tokens: int | None = None
    timeout_seconds: int = 30
```

Provider-specific fields should not leak into this model unless they are part of the common abstraction.

---

# 7. LLM Response

The provider should return a normalized response.

Example:

```python
class LLMResponse(BaseModel):
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None
    request_id: str | None = None
```

The application should not depend on provider-specific response objects.

---

# 8. Structured Output

The provider abstraction should support structured output where the selected model/provider supports it.

Conceptually:

```python
class StructuredLLMRequest(BaseModel):
    schema: dict
    ...
```

The generation layer should validate the result with Pydantic.

Provider-specific structured-output behavior remains inside the adapter.

---

# 9. Embedding Provider

Embedding generation must use an independent abstraction.

Conceptual interface:

```python
class EmbeddingProvider(Protocol):
    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        ...
```

The embedding implementation must guarantee:

* Stable vector dimensions.
* Correct ordering.
* Deterministic association between input and output.
* Batch handling.
* Error reporting.

---

# 10. Embedding Model Identity

Every stored embedding must be associated with:

* Provider.
* Model.
* Model version if available.
* Dimension.
* Creation timestamp.

Example:

```text
provider = openrouter
model = <embedding-model>
dimension = 1536
```

The actual configured model must come from configuration.

---

# 11. Embedding Model Changes

Changing the embedding model can invalidate the vector index.

Therefore:

```text
Change Embedding Model
        ↓
Validate Dimensions
        ↓
Create New Embedding Version
        ↓
Re-embed Documents
        ↓
Rebuild Vector Index
        ↓
Validate Retrieval
        ↓
Activate New Version
```

The system must not silently mix incompatible embedding spaces.

---

# 12. Reranker Provider

Reranking should also use an abstraction.

Conceptual interface:

```python
class RerankerProvider(Protocol):
    def rerank(
        self,
        query: str,
        documents: list[DocumentCandidate],
    ) -> list[RankedDocument]:
        ...
```

The retrieval layer must not depend directly on a specific reranking vendor.

---

# 13. Provider Adapter Structure

Recommended structure:

```text
src/telco_rag/infrastructure/
├── llm/
│   ├── client.py
│   └── openrouter.py
│
├── embeddings/
│   ├── client.py
│   └── openrouter.py
│
└── reranking/
    ├── client.py
    └── <provider>.py
```

The interface may eventually move into an application-facing ports package if required by the architecture.

---

# 14. OpenRouter Adapter

The OpenRouter adapter is responsible for:

* Authentication.
* Request construction.
* HTTP communication.
* Provider-specific headers.
* Timeouts.
* Retries.
* Response parsing.
* Error normalization.
* Usage extraction.
* Provider telemetry.

Example conceptual flow:

```text
GenerationService
       │
       ▼
LLMProvider
       │
       ▼
OpenRouterAdapter
       │
       ▼
OpenRouter API
```

---

# 15. API Key Management

Provider credentials must be supplied through configuration.

Example:

```text
OPENROUTER_API_KEY
```

The API key must never:

* Appear in source code.
* Appear in Git.
* Appear in logs.
* Appear in traces.
* Be returned through API responses.
* Be stored in generated prompts.

---

# 16. Provider Errors

Provider-specific errors must be normalized.

Example application-level errors:

```text
ProviderAuthenticationError
ProviderRateLimitError
ProviderTimeoutError
ProviderUnavailableError
ProviderInvalidRequestError
ProviderResponseError
```

The application should not need to understand provider-specific HTTP status codes.

---

# 17. Retry Policy

Retries must be controlled.

Retry candidates may include:

* Temporary network errors.
* Provider timeouts.
* Transient service-unavailable responses.
* Rate limiting when retry-after information is available.

Retries should not occur for:

* Invalid API keys.
* Invalid requests.
* Invalid model names.
* Invalid structured-output schemas.
* Authorization failures.

Retry behavior must be configurable.

---

# 18. Timeout Policy

Every provider operation must have a bounded timeout.

Example:

```yaml
llm:
  timeout_seconds: 30

embeddings:
  timeout_seconds: 30
```

No external provider call may block indefinitely.

---

# 19. Rate Limiting

Provider rate limits must be treated as normal operational conditions.

The system should:

1. Detect rate limiting.
2. Capture provider metadata.
3. Respect retry-after information where available.
4. Apply bounded retry behavior.
5. Return a normalized failure when the operation cannot continue.

---

# 20. Model Selection

Model selection must be configuration-driven.

Example:

```yaml
llm:
  provider: openrouter
  model: <configured-model>
```

Application code must not contain hard-coded model identifiers.

---

# 21. Model Routing

Future model routing may select models based on:

* Query complexity.
* Cost.
* Latency.
* Required context length.
* Structured output requirements.
* Quality requirements.

Example:

```text
Simple Query
    → Low-cost Model

Complex Investigation
    → Higher-quality Model
```

This capability should be introduced only after baseline RAG quality is established.

---

# 22. Cost Tracking

Provider responses should capture usage when available.

Useful fields include:

```text
input_tokens
output_tokens
total_tokens
estimated_cost
model
provider
```

Cost information should feed observability and evaluation.

---

# 23. Provider Observability

Every provider call should produce telemetry.

Recommended fields:

```text
provider
model
operation
request_id
latency_ms
input_tokens
output_tokens
retry_count
status
error_type
estimated_cost
```

Sensitive content must not be logged by default.

---

# 24. Provider Fallbacks

Provider fallback may eventually support:

```text
Primary Provider
       ↓
Failure
       ↓
Fallback Provider
```

Fallback must not be introduced prematurely.

Before enabling fallback, the system must define:

* Quality compatibility.
* Security compatibility.
* Model capability compatibility.
* Cost implications.
* Evaluation requirements.

A fallback model must not silently reduce security requirements.

---

# 25. Provider Compatibility

Providers must satisfy explicit capability requirements.

Example capabilities:

```text
text_generation
structured_output
embeddings
reranking
streaming
tool_calling
```

The application may inspect capabilities before selecting a provider.

---

# 26. Provider Contract Testing

Every provider adapter should pass contract tests.

Tests must verify:

* Request construction.
* Response normalization.
* Error mapping.
* Timeout behavior.
* Retry behavior.
* Usage extraction.
* Structured output.
* Authentication failure handling.

External provider tests should be separated from deterministic unit tests.

---

# 27. Fake Providers

Tests must have fake implementations.

Example:

```python
class FakeLLMProvider:
    ...
```

Fake providers allow testing:

* Application services.
* Generation.
* Query processing.
* Error handling.
* Evaluation.

without requiring external network access.

---

# 28. Provider Security

Provider integration must enforce:

* Secret isolation.
* TLS.
* Request timeout.
* Response validation.
* Input size limits.
* Output validation.
* Sensitive-data controls.

The provider must never receive unauthorized documents.

Security filtering happens before provider invocation.

---

# 29. Provider and Grounding

The LLM provider is not the source of truth.

The system of record is:

```text
Enterprise Knowledge
        ↓
Authorized Retrieval
        ↓
Evidence
        ↓
Grounded Prompt
        ↓
LLM
```

The model generates an answer from authorized evidence.

The model itself does not establish enterprise truth.

---

# 30. Provider and Agentic RAG

Future agents will use the same provider abstraction.

An agent may request:

```text
LLMProvider
EmbeddingProvider
RerankerProvider
```

Agents must not bypass provider abstraction to call external APIs directly.

---

# 31. Configuration

Provider selection belongs in configuration.

Example:

```yaml
llm:
  provider: openrouter
  model: <configured-model>

embeddings:
  provider: openrouter
  model: <configured-embedding-model>

reranking:
  provider: none
```

---

# 32. Provider Package

Recommended structure:

```text
src/telco_rag/infrastructure/
├── llm/
│   ├── client.py
│   └── openrouter.py
├── embeddings/
│   ├── client.py
│   └── openrouter.py
└── reranking/
    ├── client.py
    └── openrouter.py
```

Provider interfaces should remain independent of concrete implementations.

---

# 33. Definition of Done

Provider architecture is complete when:

* LLM provider abstraction exists.
* Embedding provider abstraction exists.
* Reranker provider abstraction exists.
* OpenRouter adapters exist.
* Provider errors are normalized.
* Timeouts exist.
* Retry policies exist.
* Credentials are externalized.
* Model selection is configurable.
* Usage can be recorded.
* Provider telemetry exists.
* Fake providers exist.
* Contract tests exist.
* Application code does not depend directly on OpenRouter.
* Domain code has zero provider dependencies.

---

# 34. Final Rule

**The application chooses capabilities; infrastructure chooses how those capabilities are implemented.**

OpenRouter is the initial provider, not the architecture.

