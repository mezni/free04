<!--
Sync Impact Report
==================
Template source: constitution-template (resolved via resolve-template.sh)
Version change: 1.2.0 -> 1.3.0
Bump type: MINOR (new Level 3 principles and sections added; existing
           principles expanded; no principle removed or redefined)
Source: docs/levels/level-03-advanced-retrieval/constitution.md

Modified principles:
  - "V. Explicit RAG Pipeline" -> expanded: Level 3 retrieval stages added
    (Query Processing/Query Rewriter, Retrieval Controller, Vector/BM25/
    Metadata Filter, RRF Fusion, Reranker)
  - "VIII. Make Retrieval Inspectable" -> expanded: Level 3 debug output
    exposes per-chunk vector rank, BM25 rank, RRF score, reranker score,
    final rank, and original vs rewritten query (source Section 15)
  - "X. Configuration Over Hardcoding" -> expanded: Level 3 knobs
    (retrieval.strategy, retrieval.top_k.*, fusion.method/k,
    retrieval.filters, reranking.*, query_rewriting.enabled)
    (source Section 14)
  - "XI. Tests From the Beginning" -> expanded: Level 3 test coverage
    (bm25, hybrid, rrf, reranker, query rewriter, metadata filtering,
    controller, Level 2 grounding compatibility) (source Section 13)
  - "XII. CLI First" -> expanded: `telco-rag retrieve --strategy ...
    --debug` retrieval diagnostics (source Section 7)
  - "XV. Real Before Sophisticated" -> expanded: real rank-bm25 index
    over real chunks, real cross-encoder reranker, real OpenRouter
    query rewriting
  - "XVI. Metrics Written, Not Hidden" -> expanded: evaluation matrix,
    ablation A-G, and per-stage latency recorded in Python and written
    to experiments.md (source Sections 9, 10, 14)
  - "XXII. Two-Layer Evaluation" -> expanded: strategy comparison stays
    inside the retrieval layer; answer-level evaluation unchanged
  - All other principles (I-IV, VI, VII, IX, XIII, XIV, XVII-XXI,
    XXIII) -> unchanged

Added principles:
  - "XXIV. Complexity Must Justify Itself (NON-NEGOTIABLE)"
  - "XXV. Rank Fusion, Not Score Averaging (NON-NEGOTIABLE)"
  - "XXVI. Retrieval Provenance Is Mandatory"
  - "XXVII. Failure Attribution by Decision Tree (NON-NEGOTIABLE)"
  - "XXVIII. Documents Are Truth, Indexes Are Derived"
  - "XXIX. The Original Query Is Always Preserved (NON-NEGOTIABLE)"

Added sections:
  - Purpose and Scope rewritten for Level 3 (source Sections 1, 2, 3, 5);
    Level 2 purpose preserved as subsection "Level 2 Baseline (Established)"
  - Level 3 Technology Constitution (source Section 3)
  - Level 3 BM25 Constitution (source Sections 2, 6)
  - Level 3 Metadata Filtering Constitution (source Section 7)
  - Level 3 Hybrid Retrieval and RRF Constitution (source Sections 8, 9)
  - Level 3 Reranking Constitution (source Sections 9, 10)
  - Level 3 Query Rewriting Constitution (source Sections 10, 11)
  - Level 3 Retrieval Controller and Result Model Constitution
    (source Sections 5, 6, 12)
  - Level 3 Configuration Constitution (source Section 12)
  - Level 3 CLI and Diagnostics Constitution (source Section 7)
  - Level 3 Evaluation Constitution (source Sections 8, 9, 10)
  - Level 3 Failure Analysis Constitution (source Section 11)
  - Level 3 Latency Constitution (source Section 14)
  - Level 3 Grounding Integration (source Section 12)
  - Level 3 Out of Scope (source Section 22)
  - Level 3 Backward Compatibility (builds on Levels 1-2, grounding
    contract unchanged)
  - Level 3 Quality Gates: Definition of Done (source Section 16),
    Exit Criteria (source Section 17)
  - Level 3 Completion Test

Removed sections:
  - none. Levels 1 and 2 content preserved as established baselines.
  - Clarified: the historical "Level 2 Out of Scope" retrieval
    exclusions (BM25/hybrid/reranking/query rewriting) bound Level 2
    only; Level 3 lifts them via the new Level 3 sections.

Placeholders left undefined: none.
Follow-up TODOs: none.

Date notes:
  - RATIFICATION_DATE kept at 2026-10-06 (original constitution adoption).
  - LAST_AMENDED_DATE set to 2026-10-08 (Level 3 content incorporated).
  - Governance "Runtime guidance" repointed from
    docs/levels/level-02-grounded-rag/plan.md to
    docs/levels/level-03-advanced-retrieval/plan.md.
-->

# Telco Enterprise RAG Constitution

**Level:** 3 — Advanced Retrieval | **Status:** Active
**Previous Level:** Level 2 — Grounded RAG (established) | **Next Level:** Level 4 — Knowledge Lifecycle

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

At Level 3 the retrieval stage itself expands into explicit, individually
inspectable stages; the grounding stages above MUST remain unchanged:

```text
Query Processing (optional Query Rewriter) → Retrieval Controller
  → Vector Search + BM25 Search + Metadata Filter → RRF Fusion
  → Cross-Encoder Reranker → RetrievalResult[]
  → Evidence Builder → ... (Level 2 unchanged)
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

At Level 3, retrieval inspection MUST expose per-chunk provenance: the
strategy used, vector rank, BM25 rank, RRF score, reranker score, and final
rank — plus the original query and any rewritten query. If a retrieval
decision cannot be explained from debug output, the diagnostics are
incomplete.

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

At Level 3 the following MUST additionally be configurable:

```text
retrieval strategy (vector | bm25 | hybrid | hybrid_reranked)
per-strategy top_k (vector, bm25, hybrid, final)
fusion method and k
metadata filters
reranking enabled / model / candidate_k / final_k
query_rewriting enabled
```

Every experimental capability MUST be disable-able through configuration;
controlled experiments require turning features OFF as much as ON.

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

At Level 3 the suite MUST additionally cover, at minimum:

- BM25 index and retrieval (exact terms, error codes, acronyms,
  no-result queries, top-K behavior, metadata preservation)
- hybrid vector/BM25 combination
- RRF fusion (both systems, one system, ties, duplicates, determinism)
- reranker scoring and candidate/final-K behavior
- query rewriting (original preserved, fallback on failure)
- metadata filtering (generic keys)
- retrieval controller strategy selection, deterministic behavior,
  empty results, invalid configuration
- Level 2 grounding compatibility with the advanced retriever

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

At Level 3 the CLI MUST expose retrieval directly and allow strategy
selection per invocation:

```bash
telco-rag retrieve "Why is 5G packet loss occurring?" --strategy hybrid
telco-rag retrieve "Why is 5G packet loss occurring?" \
  --strategy hybrid_reranked --debug
```

The `--debug` output MUST expose: query, rewritten query, strategy, chunk,
vector rank, BM25 rank, RRF score, reranker score, and final rank. The
`retrieve` command MUST stop at `RetrievalResult[]` — it MUST NOT generate
answers.

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

At Level 3 this means: a real BM25 index (rank-bm25) built over the same
chunks as vector retrieval, real cross-encoder scoring with
BAAI/bge-reranker-base, and real OpenRouter query rewriting — not
simulated scores, stub rerankers, or fake rewrites. A disabled feature
MUST be disabled, not stubbed.

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

At Level 3 this extends to the retrieval evaluation matrix (Vector, BM25,
Hybrid, Hybrid + Reranker × original/rewritten query), the ablation study
A-G (Recall, Precision, MRR, latency), and per-stage latency measurement.
Results MUST be recorded in
`docs/levels/level-03-advanced-retrieval/experiments.md`, never asserted;
an unmeasured cell stays marked as unmeasured.

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

At Level 3 the retrieval layer itself splits into a strategy comparison
(vector vs BM25 vs hybrid vs hybrid + reranker, original vs rewritten
query). Strategy comparison MUST be reported inside the retrieval layer and
MUST NOT replace either Level 1 retrieval metrics or Level 2 answer
metrics.

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

### XXIV. Complexity Must Justify Itself (NON-NEGOTIABLE)

Every retrieval component added at Level 3 MUST earn its place through
measured results: its quality delta and its latency cost MUST both be
recorded in `docs/levels/level-03-advanced-retrieval/experiments.md`.
A component MUST NOT ship because it is common practice in enterprise RAG;
it MUST ship because an experiment shows it improves retrieval for a class
of questions. Experimental capabilities MUST be disable-able through
configuration so that each component can be measured with and without
itself.

Rationale: "retrieve broadly, rank intelligently, measure objectively, and
only add complexity when the evidence justifies it" is worthless as a slogan
unless each added stage has a number attached to it.

### XXV. Rank Fusion, Not Score Averaging (NON-NEGOTIABLE)

Vector similarity scores and BM25 scores have different distributions and
different ranges. Combining them by averaging or otherwise mixing raw
scores MUST NOT be done. Hybrid retrieval MUST combine its retrievers
through rank-based fusion (Reciprocal Rank Fusion with configurable `k`),
which consumes only ordinal ranks.

```text
RRF(d) = Σ 1 / (k + rank_i(d))
```

Fusion MUST be deterministic: identical inputs MUST produce identical,
stable ordering, with ties broken by a documented rule.

Rationale: raw-score fusion silently weights retrievers by arbitrary score
scale; rank fusion is scale-free and directly testable.

### XXVI. Retrieval Provenance Is Mandatory

Every `RetrievalResult` MUST record how it was found. At minimum the model
carries:

```text
retrieval_method, score, rank,
vector_rank, bm25_rank, rrf_score, reranker_score, metadata
```

Not every field is populated for every strategy — absence MUST be
meaningful and MUST correspond to a stage that did not apply. Provenance
fields MUST be preserved for diagnostics and MUST NOT alter Level 2
grounding behavior.

Rationale: without provenance the failure-analysis questions ("did BM25
find it? did reranking preserve it?") cannot be answered from data.

### XXVII. Failure Attribution by Decision Tree (NON-NEGOTIABLE)

Every significant retrieval failure MUST be attributed using the decision
tree, and the FIRST stage that lost the correct chunk names the failure:

```text
Was the correct chunk in the corpus?          NO → corpus/chunking problem
Did vector retrieve it?                       NO → vector miss
Did BM25 retrieve it?                         NO → BM25 miss
Did hybrid retrieve it?                       NO → fusion miss
Did reranking preserve it?                    NO → reranker demotion
Did query rewriting help?                     (record: helped / neutral / hurt)
```

Fixes MUST target the attributed stage only; blind tuning across stages is
prohibited. Every fixed failure MUST become a named regression test in
`tests/`.

Rationale: this is the difference between a retrieval-debugging methodology
and guessing.

### XXVIII. Documents Are Truth, Indexes Are Derived

Source documents and their chunks are the source of truth. Both the vector
store and the BM25 index are derived artifacts: each MUST be reproducible
by re-running ingestion over the source documents, and MUST NOT be
hand-edited or promoted to authoritative status. If an index disagrees with
the corpus, the index is rebuilt, not patched.

Rationale: Level 3 introduces a second index; without an explicit truth
hierarchy, two derived stores become two competing sources of truth.

### XXIX. The Original Query Is Always Preserved (NON-NEGOTIABLE)

Query rewriting MUST preserve the original query unconditionally. The
system MUST support original-query and rewritten-query operation as
separate experimental modes; rewriting MUST be disabled by default and
MUST fall back to the original query on any failure. Debug output MUST
show both queries whenever a rewrite occurs. A rewrite MUST preserve user
intent and technical identifiers (error codes, acronyms, protocol names)
and MUST NOT add unsupported assumptions.

Rationale: rewriting is the only Level 3 stage that mutates user input; it
is off by default precisely because it must prove itself against the
original before being trusted.

## Purpose and Scope

This constitution defines the engineering principles and boundaries for
Level 3 of the Telco Enterprise RAG project. The objective of Level 3 is:

> Retrieve broadly, rank intelligently, measure objectively, and only add
> complexity when the evidence justifies it.

Level 3 transforms the Level 2 grounded RAG system into an advanced
retrieval system. Level 2 established:

```text
Question → Vector Retriever → Evidence → Grounded Generation
        → Citation-validated Answer
```

Level 2 proved answers can be grounded in retrieved evidence. Level 3
addresses the next fundamental problem:

> What happens when the system cannot retrieve the right evidence in the
> first place?

Grounding validates what was retrieved; it cannot recover what was never
found. Level 3 therefore attacks the retrieval layer itself:

```text
Level 2 question:  Is this answer supported by the evidence we retrieved?
Level 3 question:  Did we retrieve the right evidence at all — reliably,
                   for every class of Telco question?
```

The Level 3 architecture is:

```text
                         INGESTION
                            │
                            ↓
                      Documents → Chunks
                ┌───────────┴───────────┐
                ↓                       ↓
          Embeddings → ChromaDB     BM25 Index
                │                       │
                └───────────┬───────────┘
                            ↓
                         RETRIEVAL
                            │
Question ──→ Query Processing (optional Query Rewriter)
                            ↓
                  Retrieval Controller
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          Vector          BM25      Metadata Filter
          Search         Search
             └──────────────┼──────────────┘
                            ↓
                     RRF Fusion → Candidate Pool
                            ↓
                 Cross-Encoder Reranker (optional)
                            ↓
                    Final RetrievalResult[]
                            ↓
              Level 2 Grounding Pipeline (unchanged contract)
                            ↓
                         Answer
```

Level 3 is a retrieval-quality learning level. It is **not a
production-ready enterprise system**.

### Included

Level 3 includes only the capabilities required to demonstrate advanced
retrieval and its measurement:

- BM25 lexical retrieval (rank-bm25) over the same chunks as vector
  retrieval, with a reproducible index
- generic metadata filtering (department, product, document_type,
  classification, source — as configuration keys, not hardcoded)
- hybrid retrieval combining vector and BM25 through rank fusion
- Reciprocal Rank Fusion with configurable `k`
- cross-encoder reranking (BAAI/bge-reranker-base), disable-able, with
  candidate_k / final_k configuration
- query rewriting via OpenRouter, disabled by default, original query
  always preserved
- retrieval controller selecting strategies (vector, bm25, hybrid,
  hybrid_reranked) from configuration
- retrieval provenance in `RetrievalResult` (vector_rank, bm25_rank,
  rrf_score, reranker_score, retrieval_method)
- `telco-rag retrieve` CLI with per-strategy selection and full `--debug`
  diagnostics
- expanded evaluation dataset covering: semantic, exact terminology,
  error code, acronym, multi-concept, ambiguous, metadata-filtered, and
  unanswerable questions
- evaluation matrix (four strategies × original/rewritten query) with
  Recall@K, Precision@K, MRR
- ablation study A-G with per-stage latency measurement
- retrieval failure analysis via the decision tree (Principle XXVII)
- preservation of the complete Level 1/2 metric and grounding stack

### Explicitly Excluded

The following capabilities belong to later maturity levels. Their exclusion
is intentional:

- query decomposition, multi-hop retrieval
- document lifecycle, document approval, document governance
- RBAC, ABAC, multi-tenancy, advanced security (metadata filtering only
  lays the foundation)
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

### Level 2 Baseline (Established)

Level 2 established the grounding layer that Level 3 MUST NOT replace:

```text
Level 2: Question → Retrieve → Evidence → Generate → Structured Answer
         → Validate → Grounded Answer + Citations
Level 3: Question → Retrieval Controller → Advanced Retrieval
         → RetrievalResult[] → Evidence (Level 2, unchanged contract)
         → Grounded Answer + Citations
```

Level 2 included: evidence as first-class objects, evidence builder,
grounded prompts, structured answers, citation model and validation,
abstention, evidence sufficiency, groundedness evaluation, conflict
handling, answer-level evaluation (correctness, groundedness, citation
validity/completeness, abstention), hallucination tests, and the two-layer
evaluation separation.

The Level 2 sections below remain in force. Level 3 changes WHAT is
retrieved; HOW evidence is built, grounded, cited, validated, and checked
MUST remain contractually unchanged, and the full Level 2 test suite MUST
continue to pass.

Level 2's retrieval exclusions (BM25, hybrid search, reranking, query
rewriting) were scope boundaries of Level 2 only; Level 3 lifts exactly
those exclusions — and no others.

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

> Historical scope boundary of Level 2. The retrieval exclusions below
> (BM25, hybrid, reranking, query rewriting) bound Level 2 only and are
> lifted by the Level 3 sections; the remaining exclusions stay in force
> until their own levels.

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

## Level 3 Technology Constitution

Level 3 SHALL continue using the Level 1/2 stack. No framework SHALL be
introduced to implement advanced retrieval.

### Application

Python 3.12+, uv, Pydantic v2, PyYAML, Typer — unchanged from Level 1/2.

### Retrieval

```text
sentence-transformers, BAAI/bge-small-en-v1.5, ChromaDB — unchanged
rank-bm25                          (new — lexical retrieval)
BAAI/bge-reranker-base             (new — cross-encoder reranking)
```

### Generation

OpenRouter with the OpenAI-compatible Python SDK — unchanged from Level 2;
also used for query rewriting.

### Testing and Evaluation

pytest, pytest-cov, Ruff, mypy; Python/Pydantic evaluation logic —
unchanged (Principle XVI).

## Level 3 BM25 Constitution

BM25 SHALL be introduced as a lexical retrieval peer to vector search —
not a replacement (Principle I).

- `BM25Index` and `BM25Retriever` SHALL operate over the same chunks used
  by vector retrieval.
- The index SHALL store `chunk_id`, `document_id`, chunk text, and
  metadata.
- The index MUST be reproducible from the source documents by re-running
  ingestion (Principle XXVIII).
- The BM25 index MUST NOT be the source of truth.
- BM25 retrieval MUST be selectable as its own strategy (`strategy: bm25`)
  and MUST return ordinary `RetrievalResult[]` with `retrieval_method`
  recorded.

Rationale: embeddings blur exact identifiers; error codes, acronyms, and
protocol names ("X2 timeout 504") are where term-frequency matching beats
cosine similarity over a small embedding model.

## Level 3 Metadata Filtering Constitution

Filters SHALL be generic key/value restrictions over document metadata,
configured under `retrieval.filters`:

```yaml
retrieval:
  strategy: vector
  filters:
    department: network
    product: 5g
```

Supported keys SHALL include at least: department, product,
document_type, classification, source — but the implementation MUST be
generic over metadata keys, never hardcoded to these keys.

- Filters SHALL apply uniformly to every retrieval strategy.
- Filtering is a restriction mechanism only — it MUST NOT rank or score.
- The generic interface is the foundation future authorization policies
  MUST build on; filters MUST NOT be coupled to today's key set.

Rationale: "which chunks may the system see" is a policy question that
outlives any particular metadata schema.

## Level 3 Hybrid Retrieval and RRF Constitution

### Hybrid Retrieval

The hybrid retriever SHALL execute vector search and BM25 search and
combine the candidates (Principle XXV):

```text
Vector Search + BM25 Search → Candidate Combination
```

Averaging raw vector and BM25 scores MUST NOT be done — their score
distributions differ (Principle XXV).

### Reciprocal Rank Fusion

```text
RRF(d) = Σ 1 / (k + rank_i(d))
```

where `d` is a chunk, `rank_i` is its 1-based rank from retriever `i`,
and `k` is a configurable constant (default 60).

- Fusion SHALL consume ranks only, never raw scores.
- Fusion MUST be deterministic: identical inputs produce identical
  ordering; ties are broken by a stable, documented rule.
- Duplicate chunks across systems MUST be handled explicitly, not
  double-counted silently.
- `k` MUST be configuration (`retrieval.fusion.k`), not a literal in code.
- The fusion implementation MUST stay small and directly testable.

Rationale: RRF is scale-free — it sidesteps score calibration entirely and
is trivially testable.

## Level 3 Reranking Constitution

The cross-encoder reranker SHALL re-score the fused candidate pool:

```text
Hybrid top candidate_k (default 20) → BAAI/bge-reranker-base → final_k (default 5)
```

- Reranking SHALL be disable-able via `reranking.enabled` (Principle XXIV).
- `model`, `candidate_k`, and `final_k` SHALL be configuration.
- Reranker scores SHALL be recorded on the result (`reranker_score`), not
  discarded (Principle XXVI).
- The reranker MUST ONLY reorder candidates that fusion produced — it MUST
  NOT introduce chunks from outside the candidate pool.
- Reranking MUST NOT be applied implicitly to strategies other than
  `hybrid_reranked`.

Rationale: bi-encoder scoring is cheap but approximate (query and document
scored independently); a cross-encoder reads them jointly at a cost bounded
by reranking only the top candidates.

## Level 3 Query Rewriting Constitution

Query rewriting SHALL use OpenRouter and its prompt SHALL require:

```text
preserve user intent
expand useful terminology
preserve technical identifiers
avoid adding unsupported assumptions
return exactly one retrieval query
```

- The original query MUST always be preserved (Principle XXIX).
- Original-query and rewritten-query operation SHALL be separate
  experimental modes.
- Rewriting SHALL be disabled by default
  (`query_rewriting.enabled: false`).
- Debug output MUST show both queries whenever a rewrite occurs.
- A rewrite failure MUST fall back to the original query — a failed
  rewrite MUST NOT fail the request.
- Rewritten output MUST NOT be asserted as an improvement without an
  original-vs-rewritten measurement in `experiments.md`.

Rationale: rewriting adds a network call, latency, and a failure mode; it
must prove itself against the original before being enabled.

## Level 3 Retrieval Controller and Result Model Constitution

### Controller

The `RetrievalController` SHALL be the single entry point for retrieval,
with exactly these responsibilities:

```text
select strategy
apply filters
rewrite query if enabled
retrieve candidates
fuse candidates
rerank candidates
return final RetrievalResult[]
```

- The controller MUST NOT generate answers (Principle XXI).
- Supported strategies: `vector`, `bm25`, `hybrid`, `hybrid_reranked`.
- An unknown or misconfigured strategy MUST fail loudly at configuration
  or invocation time — silent fallback to another strategy is prohibited.
- The controller MUST be deterministic for a fixed configuration.

### Result Model

`RetrievalResult` SHALL carry provenance (Principle XXVI):

```text
RetrievalResult(
    document_id, chunk_id, text,
    score, rank,
    retrieval_method, metadata,
    vector_rank, bm25_rank,
    rrf_score, reranker_score,
)
```

Not every field is populated for every strategy; absence MUST be
meaningful. The model MUST remain backward compatible with the Level 2
Evidence Builder contract.

## Level 3 Configuration Constitution

All Level 3 behavior SHALL be configuration-driven (Principle X). Example:

```yaml
retrieval:
  strategy: hybrid
  top_k:
    vector: 20
    bm25: 20
    hybrid: 20
    final: 5
  fusion:
    method: rrf
    k: 60
  filters: {}

reranking:
  enabled: true
  model: BAAI/bge-reranker-base
  candidate_k: 20
  final_k: 5

query_rewriting:
  enabled: false
```

- Every experimental knob SHALL have a default.
- Invalid configuration MUST fail at load time, not at query time.
- Every strategy MUST be selectable without code changes.

## Level 3 CLI and Diagnostics Constitution

The CLI SHALL expose retrieval directly:

```bash
telco-rag retrieve "Why is 5G packet loss occurring?"
telco-rag retrieve "Why is 5G packet loss occurring?" --strategy vector
telco-rag retrieve "Why is 5G packet loss occurring?" --strategy bm25
telco-rag retrieve "Why is 5G packet loss occurring?" --strategy hybrid
telco-rag retrieve "Why is 5G packet loss occurring?" \
  --strategy hybrid_reranked --debug
```

`--debug` output SHALL expose, per chunk:

```text
Query | Rewritten Query | Strategy | Chunk
Vector Rank | BM25 Rank | RRF Score | Reranker Score | Final Rank
```

The `retrieve` command MUST stop at `RetrievalResult[]`; it MUST NOT
generate answers. Retrieval diagnostics MUST NEVER require reading source
code (Principle VIII).

## Level 3 Evaluation Constitution

### Evaluation Matrix

Every retrieval question SHALL be evaluated with each strategy:

```text
Vector | BM25 | Hybrid | Hybrid + Reranker
```

and separately for:

```text
Original Query | Rewritten Query
```

### Metrics

```text
Recall@1 / @3 / @5 / @10
Precision@1 / @3 / @5 / @10
MRR
Latency
```

### Ablation Study

```text
A: Vector only
B: BM25 only
C: Vector + BM25
D: Vector + BM25 + RRF
E: Hybrid + Reranker
F: Hybrid + Query Rewriting
G: Hybrid + Query Rewriting + Reranker
```

Deltas between consecutive experiments isolate the contribution of each
component; each component's quality gain MUST be judged against its
latency cost (Principle XXIV).

### Evaluation Dataset

`data/evaluation/retrieval_questions.jsonl` SHALL cover, at minimum:

```text
semantic
exact terminology
error code
acronym
multi-concept
ambiguous
metadata-filtered
unanswerable
```

Unanswerable questions SHALL be scored and reported separately — they MUST
NOT be silently averaged into answerable-question Recall.

### Recording

All results SHALL be recorded in
`docs/levels/level-03-advanced-retrieval/experiments.md`. Strategy claims
("BM25 wins for error codes") MUST trace to a measured number; an
unmeasured cell stays marked unmeasured (Principle XVI).

## Level 3 Failure Analysis Constitution

Every significant retrieval failure SHALL be diagnosed with the decision
tree (Principle XXVII):

```text
Was the correct chunk in the corpus?     NO → corpus/chunking problem
        ↓ YES
Did vector retrieve it?                  NO → vector miss
        ↓
Did BM25 retrieve it?                    NO → BM25 miss
        ↓
Did hybrid retrieve it?                  NO → fusion miss
        ↓
Did reranking preserve it?               NO → reranker demotion
        ↓
Did query rewriting help?                (helped / neutral / hurt)
```

- Each stage is a yes/no question answered from debug output or evaluation
  data.
- A failure MUST be attributed to the FIRST stage that lost the chunk, and
  fixes MUST target only that stage.
- The failure log SHALL be maintained in `experiments.md`.
- Each fixed failure MUST become a named regression test in `tests/`.

This creates a retrieval-debugging methodology rather than blind tuning.

## Level 3 Latency Constitution

Level 3 SHALL establish the first retrieval performance baseline by
recording, at minimum:

```text
embedding latency
vector retrieval latency
BM25 latency
fusion latency
reranking latency
query rewriting latency
total retrieval latency
```

- Latency SHALL be reported alongside quality metrics in the ablation
  study.
- A component whose quality gain does not justify its latency is a
  candidate for removal (Principle XXIV) — complexity must pay rent.

## Level 3 Grounding Integration

Level 2 grounding SHALL NOT be rewritten. The flow becomes:

```text
Question
   ↓
Retrieval Controller → Advanced Retrieval → RetrievalResult[]
   ↓
Evidence Builder (Level 2, unchanged contract) → Evidence[]
   ↓
Grounded Generator → Answer
   ↓
Citation Validator → Grounding Checker → Final Response
```

- The Evidence Builder MUST keep consuming `RetrievalResult[]`.
- Level 2 grounding tests MUST pass unchanged (Principle XI).
- Retrieval provenance (`vector_rank`, `rrf_score`, `reranker_score`)
  MUST NOT leak into grounding behavior unless deliberately designed and
  tested.

## Level 3 Out of Scope

The following capabilities SHALL NOT be implemented at Level 3:

**Retrieval:** query decomposition, multi-hop retrieval.

**Knowledge governance:** document lifecycle, document approval.

**Security:** RBAC, ABAC, multi-tenancy, advanced security — metadata
filtering only lays the foundation for them.

**Platform:** agents, memory, tool calling, production observability,
distributed tracing, CI/CD, Kubernetes, multi-region deployment, FinOps.

**Frameworks:** LangChain, LlamaIndex, LangGraph, RAG evaluation
frameworks, agent frameworks — unless an experiment demonstrates a specific
need, in which case the need MUST be documented before adoption
(Principle II).

## Level 3 Backward Compatibility

Level 3 MUST preserve Levels 1 and 2. The change is a richer retrieval
layer, not a redesign of grounding:

```text
Level 1: Question → Retrieve → Generate → Answer
Level 2: Question → Retrieve → Evidence → Generate → Structured Answer
         → Validate → Grounded Answer + Citations
Level 3: Question → Controller → Advanced Retrieval → RetrievalResult[]
         → Evidence → Generate → Validate → Grounded Answer + Citations
```

Level 1 retrieval metrics and diagnostics, Level 2 grounding behavior, and
both regression suites MUST remain available and passing. Declaring Level
3 complete MUST NOT mark any Level 1/2 metric or test obsolete.

## Level 3 Quality Gates

### Definition of Done

Level 3 is complete when:

- [ ] BM25 works
- [ ] vector retrieval still works
- [ ] metadata filtering works generically
- [ ] hybrid retrieval works via rank fusion
- [ ] RRF works and is deterministic
- [ ] cross-encoder reranking works and can be disabled
- [ ] query rewriting works and can be disabled
- [ ] all four strategies (vector, bm25, hybrid, hybrid_reranked) are
      configurable without code changes
- [ ] retrieval diagnostics are available via `telco-rag retrieve --debug`
- [ ] the evaluation dataset covers all eight question categories
- [ ] vector/BM25/hybrid/reranked strategies are compared in the
      evaluation matrix
- [ ] query rewriting is experimentally evaluated (original vs rewritten)
- [ ] per-stage latency is measured
- [ ] retrieval failures are documented with the decision tree
- [ ] unit tests pass
- [ ] Level 2 grounding tests pass unchanged
- [ ] experiments are documented in
      `docs/levels/level-03-advanced-retrieval/experiments.md`
- [ ] lessons learned are documented in
      `docs/levels/level-03-advanced-retrieval/lessons-learned.md`
- [ ] all Level 3 behavior is covered by tests

### Exit Criteria

Before moving beyond Level 3, the developer MUST be able to explain, from
measured results rather than assumptions:

1. which retrieval strategy works best for which type of Telco question
   (semantic → vector, exact term → BM25, mixed → hybrid, large candidate
   set → hybrid + reranker, poorly phrased → rewriting + hybrid — as
   confirmed or refuted by `experiments.md`),
2. why raw vector and BM25 scores must not be averaged,
3. what RRF buys and what it costs,
4. why the reranker may only reorder candidates it did not retrieve,
5. why query rewriting is disabled by default,
6. where the BM25 index sits in the truth hierarchy
   (documents → chunks → indexes),
7. how to attribute a retrieval failure to a specific stage,
8. how each added component's latency compares with its quality gain.

### Level 3 Completion Test

The evaluation matrix and ablation study MUST be run and recorded, and one
`--debug` trace MUST be inspected per strategy:

```text
1. vector      — semantic question
2. bm25        — error-code / exact-terminology question
3. hybrid      — mixed semantic + exact-terminology question
4. hybrid_reranked — large candidate-set question, verify provenance fields
5. hybrid + rewriting — poorly phrased question, verify both queries shown
```

For each trace, verify:

```text
strategy selected → candidates retrieved → fusion scores present
→ reranker scores present (if enabled) → final ordering → provenance fields
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

The transition to Level 3 was justified by the question Level 2 could not
answer: what happens when the system cannot retrieve the right evidence in
the first place? Level 3 answers it with BM25, hybrid retrieval, metadata
filtering, rank fusion, reranking, and query rewriting.

The transition to Level 4 (Knowledge Lifecycle) will be justified by the
problems Level 3 cannot solve — among them: document versioning, approval
flow, effective dates, and index/corpus drift over time, all of which the
derived-index truth hierarchy (Principle XXVIII) explicitly defers. Query
decomposition and multi-hop retrieval remain deferred until an evaluation
failure shows single-query retrieval is the limiting factor.

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
  Declaring Level 3 complete MUST NOT mark Level 1 metrics, Level 2
  grounding behavior, or their tests as obsolete.
- **Runtime guidance.** Day-to-day development guidance for the active level
  lives in `docs/levels/level-03-advanced-retrieval/plan.md`; it MUST remain
  consistent with this constitution and MUST NOT weaken any NON-NEGOTIABLE
  principle.

**Version**: 1.3.0 | **Ratified**: 2026-10-06 | **Last Amended**: 2026-10-08
