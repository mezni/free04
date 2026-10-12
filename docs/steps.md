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