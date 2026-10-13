"""LLM client wrapper with env key, timeout, and retry with backoff."""

from __future__ import annotations

from typing import Any, TypeVar

from anthropic import Anthropic, APIConnectionError, APIError
from pydantic import BaseModel, ValidationError

from triagekit.config import Settings

T = TypeVar("T", bound=BaseModel)

TOOL_NAME = "submit_result"


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

        response = self._create(kwargs)
        return "".join(b.text for b in response.content if b.type == "text")

    def complete_structured(
        self,
        user_text: str,
        schema: type[T],
        system: str | None = None,
        max_attempts: int = 2,
    ) -> T:
        """Force a tool call and validate its input as *schema*.

        On invalid output the model is retried with the validation error as
        feedback. Raises ``LLMError`` if no valid result is produced within
        ``max_attempts``.
        """
        if not isinstance(user_text, str) or not user_text.strip():
            raise ValueError("user_text must be a non-empty string")

        tool = {
            "name": TOOL_NAME,
            "description": "Submit the structured triage result for the ticket.",
            "input_schema": schema.model_json_schema(),
        }
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_text}]

        last_error = "no result"
        for _ in range(max_attempts):
            kwargs = {
                "model": self.settings.model,
                "max_tokens": self.settings.max_tokens,
                "messages": messages,
                "tools": [tool],
                "tool_choice": {"type": "tool", "name": TOOL_NAME},
            }
            if system:
                kwargs["system"] = system

            response = self._create(kwargs)
            block = next(
                (b for b in response.content if getattr(b, "type", None) == "tool_use"),
                None,
            )
            if block is not None:
                try:
                    return schema(**block.input)
                except ValidationError as exc:
                    last_error = str(exc)

            tool_use_id = getattr(block, "id", "toolu_error")
            messages.append(
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": tool_use_id,
                            "name": TOOL_NAME,
                            "input": getattr(block, "input", {}),
                        }
                    ],
                }
            )
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": (
                                f"Invalid result: {last_error}. Fix it and call {TOOL_NAME} again."
                            ),
                            "is_error": True,
                        }
                    ],
                }
            )

        raise LLMError(f"Model did not return a valid result: {last_error}")

    def _create(self, kwargs: dict[str, Any]):
        try:
            return self._client.messages.create(**kwargs)
        except APIConnectionError as exc:  # includes timeouts
            raise LLMError(f"Connection error: {exc}") from exc
        except APIError as exc:
            raise LLMError(f"API error: {exc}") from exc
