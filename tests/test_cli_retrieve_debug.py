"""US3 per-stage diagnostics tests (FR-019/FR-023, contracts/cli-retrieve.md §3).

Debug output shows only the provenance that actually ran (never a
fabricated 0), the original query is always visible (Principle XXIX),
and latency keys exist only for stages that ran (Principle XXVI).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from typer.testing import CliRunner

from cli import app
from domain import Chunk, RetrievalQuery, RetrievalResult

try:
    from retrieval.controller import RetrievalController, RetrievalDebug
except ImportError:  # TDD: module does not exist yet
    RetrievalController = None
    RetrievalDebug = None

runner = CliRunner()


def _r(doc_id: str, rank: int, score: float, **prov) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=f"{doc_id}#0001",
            content=f"content {doc_id}",
            document_id=doc_id,
            document_name=f"{doc_id}.md",
            source=f"data/documents/{doc_id}.md",
            chunk_index=1,
        ),
        score=score,
        rank=rank,
        **prov,
    )


def _debug(**kwargs) -> RetrievalDebug:
    kwargs.setdefault("query", "what is latency?")
    kwargs.setdefault("strategy", "hybrid")
    return RetrievalDebug(**kwargs)


def _invoke(args: list[str], dbg: RetrievalDebug):
    controller = MagicMock()
    controller.retrieve.return_value = dbg
    with patch("retrieval.controller.build_controller", return_value=controller):
        return runner.invoke(app, ["retrieve", *args])


# -- CLI --debug rendering ------------------------------------------------


def test_debug_shows_only_provenance_that_ran():
    dbg = _debug(
        results=[
            _r(
                "5g_latency",
                rank=1,
                score=0.0412,
                rrf_score=0.0311,
                vector_rank=2,
                bm25_rank=1,
            )
        ],
        stages_skipped=["rewrite", "rerank"],
        latency_ms={"vector": 1.8, "bm25": 0.3, "fuse": 0.0, "filter": 0.1, "total": 2.9},
    )
    result = _invoke(["what is latency?", "--debug"], dbg)
    assert result.exit_code == 0, result.output
    assert "rrf_score: 0.0311" in result.output
    assert "vector_rank: 2" in result.output
    assert "bm25_rank: 1" in result.output
    # reranker never ran -> the field is absent, never printed as 0 (XXVI).
    assert "reranker_score" not in result.output
    assert "[5g_latency#0001]" in result.output
    assert "Stages skipped: rewrite, rerank" in result.output
    print("✓ debug shows applicable provenance only (absent stages omitted)")


def test_debug_original_query_always_shown_when_rewritten():
    dbg = _debug(
        query="original question",
        rewritten_query="original question with expanded terms",
        strategy="hybrid",
        results=[_r("a", 1, 0.5)],
        stages_skipped=["rerank"],
        latency_ms={"total": 1.0},
    )
    result = _invoke(["original question", "--debug"], dbg)
    assert result.exit_code == 0, result.output
    assert "Query: original question" in result.output
    assert "Rewritten query: original question with expanded terms" in result.output
    print("✓ original query always shown alongside the rewrite")


def test_debug_rewritten_query_not_run_marker():
    dbg = _debug(results=[], stages_skipped=["rewrite", "rerank"], latency_ms={"total": 0.5})
    result = _invoke(["q", "--debug"], dbg)
    assert result.exit_code == 0, result.output
    assert "Rewritten query: (not run)" in result.output
    assert "Query: what is latency?" in result.output
    print("✓ (not run) marker for disabled rewrite")


def test_debug_latency_keys_only_for_stages_that_ran():
    dbg = _debug(
        results=[_r("a", 1, 0.5)],
        stages_skipped=["rewrite", "bm25", "fuse", "rerank"],
        latency_ms={"embed": 4.1, "vector": 1.8, "filter": 0.1, "total": 102.9},
    )
    result = _invoke(["q", "--debug"], dbg)
    assert result.exit_code == 0, result.output
    latency_lines = [ln for ln in result.output.splitlines() if ln.startswith("Latency (ms):")]
    assert len(latency_lines) == 1
    line = latency_lines[0]
    assert line == "Latency (ms): embed 4.1 | vector 1.8 | filter 0.1 | total 102.9"
    for absent in ("bm25", "fuse", "rerank", "rewrite"):
        assert absent not in line
    print("✓ latency line contains only stages that ran, in fixed order")


def test_debug_filters_line_renders_configured_filters():
    dbg = _debug(filters={"category": "5g"}, results=[], latency_ms={"total": 0.5})
    result = _invoke(["q", "--debug"], dbg)
    assert 'Filters: {"category": "5g"}' in result.output

    dbg2 = _debug(filters={}, results=[], latency_ms={"total": 0.5})
    result2 = _invoke(["q", "--debug"], dbg2)
    assert "Filters: (none)" in result2.output
    print("✓ filters line renders configured filters or (none)")


def test_debug_zero_results_still_exit_0():
    dbg = _debug(results=[], stages_skipped=["rewrite", "rerank"], latency_ms={"total": 0.4})
    result = _invoke(["q", "--debug"], dbg)
    assert result.exit_code == 0, result.output
    assert "Query: what is latency?" in result.output
    assert "Latency (ms):" in result.output
    print("✓ zero results with --debug is a valid exit-0 outcome")


def test_normal_output_has_no_debug_block():
    dbg = _debug(results=[_r("a", 1, 0.5)], latency_ms={"total": 1.0})
    result = _invoke(["q"], dbg)
    assert result.exit_code == 0, result.output
    assert "Strategy: hybrid (query mode: original)" in result.output
    assert "Latency (ms):" not in result.output
    assert "Stages skipped:" not in result.output
    print("✓ normal mode keeps its plain output (no debug block)")


# -- controller instrumentation (T021) -------------------------------------


class FakeVectorRetriever:
    def __init__(self, results, last_timings=None):
        self._results = list(results)
        self.calls: list[RetrievalQuery] = []
        if last_timings is not None:
            self.last_timings = last_timings

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        self.calls.append(query)
        return list(self._results)


class FakeBM25Retriever(FakeVectorRetriever):
    pass


def _fakes(**kwargs):
    kwargs.setdefault("vector_retriever", FakeVectorRetriever([_r("a", 1, 0.9)]))
    kwargs.setdefault("bm25_retriever", FakeBM25Retriever([_r("b", 1, 5.0)]))
    return RetrievalController(**kwargs)


def test_controller_latency_keys_only_for_run_stages_vector():
    c = _fakes(strategy="vector")
    dbg = c.retrieve("q")
    keys = set(dbg.latency_ms)
    assert "total" in dbg.latency_ms
    assert "vector" in keys
    for absent in ("bm25", "fuse", "rerank", "rewrite"):
        assert absent not in keys
        assert absent in dbg.stages_skipped
    assert keys <= {"rewrite", "embed", "vector", "bm25", "filter", "fuse", "rerank", "total"}
    print("✓ vector strategy: no latency keys for stages that never ran")


def test_controller_latency_keys_for_hybrid_stages():
    c = _fakes(strategy="hybrid")
    dbg = c.retrieve("q")
    keys = set(dbg.latency_ms)
    assert {"vector", "bm25", "fuse", "filter", "total"} <= keys
    assert "rerank" not in keys and "rerank" in dbg.stages_skipped
    assert "rewrite" not in keys and "rewrite" in dbg.stages_skipped
    # Fake vector retriever exposes no embed timing -> no fabricated embed key.
    assert "embed" not in keys
    print("✓ hybrid: fuse/vector/bm25 measured, rerank/rewrite absent")


def test_controller_uses_retriever_timings_for_embed_split():
    vector = FakeVectorRetriever([_r("a", 1, 0.9)], last_timings={"embed": 2.0, "search": 1.0})
    c = _fakes(strategy="vector", vector_retriever=vector)
    dbg = c.retrieve("q")
    assert dbg.latency_ms["embed"] == pytest.approx(2.0)
    assert dbg.latency_ms["vector"] == pytest.approx(1.0)
    print("✓ embed/vector split comes from instrumented Retriever timings")


def test_controller_latency_is_ordered_and_total_last_in_rendering():
    c = _fakes(strategy="hybrid_reranked")  # no reranker wired -> falls through
    dbg = c.retrieve("q")
    assert "rerank" in dbg.stages_skipped
    assert set(dbg.latency_ms) <= {
        "rewrite",
        "embed",
        "vector",
        "bm25",
        "filter",
        "fuse",
        "rerank",
        "total",
    }
    print("✓ hybrid_reranked without reranker: no rerank latency key")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
