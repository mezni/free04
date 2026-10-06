from typing import List

from domain import RetrievalResult
from embeddings.embedder import Embedder


class Retriever:
    """Question → query embedding → vector search → top-K RetrievalResults."""

    def __init__(self, vector_store: "VectorStore", embedder: Embedder, top_k: int = 4):
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(self, question: str) -> List[RetrievalResult]:
        """Search for top-K chunks relevant to the question.

        Returns a list of RetrievalResult objects containing the retrieved
        chunks, their similarity scores, and rank ordering.
        """
        # Embed the question
        query_vector = self.embedder.embed_query(question)

        # Search the vector store
        results = self.vector_store.search(query_vector, self.top_k)

        # Ensure results are ordered by descending score and ranked
        results.sort(key=lambda r: r.score, reverse=True)

        # Re-rank starting from 1
        for i, result in enumerate(results, start=1):
            result.rank = i

        return results