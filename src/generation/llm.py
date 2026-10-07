import httpx

from domain import Answer


class LLMClient:
    """Non-streaming OpenAI-compatible chat-completions client.

    Sends a single request to POST {LLM_BASE_URL}/chat/completions
    with Accept: application/json and receives the answer text from
    choices[0].message.content.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        max_tokens: int = 512,
        temperature: float = 0.0,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> Answer:
        """Generate an answer given a prompt.

        Returns an Answer object with the model's response text and
        whether context was used.
        """
        messages = [{"role": "user", "content": prompt}]

        json_body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }

        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/chat/completions"

        try:
            response = self._client.post(url, json=json_body, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            choices = data.get("choices", [])
            if choices and len(choices) > 0:
                text = choices[0].get("message", {}).get("content", "")
                text = text.rstrip()
                used_context = True
            else:
                text = ""
                used_context = False

            return Answer(text=text, used_context=used_context)

        except httpx.TimeoutException:
            raise RuntimeError(f"LLM request timed out after {self.timeout}s") from None
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"LLM API error {e.response.status_code}: {e.response.text[:200]}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}") from e

    def generate_json(self, prompt: str) -> str:
        """Generate raw text intended as a JSON object (Level 2, research R1).

        Attempts response_format={"type": "json_object"}; if the endpoint
        rejects it (provider-dependent support), falls back to a plain call
        relying on the prompt-enforced JSON instruction. Returns the raw
        message content for strict parsing by generation.generator.
        """
        messages = [{"role": "user", "content": prompt}]
        base_body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}/chat/completions"

        def _post(body: dict) -> str:
            try:
                response = self._client.post(url, json=body, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
            except httpx.TimeoutException:
                raise RuntimeError(f"LLM request timed out after {self.timeout}s") from None
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"LLM API error {e.response.status_code}: {e.response.text[:200]}"
                ) from e
            except Exception as e:
                raise RuntimeError(f"LLM request failed: {e}") from e

        try:
            return _post({**base_body, "response_format": {"type": "json_object"}})
        except RuntimeError as e:
            # Provider rejected response_format -> prompt-enforced JSON fallback.
            if "LLM API error 400" in str(e) or "LLM API error 422" in str(e):
                return _post(base_body)
            raise

    def close(self):
        """Close the underlying HTTP client."""
        if self._client:
            self._client.close()
