"""Lexical (BM25) retrieval over the same chunks as vector search.

FR-001/FR-002, research R1:
- `BM25Index` is a derived artifact built from Chunks — documents remain
  the source of truth; the index is rebuilt from them, never hand-edited.
- Tokenization is dependency-free lowercase `[a-z0-9]+` so error codes
  (504), acronyms (noc, sla) and hyphenated terms (x2-interface) match.
- Returns `RetrievalResult`s carrying `bm25_rank` provenance; fields for
  stages that did not run stay `None` (Principle XXVI).
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from domain import Chunk, RetrievalQuery, RetrievalResult

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokenization (keeps identifiers matchable)."""
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    """In-process BM25 index over a fixed chunk list (derived, rebuildable)."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks: list[Chunk] = list(chunks)
        self._tokens: list[list[str]] = [tokenize(c.content) for c in self.chunks]
        # BM25Okapi cannot score an empty corpus — guarded in search().
        self._bm25: BM25Okapi | None = BM25Okapi(self._tokens) if self._tokens else None

    @classmethod
    def build_from_chunks(cls, chunks: list[Chunk]) -> BM25Index:
        return cls(chunks)

    def search(self, question: str, top_k: int) -> list[RetrievalResult]:
        """Rank chunks by BM25 score; returns at most top_k results.

        Ties break by corpus position (stable, deterministic — FR-006/SC-004).
        Empty corpus or a query with no known tokens -> [] (no error, FR-001).
        """
        if self._bm25 is None or top_k < 1:
            return []
        query_tokens = tokenize(question)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Match = at least one query token present (BM25Okapi idf can be
        # negative for terms in every doc, so score>0 is not a match test).
        query_set = set(query_tokens)
        matching = [i for i, toks in enumerate(self._tokens) if query_set.intersection(toks)]
        # Descending score, ties broken by corpus position (deterministic, SC-004).
        order = sorted(matching, key=lambda i: (-float(scores[i]), i))[:top_k]

        results: list[RetrievalResult] = []
        for rank, i in enumerate(order, start=1):
            results.append(
                RetrievalResult(
                    chunk=self.chunks[i],
                    score=float(scores[i]),
                    rank=rank,
                    retrieval_method="bm25",
                    bm25_rank=rank,
                )
            )
        return results


class BM25Retriever:
    """RetrievalQuery interface parity with retrieval.retriever.Retriever."""

    def __init__(self, index: BM25Index):
        self.index = index

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        return self.index.search(query.question, query.top_k)


def build_bm25_index(
    document_dir: str | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> BM25Index:
    """Build the index from source documents (FR-002, Principle XXVIII).

    Reuses the Level 0 loader/chunker so the lexical corpus is byte-identical
    to the vector corpus — one truth (documents), two derived views.
    """
    from config import settings
    from ingestion.chunker import chunk_document
    from ingestion.loader import discover_documents

    docs = discover_documents(document_dir or settings.document_dir)
    chunks: list[Chunk] = []
    for doc in docs:
        chunks.extend(
            chunk_document(
                doc,
                chunk_size=chunk_size if chunk_size is not None else settings.chunk_size,
                chunk_overlap=chunk_overlap
                if chunk_overlap is not None
                else settings.chunk_overlap,
            )
        )
    return BM25Index.build_from_chunks(chunks)
