from types import SimpleNamespace

import pytest


def text_response(text="ok"):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def tool_response(payload, tool_id="tu_1", name="submit_result"):
    block = SimpleNamespace(type="tool_use", id=tool_id, name=name, input=payload)
    return SimpleNamespace(content=[block])


class FakeMessages:
    """Returns queued responses in order (the last one repeats)."""

    def __init__(self, responses, error=None):
        self.responses, self.error, self.calls = list(responses), error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


class FakeAnthropic:
    def __init__(self, text="ok", error=None, responses=None):
        self.messages = FakeMessages(responses or [text_response(text)], error)


@pytest.fixture
def fake_anthropic():
    return FakeAnthropic
