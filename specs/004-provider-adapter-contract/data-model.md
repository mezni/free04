# Data Model: Provider Adapter Contract

## Entity: AdapterPort

**Description**: The canonical interface that all provider adapters implement, defining the contract for request/response conversion and capability declaration.

**Fields**:
- `id`: UUIDv7, unique adapter port identifier
- `name`: string, adapter name (e.g., "ollama", "vllm", "openai")
- `capability_declarator`: fn() -> CapabilityDescriptor, returns the adapter's capabilities
- `convert_request`: fn(canonical_request: CanonicalRequest) -> WireFormat, converts canonical to provider wire format
- `convert_response`: fn(wire_format: WireFormat) -> CanonicalResponse, converts provider response to canonical format

**Relationships**:
- Implemented by: **Adapter** entities (one-to-many)
- Used by: **Routing** engine, **Contract Tests**

---

## Entity: CapabilityDescriptor

**Description**: Standardized description of provider capabilities, enabling capability-aware routing decisions.

**Fields**:
- `id`: UUIDv7, unique capability descriptor identifier
- `tools`: boolean, whether the provider supports tool use/function calling
- `json_mode`: boolean, whether the provider supports JSON mode response formatting
- `vision`: boolean, whether the provider supports multimodal/image inputs
- `context_window`: u32, maximum context window in tokens supported by the provider
- `streaming`: boolean, whether the provider supports streaming token response

**Relationships**:
- Referenced by: **AdapterPort** (one-to-one)
- Consumed by: **Routing policy engine** (FR-ENG-07), **Declarative routing** (AD-5)

---

## Entity: CanonicalRequest

**Description**: The normalized, provider-agnostic request format that all adapters convert from and to. This is the single source of truth for request processing within the gateway.

**Fields**:
- `id`: UUIDv7, unique request identifier
- `model_alias`: string, requested model alias (e.g., "auto", "fast", "cheap", "smart")
- `messages`: vec<ChatMessage>, conversation history
- `stream`: boolean, whether streaming is enabled
- `tools`: optional vec<ToolDefinition>, tool use configuration
- `temperature`: optional f64, sampling temperature
- `max_tokens`: optional u32, maximum tokens in response
- `top_p`: optional f64, nucleus sampling parameter
- `stop`: optional vec<string>, stop sequence strings
- `metadata`: optional map<string, string>, additional metadata

**Relationships**:
- Received from: **Transport/Validate stage**
- Converted by: **AdapterPort** → **Wire Format**
- Referenced by: **Routing policy** (cost, latency, residency, capability checks)
- Produces: **Usage events** (AD-9, AD-15)

---

## Entity: WireFormat

**Description**: The provider-specific request/response format (e.g., Ollama format, vLLM format, OpenAI format). Each adapter translates between canonical and wire format.

**Fields** (abstract; concrete fields per adapter):
- `id`: UUIDv7, unique wire format identifier
- `adapter_name`: string, which adapter produced/consume this format
- `raw_request`: bytes, provider-specific serialized request
- `raw_response`: bytes, provider-specific serialized response
- `mime_type`: string, content type (e.g., "application/json")

**Concrete adapter specializations**:
- **OllamaWireFormat**: `raw_request` contains model, messages, stream, options; `raw_response` contains response, done flag
- **vLLMWireFormat**: `raw_request` contains prompt, sampling parameters; `raw_response` contains token-by-token output
- **OpenAIWireFormat**: `raw_request` matches OpenAI Chat Completions JSON; `raw_response` matches OpenAI Chat Completions response schema

**Relationships**:
- Produced by: **AdapterPort** → **Adapter** implementation
- Consumed by: **Transport/Route stage**
- Referenced by: **Contract tests**

---

## Entity: ErrorTaxonomy

**Description**: The shared error classification and mapping scheme that translates provider-specific errors into the OpenAI-compatible error envelope with gateway error codes and request IDs.

**Fields**:
- `id`: UUIDv7, unique error taxonomy identifier
- `gateway_error_code`: string, mapped error code (e.g., "invalid_request", "context_length_exceeded", "rate_limit_error", "internal_server_error", "service_unavailable")
- `provider_error_code`: string, original provider error code for reference
- `category`: string, error category (e.g., "validation", "rate_limit", "server_error", "connection_error")
- `retryable`: boolean, whether the error is eligible for retry (per FR-RES-02, AD-3)
- `max_retry_attempts`: u32, maximum retry attempts if retryable
- `description`: human-readable error description

**Relationships**:
- Mapped from: **Adapter** failure handling
- Consumed by: **Client** calling the gateway
- Referenced by: **FR-RES-02**, **AD-3**, **AD-11**

---

## Entity: Adapter

**Description**: A concrete implementation of the adapter port for a specific provider (Ollama, vLLM, OpenAI). Each adapter satisfies the adapter port interface.

**Fields**:
- `id`: UUIDv7, unique adapter identifier
- `name`: string, adapter name matching the capability descriptor
- `provider`: string, provider identifier (e.g., "ollama", "vllm", "openai")
- **Implements**: **AdapterPort** (trait implementation)
- **Declares**: **CapabilityDescriptor** via `declare_capabilities()` method

**Relationships**:
- Implements: **AdapterPort** (one-to-one)
- Declares: **CapabilityDescriptor** (one-to-one)
- Used by: **Routing engine** (to build candidate target list)
- Tested by: **Contract tests** (against mock servers)

---

## Entity: ContractTest

**Description**: A test that verifies an adapter satisfies the adapter port interface against a mock server. Ensures all adapter contract requirements pass.

**Fields**:
- `id`: UUIDv7, unique contract test identifier
- `adapter_name`: string, which adapter is being tested
- `test_scenario`: string, name of the scenario (e.g., "request_conversion", "capability_declaration", "error_mapping")
- `status`: enum [pass, fail], test result
- `details`: string, test output or error details

**Relationships**:
- Tested **Adapter** (one-to-many)
- Part of: **Quality gate** for adapter integration

## Validation Rules (from Requirements)

| Requirement | Validation Rule |
|-------------|-----------------|
| FR-ENG-01 | `/v1/chat/completions` endpoint accepts OpenAI Chat Completions schema and returns response matching that schema |
| FR-ENG-06 | Adapters declare capabilities through CapabilityDescriptor; routing excludes targets lacking required capabilities |
| FR-RES-02 | Adapters never retry 4xx (except configured 429) and never retry after first streamed token |
| AD-4 | Adapter port contract with capability descriptor and error taxonomy is enforced (E1.S4) |
| AD-11 | Stable OpenAI-compatible error envelope; no raw provider errors in response |