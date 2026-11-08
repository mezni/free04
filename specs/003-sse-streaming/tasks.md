# Tasks: SSE Streaming with Commit Boundary

**Input**: Design documents from `/specs/003-sse-streaming/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description with file path`

- **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
- **Task ID**: Sequential number (T001, T002, T003...) in execution order
- **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
- **[Story] label**: REQUIRED for user story phase tasks only
  - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
  - Setup phase: NO story label
  - Foundational phase: NO story label
  - User Story phases: MUST have story label
  - Polish phase: NO story label
- **Description**: Clear action with exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Initialize Cargo workspace with three crates (llmgw-domain, llmgw-application, llmgw-gateway) per DDD separation (AD-1)
- [X] T002 Configure Rust edition 2024 and resolver settings for workspace
- [X] T003 [P] Enable serde derive feature for gateway crate (story 1.3 streaming req)
- [X] T004 Set up tracing subscriber with AD-10 contract (request ID, span names)
- [X] T004 [P] Configure OpenTelemetry export (Prometheus metrics, trace backend)
- [X] T005 Set up Redis client integration for rate limiting and circuit breaker state
- [X] T006 Create gateway error_envelope module (AD-11 stable error envelope)
- [X] T006 [P] Add GatewayError and ErrorResponse types per AD-11

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Configure Axum router with `POST /v1/chat/completions` route
- [X] T008 Implement request schema validation for ChatCompletionRequest (FR-VAL-01)
- [X] T009 Implement model alias validation (reject unknown models/aliases)
- [X] T010 [P] Implement resilience loop with first-token commit boundary (AD-3)
  - Track whether first token has been forwarded
  - Disable retry/failover after first token
- [X] T011 Implement SSE stream producer (delta events + done sentinel)
  - Forward upstream chunks as SSE delta events
  - Send `[DONE]` sentinel at stream completion
- [X] T012 Implement request ID generation and X-Request-Id header propagation (AD-10)
- [X] T013 Implement error envelope responses per AD-11 (no provider internals)
- [X] T013 [P] Add unit tests for error envelope format

---

## Phase 3: User Story 1 - SSE Streaming with Commit Boundary (Priority: P1) [US1] 🎯 MVP

**Goal**: Gateway streams tokens as SSE deltas with commit boundary; after first token, no retry or failover

**Independent Test**: An SSE stream from `/v1/chat/completions?stream=true` produces delta events with progressive content, ends with `[DONE]` sentinel, and X-Request-Id header. Unknown model returns 404/400 with AD-11 envelope before any stream starts.

- [X] T014 [P] [US1] Implement handler for `POST /v1/chat/completions` with `stream=true`
  - crates/gateway/src/lib.rs handler function
- [X] T015 [P] [US1] Implement ChatCompletionRequest deserialization with `stream` field
  - crates/gateway/src/lib.rs:CompletionRequest struct
- [X] T016 [P] [US1] Implement SSE delta event forwarding from upstream provider
  - crates/gateway/src/ (SSE stream production)
- [X] T017 [P] [US1] Implement done sentinel `[DONE]` at stream completion
  - SSE format: `data: [DONE]\n\n`
- [X] T018 [P] [US1] Implement first-token commit boundary tracking (AD-3)
  - Resilience loop: disable retry/failover after first token forwarded
  - Track commit state through pipeline stages
- [X] T019 [P] [US1] Implement model alias validation before streaming starts
  - Reject unknown models/aliases with 404/400 + AD-11 envelope
  - Validation runs before any upstream call or stream initiation
- [X] T020 [P] [US1] Add unit tests for SSE streaming handler
  - Test: normal streaming completion
  - Test: client disconnect mid-stream
  - Test: mid-stream upstream failure (error event + done sentinel)
- [X] T021 [P] [US1] Add integration test for SSE streaming endpoint
  - Test: full stream with mock upstream provider
  - Verify: delta events, done sentinel, request ID header

---

## Phase 4: User Story 2 - Unknown Model Alias Returns Error Envelope (Priority: P2) [US2]

**Goal**: Unknown model or alias returns 404/400 with stable error envelope (AD-11), no provider internals exposed

**Independent Test**: Posting to `/v1/chat/completions` with `stream=true` and `model=nonexistent-model` returns 404 or 400 with error envelope containing `error.code`, `error.message`, and `request_id` field. No SSE stream is initiated.

- [X] T022 [P] [US2] Implement model alias rejection before streaming initiation
  - crates/gateway/src/lib.rs: validate model against known aliases
  - Return 404/400 with error envelope when model not found
- [X] T023 [P] [US2] Ensure error envelope contains required fields (AD-11)
  - code, message, param, r#type fields
  - request_id propagated in error response
- [X] T024 [P] [US2] Add unit tests for unknown model rejection
  - Test: known model passes validation
  - Test: unknown model returns 404 with error envelope
  - Test: unknown model with stream=true returns error before stream starts
- [X] T025 [P] [US2] Add integration test for unknown model scenario
  - Test: POST with nonexistent model and stream=true
  - Verify: 404/400 status, error envelope fields, no SSE stream

---

## Phase 5: User Story 3 - Request ID Propagation in All Responses (Priority: P3) [US3]

**Goal**: X-Request-Id header present in every response (100% of requests)

**Independent Test**: Every response from the gateway includes `X-Request-Id` header, whether successful, errored, or streaming.

- [X] T026 [P] [US3] Implement request ID middleware for all gateway responses
  - Generate UUIDv7 request ID per request
  - Insert X-Request-Id header in all Axum response types
- [X] T027 [P] [US3] Propagate request ID through SSE stream events
  - Include request ID in SSE event metadata or headers
  - Verify ID present in all delta events and done sentinel
- [X] T028 [P] [US3] Propagate request ID through error envelope responses
  - Verify ID in 4xx/5xx error responses
- [X] T028 [P] [US3] Add unit tests for request ID propagation
  - Test: successful response has X-Request-Id header
  - Test: error response has X-Request-Id header
  - Test: SSE stream has request ID in events
- [X] T029 [P] [US3] Add integration test for request ID across all response types
  - Test: full request cycle verifies ID in all response types
  - Verify: 100% of requests include X-Request-Id

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Run quickstart.md validation scenarios (all 4 validation scenarios)
- [X] T031 [P] Add documentation updates for SSE streaming endpoint
- [X] T032 Code cleanup: ensure no `unwrap` or `expect` on production request paths (NFR-08)
- [X] T033 [P] Performance benchmark: proxy overhead below 5ms p99 (NFR-01)
- [X] T034 [P] Add redaction test: secrets and PII absent from SSE event logs (AD-17)
- [X] T035 [P] Review and update coverage map with FR/AD references for streaming feature
- [X] T036 [P] Verify constitution compliance: Principles I, II, III, IV, V all validated for streaming feature