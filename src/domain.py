"""Pydantic v2 domain models for the Telco RAG pipeline.

Entities (data-model.md): Document, Chunk, RetrievalQuery, RetrievalResult,
Answer. Field names kept compatible with Level 0 so regression tests still
construct them directly.
"""

from typing import Any, ClassVar, Literal

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
    """A single ranked result from any strategy (data-model.md Level 3).

    score's meaning is strategy-dependent (contracts/retrieval-result-schema.md):
    cosine similarity for vector, BM25 score for bm25, RRF score for hybrid,
    cross-encoder score for hybrid_reranked.

    Level 3 provenance fields (Principle XXVI) are optional: `None` means
    *the stage did not run* — never a fabricated value. Level 2 consumers
    read only chunk/score/rank (FR-027 compatibility).
    """

    model_config = ConfigDict(validate_assignment=False)

    chunk: Chunk
    score: float
    rank: int

    retrieval_method: str | None = None
    vector_rank: int | None = None
    bm25_rank: int | None = None
    rrf_score: float | None = None
    reranker_score: float | None = None


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
    `relevant_chunks` (optional) adds chunk-level ground truth used by the
    retrieval matrix (FR-020); when empty, document labels are the truth.
    `filters` (optional) carries the metadata restriction for
    `metadata_filtered` questions — the matrix applies them per question.
    """

    id: str
    question: str
    relevant_documents: list[str] = Field(default_factory=list)
    category: str = "general"
    relevant_chunks: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)

    CATEGORIES: ClassVar[frozenset[str]] = frozenset(
        {
            # the eight Level 3 categories (FR-020)
            "semantic",
            "exact_terminology",
            "error_code",
            "acronym",
            "multi_concept",
            "ambiguous",
            "metadata_filtered",
            "unanswerable",
            # legacy values remain readable (data-model.md)
            "general",
            "5g",
            "lte",
            "broadband",
            "enterprise",
            "operations",
            "activation",
        }
    )

    @field_validator("question")
    @classmethod
    def _question_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(f"EvaluationQuestion {value!r}: question must be non-empty")
        return value

    @field_validator("category")
    @classmethod
    def _category_known(cls, value: str) -> str:
        if value not in cls.CATEGORIES:
            raise ValueError(
                f"EvaluationQuestion category {value!r} not in {sorted(cls.CATEGORIES)}"
            )
        return value

    @property
    def is_unanswerable(self) -> bool:
        return len(self.relevant_documents) == 0


# ---------------------------------------------------------------------------
# Level 2 — Grounded RAG models (specs/003-level-2-grounded-rag/data-model.md)
# ---------------------------------------------------------------------------

EVIDENCE_ID_PREFIX = "EVIDENCE-"


class StructuredOutputError(RuntimeError):
    """Provider output failed JSON parsing or GroundedAnswer validation.

    Contract rule 1 (contracts/grounded-answer-schema.md): malformed
    structured output is detected, never silently accepted as an answer.
    """


class Evidence(BaseModel):
    """First-class retrieved evidence (Principle XVII, FR-001/FR-002).

    Lossless projection of a RetrievalResult plus a stable evidence_id;
    the boundary between retrieval and generation.
    """

    model_config = ConfigDict(validate_assignment=False)

    evidence_id: str
    document_id: str
    chunk_id: str
    title: str
    source: str
    text: str
    retrieval_score: float
    rank: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("evidence_id", "document_id", "chunk_id", "title", "source")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Evidence field must be non-empty")
        return value

    @field_validator("text")
    @classmethod
    def _text_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Evidence text must be non-empty")
        return value

    @field_validator("retrieval_score")
    @classmethod
    def _score_range(cls, value: float) -> float:
        if not -1.0 <= value <= 1.0:
            raise ValueError(f"retrieval_score must be in [-1, 1], got {value}")
        return value

    @field_validator("rank")
    @classmethod
    def _rank_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError(f"rank must be >= 1, got {value}")
        return value


class Citation(BaseModel):
    """Reference from an answer claim to a document/chunk (FR-006).

    Existence is decided by the citation validator, not at parse time.
    """

    model_config = ConfigDict(validate_assignment=False)

    document_id: str
    chunk_id: str
    evidence_id: str | None = None

    @field_validator("document_id", "chunk_id")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Citation field must be non-empty")
        return value

    @property
    def key(self) -> tuple[str, str]:
        """Identity used for validation and deduplication."""
        return (self.document_id, self.chunk_id)


CitationStatus = Literal[
    "VALID",
    "UNKNOWN_DOCUMENT",
    "UNKNOWN_CHUNK",
    "NOT_RETRIEVED",
    "MALFORMED",
]


class CitationVerdict(BaseModel):
    """Deterministic validation result for one citation (data-model.md)."""

    model_config = ConfigDict(validate_assignment=False)

    citation: Citation
    status: CitationStatus
    detail: str = ""

    @property
    def is_valid(self) -> bool:
        return self.status == "VALID"


class ConflictNote(BaseModel):
    """A reported disagreement between retrieved sources (FR-019)."""

    model_config = ConfigDict(validate_assignment=False)

    description: str
    positions: list[Citation] = Field(default_factory=list)

    @field_validator("description")
    @classmethod
    def _description_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Conflict description must be non-empty")
        return value

    @field_validator("positions")
    @classmethod
    def _at_least_two(cls, value: list[Citation]) -> list[Citation]:
        if len(value) < 2:
            raise ValueError("ConflictNote.positions requires at least 2 citations")
        return value


class GroundedAnswer(BaseModel):
    """Structured answer schema (FR-004; contracts/grounded-answer-schema.md)."""

    # extra="forbid" is contract rule 7: unknown fields are rejected.
    model_config = ConfigDict(extra="forbid", validate_assignment=False)

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    abstained: bool = False
    sufficient_evidence: bool = True
    conflicts: list[ConflictNote] = Field(default_factory=list)

    @field_validator("answer")
    @classmethod
    def _answer_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("answer must be non-empty")
        return value

    @property
    def inconsistent_abstention(self) -> bool:
        """abstained=True with citations is flagged, not a parse error (rule 4)."""
        return self.abstained and len(self.citations) > 0

    @property
    def missing_citations(self) -> bool:
        """Non-abstained factual answer with no citations (rule 5)."""
        return not self.abstained and not self.citations


SufficiencyReason = Literal[
    "NO_EVIDENCE",
    "BELOW_MIN_COUNT",
    "BELOW_THRESHOLD",
    "MODEL_REPORTS_INSUFFICIENT",
    "SUFFICIENT",
]


class EvidenceSufficiencyDecision(BaseModel):
    """Explainable evidence-sufficiency decision (FR-011, research R3)."""

    model_config = ConfigDict(validate_assignment=False)

    sufficient: bool
    reason: SufficiencyReason
    evidence_count: int = 0
    mean_score: float | None = None


GroundednessStatus = Literal["SUPPORTED", "UNSUPPORTED", "PARTIALLY_SUPPORTED"]


class GroundednessVerdict(BaseModel):
    """Per-claim support classification against evidence (FR-016)."""

    model_config = ConfigDict(validate_assignment=False)

    claim: str
    status: GroundednessStatus
    supporting_evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("claim")
    @classmethod
    def _claim_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim must be non-empty")
        return value


GroundedCaseType = Literal["answerable", "unanswerable", "partial", "conflict"]


class GroundedEvaluationCase(BaseModel):
    """A grounded-answer evaluation dataset entry (FR-015; data-model.md).

    Additive extension of EvaluationQuestion: Level 1 entries load
    unchanged. Example used by the spec for an unanswerable case:
    "What is the average 5G speed in Japan?" (SC-003).
    """

    model_config = ConfigDict(validate_assignment=False)

    id: str
    question: str
    answerable: bool
    case_type: GroundedCaseType
    expected_answer: str = ""
    relevant_documents: list[str] = Field(default_factory=list)
    relevant_chunks: list[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("id")
    @classmethod
    def _id_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("GroundedEvaluationCase id must be non-empty")
        return value

    @field_validator("question")
    @classmethod
    def _question_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("GroundedEvaluationCase question must be non-empty")
        return value

    @field_validator("expected_answer")
    @classmethod
    def _expected_answer_consistent(cls, value: str, info) -> str:
        case_type = info.data.get("case_type")
        answerable = info.data.get("answerable")
        if case_type in ("answerable", "partial", "conflict") and not value.strip():
            raise ValueError(f"case_type={case_type!r} requires a non-empty expected_answer")
        if case_type == "unanswerable" and value.strip():
            raise ValueError("case_type='unanswerable' requires expected_answer=''")
        if answerable is not None and answerable != (case_type != "unanswerable"):
            raise ValueError(
                "answerable must be True for answerable/partial/conflict cases "
                "and False for unanswerable cases"
            )
        return value
