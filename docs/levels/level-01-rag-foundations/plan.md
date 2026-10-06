# Telco Enterprise RAG

## Level 1 Plan — RAG Foundations

**Version:** 1.0
**Level:** 1
**Status:** Active

---

## 1. Objective

Upgrade the Level 0 naive RAG from:

```
Pure Python
+
Fake embeddings/vector database
```

to:

```
Pure Python application logic
+
Real embedding model
+
Real vector database
+
Structured metadata
+
Configurable retrieval
+
Retrieval evaluation
```

The goal is to understand real retrieval infrastructure without introducing a RAG framework.

---

## 2. Level 0 Starting Point

Level 0 already provides:

```
Document loading
       ↓
Chunking
       ↓
Fake embedding
       ↓
Fake vector database
       ↓
Retrieval
       ↓
Prompt construction
       ↓
LLM
       ↓
CLI
```

Level 1 will preserve this conceptual pipeline.

The infrastructure underneath retrieval changes.

---

## 3. Target Architecture

```
                    INGESTION

Markdown Documents
        ↓
     Loader
        ↓
 Document Model
        ↓
     Chunker
        ↓
  Chunk Models
        ↓
Embedding Model
        ↓
    ChromaDB
        │
        │
        └──────────────┐
                       │
                       ↓
                    RETRIEVAL

User Question
        ↓
Query Embedding
        ↓
Retriever
        ↓
Top-K + Threshold
        ↓
RetrievalResult[]
        ↓
Prompt Builder
        ↓
OpenRouter
        ↓
Answer
```

Separate evaluation:

```
Evaluation Questions
        ↓
     Retriever
        ↓
Retrieved Documents
        ↓
Expected Documents
        ↓
Recall@K
Precision@K
MRR
```

---

## 4. Technology Stack

Use:

- Python 3.12+
- uv
- Pydantic v2
- sentence-transformers
- BAAI/bge-small-en-v1.5
- ChromaDB
- OpenRouter
- OpenAI Python SDK
- PyYAML
- Typer
- pytest
- Ruff
- mypy

Do not introduce LangChain or LlamaIndex.

---

## 5. Project Structure

Update the Level 0 structure toward:

```
telco-rag/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── Makefile
│
├── config/
│   └── settings.yaml
│
├── data/
│   ├── documents/
│   │   ├── 5g_packet_loss.md
│   │   ├── 5g_latency.md
│   │   ├── lte_troubleshooting.md
│   │   ├── broadband_connectivity.md
│   │   ├── sim_activation.md
│   │   ├── enterprise_sla.md
│   │   ├── noc_incident_procedure.md
│   │   └── network_escalation.md
│   │
│   └── evaluation/
│       └── retrieval_questions.jsonl
│
├── src/
│   └── telco_rag/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── document.py
│       │   ├── chunk.py
│       │   └── retrieval.py
│       │
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── chunker.py
│       │
│       ├── embeddings/
│       │   ├── __init__.py
│       │   └── embedder.py
│       │
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── vector_store.py
│       │   └── retriever.py
│       │
│       ├── generation/
│       │   ├── __init__.py
│       │   ├── prompt.py
│       │   └── llm.py
│       │
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── dataset.py
│       │   └── metrics.py
│       │
│       └── rag/
│           ├── __init__.py
│           └── pipeline.py
│
├── tests/
│   ├── test_models.py
│   ├── test_loader.py
│   ├── test_chunker.py
│   ├── test_embeddings.py
│   ├── test_vector_store.py
│   ├── test_retriever.py
│   ├── test_evaluation.py
│   └── test_rag_pipeline.py
│
└── docs/
    └── levels/
        └── level-01-rag-foundations/
            ├── constitution.md
            ├── plan.md
            ├── experiments.md
            └── lessons-learned.md
```

---

## 6. Implementation Steps

### Step 1 — Replace the Level 0 dependency setup

Add the Level 1 dependencies.

Install:

- pydantic
- pydantic-settings
- sentence-transformers
- chromadb
- openai
- python-dotenv
- pyyaml
- typer

Development dependencies:

- pytest
- pytest-cov
- ruff
- mypy

Verify the environment works.

---

### Step 2 — Introduce Pydantic Models

Create:

- `models/document.py`
- `models/chunk.py`
- `models/retrieval.py`

Implement at minimum:

- Document
- Chunk
- RetrievalResult
- RetrievalQuery

The models should be explicit and typed.

---

### Step 3 — Upgrade the Document Loader

The loader should return:

- Document

instead of raw strings.

Generate deterministic document IDs.

For example:

```
5g_packet_loss
```

The document should retain:

- document_id
- title
- source
- content
- metadata

---

### Step 4 — Upgrade the Chunker

The chunker should accept:

- chunk_size
- chunk_overlap

from configuration.

Each generated chunk should contain:

- chunk_id
- document_id
- chunk_index
- text
- metadata

Verify that the parent document ID is preserved.

---

### Step 5 — Add the Real Embedding Model

Implement:

- `embeddings/embedder.py`

using Sentence Transformers.

Recommended initial model:

- **BAAI/bge-small-en-v1.5**

The application should expose an abstraction such as:

- `embed(text)`
- `embed_batch(texts)`

Do not allow the rest of the application to depend directly on the Sentence Transformers implementation.

---

### Step 6 — Measure Embeddings

Create a small experiment.

For several Telco sentences:

- "5G packet loss is caused by..."
- "5G latency can increase when..."
- "SIM activation requires..."
- "Enterprise SLA violations..."

generate embeddings and verify:

- vector dimensionality
- deterministic behavior
- batch embedding
- performance
- empty-input behavior

Document the findings.

---

### Step 7 — Replace the Fake Vector DB

Implement:

- `retrieval/vector_store.py`

using ChromaDB.

The vector store must support:

- create collection
- add chunks
- query vectors
- return metadata
- return documents
- return scores/distances

Do not expose ChromaDB-specific code outside this module.

---

### Step 8 — Build the Real Retriever

Implement:

- `retrieval/retriever.py`

Pipeline:

```
Question
   ↓
Embedding
   ↓
Vector Store
   ↓
Top-K
   ↓
Threshold
   ↓
RetrievalResult[]
```

The retriever should return structured results rather than raw ChromaDB responses.

---

### Step 9 — Add Retrieval Configuration

Create:

- `config/settings.yaml`

Example configuration:

```yaml
retrieval:
  top_k: 5
  similarity_threshold: 0.0

chunking:
  chunk_size: 500
  chunk_overlap: 50

embeddings:
  model: "BAAI/bge-small-en-v1.5"

vector_store:
  path: "./data/chroma"
  collection: "telco_documents"
```

The exact values are experimental rather than permanent.

---

### Step 10 — Add Retrieval Debugging

Add:

- `--debug-retrieval`

to the CLI.

Example output:

```
Query:
Why is my 5G connection experiencing packet loss?

Results:

[1]
Document: 5g_packet_loss
Chunk: 5g_packet_loss-003
Score: 0.87

Text:
...

[2]
Document: network_troubleshooting
Chunk: network_troubleshooting-002
Score: 0.79

Text:
...
```

This is one of the most important Level 1 capabilities.

---

### Step 11 — Create Retrieval Evaluation Dataset

Create:

- `data/evaluation/retrieval_questions.jsonl`

Start with approximately:

- 20–30 questions

Cover:

- 5G
- LTE
- broadband
- SIM activation
- enterprise SLA
- NOC incidents
- network escalation

Include both:

- relevant questions

and:

- questions whose answer is not represented in the corpus

---

### Step 12 — Implement Retrieval Metrics

Create:

- `evaluation/metrics.py`

Implement:

- Recall@K
- Precision@K
- MRR

Do not use an evaluation framework initially.

Implement the formulas directly.

The purpose is to understand the metrics.

---

### Step 13 — Run Retrieval Experiments

Test multiple configurations.

**Experiment A — Chunk size**
- 250
- 500
- 1000

**Experiment B — Overlap**
- 0
- 50
- 100

**Experiment C — Top-K**
- 1
- 3
- 5
- 10

**Experiment D — Threshold**
- Test several similarity thresholds.

Record:

- configuration
- Recall@K
- Precision@K
- MRR
- observations

---

### Step 14 — Analyze Retrieval Failures

For failed queries determine whether the problem came from:

- poor chunking
- wrong document
- poor semantic match
- irrelevant chunks
- insufficient top-K
- threshold too high
- threshold too low
- query ambiguity
- missing knowledge

Record the findings in:

- `docs/levels/level-01-rag-foundations/experiments.md`

---

### Step 15 — Integrate With the RAG Pipeline

Replace the Level 0 fake retrieval component.

The final pipeline becomes:

```
Question
    ↓
Real Query Embedding
    ↓
ChromaDB
    ↓
Structured Retrieval Results
    ↓
Prompt
    ↓
OpenRouter
    ↓
Answer
```

Generation should remain conceptually simple.

Do not add citations yet.

Citations are the main concern of Level 2.

---

### Step 16 — Add Tests

At minimum:

- `test_models.py`
- `test_loader.py`
- `test_chunker.py`
- `test_embeddings.py`
- `test_vector_store.py`
- `test_retriever.py`
- `test_evaluation.py`
- `test_rag_pipeline.py`

Important tests include:

**Metadata preservation**

```
Document
    ↓
Chunk
    ↓
Vector DB
    ↓
Retrieval
```

must preserve document identity.

**Top-K**

Verify that:

```
top_k = 3
```

does not return four results.

**Threshold**

Verify that results below the configured threshold are excluded.

**Deterministic IDs**

The same document should generate the same ID.

---

### Step 17 — Regression Test Level 0

Run the original Level 0 scenarios:

- 5G packet loss
- 5G latency
- SIM activation
- Enterprise SLA
- NOC incident
- Unknown question

Verify that the system still works after replacing the fake vector store.

---

### Step 18 — Update CLI

The CLI should support:

```bash
python -m telco_rag.cli "question"
```

and:

```bash
python -m telco_rag.cli "question" --debug-retrieval
```

The second command must expose retrieval information without requiring the LLM to explain it.

---

### Step 19 — Documentation

Update:

- `README.md`

with:

- Level 1 architecture
- installation
- embedding model
- ChromaDB
- configuration
- ingestion
- querying
- retrieval debugging
- evaluation
- experiments

Update:

- `docs/architecture/`

to reflect the real retrieval architecture.

---

### Step 20 — Lessons Learned

Create:

- `docs/levels/level-01-rag-foundations/lessons-learned.md`

Document:

- What worked?
- What failed?
- What surprised us?
- What does chunk size change?
- What does top-K change?
- What does the similarity score tell us?
- What does it NOT tell us?
- Where does retrieval fail?
- What problems remain?

---

## 26. Level 1 Definition of Done

Level 1 is complete when:

- [ ] Real embedding model
- [ ] Real vector database
- [ ] Structured documents
- [ ] Structured chunks
- [ ] Metadata preservation
- [ ] Configurable chunking
- [ ] Configurable top-K
- [ ] Configurable threshold
- [ ] Retrieval scores
- [ ] Retrieval debug mode
- [ ] Evaluation dataset
- [ ] Recall@K
- [ ] Precision@K
- [ ] MRR
- [ ] Retrieval tests
- [ ] RAG integration
- [ ] Level 0 regression tests
- [ ] Experiments documented
- [ ] Lessons learned documented

---

## 27. What We Deliberately Do Not Solve

At the end of Level 1, the system will still have important weaknesses.

For example:

```
Question
   ↓
Correct chunks
   ↓
LLM
   ↓
Potentially incorrect answer
```

The LLM might:

- ignore retrieved evidence
- invent information
- combine unrelated chunks
- make unsupported claims
- fail to tell the user where information came from

This is intentional.

Those problems motivate Level 2.

---

## 28. Transition to Level 2

Level 2 will ask:

**How do we know that the generated answer is actually supported by the retrieved evidence?**

That introduces:

- Citations
- Source attribution
- Grounded generation
- Abstention
- Citation validation
- Answer evaluation
- Groundedness evaluation

The progression therefore becomes:

```
Level 0
Can RAG work?
        ↓
Level 1
Can we retrieve the right knowledge?
        ↓
Level 2
Can we generate an answer that is actually grounded
in that knowledge?
```

---

## 29. Level 1 Guiding Principle

**Make retrieval real before making it sophisticated.**

Level 1 should leave the developer with a working understanding of:

```
documents
    ↓
chunks
    ↓
embeddings
    ↓
vectors
    ↓
similarity search
    ↓
retrieval
    ↓
retrieval evaluation
```

Only after these foundations are understood should advanced retrieval techniques be introduced.
