"""Pydantic v2 domain models for the Telco RAG pipeline.

Entities (data-model.md): Document, Chunk, RetrievalQuery, RetrievalResult,
Answer. Field names kept compatible with Level 0 so regression tests still
construct them directly.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    """A source knowledge file in the corpus (data-model.md)."""

    model_config = ConfigDict(validate_assignment=False)

    document_id: str
    document_name: str
    source: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def _content_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Document content must be non-empty")
        return value


class Chunk(BaseModel):
    """A fragment of a document; the unit of embedding and retrieval."""

    model_config = ConfigDict(validate_assignment=False)

    chunk_id: str
    content: str
    document_id: str
    document_name: str
    source: str
    chunk_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalQuery(BaseModel):
    """Typed input to the retrieval layer (data-model.md).

    `metadata_filter` is an internal-only capability (FR-008): it restricts
    results to matching document metadata and is NOT exposed via the CLI.
    """

    question: str
    top_k: int = 4
    similarity_threshold: float = 0.0
    metadata_filter: dict[str, Any] | None = None

    @field_validator("question")
    @classmethod
    def _question_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must be non-empty")
        return value

    @field_validator("top_k")
    @classmethod
    def _top_k_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError(f"top_k must be >= 1, got {value}")
        return value

    @field_validator("similarity_threshold")
    @classmethod
    def _threshold_range(cls, value: float) -> float:
        if not -1.0 <= value <= 1.0:
            raise ValueError(f"similarity_threshold must be in [-1, 1], got {value}")
        return value


class RetrievalResult(BaseModel):
    """A single ranked similarity-search result (data-model.md).

    score is cosine similarity; higher = more similar (store converts Chroma
    distances to scores: score = 1 - distance).
    """

    model_config = ConfigDict(validate_assignment=False)

    chunk: Chunk
    score: float
    rank: int


class Answer(BaseModel):
    """The provider's response, or the system's abstention."""

    text: str
    used_context: bool = False
    citations: list[str] = Field(default_factory=list)


class EvaluationQuestion(BaseModel):
    """A versioned retrieval-evaluation dataset entry (data-model.md).

    `relevant_documents` holds the expected `document_id`(s) for answerable
    questions; an empty list marks the question as UNANSWERABLE (FR-009a) —
    retrieval must return nothing for a correct true-negative.
    """

    id: str
    question: str
    relevant_documents: list[str] = Field(default_factory=list)
    category: str = "general"

    @field_validator("question")
    @classmethod
    def _question_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(f"EvaluationQuestion {value!r}: question must be non-empty")
        return value

    @property
    def is_unanswerable(self) -> bool:
        return len(self.relevant_documents) == 0