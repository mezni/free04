"""Domain models for ticket triage."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    """The single category assigned to a triaged ticket."""

    REFUND_DISPUTE = "refund_dispute"
    ORDER_STATUS = "order_status"
    BILLING = "billing"
    TECHNICAL_ISSUE = "technical_issue"
    OTHER = "other"
    UNKNOWN = "unknown"


class TriageResult(BaseModel):
    """Validated classification of one support ticket."""

    category: Category
    confidence: float = Field(ge=0.0, le=1.0)
    order_id: str | None = None
