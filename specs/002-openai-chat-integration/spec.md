# Feature Specification: OpenAI-Chat-Integration

**Feature Branch**: `[openai-chat-integration]`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "from docs/EPICS.md story 1.2"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - OpenAI-Chat-Integration (Priority: P1)

As an application developer,
I want to post a chat completion request to `POST /v1/chat/completions` using the OpenAI schema,
So that I can call the gateway without changing my client code.

**Why this priority**: This is the foundational endpoint for the gateway (Phase 0 Router). It enables immediate adoption by existing OpenAI clients and is independently testable.

**Independent Test**: A request posted to `/v1/chat/completions` with a valid OpenAI schema returns a response matching the OpenAI Chat Completions response shape, includes a request ID header, and rejects unknown models/aliases with a stable error envelope (404/400).

**Acceptance Scenarios**:

1. **Given** a valid chat completion request body matching the OpenAI Chat Completions schema
   **When** the caller posts to `/v1/chat/completions`
   **Then** the response matches the OpenAI Chat Completions response shape

2. **Given** a valid chat completion request
   **When** the caller posts to `/v1/chat/completions`
   **Then** a request ID is generated and returned in a response header

3. **Given** an unknown model or alias
   **When** the caller posts to `/v1/chat/completions`
   **Then** the endpoint returns 404 or 400 with the stable error envelope (AD-11)

4. **Given** a request posted to `/v1/chat/completions`
   **When** the endpoint is called
   **Then** the endpoint is versioned under `/v1` with a documented deprecation policy

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-ENG-01**: Expose an OpenAI-compatible `/v1/chat/completions` endpoint with request and response schema
- **FR-VAL-01**: Validate requests against the OpenAI Chat Completions schema and reject malformed input with 400
- **FR-AUTH-01**: Authenticate callers via OIDC/JWT and/or gateway-issued scoped API keys
- **FR-RES-02**: Never retry after the first streamed token (AD-3) — applies to non-streaming mode

*Example of marking unclear requirements:*

- **FR-ENG-02**: System MUST support non-streaming chat completion responses for v1 — *Assumption: v1 focuses on non-streaming endpoint per Story 1.2; streaming is covered in Story 1.3*

### Key Entities *(include if feature involves data)*

- **ChatCompletionRequest**: User's chat completion request with messages, model, and parameters
- **ChatCompletionResponse**: OpenAI-compatible response with choices, usage, and model name
- **RequestId**: Unique identifier generated per request, propagated in headers and telemetry

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a chat completion call using the OpenAI schema in under 30 seconds
- **SC-002**: Response matches the OpenAI Chat Completions response shape (verified against schema)
- **SC-003**: Request ID is present in every response header (100% of requests)
- **SC-004**: Unknown model or alias returns 404 or 400 with stable error envelope (100% of cases)

## Assumptions

- The gateway already has authentication (OIDC/JWT) and routing infrastructure in place (Phase 0 foundation)
- The OpenAI Chat Completions schema is well-defined and serves as the contract
- Model aliases and capabilities are managed through the control-plane configuration (AD-6, AD-4)
- No prompt or response body persistence by default (AD-17, Constitution principle IV)
- Routing policy (cost, latency, residency, capability) is configured and active (FR-ENG-07, AD-5)