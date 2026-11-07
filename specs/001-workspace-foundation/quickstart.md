# Quickstart: Duplicate Specs Validation

## Prerequisites

- Gateway running on Kubernetes (or locally via `cargo run`)
- PostgreSQL connection configured
- Redis connection configured
- `specs/001-workspace-foundation/spec.md` exists
- Gateway built with duplicate detection feature flag enabled

## Setup

### 1. Start the Gateway

```bash
# Using cargo
cargo run --package llmgw-gateway

# Or using Docker
docker compose up -d llmgw-gateway
```

### 2. Verify Gateway is Running

```bash
curl http://localhost:8080/v1/models
# Should return available models
```

### 3. Configure Redis for Duplicate Detection

The gateway requires Redis for spec ID tracking. Ensure Redis is accessible at the configured URL (default: `redis://localhost:6379`).

Check the gateway configuration:

```bash
# Check if REDIS_URL is set
echo $REDIS_URL
# Expected: redis://localhost:6379 or similar
```

## Validation Scenarios

### Scenario 1: First Request with spec_id (not a duplicate)

```bash
# Send first request with a unique spec_id
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <valid-token>" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "spec_id": "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"
  }'

# Expected response: 200 OK with chat completion
# In Redis: the spec_id should now be in the active_spec_ids SET
redis-cli SISMEMBER active_spec_ids "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"
# Expected: 1 (the spec_id is now tracked)
```

### Scenario 2: Second Request with Same spec_id (duplicate detected)

```bash
# Send second request with the same spec_id within 5 minutes
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <valid-token>" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello again"}],
    "temperature": 0.7,
    "spec_id": "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"
  }'

# Expected response: 400 Invalid Request
# Body: {"error":{"message":"A request with this specification ID already exists","type":"invalid_request_error","param":null,"code":"duplicate_spec"}}

# In Redis: the spec_id remains in the SET (already present)
redis-cli SISMEMBER active_spec_ids "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"
# Expected: 1 (still tracked)
```

### Scenario 3: Different spec_id (not a duplicate)

```bash
# Send request with a different spec_id
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <valid-token>" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "spec_id": "binyangfg-16d5-71e3-88a2-1e2e1d4f6a8c"
  }'

# Expected response: 200 OK
# In Redis: the new spec_id is added to the SET
redis-cli SISMEMBER active_spec_ids "binyangfg-16d5-71e3-88a2-1e2e1d4f6a8c"
# Expected: 1
```

### Scenario 4: Duplicate after TTL expiration

```bash
# Wait for Redis TTL to expire (5 minutes)
# Or manually delete the spec_id from the SET
redis-cli SREM active_spec_ids "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"

# Send request with previously-used spec_id (now allowed since TTL expired)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <valid-token>" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello after reset"}],
    "temperature": 0.7,
    "spec_id": "69670e8f-16d5-71e3-88a2-1e2e1d4f6a8b"
  }'

# Expected response: 200 OK (no longer a duplicate)
# In Redis: the spec_id is re-added to the SET
```

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| `redis: connection refused` | Redis not running | Start Redis: `redis-server` or ensure Docker compose includes Redis |
| `400 duplicate_spec` on first request | spec_id already tracked from previous test | Run `redis-cli SREM active_spec_ids <spec_id>` to clear |
| `500 internal error` | Redis SET operations failed | Check Redis logs; ensure TTL is set correctly |
| `spec_id` ignored (no duplicate detection) | Feature flag not enabled | Check gateway configuration for `duplicate_spec.enabled` or similar |