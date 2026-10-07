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


# ---------------------------------------------------------------------------
# Level 2 — grounded prompt (spec US1, FR-003; contracts/grounded-answer-schema.md)
# ---------------------------------------------------------------------------

GROUNDED_INSTRUCTIONS = """INSTRUCTIONS:
1. Answer using only the EVIDENCE above. Do not introduce unsupported facts.
2. Do not invent citations. Cite only evidence listed above using its document_id and chunk_id.
3. If the evidence is insufficient to answer the question, set "abstained" to true and "sufficient_evidence" to false.
4. If the evidence contradicts itself, do NOT merge the statements: fill "conflicts" with a description and both source positions.
5. Respond with ONLY a JSON object matching this schema (no markdown, no commentary):
{
  "answer": "string",
  "citations": [{"document_id": "string", "chunk_id": "string"}],
  "abstained": false,
  "sufficient_evidence": true,
  "conflicts": [{"description": "string", "positions": [{"document_id": "string", "chunk_id": "string"}]}]
}"""

GROUNDED_ANSWER_SCHEMA_HINT = (
    '{"answer": "...", "citations": [{"document_id": "...", "chunk_id": "..."}],'
    ' "abstained": false, "sufficient_evidence": true, "conflicts": []}'
)


def build_grounded_prompt(question: str, evidence: list) -> str:
    """Build the evidence-aware prompt (QUESTION / EVIDENCE / INSTRUCTIONS).

    Args:
        question: the user question.
        evidence: list of Evidence objects for this question.

    Returns:
        A formatted prompt string whose sections are directly inspectable.
    """
    lines = [f"QUESTION: {question}", "", "EVIDENCE:"]
    if not evidence:
        lines.append("(no evidence retrieved)")
    else:
        for e in evidence:
            header = (
                f"{e.evidence_id} | {e.document_id} | {e.chunk_id} | score {e.retrieval_score:.2f}"
            )
            lines.append(header)
            lines.append(e.text)
            lines.append("")
    lines.append(GROUNDED_INSTRUCTIONS)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# US6 prompt-strategy variants (T036, FR-023; research R8). All four emit the
# same structured JSON schema (parsing is shared); they differ in how the
# evidence is presented and what the instructions emphasize:
#   A — simple RAG: raw passages, no ids, no citation/abstention emphasis
#   B — evidence-only: EVIDENCE blocks with ids, no citation/abstention rules
#   C — +citations: same evidence, explicit must-cite instruction
#   D — +citations + abstention + conflicts: the grounded prompt (US1)
# ---------------------------------------------------------------------------

COMMON_SCHEMA_HINT = (
    "\n\nRespond with ONLY a JSON object matching this schema "
    '(no markdown):\n{"answer": "string", "citations": '
    '[{"document_id": "string", "chunk_id": "string"}], "abstained": false, '
    '"sufficient_evidence": true, "conflicts": []}'
)

_STRATEGY_A_INSTRUCTIONS = (
    "Instructions: answer the user's question in a single concise sentence "
    "using the context below. Do not mention any citation ids."
) + COMMON_SCHEMA_HINT

_STRATEGY_B_INSTRUCTIONS = (
    "Instructions: answer the user's question using only the EVIDENCE "
    "blocks above. Do not invent facts outside the evidence."
) + COMMON_SCHEMA_HINT

_STRATEGY_C_INSTRUCTIONS = (
    "Instructions: answer using only the EVIDENCE blocks above. For each "
    "claim, add a citation using the exact document_id and chunk_id from "
    "its evidence block. Do not invent citations."
) + COMMON_SCHEMA_HINT


def _render_evidence(evidence: list, with_ids: bool) -> list[str]:
    """Render evidence blocks; headers include ids only when requested."""
    lines: list[str] = []
    for e in evidence:
        if with_ids:
            header = (
                f"{e.evidence_id} | {e.document_id} | {e.chunk_id} | score {e.retrieval_score:.2f}"
            )
            lines.append(header)
        lines.append(e.text)
        lines.append("")
    return lines


def build_strategy_a_prompt(question: str, evidence: list) -> str:
    """Strategy A (simple RAG): plain question + raw passages, no ids."""
    lines = [f"QUESTION: {question}", "", "CONTEXT:"]
    lines.extend(_render_evidence(evidence, with_ids=False))
    lines.append(_STRATEGY_A_INSTRUCTIONS)
    return "\n".join(lines)


def build_strategy_b_prompt(question: str, evidence: list) -> str:
    """Strategy B (evidence-only): EVIDENCE blocks with ids, no citation rules."""
    lines = [f"QUESTION: {question}", "", "EVIDENCE:"]
    lines.extend(_render_evidence(evidence, with_ids=True))
    lines.append(_STRATEGY_B_INSTRUCTIONS)
    return "\n".join(lines)


def build_strategy_c_prompt(question: str, evidence: list) -> str:
    """Strategy C (+citations): evidence with ids + explicit citation rule."""
    lines = [f"QUESTION: {question}", "", "EVIDENCE:"]
    lines.extend(_render_evidence(evidence, with_ids=True))
    lines.append(_STRATEGY_C_INSTRUCTIONS)
    return "\n".join(lines)


def build_strategy_prompt(strategy: str, question: str, evidence: list) -> str:
    """Dispatch to a prompt strategy by name (A-D or the grounded prompt)."""
    builders = {
        "A": build_strategy_a_prompt,
        "B": build_strategy_b_prompt,
        "C": build_strategy_c_prompt,
        "D": build_grounded_prompt,
    }
    return builders[strategy](question, evidence)
