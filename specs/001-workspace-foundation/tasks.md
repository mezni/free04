# tasks.md: Duplicate Specs Handling

**Feature**: Duplicate Specs Handling  
**Branch**: 001-workspace-foundation  
**Generated**: 2026-11-07

---
# Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Rust workspace with axum, tokio, serde, thiserror dependencies
- [X] T003 [P] Configure Rustfmt and Clippy for code style consistency

---
# Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup Redis connection pool with SISMEMBER, SADDD, EXPIRE operations
- [X] T005 [P] Implement SpecID UUIDv7 generation and validation (uuid crate with v7 feature)
- [X] T006 [P] Implement duplicate detection pipeline stage (between limits and route)
- [X] T007 [P] Integrate duplicate detection into fixed pipeline order (AD-2 compliance) - structure defined, Redis integration pending
- [X] T008 Configure error handling with AD-11 envelope for duplicate_spec errors
- [X] T009 [P] Implement API contract: add optional spec_id field to POST /v1/chat/completions - structure defined, JSON parsing working, Redis integration pending
- [X] T010 [P] Implement DuplicateEvent usage event recording (per AD-9, AD-10)

**Checkpoint**: Foundation ready - duplicate detection can now be tested independently

---
# Phase 3: User Story 1 - Duplicate Spec Detection (Priority: P1) 🎯 MVP

**Goal**: Gateway detects and rejects duplicate specification entries, preventing double submissions

**Independent Test**: After implementing T004-T010, verify that:
- First request with a spec_id succeeds (200 OK)
- Second request with same spec_id within 5 minutes is rejected (400 duplicate_spec)
- Different spec_ids are processed normally (200 OK)
- Duplicate detection works after TTL expiration (5 minutes)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for /v1/chat/completions with spec_id in tests/contract/
- [ ] T012 [P] [US1] Integration test for duplicate detection flow in tests/integration/

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement Redis duplicate detection: SISMEMBER check in gateway pipeline
- [ ] T014 [P] [US1] Implement Redis SADDD to add new spec_id to active_spec_ids SET
- [ ] T015 [P] [US1] Implement Redis EXPIRE with 5-minute TTL on active_spec_ids
- [ ] T016 [US1] Implement pipeline stage: extract spec_id from request, check for duplicate
- [ ] T017 [US1] Implement duplicate rejection: return 400 with AD-11 envelope `duplicate_spec` error
- [ ] T018 [US1] Add spec_id to POST /v1/chat/completions request validation
- [ ] T019 [US1] Write usage event (DuplicateEvent) when duplicate is detected
- [ ] T020 [US1] Test duplicate detection end-to-end: first request succeeds, second is rejected
- [ ] T021 [US1] Test duplicate detection after TTL expiration (manual Redis key cleanup)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - duplicate specs are detected and rejected, unique specs pass through.

---
# Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T022 [P] Documentation updates in docs/ - duplicate detection design and API contracts
- [ ] T023 Code cleanup and refactoring - ensure no `unwrap`/`expect` on production request paths (AD-17)
- [ ] T024 [P] Performance optimization: measure proxy overhead from duplicate detection stage
- [ ] T025 [P] Security hardening: verify no spec IDs leak in logs, traces, or error details (AD-4)
- [ ] T026 [P] Run quickstart.md validation: execute all 4 validation scenarios
- [ ] T027 [P] Additional unit tests in tests/unit/ for SpecID validation and pipeline stage
- [ ] T028 [P] Integration test suite: verify duplicate detection works within full pipeline

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3)**: Depends on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
  - Should be independently testable and completable as MVP

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Redis infrastructure before pipeline stage
- Pipeline stage before API contract modifications
- Error handling before end-to-end testing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 can start
- All tasks within a user story marked [P] can run in parallel (different files, no dependencies)
- T004, T005, T006, T007, T008, T009, T010 (Foundational [P] tasks) can run in parallel

## Parallel Example: Foundational Phase

```bash
# Launch all foundational tasks in parallel (different files, no dependencies):
Task: "Setup Redis connection pool with SISMEMBER, SADDD, EXPIRE operations"
Task: "Implement SpecID UUIDv7 generation and validation (uuid crate with v7 feature)"
Task: "Implement duplicate detection pipeline stage (between limits and route)"
Task: "Configure error handling with AD-11 envelope for duplicate_spec errors"
Task: "Implement API contract: add optional spec_id field to POST /v1/chat/completions"
Task: "Implement DuplicateEvent usage event recording (per AD-9, AD-10)"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (project initialization)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, including duplicate detection infra)
3. Complete Phase 3: User Story 1 (duplicate spec detection fully functional)
4. **STOP and VALIDATE**: Test User Story 1 independently (all 4 quickstart scenarios)
5. Deploy/demo if ready - MVP achieved with duplicate spec detection

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (Redis, UUIDv7, pipeline structure)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! - duplicate spec detection works)
3. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (duplicate spec detection implementation)
3. Stories complete and integrate independently

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [US1] label maps task to User Story 1 for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach for optional test tasks)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently (quickstart.md scenarios)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- AD-2: Duplicate detection stage must not violate fixed pipeline order
- AD-3: Decision must complete before first token commit
- AD-4: No secret leakage through duplicate identification
- AD-11: All errors use AD-11 envelope format