import sys

from triagekit.llm_client import LLMClient, LLMError

SYSTEM = "You are a customer-support assistant. Reply in one or two sentences."


def main() -> int:
    text = " ".join(sys.argv[1:]) or "Where is my order?"
    try:
        print(LLMClient().complete(text, system=SYSTEM))
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
