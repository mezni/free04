import anthropic
import httpx
import pytest

from triagekit.config import Settings
from triagekit.llm_client import LLMClient, LLMError

SETTINGS = Settings(api_key="test-key")


def test_complete_returns_text(fake_anthropic):
    fake = fake_anthropic(text="Please share your order number.")
    client = LLMClient(SETTINGS, client=fake)
    assert client.complete("Where is my order?") == "Please share your order number."


def test_complete_sends_model_system_and_message(fake_anthropic):
    fake = fake_anthropic()
    LLMClient(SETTINGS, client=fake).complete("hi", system="be brief")
    call = fake.messages.calls[0]
    assert call["model"] == SETTINGS.model
    assert call["system"] == "be brief"
    assert call["messages"] == [{"role": "user", "content": "hi"}]


@pytest.mark.parametrize("bad", ["", "   ", None, 123])
def test_rejects_invalid_input(fake_anthropic, bad):
    with pytest.raises(ValueError):
        LLMClient(SETTINGS, client=fake_anthropic()).complete(bad)


def test_connection_error_is_wrapped(fake_anthropic):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    fake = fake_anthropic(error=anthropic.APIConnectionError(request=request))
    with pytest.raises(LLMError):
        LLMClient(SETTINGS, client=fake).complete("hi")


def test_missing_api_key_raises():
    with pytest.raises(LLMError):
        LLMClient(Settings(api_key=None))
