# API Contract: OpenAI Chat Completions

## Endpoint
`POST /v1/chat/completions`

## Request Format
OpenAI Chat Completions JSON schema as defined in the OpenAI API documentation.

**Key request fields**:
- `model`: string - model alias or specific model name
- `messages`: array of {role: string, content: string} - conversation history
- `stream`: boolean - whether to stream response chunks (v1 default: false)
- `temperature`: number - sampling temperature (0-2), optional
- `max_tokens`: integer - max tokens in response, optional
- `top_p`: number - nucleus sampling, optional
- `stop`: array of strings - stop sequences, optional
- `presence_penalty`: number, optional
- `frequency_penalty`: number, optional

## Response Format
OpenAI Chat Completions JSON schema.

**Response headers**:
- `X-Request-Id`: Unique request identifier (RFC 3339 / UUID format)

**Response body**:
- `id`: string - request identifier
- `object`: string - fixed value "chat.completion"
- `created`: integer - Unix timestamp
- `model`: string - model name
- `choices`: array of choice objects
- `usage`: object with prompt_tokens, completion_tokens, total_tokens

**Choice object**:
- `index`: integer
- `message`: {role: "assistant", content: string}
- `finish_reason`: string (e.g., "stop", "length")

## Error Responses
- `400`: Invalid request - malformed JSON, schema validation failure
- `401`: Unauthorized - missing/invalid OIDC JWT or API key
- `403`: Forbidden - insufficient scopes/permissions
- `404`: Unknown model or alias - returns stable error envelope (AD-11)
- `429`: Rate limited - with Retry-After header
- `5xx`: Provider failures - with stable error envelope

## Contract Compliance
- All responses use the AD-11 stable error envelope
- No raw provider bodies or secrets in responses (AD-11, AD-17)
- Request ID propagated in headers and telemetry (AD-10)
- Versioned under `/v1` with documented deprecation policy