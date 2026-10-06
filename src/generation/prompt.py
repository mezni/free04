from domain import RetrievalResult


PROMPT_SYSTEM_INSTRUCTION = """You are a Telco knowledge assistant. Answer the user's question using ONLY the retrieved context below.

Grounding rules:
1. Answer using only the supplied retrieved context. Do not invent facts not present in the context.
2. If the context is insufficient to answer the question, state explicitly: "I don't have enough information in the knowledge base to answer this question."
3. Answer clearly and directly in the language of the question.

Do not include any reasoning, chain-of-thought, or meta-commentary in your answer.
"""

PROMPT_TEMPLATE = """Question: {question}

Context:
{context}

Answer:"""


def build_prompt(question: str, results: list, use_context: bool = True) -> str:
    """Build the prompt for the LLM answer provider.

    Args:
        question: The user's question.
        results: List of RetrievalResult objects from the vector store search.
        use_context: Whether to include retrieved context in the prompt.

    Returns:
        A formatted prompt string ready to be sent to the LLM.
    """
    if not use_context or not results:
        return PROMPT_SYSTEM_INSTRUCTION + "\n\nQuestion: " + question + "\n\nAnswer:"

    # Build context from retrieved chunks
    context_parts = []
    for i, result in enumerate(results, start=1):
        chunk = result.chunk
        context_parts.append(f"[Chunk {i}] {chunk.content}")

    context = "\n".join(context_parts)

    return PROMPT_TEMPLATE.format(question=question, context=context)


def make_prompt_from_results(question: str, results: list) -> str:
    """Convenience function to create a prompt from retrieval results.

    Args:
        question: The user's question.
        results: List of RetrievalResult objects.

    Returns:
        formatted prompt string.
    """
    return build_prompt(question, results, use_context=True)