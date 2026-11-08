# Data Model: OpenAI-Chat-Integration

## ChatCompletionRequest

Represents an OpenAI-compatible chat completion request.

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model alias or specific model name |
| `messages` | array of message objects | Conversation history, each with `role` (system/user/assistant) and `content` |
| `stream` | boolean | *Optional: for v1, non-streaming only per assumption; streaming in Story 1.3* |
| `temperature` | number | Sampling temperature (0-2) |
| `max_tokens` | integer | Maximum tokens in response |
| `top_p` | number | Nucleus sampling parameter |
| `stop` | array of strings | Stop sequences |
| `presence_penalty` | number | Presence penalty parameter |
| `frequency_penalty` | number | Frequency penalty parameter |

**Constraints**:
- `messages` must have at least one message
- `model` must be a valid alias or supported model identifier
- `stream` flag: v1 defaults to `false` (non-streaming); `true` enabled in Story 1.3

---

## ChatCompletionResponse

Represents an OpenAI-compatible chat completion response.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Request ID, RFC 3339 UTC timestamp format (e.g., `chatcm-...`) |
| `object` | string | Fixed value: `"chat.completion"` |
| `created` | integer | Unix timestamp of response creation |
| `model` | string | Model name that matched the request |
| `choices` | array of choice objects | Response choices, each with `index`, `message`, and `finish_reason` |
| `usage` | object | Token usage counts (prompt_tokens, completion_tokens, total_tokens) |

**Choice object**:
- `index`: integer - position of the choice
- `message`: object - assistant's response with `role` (always "assistant") and `content` (string or delta for streaming)
- `finish_reason`: string - e.g., "stop", "length", "tool_calls", "function_call"

---

## RequestId

Unique identifier generated per request, used for tracing and telemetry.

- Format: UUIDv7 or timestamp-based identifier
- Propagated in response header `X-Request-Id`
- Included in all telemetry logs and traces
- Enables request correlation across pipeline stages and upstream calls

**Usage**:
- Given a request, when the response is returned, then the request ID is present in the response header
- Given a failed request, when the error response is returned, then the request ID is present
- Given telemetry collection, when a request is traced, then the request ID spans all pipeline stages