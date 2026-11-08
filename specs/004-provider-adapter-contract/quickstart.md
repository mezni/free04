# Quickstart: Provider Adapter Contract Validation

## Prerequisites

- Gateway Cargo workspace built (`cargo build --workspace` or `cargo build -p llmgw-gateway`)
- Mock provider servers running for contract tests (see `contracts/contract.md` for adapter interface)
- Test infrastructure: `cargo test -p llmgw-gateway` (runs unit, integration, and contract tests)
- Rust toolchain 1.75+ (project uses 1.99.1)

## Setup

1. **Build the gateway workspace**:

   ```bash
   cargo build -p llmgw-gateway
   ```

2. **Start mock provider servers** (Ollama, vLLM, OpenAI mocks) for contract test integration:

   ```bash
   # Example: start Ollama mock server
   cargo run -p ollama-mock-server -- --port 11434

   # Example: start vLLM mock server
   cargo run -p vllm-mock-server -- --port 8000

   # Example: start OpenAI mock server
   cargo run -p openai-mock-server -- --port 8001
   ```

3. **Run contract tests** to verify adapter compliance:

   ```bash
   cargo test -p llmgw-gateway --lib contract::*
   ```

## Validation Scenarios

### Scenario 1: Adapter Contract Conversion

**Purpose**: Verify that each adapter (Ollama, vLLM, OpenAI) can convert a canonical request to its wire format and back without loss of required information (SC-001).

**Steps**:

1. Construct a canonical `ChatCompletionRequest` with model "gpt-3.5-turbo", a user message, and `stream=false`
2. Call `OllamaAdapter::convert_request(&request)` → expect `OllamaWireFormat` with correct payload
3. Call `OllamaAdapter::convert_response(&wire_format)` → expect `ChatCompletionResponse` matching OpenAI schema
4. Repeat steps 2-3 for `VllmAdapter` and `OpenAIAdapter`
5. Verify no provider-specific fields appear in the canonical response (SC-004)

**Expected outcome**: All three adapters successfully convert requests and responses; canonical output is provider-agnostic.

---

### Scenario 2: Capability Declaration

**Purpose**: Verify that each adapter declares capabilities through a standardized capability descriptor (SC-002).

**Steps**:

1. Call `OllamaAdapter::declare_capabilities()` → expect `{tools: false, json_mode: true, vision: false, context_window: 4096, streaming: true}`
2. Call `VllmAdapter::declare_capabilities()` → expect `{tools: true, json_mode: true, vision: true, context_window: 8192, streaming: true}`
3. Call `OpenAIAdapter::declare_capabilities()` → expect `{tools: true, json_mode: true, vision: true, context_window: 16385, streaming: true}`
4. Verify the routing policy engine can filter targets based on capability requirements (SC-005)

**Expected outcome**: Each adapter returns a capability descriptor; routing can exclude targets lacking required capabilities.

---

### Scenario 3: Error Taxonomy Mapping

**Purpose**: Verify that each adapter maps failures into the shared error taxonomy, producing OpenAI-compatible error envelopes (SC-005).

**Steps**:

1. Trigger a timeout failure in `OllamaAdapter` → expect error with gateway error code "service_unavailable" and request ID
2. Trigger a validation error in `OpenAIAdapter` → expect error with gateway error code "invalid_request"
3. Trigger a 429 rate limit in `VllmAdapter` → expect error with gateway error code "rate_limit_error" and Retry-After header
4. Verify the error envelope does not contain provider internals (SC-005)

**Expected outcome**: All failure types are mapped to valid OpenAI-compatible error envelopes without exposing provider internals.

---

### Scenario 4: No Provider-Specific Fields in Response

**Purpose**: Verify the core contract requirement that no provider-specific field appears in the OpenAI-compatible response (SC-004).

**Steps**:

1. Send a request through each adapter
2. Inspect the response for any fields not part of the OpenAI Chat Completions schema
3. Verify the response contains only: `id`, `object`, `created`, `model`, `choices`, `usage`, and optional `error`
4. Specifically check for absence of: provider model IDs, internal error codes, credential material, raw prompt/response bodies (SC-004)

**Expected outcome**: Response is fully OpenAI-compatible with no provider-specific leakage.

## Contract Test Reference

For detailed contract test implementations, see `contracts/contract.md` which defines the adapter port interface (`convert_request`, `convert_response`, `declare_capabilities`).

For data model details (entity definitions, field types, relationships), see `data-model.md`.

## Running All Validations

```bash
# Build
cargo build -p llmgw-gateway

# Run contract tests (verifies adapter contract compliance)
cargo test -p llmgw-gateway --lib contract::*

# Run integration tests (verifies end-to-end request flow)
cargo test -p llmgw-gateway --integration adapter_*

# Run unit tests (verifies individual components)
cargo test -p llmgw-gateway --lib
```