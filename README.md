# Telco Enterprise RAG - Master Maturity Roadmap

A structured roadmap for building an enterprise-grade Retrieval-Augmented Generation (RAG) system for telecommunications use cases.

## Setup (uv only)

```bash
uv sync                    # install dependencies + `telco-rag` console script
uv run pytest              # run the full test suite (155 tests)
```

Configuration lives in `config/settings.yaml` (corpus path, chunk size/overlap,
retrieval top-k/similarity-threshold, embedding model, LLM endpoint) and is
overridden by environment variables (`LLM_BASE_URL`, `LLM_MODEL`, `CHUNK_SIZE`,
`CHUNK_OVERLAP`, `TOP_K`, `SIMILARITY_THRESHOLD`, ...). Set `LLM_API_KEY` for a
real OpenRouter-backed model.

## Usage

```bash
uv run telco-rag ingest                  # embed data/documents into ChromaDB (data/chroma)
uv run telco-rag query "How do I fix 5G packet loss?" --debug-retrieval
uv run telco-rag evaluate --threshold 0.65   # Recall@K / Precision@K / MRR on the eval set
```

Full runnable walkthrough with success criteria: `specs/002-level-1-rag-foundations/quickstart.md`.

## Maturity Levels

| Level | Features | Problems to Solve |
|---|---|---|
| **0 — Naive RAG** | Document loading, basic chunking, embeddings, vector DB, similarity search, LLM answer generation | Can we build a working RAG system at all? What are its basic limitations? |
| **1 — RAG Foundations** | Better chunking, metadata, document IDs, configurable top-k, similarity thresholds, prompts | Why are answers irrelevant, incomplete, or inconsistent? How do we debug retrieval? |
| **2 — Grounded RAG** | Source citations, context-aware prompting, answer abstention, citation validation, confidence signals | How do we prevent hallucinations? How can users verify answers? |
| **3 — Advanced Retrieval** | BM25, vector search, hybrid retrieval, metadata filtering, reranking, query rewriting | Why does semantic search fail on exact telco terminology, IDs, acronyms, and technical queries? |
| **4 — Knowledge & Document Lifecycle** | Ingestion pipeline, document validation, versioning, status, ownership, approval, publishing, superseding, archival, deletion, freshness | How do we know which document is authoritative? What happens when a runbook changes or becomes obsolete? |
| **5 — Knowledge Governance** | Document classification, source authority, lineage, retention policies, ownership, review dates, expiration, provenance | Who owns knowledge? Can we prove where an answer came from? What happens to stale or unapproved knowledge? |
| **6 — Authentication & RBAC** | Authentication, users, roles, groups, permissions, document-level ACLs, role-based retrieval filtering | How do we prevent users from retrieving information they aren't authorized to see? |
| **7 — ABAC & Multi-Tenancy** | Tenant isolation, attributes, department/business-unit policies, location/security-level restrictions, tenant-specific indexes/namespaces | How do we support multiple telco organizations/business units without data leakage? |
| **8 — Evaluation** | Golden datasets, expected answers, expected sources, retrieval evaluation, answer evaluation, faithfulness, groundedness, regression tests | How do we objectively know whether RAG is getting better or worse? |
| **9 — RAG Testing** | Unit tests, integration tests, retrieval tests, authorization tests, adversarial tests, prompt-injection tests, regression suites | What happens when code, prompts, models, documents, or permissions change? Can we detect regressions automatically? |
| **10 — CI/CD & DevSecOps** | Git workflow, linting, type checking, unit/integration tests, RAG evaluation gates, security scanning, dependency scanning, container scanning, artifact builds, deployment pipelines | How do we safely move RAG changes from development to production? How do we prevent a bad prompt/model/index change from being deployed? |
| **11 — Configuration & Environment Management** | Dev/test/staging/prod, configuration management, secrets, environment variables, feature flags, model configuration | How do we prevent environment-specific configuration errors and secret leakage? |
| **12 — Observability** | Structured logs, metrics, distributed tracing, retrieval traces, LLM traces, token usage, latency, errors, dashboards | Why did this answer fail? Which retrieval step, model, document, or dependency caused the problem? |
| **13 — Reliability & Resilience** | Timeouts, retries, circuit breakers, fallbacks, graceful degradation, health checks, dependency checks, idempotency | What happens when the LLM, embedding service, vector DB, or document source fails? |
| **14 — Performance & Scalability** | Caching, connection pooling, async processing, batch ingestion, indexing strategies, horizontal scaling, load testing | Can the system handle thousands/millions of documents and many concurrent users? |
| **15 — Security Engineering** | Encryption, secrets management, network security, PII detection, prompt-injection defense, data-exfiltration protection, secure logging | How do we protect enterprise knowledge and prevent malicious users/documents from manipulating the system? |
| **16 — API & Platform** | REST API, API versioning, authentication, authorization, rate limits, quotas, pagination, error contracts, OpenAPI | How can enterprise applications safely consume RAG as a platform service? |
| **17 — FinOps** | Token accounting, embedding costs, retrieval costs, storage costs, model costs, tenant cost attribution, budgets, quotas | How much does each query/document/tenant cost? How do we prevent uncontrolled LLM spending? |
| **18 — Operations** | Deployment automation, migrations, backups, restore, rollback, health checks, operational runbooks, incident response | Can an operations team actually run this system in production? |
| **19 — Audit & Compliance** | Audit events, user activity, access logs, document lineage, model/prompt versions, retention, compliance reporting | Who accessed what? Which model produced an answer? Which documents supported it? Can we reconstruct an incident? |
| **20 — Enterprise Change Management** | Prompt registry, model registry, document approval workflows, evaluation gates, release approvals, rollback, version compatibility | How do we safely change models, prompts, retrieval algorithms, schemas, and knowledge without breaking production? |
| **21 — Advanced RAG** | Multi-query retrieval, contextual compression, parent-child retrieval, hierarchical retrieval, query decomposition, temporal retrieval | How do we handle complex enterprise questions that require multiple retrieval strategies? |
| **22 — Agentic RAG** | Tools, planning, tool selection, workflow orchestration, memory, external systems, human approval | When should the system retrieve information, call another system, or ask a human? How do we control agent actions? |
| **23 — Agent Governance** | Tool permissions, action authorization, human-in-the-loop, action budgets, guardrails, agent audit trails, policy enforcement | How do we prevent an agent from taking unauthorized or dangerous actions? |
| **24 — Production Enterprise Platform** | HA architecture, multi-region strategy, DR, autoscaling, enterprise API gateway, centralized IAM, observability platform, governance, FinOps, platform operations | Can this become a shared, reliable enterprise RAG platform used across a real telco? |

## Current Status: Level 2 — Grounded RAG (0.4.0)

Level 1 landing is unchanged; Level 2 adds grounded answers, verifiable
sources, abstention, and two-layer evaluation:

- **Evidence (US1):** retrieval results become first-class `Evidence`
  objects (`EVIDENCE-nnn`) carrying document/chunk identity, metadata, and
  retrieval score; the generation prompt separates Question / Evidence /
  Instructions and demands a structured `GroundedAnswer` (answer + citations
  + abstained/sufficient_evidence/conflicts). `StructuredOutputError` guards
  malformed model output.
- **Citations (US2):** every generated citation is validated against the
  retrieved evidence — nonexistent documents (`UNKNOWN_DOCUMENT`),
  misattributed chunks (`UNKNOWN_CHUNK`), unretrieved chunks
  (`NOT_RETRIEVED`), empty ids (`MALFORMED`). Invalid citations never reach
  the user; `query` surfaces only `Sources:` that were actually retrieved.
- **Abstention (US3):** the system abstains when there is no evidence, too
  little evidence (`min_evidence` / `sufficiency_threshold`), or when the
  model reports insufficiency — instead of fabricating an answer.
- **Conflicts (US4/US6):** contradictory sources are surfaced as a named
  `Conflicts:` block, never silently merged.
- **Two-layer evaluation (US5):** `uv run telco-rag evaluate` still reports
  the retrieval layer (`Recall@K` / `Precision@K` / `MRR`); `--answers`
  adds a separately-labeled answer layer over
  `data/evaluation/grounded_answers.jsonl` (answer correctness, abstention
  accuracy, citation validity, citation completeness, groundedness counts).
- **Diagnostics (US4):** `--debug-grounding` prints the full grounding path
  (Retrieved Evidence → sufficiency → Generated Answer → Citations →
  Validation → Conflicts → Final Response).

Level 2 quickstart (scenarios V1–V10), data model, contracts, and recorded
prompt-strategy experiments: `specs/003-level-2-grounded-rag/`. Deterministic
tests (`FakeLLM`, science-only judging) keep the suite hermetic (FR-022);
live-model behavior is recorded in
`docs/levels/level-02-grounded-rag/experiments.md`, never asserted.

## Notes

- This roadmap is cumulative - each level builds on the capabilities of previous levels.
- For a telco enterprise deployment, prioritize groundedness (Level 2), governance (Levels 4-5), security (6-7, 15), and compliance (19) early alongside core retrieval quality.
- Use the "Problems to Solve" column to drive acceptance criteria and measurable outcomes at each maturity level.