from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A source knowledge file in the corpus."""

    document_id: str
    document_name: str
    source: str
    content: str

    def __post_init__(self):
        if not self.content.strip():
            raise ValueError("Document content must be non-empty")


@dataclass
class Chunk:
    """A fragment of a document; the unit of embedding and retrieval."""

    chunk_id: str
    content: str
    document_id: str
    document_name: str
    source: str

    def __post_init__(self):
        if not self.content.strip():
            raise ValueError("Chunk content must be non-empty")


@dataclass
class RetrievalResult:
    """The outcome of searching a query embedding against the store."""

    chunk: Chunk
    score: float
    rank: int

    @property
    def used_context(self) -> bool:
        return self.score > 0.0


@dataclass
class Answer:
    """The provider's response, or the system's abstention."""

    text: str
    used_context: bool = False
    citations: list = field(default_factory=list)

    @property
    def citations(self) -> list:
        return self._citations

    @citations.setter
    def citations(self, value: list):
        self._citations = value