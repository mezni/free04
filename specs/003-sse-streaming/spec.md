# Feature Specification: SSE Streaming with Commit Boundary

**Feature Branch**: `[003-sse-streaming]`

**Created**: 2026-11-07

**Status**: Draft

**Input**: From docs/EPICS.md story 1.3 - "As an application developer, I want the gateway to stream tokens as they arrive, so that time-to-first-token matches a direct provider call."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - SSE Streaming with Commit Boundary (Priority: P1)

As an application developer,
I want the gateway to stream tokens as they arrive,
So that time-to-first-token matches a direct provider call.

**Why this priority**: This is the foundational streaming endpoint for the gateway (Phase 0 Router). It enables immediate adoption by existing OpenAI clients that use `stream=true` and is independently testable.

**Independent Test**: A request posted to `/v1/chat/completions` with `stream=true` returns an SSE stream with delta events and done sentinel, includes a request ID header, and rejects unknown models/aliases with a stable error envelope (AD-11). After the first forwarded token, no retry or failover occurs (AD-3).

**Acceptance Scenarios**:

1. **Given** a request with `stream=true`
   **When** the caller posts to `/v1/chat/completions`
   **Then** each upstream chunk is forwarded as an SSE delta without buffering the full response
   **And** the stream ends with the done sentinel `[DONE]`

2. **Given** a request with `stream=true`
   **When** the upstream emits chunks
   **Then** each chunk is forwarded as an SSE delta without buffering the full response
   **And** the stream ends with the done sentinel

3. **Given** a request with `stream=true`
   **When** the upstream fails mid-stream
   **Then** one gateway error event is emitted followed by the done sentinel
   **And** no retry or failover occurs after the first token (AD-3)

4. **Given** a request with `stream=false` (or omitted)
   **When** the caller posts to `/v1/chat/completions`
   **Then** a complete response is returned immediately (not SSE stream)
   **And** response matches the OpenAI Chat Completions response shape

5. **Given** an unknown model or alias
   **When** the caller posts to `/v1/chat/completions` with `stream=true`
   **Then** the endpoint returns 404 or 400 with the stable error envelope (AD-11)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-ENG-02**: Stream SSE chunks without buffering the full response. (REQ-ENG-02, P0)
- **FR-RES-02**: Never retry 4xx (except configured 429) and never retry after the first streamed token. (REQ-RES-02, P0)
- **AD-3**: Failover and retry only before the first token; mid-stream failure terminates the stream. Enforced by E1.S3 and E1.S10.
- **AD-11**: Stable OpenAI-compatible error envelope; no raw provider errors. Enforced by E1.S5.

### Key Entities *(include if feature involves data)*

- **ChatCompletionRequest**: User's chat completion request with messages, model, and parameters. `stream` must be `true` for streaming.
- **SSE Delta Event**: Server-Sent Event containing partial choice updates with `delta.content` and `finish_reason: null`.
- **SSE Done Sentinel**: Final event `[DONE]` signaling stream completion.
- **Usage Event**: One immutable usage event per attempt, recording principal, team, alias, provider, model, tokens, latency, and outcome.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can initiate a streaming chat completion call using the OpenAI schema with `stream=true` in under 30 seconds
- **SC-002**: Response contains SSE delta events with `choices[].delta.content` progressively revealing the assistant's response
- **SC-003**: Stream concludes with `data: [DONE]\n\n` sentinel after the last delta event
- **SC-004**: After the first forwarded token, no retry or failover occurs (AD-3) — 100% of streaming requests respect the commit boundary
- **SC-005**: Unknown model or alias returns 404 or 400 with stable error envelope (AD-11) — 100% of cases
- **SC-006**: `X-Request-Id` header is present in every response (100% of requests)
- **SC-007**: Mid-stream upstream failure emits exactly one gateway error event followed by the done sentinel

---

## Assumptions

- The gateway already has authentication (OIDC/JWT) and routing infrastructure in place (Phase 0 foundation)
- The OpenAI Chat Completions schema is well-defined and serves as the contract
- Model aliases and capabilities are managed through the control-plane configuration (AD-6, AD-4)
- No prompt or response body persistence by default (AD-17, Constitution principle IV)
- Routing policy (cost, latency, residency, capability) is configured and active (FR-ENG-07, AD-5)
- The `stream` parameter, when `true`, triggers the SSE streaming pipeline; when `false` or absent, the endpoint returns a non-streaming response
- Constitution Principle III (First-Token Commit Boundary) is enforced: failover and retry are allowed only before the first token is forwarded; after the first token, the stream is committed
- SSE events follow the OpenAI delta shape with one done sentinel (technology stack conventions)
- Integer micro-units for cost; UUIDv7 for request/attempt IDs; RFC 3339 UTC timestamps

---

## Edge Cases

- What happens when `stream=true` but the model has no streaming support?
- How does the system handle a client disconnect mid-stream?
- What if the upstream provider returns an empty response stream?
- What if the first token takes extremely long (timeout scenario)?
- How are concurrent streaming requests from the same principal handled?
- What if `stream=true` is combined with unsupported parameters (e.g., `function_call`)?