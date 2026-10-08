"""Optional LLM query rewriting with the original preserved (FR-015…FR-017).

Research R6 + Principle XXIX (NON-NEGOTIABLE):
- Reuses the existing OpenRouter chat client (generation/llm.py) at
  temperature 0.0 — no new dependency.
- The prompt embeds the ORIGINAL query verbatim and mandates exactly one
  query line: preserve intent and technical identifiers, no assumptions.
- Any gateway error, empty/whitespace reply, non-string, or absurdly
  long reply falls back to the original query with a warning on stderr —
  retrieval never fails because of a rewrite (FR-017).
- The class never mutates its input and never decides policy: the
  controller decides whether rewriting is enabled at all.
"""

from __future__ import annotations

import sys

REWRITE_PROMPT = """You are a retrieval query rewriter for a telecom knowledge base.

Original query: {question}

Rewrite the query to improve retrieval. Rules:
- Preserve the original intent and every technical identifier (error codes, acronyms, protocol names, product names).
- Expand domain terminology with relevant synonyms.
- Make no assumptions that are not supported by the original query.
- Return EXACTLY ONE query as a single line: no quotes, no numbering, no preamble, no explanation.

Rewritten query:"""


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


class QueryRewriter:
    """Turns a question into a retrieval-friendlier one; None = use original."""

    def __init__(self, llm_client, *, max_length: int = 500):
        self.llm_client = llm_client
        self.max_length = max_length

    @classmethod
    def from_settings(cls, settings) -> QueryRewriter:
        """Build from app settings using the shared gateway (research R6).

        Temperature is pinned to 0.0 regardless of config: rewrites must
        be as reproducible as an LLM call allows.
        """
        from generation.llm import LLMClient

        client = LLMClient(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            max_tokens=128,
            temperature=0.0,
        )
        return cls(client)

    def rewrite(self, question: str) -> str | None:
        """Return a validated single-line rewrite, or None (use original)."""
        prompt = REWRITE_PROMPT.format(question=question)
        try:
            answer = self.llm_client.generate(prompt)
        except Exception as e:
            _warn(f"query rewrite failed ({e}); using original query: {question!r}")
            return None

        text = getattr(answer, "text", None)
        if not isinstance(text, str):
            _warn(f"query rewrite returned a non-string; using original query: {question!r}")
            return None

        line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        line = line.strip("\"'")
        if not line:
            _warn(f"query rewrite returned an empty query; using original query: {question!r}")
            return None
        if len(line) > self.max_length:
            _warn(
                f"query rewrite returned {len(line)} chars (max {self.max_length}); "
                f"using original query: {question!r}"
            )
            return None
        return line
