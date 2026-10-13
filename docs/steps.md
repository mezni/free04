# Step 0: Init project

Goal: A reproducible repo anyone can clone and run in two commands.

Problem: No structure, no tooling, "works on my machine."

Solution: `uv init --package`, `src/` layout, ruff and pytest configured in `pyproject.toml`, `.env.example`, `.gitignore`, a CI workflow, and one smoke test.

Trade-offs: uv is fast and modern, but newer than pip/poetry, so some recruiters may be less familiar with it. A `src/` layout adds a bit of ceremony but prevents import bugs.

Input: `uv sync && uv run pytest`

Expected output: 1 passed and `ruff check .` reports `All checks passed!` to `docs/steps.md`

## Step 1: First LLM call

Goal: Send a ticket to an LLM and get a text reply back.

Problem: Hard-coded API keys, no timeouts, crashes on rate limits.

Solution: `llm_client.py` wrapper with key from env, timeout, retry with backoff on 429/5xx, and a `scripts/hello_llm.py` demo.

Trade-offs: A thin wrapper gives control and teaches the fundamentals, whereas an SDK-only call is shorter but hides behavior. Retries improve reliability but can multiply latency and cost.

Input: "Where is my order?"

Expected output: "I can help with that. Could you share your order number?" (free text, non-deterministic) to `docs/steps.md`

## Step 3: Prompt design and few-shot

Goal: Make LLM classifications consistent across runs and phrasings, with prompts that live in one versioned module instead of inline strings.

Problem: The one-line system prompt from Step 2 leaves the model to guess what each category means, how to handle overlapping intents, and when to leave `order_id` null. Results drift between runs, and ticket text containing instructions could steer the model.

Solution: A `prompts.py` module with explicit category definitions, precedence rules, a confidence scale, 9 few-shot examples (validated against `TriageResult` at import), and a `wrap_ticket()` helper that marks the ticket as data.

Trade-offs: A longer, example-rich prompt costs more tokens and latency on every call, and few-shot examples can bias the model toward their surface wording, so they need reviewing like code. Validating examples against `TriageResult` at import catches copy-paste mistakes early but adds import-time work.

Input: A free-text ticket such as "I was charged twice for order #1234, please refund me."

Expected output: A schema-valid `TriageResult` (e.g. `category="billing"`, `order_id="1234"`, calibrated `confidence`) that is stable across repeated runs and malformed-ticket attempts.