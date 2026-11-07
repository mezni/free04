# Specification: Duplicate Specs Handling

## Summary
The gateway should detect and handle duplicate specification entries in requests, preventing accidental double submissions and ensuring consistent routing based on unique specification identifiers.

## Technical Context

**Language/Version**: Rust 1.75

**Primary Dependencies**: axum, tokio, serde, thiserror

**Storage**: PostgreSQL (usage events), Redis (rate limiting, health cache)

**Testing**: cargo test

**Target Platform**: Kubernetes 1.35

**Project Type**: library/cli/web-service

**Performance Goals**: <5ms p99 proxy overhead for duplicate detection

**Constraints**: Must not introduce latency budget violations; must work within fixed pipeline order (AD-2); secrets must not leak (AD-4)

**Scale/Scope**: Internal teams; per-team quota enforcement

**Primary Requirement**: Implement a pipeline stage that detects duplicate specification entries and routes them appropriately, ensuring no two requests with the same spec ID are processed simultaneously.

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

- **AD-2 (Fixed Pipeline Order)**: The duplicate detection stage must fit within the fixed pipeline: transport → validate → authenticate → authorize → rate limit → input guardrail → route → resilience → provider → output guardrail → meter → audit. Adding a new stage requires explicit governance approval.
- **AD-4 (Secret Isolation)**: Duplicate detection must not expose or leak any specification identifiers in logs or telemetry beyond what is necessary for routing decisions.
- **AD-3 (First-Token Commit Boundary)**: Duplicate detection must complete before the first token is forwarded; no retry or failover after commit.

**Gates:**
1. Duplicate detection stage must not violate fixed pipeline order (AD-2)
2. No secret leakage through duplicate identification (AD-4)  
3. Decision must be made before first token commit (AD-3)

## Project Structure

### Documentation (this feature)
```
specs/001-workspace-foundation/
├── plan.md              # Implementation plan
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 validation guide
├── contracts/           # Phase 1 interface contracts
└── tasks.md             # Phase 2 tasks
```

### Source Code (repository root)
- `crates/gateway/src/`: HTTP transport, pipeline stages
- `crates/application/src/`: Port traits, use cases
- `crates/domain/src/`: Pure routing function, capability matching

**Structure Decision**: Single project with hexagonal architecture (Option 1: Single project)

## Technical Design

### Duplicate Detection Stage
Added after the rate limit/quota stage and before the route stage in the fixed pipeline. This stage:
1. Extracts the specification ID from the request
2. Checks Redis for recent spec IDs to detect duplicates
3. If duplicate detected: rejects with appropriate error code
4. If not duplicate: records the spec ID in Redis with TTL

### Data Model
- **SpecID**: UUIDv7 unique identifier for a specification entry
- **SeenSpecs**: Redis set with TTL of 5 minutes, containing recent spec IDs
- **DuplicateEvent**: Usage event recorded when a duplicate is detected

### Interface Contracts
- `/v1/chat/completions` - Modified to include spec ID in request metadata
- Internal Redis protocol for spec ID tracking

### Quickstart Validation
1. Start the gateway
2. Send a request with a spec ID
3. Send a second request with the same spec ID within 5 minutes
4. Verify the second request is rejected with 409 or appropriate error

## Research Tasks Needed
- [ ] Research best practices for duplicate detection in Redis-backed services
- [ ] Research UUIDv7 implementation in Rust
- [ ] Research error handling patterns for pipeline-stage rejections

## Constitution Compliance
All design decisions must comply with AD-2 (fixed pipeline), AD-3 (first-token boundary), and AD-4 (secret isolation). No `unwrap` or `expect` on production request paths.