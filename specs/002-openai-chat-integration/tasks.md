# Tasks: OpenAI-Chat-Integration

**Feature**: OpenAI-Chat-Integration (Phase 0 Router)
**Branch**: `002-openai-chat-integration`
**Spec**: specs/002-openai-chat-integration/spec.md

**Input**: Design documents from `/specs/002-openai-chat-integration/`
- plan.md (required) - Tech stack: Rust 1.75, axum 0.8.9, tokio 1.54.1
- spec.md (required) - User stories with priorities
- research.md (optional) - Decisions and constraints
- data-model.md (optional) - Entities: ChatCompletionRequest, ChatCompletionResponse, RequestId
- contracts/ (optional) - API contract: POST /v1/chat/completions

**Tests**: Optional - only include if explicitly requested. This feature specification does not explicitly request TDD, so test tasks are marked as optional with guidance to write them first and ensure they FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Each user story should be independently completable and testable.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan (cargo workspace scaffold)
- [x] T002 Initialize Rust project with axum 0.8.9, tokio 1.54.1, serde 1.0.229 dependencies
- [x] T003 [P] Configure clippy with warnings denied and rustfmt formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Setup API routing structure with axum Router for `/v1/chat/completions`
- [x] T005 [P] Implement request validation middleware against OpenAI Chat Completions schema
- [x] T006 [P] Configure error handling with thiserror for stable error envelope (AD-11)
- [x] T007 [P] Setup tracing/logging with request ID propagation (AD-10 contract)
- [x] T008 Configure middleware structure (CORS, request ID extraction, error mapping)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - OpenAI-Chat-Integration (Priority: P1) 🎯

**Goal**: Expose `POST /v1/chat/completions` to accept and return the OpenAI schema, so that application developers can call the gateway without changing their client code.

**Independent Test**: A request posted to `/v1/chat/completions` with a valid OpenAI schema returns a response matching the OpenAI Chat Completions response shape, includes a request ID header, and rejects unknown models/aliases with a stable error envelope (404/400).

### Tests for User Story 1 (OPTIONAL - only if tests requested ⚠️)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Contract test for `/v1/chat/completions` in `tests/contract/chat_completion.py`
- [x] T011 [P] [US1] Integration test for chat completion journey in `tests/integration/chat_completion.rs`

### Implementation for User Story 1

- [x] T012 [P] [US1] Create `ChatCompletionRequest` model in `src/models/chat_request.rs`
  - Fields: `model: String`, `messages: Vec<Message>`, `stream: bool`, `temperature: Option<f64>`, `max_tokens: Option<u32>`, `top_p: Option<f64>`, `stop: Option<Vec<String>>`, `presence_penalty: Option<f64>`, `frequency_penalty: Option<f64>`
  - Constraint: `messages` must have at least one message

- [x] T013 [P] [US1] Create `ChatCompletionResponse` model in `src/models/chat_response.rs`
  - Fields: `id: String` (UUIDv7), `object: String` (fixed "chat.completion"), `created: i64` (Unix timestamp), `model: String`, `choices: Vec<Choice>`, `usage: Usage`
  - Nested: `Choice` with `index: usize`, `message: Message`, `finish_reason: String`
  - Nested: `Usage` with `prompt_tokens: u64`, `completion_tokens: u64`, `total_tokens: u64`

- [x] T014 [P] [US1] Implement routing handler in `src/handlers/chat_completion.rs`
  - Accept `POST /v1/chat/completions` with `ChatCompletionRequest`
  - Validate request schema and reject malformed input with 400
  - Generate request ID and propagate in response header `X-Request-Id`
  - Return `ChatCompletionResponse` matching OpenAI schema

- [x] T015 [US1] Implement request validation against OpenAI Chat Completions schema
  - Reject malformed JSON with 400
  - Reject unknown models/aliases with 404/400 and stable error envelope (AD-11)
  - Ensure no upstream call is made for rejected requests

- [x] T016 [US1] Implement response formatting per OpenAI Chat Completions schema
  - Include `id`, `object`, `created`, `model`, `choices`, `usage` in response
  - Ensure `choices[0].message.role` is always "assistant"
  - Ensure `X-Request-Id` header present in every response

- [x] T017 [US1] Add request ID generation and error header propagation
  - Generate UUIDv7 per request
  - Include in response header `X-Request-Id`
  - Include in all telemetry logs and traces (AD-10)
  - Propagate through pipeline stages without exposure in error responses (AD-11)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T020 [P] Documentation updates in spec and README
- [x] T021 Code cleanup and refactoring - remove unused imports, fix clippy warnings
- [x] T022 [P] Performance optimization - verify <5ms p99 proxy overhead (NFR-01)
- [x] T023 [P] Security hardening - ensure no prompt/response body in logs/traces (AD-17, Constitution IV)
- [x] T024 Run quickstart.md validation - execute all 4 validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- Each user story should be independently testable and completable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for /v1/chat/completions in tests/contract/chat_completion.py"
Task: "Integration test for chat completion journey in tests/integration/chat_completion.rs"

# Launch all models for User Story 1 together:
Task: "Create ChatCompletionRequest model in src/models/chat_request.rs"
Task: "Create ChatCompletionResponse model in src/models/chat_response.rs"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (run contract + integration tests)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: (Future stories if any)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence