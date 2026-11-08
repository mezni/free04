# Quickstart Validation Guide: OpenAI-Chat-Integration

## Prerequisites

- Gateway built and running (Phase 0 build)
- `cargo build --release` has been executed
- Target environment: Kubernetes or local development setup

## Validation Scenarios

### Scenario 1: Basic Chat Completion Call

**Goal**: Verify the `/v1/chat/completions` endpoint accepts and returns the OpenAI schema.

**Steps**:
1. Start the gateway server
2. Post a valid chat completion request:
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [{"role": "user", "content": "Hello, how are you?"}]
     }'
   ```
3. Verify response matches OpenAI Chat Completions schema:
   - Response contains `id`, `object`, `created`, `model`, `choices`, `usage`
   - `choices[0].message.role` is `"assistant"`
   - `choices[0].message.content` contains the response text
   - `X-Request-Id` header is present

**Expected outcome**: Successful response with proper OpenAI schema format and request ID header

---

### Scenario 2: Unknown Model Alias

**Goal**: Verify unknown models/aliases return 404/400 with stable error envelope.

**Steps**:
1. Post request with invalid/unknown model:
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "nonexistent-model",
       "messages": [{"role": "user", "content": "Hello"}]
     }'
   ```
2. Verify response:
   - Status code: 404 or 400
   - Response body uses stable error envelope (AD-11)
   - Contains `error.code` and `error.message` (not provider internals)
   - Contains `request_id` field

**Expected outcome**: 404/400 with stable error envelope, no provider internals exposed

---

### Scenario 3: Request ID Propagation

**Goal**: Verify request ID is present in every response.

**Steps**:
1. Make multiple requests to the gateway
2. Check each response for `X-Request-Id` header
3. Verify the request ID is also present in logs and telemetry

**Expected outcome**: 100% of requests include `X-Request-Id` header; ID present in all telemetry

---

### Scenario 4: v1 Non-Streaming Mode

**Goal**: Verify v1 defaults to non-streaming mode.

**Steps**:
1. Post request without `stream` parameter (or with `stream=false`)
2. Verify response is a complete response (not SSE chunks)
3. Response contains all choices and usage data immediately

**Expected outcome**: Single complete response; no streaming behavior (streaming is Story 1.3)

---

## Validation Commands

```bash
# Build the gateway
cargo build --release

# Run integration tests (if available)
cargo test --test integration -- chat Completion

# Quick health check
curl - http://localhost:8000/health
```