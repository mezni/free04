"""Rule-based baseline classifier (step 4).

Deliberately simple: first matching category wins, in precedence order.
Step 5 adds confidence ranking, review flags, assumptions and input validation.
"""

import re

from triagekit.models import Category, TriageResult

MATCH_CONFIDENCE = 0.8
NO_MATCH_CONFIDENCE = 0.2

# Explicit forms only: "#4821", "order 4821", "order number 4821", "order no. 4821",
# "order id: 4821", "package 7712". Bare numbers are ignored on purpose
# (phone numbers, card numbers, quantities).
_ORDER_ID = re.compile(
    r"(?:#\s*|\b(?:order|package|parcel|shipment)\s*(?:number|no\.?|id|#)?\s*[:#]?\s*)"
    r"(\d{3,12})\b",
    re.IGNORECASE,
)


def _compile(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(patterns), re.IGNORECASE)


# Order matters: this IS the precedence (refund > order > billing > technical).
RULES: tuple[tuple[Category, re.Pattern[str]], ...] = (
    (
        Category.REFUND_DISPUTE,
        _compile(r"\brefund", r"money back", r"\bchargeback", r"\bdispute", r"\breimburs"),
    ),
    (
        Category.ORDER_STATUS,
        _compile(
            r"where(?: is|['’]s) my (?:order|package|parcel)",
            r"\btrack",
            r"\barriv",
            r"\bdeliver",
            r"\bshipp?(?:ed|ing|ment)",
            r"\bparcel",
            r"\bpackage",
        ),
    ),
    (
        Category.BILLING,
        _compile(
            r"\binvoice",
            r"\bcharg(?:e|es|ed|ing)\b",
            r"\bbilling",
            r"\bsubscription",
            r"\bpayment",
            r"\bprice\b",
        ),
    ),
    (
        Category.TECHNICAL_ISSUE,
        _compile(
            r"\bcrash",
            r"\bbug\b",
            r"\berror",
            r"not working",
            r"(?:does not|doesn['’]t) work",
            r"\blog ?in\b",
            r"\bpassword",
            r"\bapp\b",
            r"\bwebsite",
        ),
    ),
)


def extract_order_id(text: str) -> str | None:
    match = _ORDER_ID.search(text)
    return match.group(1) if match else None


def classify(text: str) -> TriageResult:
    normalized = " ".join(text.split())
    order_id = extract_order_id(normalized)

    for category, pattern in RULES:
        if pattern.search(normalized):
            return TriageResult(category=category, confidence=MATCH_CONFIDENCE, order_id=order_id)

    # Rules cannot tell "other" from "unknown", so no match means unknown.
    return TriageResult(
        category=Category.UNKNOWN, confidence=NO_MATCH_CONFIDENCE, order_id=order_id
    )
