"""Generic metadata filtering (FR-010/FR-011, US4, research R6).

Filters are plain `{key: value}` dicts with all-equality semantics —
generic over keys, so new metadata keys work without code changes.
Filtering is restriction-only: it never reorders or rescores results
(US4 acceptance scenario 4). A filter key absent from a chunk's
metadata fails the match (missing = no access), yielding an empty set
without error — never a silent pass-through.
"""

from __future__ import annotations

from typing import Any

from domain import RetrievalResult


def matches_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    """True when every filter key equals the metadata value (AND semantics).

    An empty filter set matches everything (baseline identity).
    """
    if not filters:
        return True
    return all(key in metadata and metadata[key] == value for key, value in filters.items())


def apply_filters(results: list[RetrievalResult], filters: dict[str, Any]) -> list[RetrievalResult]:
    """Restrict results to matching metadata, preserving order and scores."""
    if not filters:
        return list(results)
    return [r for r in results if matches_filters(r.chunk.metadata, filters)]
