"""LLM client wrapper with env key, timeout, and retry with backoff."""

from __future__ import annotations

from anthropic import Anthropic, APIConnectionError, APIError

from triagekit.config import Settings


class LLMError(Exception):
    """Raised when the LLM call fails after retries."""


class LLMClient:
    """Thin wrapper around the Anthropic SDK.

    Retries (429/5xx/connection errors) and timeouts are handled by the SDK
    via ``max_retries`` and ``timeout``. Failures are re-raised as ``LLMError``
    so the rest of the code never depends on SDK exception types.

    The *client* argument allows injecting a mock (e.g. ``FakeAnthropic``) for
    unit testing.
    """

    def __init__(self, settings: Settings | None = None, client=None) -> None:
        self.settings = settings or Settings()
        if client is None:
            if not self.settings.api_key:
                raise LLMError("ANTHROPIC_API_KEY is not set")
            client = Anthropic(
                api_key=self.settings.api_key,
                timeout=self.settings.timeout_s,
                max_retries=self.settings.max_retries,
            )
        self._client = client

    def complete(self, user_text: str, system: str | None = None) -> str:
        if not isinstance(user_text, str) or not user_text.strip():
            raise ValueError("user_text must be a non-empty string")

        kwargs = {
            "model": self.settings.model,
            "max_tokens": self.settings.max_tokens,
            "messages": [{"role": "user", "content": user_text}],
        }
        if system:
            kwargs["system"] = system

        try:
            response = self._client.messages.create(**kwargs)
        except APIConnectionError as exc:  # includes timeouts
            raise LLMError(f"Connection error: {exc}") from exc
        except APIError as exc:
            raise LLMError(f"API error: {exc}") from exc

        return "".join(b.text for b in response.content if b.type == "text")