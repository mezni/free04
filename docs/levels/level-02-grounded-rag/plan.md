# Telco Enterprise RAG

## Level 2 Plan — Grounded RAG

**Version:** 1.0
**Level:** 2
**Status:** Active

---

# 1. Objective

Upgrade Level 1 from:

```text
Question
    ↓
Retrieve
    ↓
Generate
    ↓
Answer
```

to:

```text
Question
    ↓
Retrieve
    ↓
Evidence
    ↓
Generate
    ↓
Structured Answer
    ↓
Validate
    ↓
Grounded Answer + Citations
```

The central objective is to determine whether the answer is actually supported by the retrieved knowledge.

---

# 2. Starting Point

Level 1 already provides:

```text
Real embeddings
ChromaDB
Structured chunks
Metadata
Configurable retrieval
Retrieval scores
Recall@K
Precision@K
MRR
Retrieval debugging
```

Level 2 builds on these components.

Do not replace them.

---

# 3. Target Project Structure

Add the following:

```text
src/telco_rag/
├── models/
│   ├── document.py
│   ├── chunk.py
│   ├── retrieval.py
│   ├── evidence.py
│   └── answer.py
│
├── generation/
│   ├── prompt.py
│   ├── llm.py
│   └── generator.py
│
├── grounding/
│   ├── __init__.py
│   ├── evidence_builder.py
│   ├── citation_validator.py
│   ├── grounding_checker.py
│   └── abstention.py
│
├── evaluation/
│   ├── dataset.py
│   ├── retrieval_metrics.py
│   ├── answer_metrics.py
│   └── groundedness.py
│
└── rag/
    └── pipeline.py
```

Tests:

```text
tests/
├── test_evidence.py
├── test_answer_schema.py
├── test_citations.py
├── test_abstention.py
├── test_grounding.py
├── test_answer_evaluation.py
└── test_rag_pipeline.py
```

Documentation:

```text
docs/levels/level-02-grounded-rag/
├── constitution.md
├── plan.md
├── experiments.md
└── lessons-learned.md
```

---

# 4. Step 1 — Create Evidence Model

Create:

```text
models/evidence.py
```

Represent retrieved evidence explicitly.

Conceptually:

```python
Evidence(
    evidence_id=...,
    document_id=...,
    chunk_id=...,
    title=...,
    source=...,
    text=...,
    retrieval_score=...,
)
```

The evidence model becomes the boundary between retrieval and generation.

---

# 5. Step 2 — Build Evidence Builder

Create:

```text
grounding/evidence_builder.py
```

Transform:

```text
RetrievalResult[]
```

into:

```text
Evidence[]
```

The evidence builder should:

* preserve IDs
* preserve metadata
* preserve retrieval scores
* assign stable evidence identifiers

Example:

```text
EVIDENCE-001
EVIDENCE-002
EVIDENCE-003
```

---

# 6. Step 3 — Design the Grounded Prompt

Update:

```text
generation/prompt.py
```

The prompt should clearly separate:

```text
QUESTION

EVIDENCE

INSTRUCTIONS
```

The model should be told:

```text
Answer using only the supplied evidence.

Do not invent facts.

Do not invent citations.

If the evidence is insufficient, abstain.

Cite supporting evidence.
```

Keep the prompt simple enough that you can inspect exactly what the model receives.

---

# 7. Step 4 — Introduce Structured Answer Output

Create:

```text
models/answer.py
```

Initially use a schema similar to:

```text
Answer
├── answer
├── citations[]
└── abstained
```

A citation should contain:

```text
document_id
chunk_id
```

Optionally:

```text
evidence_id
```

Do not add unnecessary fields until experiments justify them.

---

# 8. Step 5 — Make OpenRouter Return Structured Data

Use the OpenRouter/OpenAI-compatible client to request structured JSON output where supported.

The application should parse the result using Pydantic.

Pipeline:

```text
LLM
 ↓
JSON
 ↓
Pydantic
 ↓
Answer
```

Malformed responses should be detected rather than silently accepted.

---

# 9. Step 6 — Implement Citation Validation

Create:

```text
grounding/citation_validator.py
```

Given:

```text
retrieved evidence
+
generated citations
```

verify that every citation corresponds to actual evidence.

Test:

```text
Valid citation
Invalid document
Invalid chunk
Chunk not retrieved
Duplicate citation
Missing citation
```

---

# 10. Step 7 — Implement Abstention

Create:

```text
grounding/abstention.py
```

The system should support:

```text
answerable
```

and:

```text
not sufficiently supported
```

For example:

```text
Question:
What is the average 5G speed in Japan?

Corpus:
Only contains internal Telco troubleshooting documentation.

Result:
Abstain.
```

The model should not manufacture an answer from general knowledge.

---

# 11. Step 8 — Add Evidence Sufficiency

Create an initial evidence sufficiency mechanism.

Start simple.

Possible signals:

```text
retrieval result count
similarity threshold
retrieval scores
```

Then allow the LLM to explicitly indicate:

```text
sufficient_evidence
```

as part of the structured response.

Do not attempt sophisticated semantic entailment yet.

---

# 12. Step 9 — Build Citation-Aware CLI Output

Normal mode:

```text
Question:
Why is 5G packet loss occurring?

Answer:
5G packet loss can occur because of ...

Sources:
[5g_packet_loss:chunk-003]
```

Debug mode:

```text
Question:
...

Retrieved Evidence:
...

Generated Answer:
...

Citations:
...

Citation Validation:
PASS
```

This should make the entire grounded-generation pipeline observable.

---

# 13. Step 10 — Extend the Evaluation Dataset

Extend:

```text
data/evaluation/retrieval_questions.jsonl
```

or create:

```text
data/evaluation/grounded_answers.jsonl
```

Each example should contain:

```text
question
answerable
expected_answer
relevant_documents
relevant_chunks
```

Include:

### Answerable questions

Questions directly supported by the corpus.

### Unanswerable questions

Questions for which the corpus has insufficient information.

### Partial-evidence questions

Questions where only part of the requested answer is supported.

### Conflict questions

Questions where documents provide conflicting information.

---

# 14. Step 11 — Implement Answer Evaluation

Create:

```text
evaluation/answer_metrics.py
```

Initially evaluate:

```text
answer correctness
abstention correctness
citation validity
```

Keep metrics simple and transparent.

Do not hide evaluation behind an external framework.

---

# 15. Step 12 — Implement Groundedness Evaluation

Create:

```text
evaluation/groundedness.py
```

For each generated answer:

```text
Answer
 ↓
Claims
 ↓
Supporting Evidence
```

Determine whether the important claims are supported.

Initially this can use a structured LLM judge.

For example:

```text
Claim:
Packet loss can be caused by radio interference.

Evidence:
"Radio interference can cause packet loss..."

Result:
SUPPORTED
```

The evaluator must distinguish:

```text
SUPPORTED
UNSUPPORTED
PARTIALLY_SUPPORTED
```

---

# 16. Step 13 — Test Citation Hallucination

Create tests where the model attempts to produce:

```text
[document-that-does-not-exist:chunk-99]
```

The validator must detect it.

Also test:

```text
valid document
invalid chunk
```

and:

```text
valid chunk
but not retrieved for this question
```

All must be rejected.

---

# 17. Step 14 — Test Hallucination Scenarios

Create explicit experiments.

### Scenario A

Correct evidence → correct answer.

### Scenario B

Correct evidence → unsupported additional claim.

### Scenario C

Insufficient evidence → model should abstain.

### Scenario D

No evidence → model should abstain.

### Scenario E

Conflicting evidence → model should report uncertainty/conflict.

### Scenario F

Valid answer → missing citation.

The objective is to observe how the model behaves.

---

# 18. Step 15 — Compare Prompt Strategies

Create experiments such as:

```text
Experiment A
Simple RAG prompt

Experiment B
Evidence-only prompt

Experiment C
Evidence-only + citation requirement

Experiment D
Evidence-only + citation + abstention
```

Measure:

```text
answer correctness
groundedness
citation validity
citation completeness
abstention accuracy
```

Document which prompt strategy performs best.

---

# 19. Step 16 — Separate Retrieval and Generation Failures

This is an important Level 2 exercise.

For every failure ask:

```text
Was the correct evidence retrieved?
```

If NO:

```text
Retrieval problem
```

If YES:

```text
Generation/grounding problem
```

This distinction prepares the project for Level 3.

---

# 20. Step 17 — Add Regression Tests

Every discovered failure should become a regression test.

For example:

```text
test_answer_does_not_use_external_knowledge
test_unknown_question_abstains
test_invalid_citation_rejected
test_unretrieved_citation_rejected
test_supported_answer_has_citation
test_conflicting_evidence_is_reported
```

The test suite becomes a growing knowledge base of failure modes.

---

# 21. Step 18 — Preserve Level 1 Metrics

Do not remove:

```text
Recall@K
Precision@K
MRR
```

Level 2 evaluation should now look like:

```text
                   RAG Evaluation
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
        Retrieval                Generation
             │                       │
      Recall@K                  Correctness
      Precision@K               Groundedness
      MRR                       Citation validity
                                Citation completeness
                                Abstention
```

This separation is fundamental.

---

# 22. Step 19 — Document Experiments

Create:

```text
docs/levels/level-02-grounded-rag/experiments.md
```

Document:

* prompt experiments
* citation experiments
* abstention experiments
* grounding experiments
* hallucination tests
* conflicting evidence tests
* evaluation results

---

# 23. Step 20 — Document Lessons Learned

Create:

```text
docs/levels/level-02-grounded-rag/lessons-learned.md
```

Answer:

```text
What causes unsupported answers?

Does a high retrieval score guarantee grounding?

How often does the LLM invent citations?

How effective is prompt-only grounding?

When does the system abstain incorrectly?

How often are citations incomplete?

What retrieval failures are actually generation failures?
```

---

# 24. Definition of Done

Level 2 is complete when:

```text
[✓] Evidence model
[✓] Evidence builder
[✓] Grounded prompt
[✓] Structured answer
[✓] Citation model
[✓] Citation validator
[✓] Abstention
[✓] Evidence sufficiency
[✓] Grounded CLI
[✓] Answer evaluation dataset
[✓] Answer correctness evaluation
[✓] Groundedness evaluation
[✓] Citation validation tests
[✓] Hallucination tests
[✓] Conflict tests
[✓] Regression tests
[✓] Level 1 retrieval metrics preserved
[✓] Experiments documented
[✓] Lessons learned documented
```

---

# 25. Level 2 Completion Test

Run a final set of questions:

```text
1. Known Telco question
2. Unknown question
3. Partially supported question
4. Question with conflicting evidence
5. Question where retrieval succeeds but generation can hallucinate
```

For each query inspect:

```text
retrieved evidence
        ↓
generated answer
        ↓
citations
        ↓
citation validation
        ↓
groundedness evaluation
        ↓
final response
```

---

# 26. Transition to Level 3

At the end of Level 2, the system should reliably answer:

> **Is this answer supported by the evidence we retrieved?**

The next problem becomes:

> **What happens when the system cannot retrieve the right evidence in the first place?**

That motivates Level 3:

```text
BM25
+
Vector Search
+
Hybrid Retrieval
+
Metadata Filtering
+
Reranking
+
Query Rewriting
```

The progression becomes:

```text
Level 0
Can we build RAG?
       ↓
Level 1
Can we retrieve relevant knowledge?
       ↓
Level 2
Can we generate a grounded answer?
       ↓
Level 3
Can we retrieve the right knowledge reliably
even for difficult queries?
```

---

# 27. Guiding Principle

> **A retrieved document is evidence; an LLM statement is a claim. Level 2 exists to connect those two and verify the connection.**
