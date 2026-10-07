# Telco Enterprise RAG

## Level 2 Constitution — Grounded RAG

**Version:** 1.0
**Level:** 2
**Status:** Active
**Previous Level:** Level 1 — RAG Foundations
**Next Level:** Level 3 — Advanced Retrieval

---

# 1. Purpose

Level 2 transforms the Level 1 retrieval system into a **grounded RAG system**.

Level 1 established:

```text
Question
    ↓
Real Embedding
    ↓
ChromaDB
    ↓
Retrieved Chunks
```

Level 2 addresses the next fundamental problem:

> **How do we ensure that the generated answer is supported by the retrieved evidence?**

The system must distinguish between:

```text
retrieved knowledge
```

and:

```text
generated claims
```

An answer is not considered trustworthy merely because the correct document was retrieved.

---

# 2. Core Principle

> **The LLM must answer from evidence, not merely from retrieved context.**

The system shall make the evidence used for an answer explicit.

The final response should be traceable to:

```text
Answer
   ↓
Claims
   ↓
Evidence
   ↓
Source Document
   ↓
Source Chunk
```

---

# 3. Technology Constitution

Level 2 shall continue using the Level 1 stack.

## Application

```text
Python 3.12+
uv
Pydantic v2
PyYAML
Typer
```

## Retrieval

```text
sentence-transformers
BAAI/bge-small-en-v1.5
ChromaDB
```

## Generation

```text
OpenRouter
OpenAI Python SDK
```

## Testing

```text
pytest
pytest-cov
Ruff
mypy
```

## Evaluation

Level 2 shall initially use:

```text
Python
Pydantic
pytest
```

for evaluation rather than introducing a specialized RAG evaluation framework.

This keeps the evaluation logic understandable.

---

# 4. What Is New in Level 2

Level 2 introduces:

```text
Evidence-aware prompts
        ↓
Source attribution
        ↓
Citations
        ↓
Abstention
        ↓
Citation validation
        ↓
Groundedness evaluation
        ↓
Answer evaluation
```

---

# 5. Target Architecture

The Level 2 architecture becomes:

```text
                         INGESTION
                            │
                            ↓
                       Documents
                            ↓
                         Chunks
                            ↓
                       Embeddings
                            ↓
                         ChromaDB
                            │
                            │
                            ↓
                         RETRIEVAL
                            │
User Question ───────→ Retriever
                            │
                            ↓
                    RetrievalResult[]
                            │
                            ↓
                     Evidence Builder
                            │
                            ↓
                    Grounded Prompt
                            │
                            ↓
                         OpenRouter
                            │
                            ↓
                    Structured Answer
                            │
                ┌───────────┴───────────┐
                ↓                       ↓
             Citations              Claims
                │                       │
                └───────────┬───────────┘
                            ↓
                    Citation Validator
                            │
                            ↓
                     Final Response
```

---

# 6. Evidence Is a First-Class Object

Retrieved text shall not simply be concatenated into a prompt.

Level 2 shall introduce an explicit evidence representation.

Conceptually:

```text
Evidence
├── evidence_id
├── document_id
├── chunk_id
├── title
├── source
├── text
└── retrieval_score
```

Example:

```text
EVIDENCE-001
Document: 5G Packet Loss
Chunk: 5g-packet-loss-003
Score: 0.87

Text:
Packet loss may occur when...
```

---

# 7. Citation Constitution

Every factual answer generated from retrieved knowledge should identify its supporting source.

A citation should identify at least:

```text
document_id
chunk_id
```

The citation format may initially be simple:

```text
[5g_packet_loss:chunk-003]
```

The exact presentation can evolve later.

The important requirement is that citations correspond to real retrieved evidence.

---

# 8. Citation Validation

The application shall validate citations before returning the answer.

For example:

```text
Answer cites:
[5g_packet_loss:chunk-003]
```

The validator must verify that:

```text
5g_packet_loss:chunk-003
```

was actually present in the retrieval results.

The system must reject or flag citations that refer to:

* nonexistent documents
* nonexistent chunks
* chunks not retrieved for the current question

The LLM must not be allowed to invent source identifiers.

---

# 9. Grounded Answer Constitution

The generation prompt shall explicitly instruct the LLM:

```text
Use only the supplied evidence.

Do not introduce unsupported facts.

If the evidence does not answer the question,
say that the available information is insufficient.

Cite the evidence supporting factual claims.
```

This instruction is necessary but not sufficient.

Level 2 must therefore combine:

```text
prompt constraints
+
structured output
+
citation validation
+
evaluation
```

---

# 10. Structured Generation

The generated response shall use a structured schema.

Conceptually:

```text
Answer
├── answer
├── citations[]
└── confidence / groundedness indicator
```

For example:

```json
{
  "answer": "Packet loss can occur because of radio interference or network congestion.",
  "citations": [
    {
      "document_id": "5g_packet_loss",
      "chunk_id": "5g_packet_loss-003"
    }
  ]
}
```

The schema may evolve as experiments reveal better requirements.

---

# 11. Abstention Constitution

The system must be able to say:

> The available documents do not contain enough information to answer this question.

Abstention is a valid result.

The system must not attempt to answer every question.

Especially for questions outside the knowledge base:

```text
Unknown Question
       ↓
No sufficient evidence
       ↓
Abstain
```

---

# 12. Evidence Sufficiency

Level 2 shall distinguish between:

```text
retrieval succeeded
```

and:

```text
retrieved evidence is sufficient to answer
```

High retrieval similarity does not automatically prove answerability.

The application should therefore introduce an evidence-sufficiency decision.

Initially this can be based on:

* retrieval threshold
* number of useful evidence chunks
* LLM structured assessment
* explicit prompt rules

A sophisticated semantic entailment model is not required yet.

---

# 13. Groundedness

Level 2 shall evaluate whether generated claims are supported by the retrieved evidence.

Conceptually:

```text
Question
   ↓
Evidence
   ↓
Answer
   ↓
Claims
   ↓
Evidence Support
```

A claim is grounded when the evidence supports it.

---

# 14. Evaluation Constitution

Level 2 shall introduce answer-level evaluation.

At minimum evaluate:

```text
Answer correctness
Answer groundedness
Citation correctness
Citation completeness
Abstention behavior
```

Retrieval metrics from Level 1 remain important:

```text
Recall@K
Precision@K
MRR
```

Level 2 must not replace retrieval evaluation with answer evaluation.

Both layers must be evaluated separately.

---

# 15. Evaluation Dataset

Extend the Level 1 evaluation dataset.

Each test case should eventually contain:

```text
question
expected_answer
relevant_documents
relevant_chunks
answerable
```

Example:

```json
{
  "question": "What can cause packet loss on a 5G network?",
  "answerable": true,
  "relevant_documents": [
    "5g_packet_loss"
  ],
  "expected_answer": "...",
  "relevant_chunks": [
    "5g_packet_loss-003"
  ]
}
```

Unknown questions should also be included.

---

# 16. Citation Completeness

Level 2 shall distinguish:

### Citation correctness

Does the citation actually support the claim?

### Citation validity

Does the cited chunk actually exist and belong to the retrieval result?

### Citation completeness

Are important factual claims supported by citations?

These are separate concepts and should not be collapsed into one metric.

---

# 17. Hallucination Constitution

Level 2 shall explicitly test for unsupported generation.

Test scenarios shall include:

```text
Correct evidence
Incorrect evidence
Incomplete evidence
Conflicting evidence
No evidence
Unknown question
```

The objective is not to eliminate hallucination completely.

The objective is to **measure and reduce unsupported generation**.

---

# 18. Conflict Handling

If retrieved documents contain conflicting information, the system shall not silently merge the statements into one fact.

The answer should acknowledge uncertainty or conflict.

For example:

```text
The available documents provide conflicting information.
Document A states X, while Document B states Y.
```

Advanced source authority and document governance are deferred to later levels.

---

# 19. Separation of Responsibilities

The architecture shall maintain:

```text
Retriever
    ↓
Evidence
    ↓
Generator
    ↓
Answer
    ↓
Validator
```

The generator must not directly access the vector database.

The validator must not perform retrieval.

Each component should have one clear responsibility.

---

# 20. Explicitly Out of Scope

Level 2 shall not introduce:

```text
BM25
Hybrid search
Reranking
Query rewriting
Query decomposition
Document lifecycle
Document approval
RBAC
ABAC
Multi-tenancy
Advanced security
Agents
Memory
Tool calling
Production observability
Distributed tracing
CI/CD
Kubernetes
Multi-region deployment
FinOps
```

These remain later maturity capabilities.

---

# 21. Framework Constitution

Do not introduce:

```text
LangChain
LlamaIndex
LangGraph
RAG evaluation frameworks
agent frameworks
```

unless an experiment demonstrates a specific need.

The goal remains to understand the underlying mechanism.

---

# 22. Definition of Done

Level 2 is complete when:

* answers are generated from explicit evidence
* evidence is represented as structured objects
* generated answers contain citations
* citations reference actual retrieved chunks
* invalid citations are detected
* the LLM can abstain
* unknown questions are tested
* structured answer output is validated
* groundedness is evaluated
* citation correctness is evaluated
* citation completeness is evaluated
* answer correctness is evaluated
* retrieval metrics remain available
* hallucination/unsupported-answer tests exist
* conflicting evidence is handled explicitly
* all behavior is covered by tests

---

# 23. Exit Criteria

Before moving to Level 3, the developer must be able to explain:

1. Why retrieval correctness does not guarantee answer correctness.
2. What grounding means.
3. What evidence means in a RAG system.
4. Why citations must be validated.
5. Why the LLM cannot be trusted to invent citation identifiers.
6. What abstention means.
7. The difference between citation validity and citation correctness.
8. The difference between citation correctness and citation completeness.
9. How to identify unsupported claims.
10. Why retrieval evaluation and answer evaluation are separate.
11. How conflicting evidence should be handled.
12. Why prompt instructions alone are insufficient for reliable grounding.

---

# 24. Level 2 Guiding Principle

> **Retrieve evidence, generate from evidence, cite the evidence, and verify the citations.**
