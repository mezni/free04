"""Configuration settings for the triage kit."""


class Settings:
    """Load settings from environment or pass explicitly."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model or "claude-3-haiku-20240307"
        self.max_tokens = max_tokens or 500
        self.timeout_s = timeout or 30.0
        self.max_retries = max_retries or 3

    @property
    def api_key(self) -> str | None:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str | None) -> None:
        if value is None or value == "":
            self._api_key = None
        else:
            self._api_key = value

    def __repr__(self) -> str:
        return (
            f"Settings(api_key={self._api_key!r}, model={self.model!r}, "
            f"max_tokens={self.max_tokens!r}, timeout_s={self.timeout_s!r}, "
            f"max_retries={self.max_retries!r})"
        )