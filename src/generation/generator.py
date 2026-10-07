"""Generator: LLM -> JSON -> Pydantic GroundedAnswer (FR-004, research R1).

Parse failures raise StructuredOutputError — contract rule 1: malformed
structured output is detected, never silently accepted.
"""

import json

from domain import GroundedAnswer, StructuredOutputError


def parse_grounded_answer(raw: str) -> GroundedAnswer:
    """Strictly parse provider output into a GroundedAnswer.

    Raises StructuredOutputError on JSON parse failure or schema failure.
    """
    if not raw or not raw.strip():
        raise StructuredOutputError("empty structured output")

    text = raw.strip()
    # Tolerate ```json fences some models emit despite instructions.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[len("json") :]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise StructuredOutputError(f"output is not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise StructuredOutputError(
            f"structured output must be a JSON object, got {type(data).__name__}"
        )

    try:
        return GroundedAnswer.model_validate(data)
    except Exception as e:
        raise StructuredOutputError(f"output failed schema validation: {e}") from e


def generate_grounded(prompt: str, llm_client) -> GroundedAnswer:
    """Run the grounded generation pipeline: LLM -> JSON -> Pydantic.

    Args:
        prompt: the evidence-aware grounded prompt.
        llm_client: any client exposing generate_json(prompt) -> str.

    Returns:
        A validated GroundedAnswer.

    Raises:
        StructuredOutputError: on malformed or schema-invalid output.
        RuntimeError: on transport/LLM API failures (propagated).
    """
    raw = llm_client.generate_json(prompt)
    return parse_grounded_answer(raw)
