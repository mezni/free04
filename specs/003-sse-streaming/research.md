# Research: SSE Streaming with Commit Boundary

## Research Tasks

### 1. SSE Event Format (FR-ENG-02)

**Question**: What is the exact SSE event format for OpenAI-compatible streaming chat completions?

**Context**: Story 1.3 requires streaming tokens as SSE deltas without buffering the full response. The stream must end with a done sentinel. Research needed on the exact JSON format for:
- Delta events (partial choices with new content)
- Done sentinel (stream completion marker)
- Request ID propagation in SSE events

**Rationale**: The OpenAI Chat Completions SSE format uses specific JSON structures that the gateway must replicate exactly for client compatibility.

**Decision**: [Pending research]

**Alternatives Considered**:
- `data: {choices: [{delta: {role: "assistant", content: "..."}}]}` per chunk + `data: [DONE]` sentinel
- `data: {id, choices: [{index, delta: {content: "..."}}]}` per chunk
- Custom format (would break OpenAI client compatibility)

---

### 2. First-Token Commit Boundary (AD-3)

**Question**: How is the "first token commit boundary" enforced in the resilience loop?

**Context**: Constitution Principle III states: "Failover and retry are allowed only before the first token is forwarded. After the first token, the stream is committed: no retry, no failover." Story 1.3 also states: "After the first forwarded token no retry or failover occurs (AD-3)."

**Rationale**: This is a critical architectural constraint - the gateway must track whether the first token has been sent and disable retry/failover mechanisms thereafter to prevent double billing and corrupted responses.

**Decision**: [Pending research]

**Alternatives Considered**:
- Atomic flag set on first `yield`/`send` in the stream handler
- Resilience loop counter tracking tokens forwarded
- Separate "committed" state passed through the pipeline stages

---

### 3. Mid-Stream Failure Handling

**Question**: What exactly happens when the upstream fails mid-stream?

**Context**: Story 1.3 acceptance criteria: "a mid-stream upstream failure emits one gateway error event followed by the done sentinel."

**Rationale**: The gateway must produce a well-defined error response even during streaming - a single error event SSE delta followed by the `[DONE]` sentinel, rather than hanging or producing partial/duplicate events.

**Decision**: [Pending research]

**Alternatives Considered**:
- Error event + `[DONE]` then disconnect
- `[DONE]` first, then error event  
- Hang indefinitely (bad)
- Abrupt disconnect without sentinel (bad for client)

---

### 4. Contract Test Structure for Streaming

**Question**: What do contract tests for SSE streaming look like?

**Context**: Story 1.3: "contract tests cover normal completion, client disconnect, and mid-stream failure."

**Rationale**: Need to define the test scenarios and expected outputs for:
- Normal completion (stream ends properly)
- Client disconnect (client closes connection mid-stream)
- Mid-stream upstream failure (one error event + done sentinel)

**Decision**: [Pending research]

**Alternatives Considered**:
- tokio test with mock upstream
- Integration test with real SSE client
- Unit tests with simulated stream

---

### 5. Axum/Tokio Streaming Pattern

**Question**: What is the idiomatic Tokio/Axum pattern for SSE streaming?

**Context**: The gateway is built with axum 0.8.9 and tokio 1.54.1. Need to understand the pattern for:
- Stream production via `tokio::sync::mpsc`
- Axum handler returning `impl Sse` or `impl Stream`
- Buffering vs. passthrough of upstream chunks
- Graceful shutdown/abort on client disconnect

**Decision**: [Pending research]

**Alternatives Considered**:
- `axum::extract::Sse` with `impl Stream<Item = String>`
- `tokio::sync::mpsc` channel from resilience loop
- `tower::util::either` for multi-path streaming

---

## Research Consolidation

**Output**: research.md with all NEEDS CLARIFICATION resolved

*To be completed after research agents are dispatched. Each unknown above will be resolved by a dedicated research task, and the Decision fields will be populated with the chosen approach.*