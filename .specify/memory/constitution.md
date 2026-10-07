<!--
Sync Impact Report
==================
Template source: constitution-template (resolved via resolve-template.sh)
Version change: 1.1.0 -> 1.2.0
Bump type: MINOR (new Level 2 principles and sections added; existing
           principles expanded; no principle removed or redefined)

Modified principles:
  - "V. Explicit RAG Pipeline" -> expanded: Level 2 pipeline adds Evidence
    Builder, Grounded Prompt, Structured Answer, and Citation Validator
  - "VII. No Knowledge Outside the Corpus" -> expanded: abstention,
    citations, and citation validation required; prompt instruction alone
    is insufficient (Level 2 source Sections 9, 11)
  - "XI. Tests From the Beginning" -> expanded: Level 2 test coverage
    (evidence, answer schema, citations, abstention, grounding, answer
    evaluation, pipeline, regression)
  - "XII. CLI First" -> expanded: grounded output with sources; debug mode
    exposes evidence, citations, and citation-validation result
  - All other principles (I-IV, VI, VIII-X, XIII-XVI) -> unchanged

Added principles:
  - "XVII. Evidence Is a First-Class Object (NON-NEGOTIABLE)"
  - "XVIII. Validated Citations Only (NON-NEGOTIABLE)"
  - "XIX. Abstention Is a Valid Result (NON-NEGOTIABLE)"
  - "XX. Prompt Constraints Alone Are Insufficient (NON-NEGOTIABLE)"
  - "XXI. Separation of Retrieval, Generation, and Validation"
  - "XXII. Two-Layer Evaluation (NON-NEGOTIABLE)"
  - "XXIII. Surface Conflicts, Never Merge Them"

Added sections:
  - Purpose and Scope rewritten for Level 2 (source Sections 1, 5, 20);
    Level 1 scope preserved as subsection "Level 1 Baseline (Established)"
  - Level 2 Technology Constitution (source Section 3)
  - Level 2 Evidence Constitution (source Section 6)
  - Level 2 Citation Constitution (source Sections 7, 8, 16)
  - Level 2 Grounded Answer Constitution (source Sections 9, 10)
  - Level 2 Abstention and Evidence Sufficiency (source Sections 11, 12)
  - Level 2 Groundedness and Conflict Handling (source Sections 13, 18)
  - Level 2 Evaluation Constitution (source Sections 14, 15, 17)
  - Level 2 Separation of Responsibilities (source Section 19)
  - Level 2 Out of Scope (source Section 20)
  - Level 2 Quality Gates: Definition of Done (source Section 22),
    Exit Criteria (source Section 23)
  - Level 2 Guiding Principle (source Section 24)
  - Level 2 Backward Compatibility (builds on Level 1, does not replace it)

Removed sections:
  - none. Level 1 content preserved as the established baseline.

Placeholders left undefined: none.
Follow-up TODOs: none.

Date notes:
  - RATIFICATION_DATE kept at 2026-10-06 (original constitution adoption).
  - LAST_AMENDED_DATE set to 2026-10-07 (Level 2 content incorporated).
  - Governance "Runtime guidance" repointed from
    docs/levels/level-01-rag-foundations/plan.md to
    docs/levels/level-02-grounded-rag/plan.md.
-->

# Telco Enterprise RAG Constitution

**Level:** 2 — Grounded RAG | **Status:** Active
**Previous Level:** Level 1 — RAG Foundations (established) | **Next Level:** Level 3 — Advanced Retrieval

## Core Principles

### I. Learn From the Level (NON-NEGOTIABLE)

The active level's implementation MUST remain simple enough that the
developer can understand every component. No abstraction MAY be introduced
merely because it is common in enterprise RAG systems. Every component MUST
answer the question "What active-level problem does this component solve?";
any component that cannot answer it MUST be deferred to a later level.

Rationale: each level is a learning milestone; opaque abstractions defeat
its purpose.

### II. Simple Before Sophisticated (NON-NEGOTIABLE)

The active level MUST prefer a simple implementation over framework
complexity. The implementation MUST NOT introduce agent frameworks,
orchestration frameworks, microservices, distributed systems, message
queues, Kubernetes, or complex databases unless no level requirement can be
met without them.

Rationale: RAG fundamentals must be understood before enterprise
infrastructure is introduced.

### III. Telco Domain From Day One

The knowledge base MUST contain Telco-oriented documents covering at least:
5G troubleshooting, LTE troubleshooting, network incidents, NOC procedures,
SIM activation, broadband troubleshooting, enterprise SLA, and network
operations. The domain must be realistic enough to expose RAG-specific
problems even though the implementation is naive.

All documents MUST be synthetic. No real customer data or confidential
telecom information MAY be ingested, at any level.

### IV. Reproducibility

A developer MUST be able to clone the repository and reproduce the system
using documented steps alone. The project MUST define: Python version,
dependency management (uv), environment configuration, required environment
variables, installation instructions, execution instructions, and test
instructions.

Dependencies MUST be pinned/locked through uv (`uv.lock`). Given the same
input documents and configuration, retrieval behavior MUST be reproducible
within reasonable embedding/model variability.

### V. Explicit RAG Pipeline

The implementation MUST make every RAG stage visible as a distinct,
identifiable responsibility:

```text
Document Loader
      ↓
Chunker
      ↓
Embedder
      ↓
Vector Store
      ↓
Retriever
      ↓
Prompt Builder
      ↓
LLM
      ↓
Answer
```

Evaluation is a separate path:

```text
Evaluation Dataset → Query → Retriever → Retrieved Documents
                   → Expected Documents → Retrieval Metrics
```

Stage responsibilities MUST NOT be hidden inside one opaque function.

At Level 2 the pipeline extends with explicit grounding stages:

```text
Retriever → Evidence Builder → Grounded Prompt → LLM
          → Structured Answer → Citation Validator → Final Response
```

Rationale: the pipeline is educational as well as architectural; learners
MUST be able to point at each stage in the code.

### VI. Retrieval Before Generation

The LLM MUST NOT be treated as the knowledge source. For every question the
application MUST, in order:

1. receive the question,
2. retrieve relevant context from the vector store,
3. construct a prompt containing the retrieved context,
4. ask the LLM to answer using that context.

Any code path that sends a user question directly to the LLM without
retrieval violates this principle.

### VII. No Knowledge Outside the Corpus

The prompt MUST instruct the model to answer using only the supplied
retrieved context. When the retrieved context does not contain enough
information, the system MUST produce an explicit inability-to-answer response
rather than invent unsupported facts, for example:

```text
I don't have enough information in the knowledge base
to answer this question.
```

At Level 2 this principle becomes enforceable, not merely aspirational. The
system MUST combine prompt constraints with structured answer output,
citations, citation validation, and abstention. A prompt instruction alone
MUST NOT be treated as sufficient grounding (see Principle XX).

Rationale: this baseline grounding behavior is what later levels refine into
citations, abstention, and evaluation.

### VIII. Make Retrieval Inspectable

Every query MUST expose, at minimum:

```text
Question
Retrieved chunks
Similarity scores
Final answer
```

The system MUST provide a way to inspect retrieval independently from answer
generation (e.g., a `--debug-retrieval` CLI flag). The project MUST NOT
require the user to inspect the final LLM answer to understand retrieval
behavior.

Rationale: each level exists to teach the fundamental RAG debugging
question — did the system retrieve the right information before asking
whether the LLM generated the right answer? An opaque answer is a failed
debug session.

### IX. Minimal Metadata

Every document and chunk MUST carry metadata identifying its origin. At
minimum:

```text
document_id
title
source
chunk_id
chunk_index
```

Metadata MUST survive the complete ingestion → retrieval pipeline. The
design MUST leave room for future enterprise metadata (tenant_id, owner,
department, classification, version, status, effective_from,
effective_until, access_policy) even though those fields are not
implemented as access-control mechanisms yet.

Rationale: metadata architecture becomes increasingly important at later
enterprise levels; designing for it now prevents costly rework.

### X. Configuration Over Hardcoding

Model names, API endpoints, embedding configuration, retrieval parameters,
and other environment-specific settings MUST be centralized in configuration
and MUST NOT be scattered through the source code.

At minimum, the following MUST be configurable:

```text
embedding model
chunk_size
chunk_overlap
top_k
similarity_threshold
vector database path
LLM configuration
```

Secrets MUST NEVER be committed to Git. The `.env` file MUST be excluded
from source control, and a `.env.example` template listing all required
variables (without values) MUST be provided.

### XI. Tests From the Beginning

Code MUST be testable from the first commit. Tests MUST cover, at minimum:

- document models
- chunk models
- chunking
- embeddings
- vector-store operations
- retrieval
- metadata preservation
- retrieval thresholds
- retrieval evaluation
- RAG integration

At Level 2 the suite MUST additionally cover, at minimum:

- evidence model and evidence builder
- answer schema and structured-output parsing
- citation validation (valid, invalid, and unretrieved citations)
- abstention on unknown questions
- groundedness evaluation
- answer evaluation metrics
- grounded RAG pipeline integration

Tests MUST distinguish deterministic application logic from external LLM
behavior; assertions against live LLM output MUST be isolated from
deterministic unit tests.

Level 0 and Level 1 regression tests MUST continue to pass unless a
deliberate behavioral change is documented.

### XII. CLI First

The system MUST expose a simple command-line interface, for example:

```bash
python -m telco_rag.cli "Why is my 5G connection experiencing packet loss?"
```

The CLI MUST support retrieval diagnostics:

```bash
python -m telco_rag.cli "question" --debug-retrieval
```

At Level 2 the CLI MUST display the sources supporting an answer, for
example:

```text
Sources:
[5g_packet_loss:chunk-003]
```

and a debug mode MUST expose the full grounding path: retrieved evidence,
generated answer, citations, and the citation-validation result (PASS/FAIL).

The CLI MUST make experimentation fast. A web UI MUST NOT be built at this
level.

### XIII. No Premature Enterprise Architecture

The active level MUST NOT claim or simulate production readiness. The
architecture documentation MUST explicitly list known limitations, including
at minimum:

```text
No authentication
No RBAC
No document lifecycle
No tenant isolation
No production monitoring
No HA
No CI/CD
No enterprise evaluation framework
```

Rationale: these limitations are deliberate starting points for later levels,
not defects to be papered over with stub enterprise features.

### XIV. Every Level Must Expose the Next Problem

The project is a maturity progression. Completing a level MUST leave its
known problems documented — at minimum: poor chunking, irrelevant retrieval,
lack of metadata, weak source traceability, inability to measure retrieval
quality, inability to manage document versions, and inability to enforce
access control.

Each level MUST end by identifying the problems it cannot solve; those
problems become the justification for the subsequent level.

### XV. Real Before Sophisticated (NON-NEGOTIABLE)

The active level MUST replace simulated infrastructure with real
infrastructure before adding sophistication. At Level 1 this means: real
embeddings (sentence-transformers), a real vector database (ChromaDB), and
structured Pydantic models — not additional abstractions on top of fake
components.

At Level 2 this means: real citation validation against real retrieval
results, and real structured output from the LLM — not simulated grounding
signals.

Rationale: replacing simulation with reality is the core upgrade of each
early level; sophistication built on simulation teaches nothing about real
retrieval behavior.

### XVI. Metrics Written, Not Hidden (NON-NEGOTIABLE)

Retrieval metrics (Recall@K, Precision@K, MRR) MUST be implemented directly
in Python rather than delegated to an evaluation framework. The developer
MUST be able to explain the formula behind each metric.

At Level 2 this extends to answer-level metrics (answer correctness,
groundedness, citation validity, citation completeness, abstention
behavior): they MUST be implemented in Python with transparent logic, not
hidden behind a RAG evaluation framework.

Rationale: the purpose of evaluation is to understand what the metrics
measure, not to run a black-box benchmark.

### XVII. Evidence Is a First-Class Object (NON-NEGOTIABLE)

Retrieved text MUST NOT be concatenated into a prompt as anonymous strings.
Retrieval results MUST be transformed into explicit evidence objects before
generation. At minimum an evidence object carries:

```text
evidence_id
document_id
chunk_id
title
source
text
retrieval_score
```

Evidence identifiers MUST be stable and MUST preserve the identity of the
originating document and chunk.

Rationale: evidence is the boundary between retrieval and generation; only
what is represented as evidence can later be cited, validated, or evaluated.

### XVIII. Validated Citations Only (NON-NEGOTIABLE)

Every factual answer generated from retrieved knowledge MUST cite its
supporting evidence. The application MUST validate every generated citation
against the actual retrieval result before returning the answer. A citation
MUST identify at least `document_id` and `chunk_id`.

Citations that refer to nonexistent documents, nonexistent chunks, or chunks
not retrieved for the current question MUST be rejected or flagged. The LLM
MUST NOT be allowed to invent source identifiers.

Rationale: the model has no privileged knowledge of the corpus; an
unvalidated citation is a hallucination with a confident label.

### XIX. Abstention Is a Valid Result (NON-NEGOTIABLE)

The system MUST be able to answer:

> The available documents do not contain enough information to answer this
> question.

The system MUST NOT attempt to answer every question. When retrieved evidence
is insufficient for the question, the correct output is abstention — not an
answer assembled from the model's general knowledge.

Rationale: a system that always answers cannot be trusted on the questions
where it is wrong.

### XX. Prompt Constraints Alone Are Insufficient (NON-NEGOTIABLE)

Grounding MUST be enforced by the combination of:

```text
prompt constraints
+
structured output
+
citation validation
+
evaluation
```

Prompt instructions alone MUST NOT be treated as a grounding mechanism. Any
claim that the system is grounded MUST be backed by validation logic and
evaluation results, not by prompt wording.

Rationale: instruction-following is probabilistic; only deterministic
validation and measurement make grounding claims testable.

### XXI. Separation of Retrieval, Generation, and Validation

The architecture MUST maintain distinct responsibilities:

```text
Retriever → Evidence → Generator → Answer → Validator
```

The generator MUST NOT access the vector database directly. The validator
MUST NOT perform retrieval. Each component MUST have one clear
responsibility.

Rationale: separation is what makes it possible to attribute a failure to
retrieval or to generation instead of guessing.

### XXII. Two-Layer Evaluation (NON-NEGOTIABLE)

Retrieval evaluation and answer evaluation are separate layers and MUST be
reported separately. Level 1 retrieval metrics (Recall@K, Precision@K, MRR)
MUST be preserved. Level 2 answer metrics (correctness, groundedness,
citation validity, citation completeness, abstention) MUST NOT replace them.

Retrieval correctness MUST NOT be used as evidence of answer correctness.

Rationale: a correct answer can follow from wrong retrieval and an incorrect
answer can follow from correct retrieval; collapsing the layers hides both
failure modes.

### XXIII. Surface Conflicts, Never Merge Them

When retrieved documents contain conflicting information, the system MUST
NOT silently merge the statements into a single fact. The answer MUST
acknowledge the uncertainty or conflict and identify the differing sources.

```text
The available documents provide conflicting information.
Document A states X, while Document B states Y.
```

Rationale: silent merging fabricates a consensus that the corpus does not
contain.

## Purpose and Scope

This constitution defines the engineering principles and boundaries for
Level 2 of the Telco Enterprise RAG project. The objective of Level 2 is:

> Retrieve evidence, generate from evidence, cite the evidence, and verify
> the citations.

Level 2 transforms the Level 1 retrieval system into a grounded RAG system.
Level 1 established a real, measurable retrieval pipeline:

```text
Question → Real Embedding → ChromaDB → Retrieved Chunks
```

Level 2 addresses the next fundamental problem:

> How do we ensure that the generated answer is supported by the retrieved
> evidence?

The system MUST distinguish retrieved knowledge from generated claims. An
answer is not trustworthy merely because the correct document was retrieved.

The Level 2 architecture is:

```text
                         INGESTION
                            │
                            ↓
                       Documents → Chunks → Embeddings → ChromaDB
                            │
                            ↓
                         RETRIEVAL
                            │
User Question ───────→ Retriever → RetrievalResult[]
                            │
                            ↓
                     Evidence Builder → Grounded Prompt → OpenRouter
                            │
                            ↓
                    Structured Answer
                            │
                ┌───────────┴───────────┐
                ↓                       ↓
             Citations              Claims
                └───────────┬───────────┘
                            ↓
                    Citation Validator → Final Response
```

Level 2 is a grounding and evaluation learning level. It is **not a
production-ready enterprise system**.

### Included

Level 2 includes only the capabilities required to demonstrate grounded
answer generation:

- evidence represented as explicit structured objects
- evidence builder transforming retrieval results into evidence
- evidence-aware (grounded) prompts with clearly separated QUESTION,
  EVIDENCE, and INSTRUCTIONS sections
- structured answer output (answer, citations, abstention indicator)
- structured JSON generation through OpenRouter, parsed with Pydantic
- citation model (document_id, chunk_id, optionally evidence_id)
- citation validation against actual retrieval results
- abstention when evidence is insufficient
- evidence-sufficiency signals (retrieval count, threshold, scores, LLM
  structured assessment)
- citation-aware CLI output with debug mode
- extended evaluation dataset (answerable, unanswerable, partial-evidence,
  and conflict questions)
- answer correctness, groundedness, citation validity, citation
  completeness, and abstention evaluation
- hallucination and conflicting-evidence tests
- regression tests for every discovered failure
- preservation of Level 1 retrieval metrics (Recall@K, Precision@K, MRR)

### Explicitly Excluded

The following capabilities belong to later maturity levels. Their exclusion
is intentional:

- BM25, hybrid search, reranking, query rewriting, query decomposition
- document lifecycle, document approval, document governance
- RBAC, ABAC, multi-tenancy, advanced security
- agents, memory, tool calling
- production observability, distributed tracing, CI/CD, Kubernetes,
  multi-region deployment, FinOps
- LangChain, LlamaIndex, LangGraph, RAG evaluation frameworks, agent
  frameworks

### Level 1 Baseline (Established)

Level 1 established the real-infrastructure retrieval layer that Level 2
builds upon and MUST NOT replace:

```text
Level 1: Question → Real embedding → Real vector retrieval → Generate
Level 2: Question → Retrieve → Evidence → Generate → Structured Answer
         → Validate → Grounded Answer + Citations
```

Level 1 included: Python with Pydantic v2 models, uv dependency management,
local synthetic Telco documents, configurable chunking with metadata
preservation, real embeddings (sentence-transformers,
BAAI/bge-small-en-v1.5), persistent ChromaDB storage, similarity search with
metadata, configurable top-K and similarity threshold, retrieval
diagnostics, retrieval evaluation (Recall@K, Precision@K, MRR), prompt
construction, LLM answer generation (OpenRouter), Typer CLI, externalized
configuration (YAML + Pydantic Settings), tests, and project documentation.

Level 1 exclusions (BM25/hybrid/reranking, knowledge lifecycle, security,
platform, operations, frameworks) remain in force; see "Level 1 Out of
Scope" below.

## Level 2 Technology Constitution

Level 2 SHALL continue using the Level 1 stack. No new framework SHALL be
introduced to implement grounding.

### Application

Python 3.12+, uv, Pydantic v2, PyYAML, Typer — unchanged from Level 1.

### Retrieval

sentence-transformers, BAAI/bge-small-en-v1.5, ChromaDB — unchanged from
Level 1.

### Generation

OpenRouter with the OpenAI-compatible Python SDK as client. Structured JSON
output SHALL be requested where supported and parsed with Pydantic.
Malformed responses SHALL be detected, not silently accepted.

### Testing

pytest, pytest-cov, Ruff, mypy — unchanged from Level 1.

### Evaluation

Level 2 SHALL use Python, Pydantic, and pytest for evaluation rather than
introducing a specialized RAG evaluation framework. Evaluation logic MUST
remain readable and explainable (see Principle XVI).

## Level 2 Evidence Constitution

Evidence SHALL be a first-class object, not concatenated anonymous text
(Principle XVII). Conceptually:

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

An evidence builder SHALL transform `RetrievalResult[]` into `Evidence[]`,
preserving IDs, metadata, and retrieval scores, and assigning stable
evidence identifiers (`EVIDENCE-001`, `EVIDENCE-002`, ...). The evidence
model is the boundary between retrieval and generation.

## Level 2 Citation Constitution

### Citation Requirements

Every factual answer generated from retrieved knowledge SHALL identify its
supporting source. A citation SHALL identify at least `document_id` and
`chunk_id`. The format MAY initially be simple:

```text
[5g_packet_loss:chunk-003]
```

The presentation MAY evolve; the requirement that citations correspond to
real retrieved evidence MUST NOT.

### Citation Validation

The application SHALL validate citations before returning the answer. The
validator SHALL verify that every cited `document_id:chunk_id` was actually
present in the current retrieval result. The system SHALL reject or flag
citations referring to:

- nonexistent documents
- nonexistent chunks
- chunks not retrieved for the current question

The LLM MUST NOT be allowed to invent source identifiers (Principle XVIII).

### Three Distinct Concepts

Level 2 SHALL keep these separate and MUST NOT collapse them into one
metric:

- **Citation validity** — does the cited chunk exist and belong to the
  retrieval result?
- **Citation correctness** — does the citation actually support the claim?
- **Citation completeness** — are important factual claims supported by
  citations?

## Level 2 Grounded Answer Constitution

### Grounded Prompt

The generation prompt SHALL explicitly instruct the LLM:

```text
Use only the supplied evidence.

Do not introduce unsupported facts.

If the evidence does not answer the question,
say that the available information is insufficient.

Cite the evidence supporting factual claims.
```

This instruction is necessary but not sufficient (Principle XX). The prompt
SHALL clearly separate QUESTION, EVIDENCE, and INSTRUCTIONS so that exactly
what the model receives is inspectable.

### Structured Generation

The generated response SHALL conform to a structured schema:

```text
Answer
├── answer
├── citations[]
└── confidence / groundedness indicator
```

Example:

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

The pipeline from the model SHALL be: LLM → JSON → Pydantic → Answer. The
schema MAY evolve as experiments reveal better requirements; fields MUST NOT
be added until experiments justify them.

## Level 2 Abstention and Evidence Sufficiency

### Abstention

The system SHALL abstain when the knowledge base cannot answer the question
(Principle XIX):

```text
Unknown Question → No sufficient evidence → Abstain
```

Abstention SHALL be represented explicitly in the structured answer
(`abstained`). The model MUST NOT manufacture an answer from general
knowledge.

### Evidence Sufficiency

Level 2 SHALL distinguish:

```text
retrieval succeeded
```

from:

```text
retrieved evidence is sufficient to answer
```

High retrieval similarity does not prove answerability. An
evidence-sufficiency decision SHALL be based initially on: retrieval
threshold, number of useful evidence chunks, retrieval scores, explicit
prompt rules, and an LLM structured assessment of `sufficient_evidence`.
A sophisticated semantic entailment model is NOT required at Level 2.

## Level 2 Groundedness and Conflict Handling

### Groundedness

Level 2 SHALL evaluate whether generated claims are supported by the
retrieved evidence:

```text
Question → Evidence → Answer → Claims → Evidence Support
```

A claim is grounded when the evidence supports it. Evaluation SHALL
distinguish at minimum:

```text
SUPPORTED
UNSUPPORTED
PARTIALLY_SUPPORTED
```

Initially this MAY use a structured LLM judge over claim/evidence pairs.

### Conflict Handling

When retrieved documents conflict, the system SHALL NOT silently merge
statements (Principle XXIII). The answer SHALL acknowledge uncertainty and
name the differing sources. Advanced source authority and document
governance are deferred to later levels.

## Level 2 Evaluation Constitution

### Two Layers, Reported Separately

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

Level 2 MUST NOT replace retrieval evaluation with answer evaluation
(Principle XXII).

### Evaluation Dataset

The Level 1 evaluation dataset SHALL be extended. Each test case SHALL
contain:

```text
question
answerable
expected_answer
relevant_documents
relevant_chunks
```

Example:

```json
{
  "question": "What can cause packet loss on a 5G network?",
  "answerable": true,
  "relevant_documents": ["5g_packet_loss"],
  "expected_answer": "...",
  "relevant_chunks": ["5g_packet_loss-003"]
}
```

The dataset SHALL include: answerable questions, unanswerable (unknown)
questions, partial-evidence questions, and conflict questions.

### Hallucination Testing

Level 2 SHALL explicitly test for unsupported generation across these
scenarios:

```text
Correct evidence
Incorrect evidence
Incomplete evidence
Conflicting evidence
No evidence
Unknown question
```

The objective is not to eliminate hallucination completely; it is to measure
and reduce unsupported generation.

### Failure Attribution

Every failure SHALL be classified by asking: was the correct evidence
retrieved? If NO → retrieval problem. If YES → generation/grounding
problem. This distinction prepares the project for Level 3.

## Level 2 Separation of Responsibilities

The architecture SHALL maintain:

```text
Retriever → Evidence → Generator → Answer → Validator
```

The generator MUST NOT directly access the vector database. The validator
MUST NOT perform retrieval. Each component SHALL have exactly one
responsibility (Principle XXI).

## Level 2 Out of Scope

The following capabilities SHALL NOT be implemented at Level 2:

**Retrieval:** BM25, hybrid search, reranking, query rewriting, query
decomposition.

**Knowledge governance:** document lifecycle, document approval.

**Security:** RBAC, ABAC, multi-tenancy, advanced security.

**Platform:** agents, memory, tool calling, production observability,
distributed tracing, CI/CD, Kubernetes, multi-region deployment, FinOps.

**Frameworks:** LangChain, LlamaIndex, LangGraph, RAG evaluation
frameworks, agent frameworks — unless an experiment demonstrates a specific
need, in which case the need MUST be documented before adoption.

These capabilities belong to later maturity levels.

## Level 2 Backward Compatibility

Level 2 MUST preserve Level 1 behavior. The major change is the addition of
an explicit grounding layer, not a redesign of retrieval:

```text
Level 1: Question → Retrieve → Generate → Answer
Level 2: Question → Retrieve → Evidence → Generate → Structured Answer
         → Validate → Grounded Answer + Citations
```

Level 1 retrieval metrics, retrieval diagnostics, and regression tests MUST
remain available and passing.

## Level 2 Quality Gates

### Definition of Done

Level 2 is complete when:

- [ ] answers are generated from explicit evidence
- [ ] evidence is represented as structured objects
- [ ] evidence builder transforms retrieval results into evidence
- [ ] generated answers contain citations
- [ ] citations reference actual retrieved chunks
- [ ] invalid citations are detected
- [ ] the LLM can abstain
- [ ] unknown questions are tested
- [ ] structured answer output is validated
- [ ] evidence sufficiency is decided explicitly
- [ ] groundedness is evaluated
- [ ] citation correctness is evaluated
- [ ] citation validity is evaluated
- [ ] citation completeness is evaluated
- [ ] answer correctness is evaluated
- [ ] retrieval metrics (Recall@K, Precision@K, MRR) remain available
- [ ] hallucination/unsupported-answer tests exist
- [ ] conflicting evidence is handled explicitly
- [ ] retrieval failures are separated from generation failures
- [ ] regression tests exist for every discovered failure
- [ ] experiments are documented in
      `docs/levels/level-02-grounded-rag/experiments.md`
- [ ] lessons learned are documented in
      `docs/levels/level-02-grounded-rag/lessons-learned.md`
- [ ] all behavior is covered by tests

### Exit Criteria

Before moving to Level 3, the developer MUST be able to explain:

1. why retrieval correctness does not guarantee answer correctness,
2. what grounding means,
3. what evidence means in a RAG system,
4. why citations must be validated,
5. why the LLM cannot be trusted to invent citation identifiers,
6. what abstention means,
7. the difference between citation validity and citation correctness,
8. the difference between citation correctness and citation completeness,
9. how to identify unsupported claims,
10. why retrieval evaluation and answer evaluation are separate,
11. how conflicting evidence should be handled,
12. why prompt instructions alone are insufficient for reliable grounding.

### Level 2 Completion Test

A final set of questions MUST be run and inspected end to end:

```text
1. Known Telco question
2. Unknown question
3. Partially supported question
4. Question with conflicting evidence
5. Question where retrieval succeeds but generation can hallucinate
```

For each query, inspect:

```text
retrieved evidence → generated answer → citations → citation validation
→ groundedness evaluation → final response
```

## Future Evolution

Each level MUST grow out of documented limitations of the previous one
rather than reimplementing the final architecture prematurely:

```text
Level 0   Naive RAG — Can RAG work?
Level 1   RAG Foundations — Can we retrieve the right knowledge?
Level 2   Grounded RAG — Is the answer supported by retrieved evidence?
Level 3   Advanced Retrieval — Can we retrieve the right knowledge
          reliably even for difficult queries?
Level 4   Knowledge Lifecycle
Level 5   Knowledge Governance
Level 6   Authentication + RBAC
Level 7   ABAC + Multi-tenancy
Level 8   Evaluation
Level 9   Testing
Level 10  CI/CD + DevSecOps
...
Level 24  Enterprise RAG Platform
```

The transition to Level 3 is justified by the question Level 2 cannot
answer: what happens when the system cannot retrieve the right evidence in
the first place? That motivates BM25, hybrid retrieval, metadata filtering,
reranking, and query rewriting.

## Governance

- **Supremacy.** This constitution supersedes all other engineering
  practices for the active level. Where a plan, task, or code convention
  conflicts with a principle here, the principle wins.
- **Amendment procedure.** Amendments MUST be made by editing this file in a
  dedicated change that states the rationale, records the impact in the
  Sync Impact Report at the top of the file, and includes a migration plan
  when the amendment invalidates existing work or documents. Amendments
  require review and explicit approval before merge.
- **Versioning policy.** The constitution uses semantic versioning:
  MAJOR for backward-incompatible principle removals or redefinitions,
  MINOR for new principles or materially expanded guidance, PATCH for
  clarifications and wording fixes. The version line at the bottom of this
  file MUST match the version stated in the Sync Impact Report.
- **Compliance review.** Every pull request and design review MUST verify
  compliance with the Core Principles and the active level's Quality Gates.
  Deviations MUST be justified explicitly in the PR description; unjustified
  complexity or scope creep MUST be rejected. Complexity that cannot be
  tied to an active-level problem MUST be deferred per Principle I.
- **Level completion gate.** A maturity level MAY be declared complete only
  when all of its Definition of Done and Exit Criteria items are met.
  Declaring Level 2 complete MUST NOT mark Level 1 metrics or tests as
  obsolete.
- **Runtime guidance.** Day-to-day development guidance for the active level
  lives in `docs/levels/level-02-grounded-rag/plan.md`; it MUST remain
  consistent with this constitution and MUST NOT weaken any NON-NEGOTIABLE
  principle.

**Version**: 1.2.0 | **Ratified**: 2026-10-06 | **Last Amended**: 2026-10-07
