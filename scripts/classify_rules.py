import sys

from triagekit.classifier import classify


def main() -> int:
    text = " ".join(sys.argv[1:]) or "I need a refund for order #4821"
    print(classify(text).model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
