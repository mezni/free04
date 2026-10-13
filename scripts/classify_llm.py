import sys

from triagekit.llm_classifier import classify_with_llm
from triagekit.llm_client import LLMClient, LLMError


def main() -> int:
    text = " ".join(sys.argv[1:]) or "I need a refund for order #4821"
    try:
        result = classify_with_llm(text, LLMClient())
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
