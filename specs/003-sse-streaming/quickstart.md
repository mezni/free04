# Quickstart Validation Guide: SSE Streaming with Commit Boundary

## Prerequisites

- Gateway built and running (`cargo build --release` has been executed)
- Target environment: Kubernetes or local development setup
- curl or HTTP client supporting SSE event streaming
- OpenAI-compatible chat completion client (or curl)

## Validation Scenarios

### Scenario 1: Basic SSE Streaming

**Goal**: Verify the `/v1/chat/completions` endpoint with `stream=true` streams tokens as SSE deltas.

**Steps**:
1. Start the gateway server
2. Post a chat completion request with streaming:
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [{"role": "user", "content": "Hello, how are you?"}],
       "stream": true
     }'
   ```
3. Observe the SSE stream output:
   - Multiple `data: {…}` lines (delta events) streaming in real-time
   - Each delta contains `choices[0].delta.content` with partial content
   - Stream ends with `data: [DONE]\n\n`
   - `X-Request-Id` header present in response

**Expected outcome**: Successful SSE stream with delta events and done sentinel; request ID in headers

---

### Scenario 2: Non-Streaming Fallback (stream=false)

**Goal**: Verify that `stream=false` (or omitted) returns a complete response immediately.

**Steps**:
1. Post a chat completion request without `stream` parameter:
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [{"role": "user", "content": "Hello, how are you?"}]
     }'
   ```
2. Observe the response:
   - Single complete JSON response (not SSE stream)
   - Contains `id`, `object`, `created`, `model`, `choices`, `usage`
   - `choices[0].message.role` is `"assistant"`
   - `X-Request-Id` header present

**Expected outcome**: Single complete response matching OpenAI Chat Completions schema

---

### Scenario 3: Unknown Model Alias with Streaming

**Goal**: Verify unknown models return 404/400 with stable error envelope even in streaming context.

**Steps**:
1. Post request with invalid model and `stream=true`:
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "nonexistent-model",
       "messages": [{"role": "user", "content": "Hello"}],
       "stream": true
     }'
   ```
2. Verify response:
   - Status code: 404 or 400
   - Response body uses stable error envelope (AD-11)
   - Contains `error.code` and `error.message` (not provider internals)
   - Contains `request_id` field
   - No SSE stream started (error returned before stream)

**Expected outcome**: 404/400 with stable error envelope, no provider internals exposed

---

### Scenario 4: Mid-Stream Failure

**Goal**: Verify that an upstream failure mid-stream produces one error event followed by done sentinel.

**Expected outcome**: One gateway error SSE event followed by `[DONE]` sentinel; no retries or additional events after the first token

---

## Validation Commands

```bash
# Build the gateway
cargo build --release

# Quick health check (non-streaming)
curl - http://localhost:8000/health

# Test streaming (will show SSE output in terminal)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello"}],"stream":true}'
```