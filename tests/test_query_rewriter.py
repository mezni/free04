"""Query rewriting tests (FR-015…FR-017, US6, Principle XXIX NON-NEGOTIABLE).

Default OFF; the original query is always preserved on the debug object;
any gateway failure, empty, or broken reply falls back to the original
with a stderr warning — retrieval never fails because of a rewrite.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from domain import Answer, Chunk, RetrievalQuery, RetrievalResult

try:
    from retrieval.query_rewriter import QueryRewriter
except ImportError:  # TDD: module does not exist yet
    QueryRewriter = None

try:
    from retrieval.controller import RetrievalController
except ImportError:
    RetrievalController = None


class FakeLLMClient:
    """Stands in for generation.llm.LLMClient (hermetic, no gateway)."""

    def __init__(self, text: str = "rewritten query", error: Exception | None = None):
        self.text = text
        self.error = error
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> Answer:
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return Answer(text=self.text, used_context=True)


class RecordingRetriever:
    def __init__(self, results):
        self._results = list(results)
        self.calls: list[RetrievalQuery] = []

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        self.calls.append(query)
        return list(self._results)


def _r(doc_id: str, rank: int, score: float) -> RetrievalResult:
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
    )


def _controller(rewriter, **kwargs):
    kwargs.setdefault("vector_retriever", RecordingRetriever([_r("a", 1, 0.9)]))
    kwargs.setdefault("bm25_retriever", RecordingRetriever([_r("b", 1, 5.0)]))
    return RetrievalController(strategy="vector", rewriter=rewriter, **kwargs)


# -- validation + fallback (QueryRewriter unit level) -----------------------


def test_valid_rewrite_returns_single_query():
    rewriter = QueryRewriter(FakeLLMClient(text="5G packet loss troubleshooting RF interference"))
    out = rewriter.rewrite("5g packet loss?")
    assert out == "5G packet loss troubleshooting RF interference"
    print("✓ valid reply accepted")


def test_prompt_mandates_one_query_and_preserves_identifiers():
    client = FakeLLMClient(text="ok")
    rewriter = QueryRewriter(client)
    rewriter.rewrite("X2 interface timeout 504")
    prompt = client.prompts[0]
    assert "X2 interface timeout 504" in prompt  # original embedded verbatim
    assert "exactly one" in prompt.lower()
    print("✓ prompt carries the original and the one-query mandate")


def test_empty_or_whitespace_reply_falls_back():
    for bad in ("", "   \n  \n"):
        rewriter = QueryRewriter(FakeLLMClient(text=bad))
        assert rewriter.rewrite("q") is None
    print("✓ empty/whitespace reply -> fallback (None)")


def test_multiline_reply_normalized_to_first_line():
    rewriter = QueryRewriter(FakeLLMClient(text="first query line\nsecond line\nthird"))
    assert rewriter.rewrite("q") == "first query line"
    print("✓ multiline reply -> exactly one query (first line)")


def test_excessive_length_falls_back():
    rewriter = QueryRewriter(FakeLLMClient(text="x" * 5000))
    assert rewriter.rewrite("q") is None
    print("✓ absurdly long reply -> fallback")


def test_quoted_reply_is_unquoted():
    rewriter = QueryRewriter(FakeLLMClient(text='"the rewritten query"'))
    assert rewriter.rewrite("q") == "the rewritten query"
    print("✓ quoted reply stripped to the query")


def test_gateway_error_warns_on_stderr_and_falls_back(capsys):
    rewriter = QueryRewriter(FakeLLMClient(error=RuntimeError("LLM request timed out")))
    assert rewriter.rewrite("original question") is None
    captured = capsys.readouterr()
    assert "warning" in captured.err.lower()
    assert "original question" in captured.err  # names the query of record
    print("✓ gateway error -> stderr warning, fallback to original")


# -- controller integration (T037 wiring) ------------------------------------


def test_default_disabled_never_calls_rewriter():
    class ExplodingRewriter:
        calls = 0

        def rewrite(self, q):
            ExplodingRewriter.calls += 1
            return "should never be used"

    c = _controller(ExplodingRewriter(), rewriting_enabled=False)
    dbg = c.retrieve("the original?")
    assert ExplodingRewriter.calls == 0
    assert dbg.rewritten_query is None
    assert dbg.query == "the original?"
    assert "rewrite" in dbg.stages_skipped
    assert c.vector_retriever.calls[0].question == "the original?"
    print("✓ default disabled: no rewrite attempted, original used (XXIX)")


def test_rewrite_runs_and_original_stays_query_of_record():
    rewriter = QueryRewriter(FakeLLMClient(text="expanded 5G query"))
    c = _controller(rewriter, rewriting_enabled=True)
    dbg = c.retrieve("the original question")
    assert dbg.query == "the original question"  # original preserved
    assert dbg.rewritten_query == "expanded 5G query"
    # Retrieval used the rewritten string (FR-015/FR-016).
    assert c.vector_retriever.calls[0].question == "expanded 5G query"
    assert "rewrite" not in dbg.stages_skipped
    print("✓ rewrite runs: original kept, retrieval uses rewritten query")


def test_failed_rewrite_falls_back_to_original_in_controller():
    rewriter = QueryRewriter(FakeLLMClient(error=RuntimeError("gateway down")))
    c = _controller(rewriter, rewriting_enabled=True)
    dbg = c.retrieve("original question?")
    assert dbg.rewritten_query is None  # fallback: no rewrite recorded
    assert dbg.query == "original question?"
    assert c.vector_retriever.calls[0].question == "original question?"
    assert "rewrite" not in dbg.stages_skipped  # stage ran, produced no rewrite
    print("✓ failed rewrite: retrieval still runs on the original, exit-0 path")


def test_rewrite_latency_recorded_when_stage_runs():
    rewriter = QueryRewriter(FakeLLMClient(text="expanded"))
    c = _controller(rewriter, rewriting_enabled=True)
    dbg = c.retrieve("q")
    assert "rewrite" in dbg.latency_ms

    c2 = _controller(QueryRewriter(FakeLLMClient(text="x")), rewriting_enabled=False)
    dbg2 = c2.retrieve("q")
    assert "rewrite" not in dbg2.latency_ms
    print("✓ rewrite latency key present only when the stage ran")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
