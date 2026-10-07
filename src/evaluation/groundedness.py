"""Deterministic claim-support baseline and GroundednessJudge interface (FR-016).

Split by determinism (research R4):
- Lexical claim/evidence support baseline runs in CI-style tests with no
  LLM (token overlap against cited/citing evidence text).
- Claim-level SUPPORTED / UNSUPPORTED / PARTIALLY_SUPPORTED verdicts are
  produced by a `GroundednessJudge` (structured LLM call, isolated);
  unit tests use fixture judges only (FR-022).

No frameworks, transparent Python (Principle XVI).
"""

from __future__ import annotations

import re
from typing import Protocol

from domain import Evidence, GroundednessVerdict

# Token-overlap ratios for the lexical baseline (thresholds are exported
# so callers and experiments can reason about the exact decision boundary).
SUPPORTED_RATIO = 0.85
PARTIAL_RATIO = 0.40

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "of",
        "to",
        "in",
        "on",
        "at",
        "by",
        "for",
        "with",
        "from",
        "as",
        "be",
        "is",
        "are",
        "was",
        "were",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "do",
        "does",
        "did",
        "can",
        "could",
        "would",
        "will",
        "may",
        "might",
        "not",
        "no",
        "yes",
        "how",
        "what",
        "why",
        "which",
        "when",
        "where",
        "who",
        "whom",
        "than",
    }
)

_TOKEN = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> set[str]:
    """Significant tokens (lowercased, stopwords removed)."""
    return {w for w in _TOKEN.findall(text.lower())} - STOPWORDS


def lexical_support(claim: str, evidence_texts: list[str]) -> float:
    """Fraction of claim tokens present in the evidence texts (0.0-1.0)."""
    claim_tokens = tokenize(claim)
    if not claim_tokens:
        return 0.0
    covered: set[str] = set()
    for text in evidence_texts:
        covered |= tokenize(text)
    return len(claim_tokens & covered) / len(claim_tokens)


def extract_claims(answer: str) -> list[str]:
    """Split an answer into claim sentences (deterministic)."""
    if not answer or not answer.strip():
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer.strip()) if s.strip()]


def classify_claim(
    claim: str,
    evidence_texts: list[str],
    evidence_ids: list[str] | None = None,
) -> GroundednessVerdict:
    """Lexical claim-support classification (no LLM).

    Args:
        claim: the claim to classify.
        evidence_texts: evidence passages used for support.
        evidence_ids: optional evidence ids aligned with evidence_texts;
            contributing ids populate supporting_evidence_ids.

    Returns:
        A GroundednessVerdict with EXACT token-overlap semantics.
    """
    claim_tokens = tokenize(claim)
    claim_clean = claim.strip()
    if not claim_clean:
        raise ValueError("claim must be non-empty")
    if not claim_tokens:
        return GroundednessVerdict(
            claim=claim_clean, status="UNSUPPORTED", supporting_evidence_ids=[]
        )

    evidence_token_sets = [tokenize(t) for t in evidence_texts]
    covered: set[str] = set()
    for tokens in evidence_token_sets:
        covered |= tokens

    ratio = len(claim_tokens & covered) / len(claim_tokens)
    if ratio >= SUPPORTED_RATIO:
        status = "SUPPORTED"
    elif ratio >= PARTIAL_RATIO:
        status = "PARTIALLY_SUPPORTED"
    else:
        status = "UNSUPPORTED"

    supporting: list[str] = []
    if evidence_ids is not None:
        for eid, tokens in zip(evidence_ids, evidence_token_sets, strict=True):
            if claim_tokens & tokens:
                supporting.append(eid)

    return GroundednessVerdict(
        claim=claim_clean,
        status=status,  # type: ignore[arg-type]
        supporting_evidence_ids=supporting,
    )


class GroundednessJudge(Protocol):
    """Interface for model-based claim-level judgment (research R4)."""

    def judge(self, claim: str, evidence: list[Evidence]) -> GroundednessVerdict:
        """Return a SUPPORTED/UNSUPPORTED/PARTIALLY_SUPPORTED verdict."""


class StructuredJudge:
    """Isolated structured-LLM judge; live use recorded only in experiments.

    Not exercised by the deterministic test suite (FR-022); a fixture judge
    is used in unit tests instead.
    """

    def __init__(self, llm_client) -> None:
        self.llm_client = llm_client

    def judge(self, claim: str, evidence: list[Evidence]) -> GroundednessVerdict:
        prompt = (
            "Classify whether the CLAIM is supported by the EVIDENCE.\n\n"
            f"CLAIM: {claim}\n\nEVIDENCE:\n"
            + "\n".join(f"{e.evidence_id}: {e.text}" for e in evidence)
            + '\n\nReply with ONLY JSON: {"claim": "...", '
            '"status": "SUPPORTED|UNSUPPORTED|PARTIALLY_SUPPORTED",'
            ' "supporting_evidence_ids": ["EVIDENCE-nnn", ...]}'
        )
        raw = self.llm_client.generate_json(prompt)
        return _parse_judge_response(raw, claim)


def _parse_judge_response(raw: str, claim: str) -> GroundednessVerdict:
    import json

    from domain import GroundednessStatus

    try:
        data = json.loads(raw)
        status = data["status"]
        if status not in GroundednessStatus.__args__:  # type: ignore[attr-defined]
            raise ValueError(f"unknown status {status!r}")
        return GroundednessVerdict(
            claim=data.get("claim") or claim,
            status=status,
            supporting_evidence_ids=list(data.get("supporting_evidence_ids", [])),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"judge returned unusable verdict: {exc}") from exc


def evaluate_claim(
    claim: str,
    evidence: list[Evidence],
    judge: GroundednessJudge | None = None,
) -> GroundednessVerdict:
    """Verdict for one claim: judge when given, else the lexical baseline.

    Args:
        claim: claim text.
        evidence: Evidence objects for the current question.
        judge: optional model-based judge (isolated; not used in tests).

    Returns:
        A GroundednessVerdict.
    """
    if judge is not None:
        return judge.judge(claim, evidence)
    return classify_claim(
        claim,
        [e.text for e in evidence],
        evidence_ids=[e.evidence_id for e in evidence] if evidence else None,
    )
