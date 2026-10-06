"""Evaluation metrics tests (constitution XVI, FR-009a, evaluation-contract.md)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from domain import Chunk, EvaluationQuestion, RetrievalQuery
from evaluation.dataset import load_questions, missing_docs
from evaluation.metrics import (
    evaluate_retrieval,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from retrieval.retriever import Retriever
from retrieval.vector_store import VectorStore

DIM = 4


class _EvalEmbedder:
    """Deterministic embedder mapping a doc id to its basis vector."""

    _doc_to_index = {
        "5g_latency": 0,
        "5g_packet_loss": 1,
        "broadband_connectivity": 2,
        "enterprise_sla": 3,
        "lte_troubleshooting": 0,
        "network_escalation": 1,
        "noc_incident_procedure": 2,
        "sim_activation": 3,
    }

    def embed_query(self, question: str) -> np.ndarray:
        vec = np.zeros(DIM, dtype=np.float32)
        for ch in question:
            vec[ord(ch) % DIM] += 1.0
        return vec

    def embed(self, question: str) -> np.ndarray:
        return self.embed_query(question)


def _chunk(doc_id: str, content: str) -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}#0001",
        content=content,
        document_id=doc_id,
        document_name=f"{doc_id}.md",
        source=f"data/documents/{doc_id}.md",
        chunk_index=1,
    )


def _setup(tmp_path):
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma"), collection_name="test_c", dimension=DIM
    )
    docs = [
        "5g_latency",
        "5g_packet_loss",
        "broadband_connectivity",
        "enterprise_sla",
    ]
    store.add(
        [_chunk(d, f"content about {d}") for d in docs],
        [np.eye(DIM, dtype=np.float32)[i] for i in range(len(docs))],
    )
    return Retriever(store, _EvalEmbedder())


def test_recall_at_k_expected_doc_in_top3(tmp_path):
    # 3 docs with DISTINCT cosine scores against the query => deterministic ranks.
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma_recall"),
        collection_name="test_c",
        dimension=DIM,
    )
    store.add(
        [
            _chunk("broadband_connectivity", "content broadband"),
            _chunk("5g_latency", "content latency"),
            _chunk("5g_packet_loss", "content packet loss"),
        ],
        [
            np.eye(DIM, dtype=np.float32)[0],
            np.eye(DIM, dtype=np.float32)[1],
            np.eye(DIM, dtype=np.float32)[2],
        ],
    )

    class _Top3NotRelevant:
        def embed_query(self, question: str) -> np.ndarray:
            # cosines: broadband=1, latency=2, packet_loss=3 (all distinct)
            return np.array([1.0, 2.0, 3.0, 0.5], dtype=np.float32)

    r = Retriever(store, _Top3NotRelevant())

    q = EvaluationQuestion(id="q", question="aaaa", relevant_documents=["5g_latency"])
    results = r.retrieve(RetrievalQuery(question="aaaa", top_k=3))
    # rank order: packet_loss(3), latency(2), broadband(1) -> latency is in top-3
    assert [res.chunk.document_id for res in results] == [
        "5g_packet_loss",
        "5g_latency",
        "broadband_connectivity",
    ]
    assert recall_at_k(results, q, 3) == 1.0
    print("✓ recall@k expected doc in top-3 -> 1")


def test_recall_at_k_expected_doc_not_retrieved(tmp_path):
    r = _setup(tmp_path)
    q = EvaluationQuestion(id="q", question="aaaa", relevant_documents=["lte_troubleshooting"])
    results = r.retrieve(RetrievalQuery(question="eeee", top_k=1))
    assert recall_at_k(results, q, 1) == 0.0
    print("✓ recall@k expected doc absent -> 0")


def test_precision_at_k_denominator_is_k(tmp_path):
    r = _setup(tmp_path)
    q = EvaluationQuestion(id="q", question="aaaa", relevant_documents=["5g_latency"])
    results = r.retrieve(RetrievalQuery(question="eeee", top_k=4))
    # exactly one relevant hit out of 4 retrieved -> precision = 1/4
    assert precision_at_k(results, q, 4) == 1.0 / 4.0
    print("✓ precision@k uses K denominator")


def test_mrr_expected_doc_at_rank_3_is_one_third(tmp_path):
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma_mrr"),
        collection_name="test_c",
        dimension=DIM,
    )
    class _Ranked:
        """query=[4,3,2,1] -> broadband(4) rank1, enterprise(3) rank2,
        latency(2) rank3, packet_loss(1) rank4 (distinct cosines, no ties)."""

        def embed_query(self, question: str) -> np.ndarray:
            return np.array([4.0, 3.0, 2.0, 1.0], dtype=np.float32)

    store.add(
        [
            _chunk("broadband_connectivity", "content broadband"),
            _chunk("enterprise_sla", "content sla"),
            _chunk("5g_latency", "content latency"),
            _chunk("5g_packet_loss", "content packet loss"),
        ],
        [
            np.eye(DIM, dtype=np.float32)[0],
            np.eye(DIM, dtype=np.float32)[1],
            np.eye(DIM, dtype=np.float32)[2],
            np.eye(DIM, dtype=np.float32)[3],
        ],
    )
    retriever = Retriever(store, _Ranked())

    q = EvaluationQuestion(id="q", question="aaaa", relevant_documents=["5g_latency"])
    results = retriever.retrieve(RetrievalQuery(question="aaaa", top_k=4))
    assert [r.chunk.document_id for r in results] == [
        "broadband_connectivity",
        "enterprise_sla",
        "5g_latency",
        "5g_packet_loss",
    ]
    assert reciprocal_rank(results, q) == 1.0 / 3.0
    print("✓ mrr expected doc at rank 3 -> 1/3")


def test_unanswerable_excluded_and_counted(tmp_path):
    r = _setup(tmp_path)
    unanswerable_q = EvaluationQuestion(
        id="q-un", question="xxxxxx", relevant_documents=[]
    )
    answerable_q = EvaluationQuestion(
        id="q-a", question="eeee", relevant_documents=["5g_latency"]
    )
    # "xxxxxx" -> embedding near e2 (broadband) = a false positive
    report = evaluate_retrieval([unanswerable_q, answerable_q], r, k=4)
    assert report["recall_at_k"] == 1.0
    assert report["precision_at_k"] == 1.0 / 4.0
    # unanswerable excluded from aggregates but counted:
    assert report["false_positives"] == 1
    assert report["true_negatives"] == 0
    print("✓ unanswerable excluded from aggregate + counted as FP")


def test_true_negative_when_unanswerable_returns_nothing(tmp_path):
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma_tn"),
        collection_name="test_c",
        dimension=DIM,
    )
    # empty store -> nothing retrieved for any question
    retriever = Retriever(store, _EvalEmbedder())
    q = EvaluationQuestion(id="q-un", question="xxxxxx", relevant_documents=[])
    report = evaluate_retrieval([q], retriever, k=4)
    assert report["true_negatives"] == 1
    assert report["false_positives"] == 0
    print("✓ unanswerable with no retrievals -> true negative")


def test_dataset_loads_real_questions():
    questions = load_questions("data/evaluation/retrieval_questions.jsonl")
    assert len(questions) >= 20
    answerable = [q for q in questions if not q.is_unanswerable]
    unanswerable = [q for q in questions if q.is_unanswerable]
    assert len(unanswerable) >= 2
    assert len(answerable) > len(unanswerable)
    # every relevant doc id exists in the corpus
    assert missing_docs(questions) == []
    print("✓ dataset loads + doc ids all in corpus")


def test_unanswerable_filters_to_true_negative_with_threshold(tmp_path):
    """FR-009a: a high-enough similarity_threshold turns unanswerable into true-negatives."""
    store = VectorStore(
        persist_directory=str(tmp_path / "chroma_thr"),
        collection_name="test_c",
        dimension=DIM,
    )
    store.add(
        [_chunk("5g_latency", "content latency")],
        [np.eye(DIM, dtype=np.float32)[0]],
    )

    class _UnanswerableEmbedder:
        def embed_query(self, question: str) -> np.ndarray:
            # orthogonal to the single stored doc => cosine 0.0 < threshold 0.3
            return np.eye(DIM, dtype=np.float32)[1]

    retriever = Retriever(store, _UnanswerableEmbedder())
    q = EvaluationQuestion(id="q-un", question="xxxx", relevant_documents=[])
    # threshold 0.3: single hit (score 0.0) is filtered out -> true negative.
    report = evaluate_retrieval(
        [q], retriever, k=4, similarity_threshold=0.3
    )
    assert report["true_negatives"] == 1
    assert report["false_positives"] == 0
    # threshold 0.0 (no filtering): the hit remains -> false positive.
    report0 = evaluate_retrieval([q], retriever, k=4, similarity_threshold=0.0)
    assert report0["false_positives"] == 1
    print("✓ evaluation threshold drives true negatives")


def test_dataset_invalid_line_raises(tmp_path):
    p = tmp_path / "broken.jsonl"
    p.write_text('{"id": "x", "question": "", "relevant_documents": []}\n', encoding="utf-8")
    try:
        load_questions(p)
    except ValueError:
        print("✓ invalid dataset line raises")
        return
    raise AssertionError("invalid line should raise")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_recall_at_k_expected_doc_in_top3(Path(td))
        test_recall_at_k_expected_doc_not_retrieved(Path(td))
        test_precision_at_k_denominator_is_k(Path(td))
        test_mrr_expected_doc_at_rank_3_is_one_third(Path(td))
        test_unanswerable_excluded_and_counted(Path(td))
        test_true_negative_when_unanswerable_returns_nothing(Path(td))
        test_unanswerable_filters_to_true_negative_with_threshold(Path(td))
        test_dataset_loads_real_questions()
        test_dataset_invalid_line_raises(Path(td))
    print("✓ All evaluation tests passed")