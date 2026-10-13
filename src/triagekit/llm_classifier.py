from triagekit.llm_client import LLMClient
from triagekit.models import TriageResult
from triagekit.prompts import SYSTEM_PROMPT, wrap_ticket


def classify_with_llm(text: str, client: LLMClient) -> TriageResult:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    return client.complete_structured(wrap_ticket(text), TriageResult, system=SYSTEM_PROMPT)
