import pytest

from tests.conftest import FakeAnthropic, text_response, tool_response
from triagekit.config import Settings
from triagekit.llm_classifier import classify_with_llm
from triagekit.llm_client import LLMClient, LLMError
from triagekit.models import Category

SETTINGS = Settings(api_key="test-key")
GOOD = {"category": "refund_dispute", "confidence": 0.92, "order_id": "4821"}


def make(*responses):
    fake = FakeAnthropic(responses=list(responses))
    return LLMClient(SETTINGS, client=fake), fake


def test_valid_tool_call_is_parsed():
    client, _ = make(tool_response(GOOD))
    result = classify_with_llm("I need a refund for order #4821", client)
    assert result.category is Category.REFUND_DISPUTE
    assert result.order_id == "4821"


def test_request_forces_the_tool_and_sends_schema():
    client, fake = make(tool_response(GOOD))
    classify_with_llm("refund please", client)
    call = fake.messages.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "submit_result"}
    assert "category" in call["tools"][0]["input_schema"]["properties"]


def test_invalid_output_is_retried_with_feedback():
    bad = tool_response({"category": "refund_dispute", "confidence": 1.7})
    client, fake = make(bad, tool_response(GOOD, tool_id="tu_2"))
    result = classify_with_llm("refund please", client)
    assert result.confidence == 0.92
    assert len(fake.messages.calls) == 2
    feedback = fake.messages.calls[1]["messages"][-1]["content"][0]
    assert feedback["is_error"] is True


def test_gives_up_after_max_attempts():
    bad = tool_response({"category": "nope", "confidence": 0.5})
    client, fake = make(bad)
    with pytest.raises(LLMError):
        classify_with_llm("hello", client)
    assert len(fake.messages.calls) == 2


def test_missing_tool_call_raises():
    client, _ = make(text_response("I think it is a refund"))
    with pytest.raises(LLMError):
        classify_with_llm("hello", client)
