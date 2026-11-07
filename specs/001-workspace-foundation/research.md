# Research: Duplicate Specs Handling

## Research Tasks

### 1. UUIDv7 Implementation in Rust
- **Decision**: Use uuid crate with v7 feature flag
- **Rationale**: UUIDv7 provides time-sorted unique identifiers suitable for spec ID tracking; enables efficient Redis operations and monotonic ordering
- **Alternatives considered**:
  - UUIDv4: Random-based, no ordering guarantees; would work but lacks time-sorting benefits
  - UUIDv1: Time-based but requires MAC address, privacy concerns in internal context
  - Custom ID scheme: Would work but reinvents the wheel; uuid crate is battle-tested

### 2. Duplicate Detection Patterns in Redis-backed Services
- **Decision**: Use Redis SET with TTL for recent spec ID tracking
- **Rationale**: SET data structure provides O(1) membership checking; TTL automatically expires old entries; atomic operations (SADD, SISMEMBER) ensure race-condition-free detection
- **Alternatives considered**:
  - Redis sorted set with timestamps: More overhead than needed; SET is sufficient for membership testing
  - Bloom filter: Probabilistic may allow false positives; SET gives definitive answers
  - Separate Redis key per spec: Wasteful; SET with TTL is more compact

### 3. Pipeline Stage Insertion Patterns in Hexagonal Architectures
- **Decision**: Insert duplicate detection stage after rate limit/quota, before route stage in fixed pipeline
- **Rationale**: Preserves AD-2 (fixed pipeline order); rate limiting ensures we check duplicates after quota enforcement; placement before route ensures we don't route duplicate requests
- **Alternatives considered**:
  - After route stage: Would allow duplicate requests to be routed before detection; violates AD-3 (commit boundary concerns)
  - Before rate limit stage: Would check duplicates too early; rate-limited requests might still be valid unique requests

### 4. Error Handling for Pipeline Stage Rejections
- **Decision**: Use AD-11 error taxonomy; map duplicate detection to `invalid_request` (400) or create `duplicate_spec` error
- **Rationale**: Consistent error handling across the gateway; AD-11 envelope ensures stable SDK/UI behavior; provides clear error message without leaking implementation details
- **Alternatives considered**:
  - Map to 409 Conflict: Semantically closer but not in AD-11 taxonomy; would require extension
  - Map to 429 Too Many Requests: Incorrect semantics; duplicate is not a rate limit issue

## Best Practices Discovered

### Redis Duplicate Detection Pattern
```rust
// Check if spec ID has been seen recently
let is_duplicate = redis.sismember("active_spec_ids", spec_id).await?;

// If not duplicate, add to seen set with TTL
if !is_duplicate {
    redis.sadd("active_spec_ids", spec_id).await?;
    redis.expire("active_spec_ids", 300).await?; // 5-minute TTL
}
```

### Error Taxonomy Integration
- Add `duplicate_spec` error variant to the AD-11 error envelope
- Error response: `{"error": "duplicate_spec", "message": "A request with this specification ID already exists"}`
- No prompt/body data included in error to comply with AD-17

### Pipeline Stage Compliance
- Stage function signature: `&Request -> Result<Continue, Reject>` 
- Fits between `limits` and `route` stages in the fixed pipeline
- No I/O in the critical path; Redis check uses connection pool with short timeout
- Decision must be made before first token commit (AD-3)