from types import SimpleNamespace

import pytest


class FakeMessages:
    def __init__(self, text="ok", error=None):
        self.text, self.error, self.calls = text, error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.text)])


class FakeAnthropic:
    def __init__(self, text="ok", error=None):
        self.messages = FakeMessages(text, error)


@pytest.fixture
def fake_anthropic():
    return FakeAnthropic
