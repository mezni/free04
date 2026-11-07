# Data Model: Duplicate Specs Handling

## Entities

### SpecID
- **Description**: Unique identifier for a specification/entry in the LLM gateway routing system
- **Type**: UUIDv7
- **Format**: RFC 4122 version 7, represented as a string hex identifier
- **Constraints**: Must be unique per specification entry; time-sorted for efficient Redis operations
- **Lifecycle**: Created per request; tracked in Redis for duplicate detection; expired after TTL (5 minutes)

**Fields**:
- `id`: UUIDv7 (primary identifier)
- `created_at`: RFC 3339 UTC timestamp (when the spec ID was generated)
- `originating_request_id`: string (correlates with the main request ID)

### DuplicateDetectionState
- **Description**: Redis-based state tracking for recent spec IDs to detect duplicates
- **Type**: Redis SET with TTL
- **Key**: `active_spec_ids`
- **Members**: UUIDv7 strings of recently processed spec IDs
- **TTL**: 300 seconds (5 minutes)

**Operations**:
- `SISMEMBER active_spec_ids <spec_id>`: Check if spec ID has been seen
- `SADD active_spec_ids <spec_id>`: Add spec ID to tracked set
- `EXPIRE active_spec_ids 300`: Set TTL on the set

### DuplicateEvent
- **Description**: Usage event recorded when a duplicate specification is detected
- **Type**: Immutable usage event per AD-9 and AD-10
- **Key**: request_id + attempt_id (composite key)
- **Fields**:
  - `request_id`: string (the original request identifier)
  - `attempt_id`: string (the attempt number, 1-based)
  - `spec_id`: UUIDv7 (the duplicate specification identifier)
  - `principal`: string (the team/principal who sent the duplicate)
  - `outcome`: "duplicate" (the event outcome)
  - `tokens_upstream`: integer (tokens consumed before duplicate detection)
  - `cost_micros`: integer (cost snapshot from price table version at event time)
  - `timestamp`: RFC 3339 UTC

## Relationships

- **SpecID → DuplicateEvent**: One-to-many. A specification ID can be involved in multiple duplicate detection events across different requests.
- **DuplicateEvent → UsageEvent**: DuplicateEvent is a type of UsageEvent (AD-9: immutable usage events).
- **SpecID → SeenSpecs (Redis)**: Many-to-one mapping. Multiple spec IDs are tracked in the Redis SET for duplicate detection.

## Validation Rules

### SpecID Validation
- Must be valid UUIDv7 format
- Must not be zero UUID (all bits zero)
- Must be parseable by the uuid crate with v7 feature

### Duplicate Detection Rules
- A spec ID is considered "duplicate" if it appears in the `active_spec_ids` Redis SET
- Duplicate detection occurs once per pipeline traversal (after rate limit, before route)
- If duplicate detected: request rejected with `invalid_request` error (AD-11 envelope)
- If not duplicate: spec ID added to Redis SET with 5-minute TTL

### Usage Event Rules
- Per AD-9: Each usage event is immutable once written
- Per AD-10: Telemetry carries request id, team, alias, provider; no prompt bodies
- Per AD-4: Secrets never in config, logs, or traces

## State Transitions

### Normal Path (no duplicate)
1. Request received with spec ID
2. Pipeline traverses stages (transport, validate, authenticate, authorize, limits, input guardrail, route, resilience, provider, output guardrail, meter, audit)
3. At duplicate detection stage: `SISMEMBER` returns `false`
4. `SADD` adds spec ID to Redis SET
5. `EXPIRE` ensures 5-minute TTL
6. Request continues through remaining pipeline stages
7. Usage event emitted for the attempt

### Duplicate Path
1. Request received with spec ID already in active set
2. At duplicate detection stage: `SISMEMBER` returns `true`
3. Request rejected with `invalid_request` error (AD-11)
4. No further pipeline stages processed
5. DuplicateUsageEvent emitted with tokens consumed and cost snapshot
6. No routing occurs; no provider call made

## Redis Key Schema

```
Key: active_spec_ids
Type: SET
Members: UUIDv7 hex strings (e.g., "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b")
TTL: 300 seconds (5 minutes)
Purpose: Track recently processed specification IDs for duplicate detection
```

## PostgreSQL Schema (usage events table)

```sql
CREATE TABLE usage_events (
    request_id UUID NOT NULL,
    attempt_id INTEGER NOT NULL,
    spec_id UUID,
    principal VARCHAR NOT NULL,
    outcome VARCHAR NOT NULL,
    tokens_upstream INTEGER NOT NULL,
    cost_micros BIGINT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (request_id, attempt_id)
);
```

-- Index for spec_id lookups (for audit/analysis)
CREATE INDEX idx_usage_events_spec_id ON usage_events(spec_id);