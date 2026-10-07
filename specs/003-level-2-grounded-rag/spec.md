# Feature Specification: Level 2 Grounded RAG

**Feature Branch**: `003-level-2-grounded-rag`

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "read all plan from docs/levels/level-02-grounded-rag/plan.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Grounded Answer With Evidence and Citations (Priority: P1)

As a developer learning RAG, I want every answer to be generated from
explicit, structured evidence and to display the citations that support it,
so that I can verify the answer came from the knowledge base rather than
from the model's general knowledge.

**Why this priority**: This is the core upgrade of Level 2. Without evidence
objects, structured answers, and citations, the system is still a Level 1
retriever with a prompt — there is nothing to validate, evaluate, or debug
about groundedness.

**Independent Test**: Ask a known Telco question, and verify that the
response contains an answer, at least one citation identifying a document
and chunk that were actually retrieved, and that the evidence shown matches
the retrieved chunks.

**Acceptance Scenarios**:

1. **Given** documents are ingested, **When** a user asks "What can cause
   packet loss on a 5G network?", **Then** the response contains an answer,
   citations naming real retrieved document/chunk pairs, and the sources are
   displayed to the user.
2. **Given** a query has been retrieved, **When** the evidence builder runs,
   **Then** each retrieved result becomes an explicit evidence object with a
   stable identifier, document ID, chunk ID, title, source, text, and
   retrieval score.
3. **Given** a generated answer, **When** the structured response is parsed,
   **Then** malformed or non-conforming output is detected and reported
   rather than silently accepted.
4. **Given** an answer with factual claims, **When** citations are listed,
   **Then** every claim that relies on the knowledge base is supported by at
   least one citation.

---

### User Story 2 - Citation Validation Against Retrieval Results (Priority: P1)

As a developer, I want every generated citation to be validated against the
actual retrieval result before the answer is returned, so that invented or
unverifiable source identifiers are rejected.

**Why this priority**: The model cannot be trusted to invent citation
identifiers. Without validation, citations add a false sense of trust — the
failure mode is worse than having no citations at all.

**Independent Test**: Feed a generated answer containing a citation to a
nonexistent document or a chunk that was not retrieved, and verify the
validator flags it as invalid.

**Acceptance Scenarios**:

1. **Given** an answer citing a chunk that was retrieved for the current
   question, **When** validation runs, **Then** the citation passes.
2. **Given** an answer citing a nonexistent document, **When** validation
   runs, **Then** the citation is rejected and the rejection is reported.
3. **Given** an answer citing a valid document but a chunk that was not
   retrieved for this question, **When** validation runs, **Then** the
   citation is rejected.
4. **Given** an answer citing a valid document with an invalid chunk ID,
   **When** validation runs, **Then** the citation is rejected.
5. **Given** duplicate citations for the same chunk, **When** validation
   runs, **Then** duplicates are handled deterministically (deduplicated or
   flagged), not counted twice.

---

### User Story 3 - Abstention When Evidence Is Insufficient (Priority: P2)

As a developer, I want the system to abstain when the knowledge base does
not contain enough information, so that I can trust it not to fabricate
answers from general knowledge.

**Why this priority**: Abstention is what makes the system honest about its
boundaries. It depends on evidence sufficiency signals (P1) and the
structured answer (P1), but is independently observable once those exist.

**Independent Test**: Ask a question outside the corpus (e.g., "What is the
average 5G speed in Japan?") and verify the system states that the available
information is insufficient instead of answering.

**Acceptance Scenarios**:

1. **Given** a question with no relevant evidence in the corpus, **When** a
   query runs, **Then** the system abstains and the response is marked as
   abstained.
2. **Given** a question where retrieved evidence is below the sufficiency
   threshold, **When** evidence sufficiency is assessed, **Then** the system
   abstains rather than answering from partial evidence.
3. **Given** a question where evidence is sufficient, **When** a query runs,
   **Then** the system answers with citations and does not abstain.
4. **Given** an answerable and an unanswerable question in the evaluation
   set, **When** evaluation runs, **Then** abstention correctness is scored
   for both.

---

### User Story 4 - Observable Grounded Pipeline in the CLI (Priority: P2)

As a developer, I want the CLI to show the full grounding path — evidence,
answer, citations, and citation-validation result — so that I can see where
a grounded-answer failure occurs.

**Why this priority**: Observability is the learning vehicle of the level.
It can be built independently of evaluation and depends only on the grounded
pipeline (P1) existing.

**Independent Test**: Run a query in debug mode and verify the output shows
retrieved evidence, the generated answer, the citations, and a PASS/FAIL
citation-validation result.

**Acceptance Scenarios**:

1. **Given** a normal query, **When** the answer is displayed, **Then** the
   supporting sources are shown alongside the answer.
2. **Given** a query in debug mode, **When** the run completes, **Then** the
   output shows retrieved evidence, generated answer, citations, and
   citation-validation status.
3. **Given** a query where the generation backend is unavailable, **When**
   the run fails, **Then** the user sees a clear error, and debug mode still
   shows the retrieved evidence gathered before the failure.
4. **Given** conflicting evidence in the retrieval result, **When** an
   answer is generated, **Then** the output acknowledges the conflict and
   names the differing sources instead of silently merging them.

---

### User Story 5 - Answer and Groundedness Evaluation (Priority: P3)

As a developer, I want an extended evaluation dataset and answer-level
metrics — correctness, groundedness, citation validity, citation
completeness, and abstention — so that I can measure whether grounding
actually improves and compare prompt strategies.

**Why this priority**: Evaluation proves the level's claims, but it depends
on the grounded pipeline, abstention, and validation (P1/P2) producing
answers to evaluate.

**Independent Test**: Run the evaluation suite over the extended dataset and
verify it reports each metric per test case, while Level 1 retrieval metrics
are still reported separately.

**Acceptance Scenarios**:

1. **Given** the extended evaluation dataset, **When** evaluation runs,
   **Then** each case reports answer correctness, groundedness, citation
   validity, citation completeness, and abstention outcome.
2. **Given** the dataset, **When** cases are inspected, **Then** it contains
   answerable, unanswerable, partial-evidence, and conflict questions, each
   with expected answer and relevant documents/chunks.
3. **Given** generated answers, **When** groundedness is evaluated, **Then**
   claims are classified as supported, unsupported, or partially supported.
4. **Given** the Level 1 retrieval metrics, **When** evaluation runs, **Then**
   Recall@K, Precision@K, and MRR are still available and reported
   separately from answer-level metrics.

---

### User Story 6 - Hallucination Tests, Experiments, and Regression Suite (Priority: P3)

As a developer, I want explicit hallucination and conflict scenarios,
prompt-strategy experiments, and a regression test for every discovered
failure, so that the test suite becomes a durable record of failure modes
and Level 1/0 behavior cannot silently break.

**Why this priority**: This hardens everything above into repeatable
knowledge. It depends on the grounded pipeline and evaluation existing, so
it is the last slice — but it is required for the level to be declared
complete.

**Independent Test**: Introduce a deliberate grounding defect (e.g., allow
unvalidated citations) and verify a regression test fails; then confirm the
full pre-existing suite still passes after all Level 2 changes.

**Acceptance Scenarios**:

1. **Given** hallucination scenarios (correct, incorrect, incomplete,
   conflicting, no evidence, unknown question), **When** tests run, **Then**
   each scenario has an explicit expected behavior and assertion.
2. **Given** prompt-strategy experiments, **When** results are recorded,
   **Then** each experiment documents the strategy, metrics measured, and
   which strategy performed best.
3. **Given** every discovered failure, **When** the suite grows, **Then** a
   regression test exists for it (unknown-question abstains, invalid
   citation rejected, unretrieved citation rejected, supported answer has
   citation, conflict reported, no external knowledge used).
4. **Given** all Level 2 changes, **When** the full suite runs, **Then**
   Level 0 and Level 1 regression tests still pass.
5. **Given** a failure, **When** it is analyzed, **Then** it is classified as
   a retrieval problem or a generation/grounding problem based on whether
   the correct evidence was retrieved.

---

### Edge Cases

- The generation backend returns malformed JSON or text instead of the
  structured answer → detected, reported as an error, not treated as an
  answer.
- The generation backend is unreachable or errors mid-query → clear error to
  the user; debug mode still shows evidence retrieved before failure.
- Retrieval returns zero evidence → evidence sufficiency fails and the
  system abstains without open-ended generation.
- The answer contains no citations for a factual response → flagged as
  incomplete citations.
- The answer abstains but still lists citations → handled deterministically
  (abstention takes precedence; inconsistent output is flagged).
- Retrieved documents contradict each other → conflict is surfaced in the
  answer, not merged.
- Duplicate citations, or citations with unknown/malformed identifier
  format → validator rejects or deduplicates deterministically.
- Evaluation cases marked unanswerable but the system answers → scored as
  abstention failure.

## Requirements *(mandatory)*

### Functional Requirements

**Evidence and grounding pipeline**

- **FR-001**: The system MUST represent every retrieved result as an
  explicit evidence object carrying at minimum: evidence ID, document ID,
  chunk ID, title, source, text, and retrieval score.
- **FR-002**: The system MUST include an evidence builder that transforms
  retrieval results into evidence objects while preserving IDs, metadata,
  and scores, and assigning stable, ordered evidence identifiers.
- **FR-003**: The generation prompt MUST clearly separate question,
  evidence, and instructions, and MUST instruct the model to use only the
  supplied evidence, avoid unsupported facts, avoid invented citations,
  cite supporting evidence, and state insufficiency when evidence is
  lacking.
- **FR-004**: The system MUST request and parse a structured answer
  containing at minimum: answer text, a list of citations (document ID and
  chunk ID), and an abstention indicator; malformed responses MUST be
  detected rather than silently accepted.
- **FR-005**: The generator MUST NOT access the vector store directly; it
  receives only the evidence built for the question.

**Citations**

- **FR-006**: Every factual answer based on retrieved knowledge MUST
  include citations identifying at least the document and chunk supporting
  each claim.
- **FR-007**: The system MUST validate every citation against the current
  retrieval result before returning an answer, rejecting citations to
  nonexistent documents, nonexistent chunks, or chunks not retrieved for
  the current question.
- **FR-008**: The validator MUST NOT perform retrieval itself; it verifies
  only against the evidence already retrieved for the question.
- **FR-009**: The system MUST keep citation validity (exists in retrieval
  result), citation correctness (supports the claim), and citation
  completeness (important claims are cited) as distinct, separately
  reported concepts.

**Abstention and evidence sufficiency**

- **FR-010**: The system MUST abstain with an explicit
  insufficient-information response when retrieved evidence cannot answer
  the question, and MUST mark the answer as abstained.
- **FR-011**: The system MUST make an explicit evidence-sufficiency
  decision using, at minimum, retrieval result count, similarity threshold,
  retrieval scores, prompt rules, and a structured model assessment of
  evidence sufficiency.
- **FR-012**: The system MUST NOT answer questions outside the knowledge
  base from the model's general knowledge.

**Observability**

- **FR-013**: The normal CLI output MUST display the answer together with
  its supporting sources.
- **FR-014**: A debug mode MUST display the full grounding path: retrieved
  evidence, generated answer, citations, and the citation-validation
  result (pass/fail with reasons).

**Evaluation**

- **FR-015**: The evaluation dataset MUST be extended with cases covering
  answerable, unanswerable, partial-evidence, and conflict questions; each
  case MUST include question, answerable flag, expected answer, relevant
  documents, and relevant chunks.
- **FR-016**: The system MUST evaluate, at minimum: answer correctness,
  groundedness of claims (supported / unsupported / partially supported),
  citation validity, citation completeness, and abstention correctness —
  implemented transparently in-repo rather than delegated to an external
  evaluation framework.
- **FR-017**: Level 1 retrieval metrics (Recall@K, Precision@K, MRR) MUST
  be preserved and reported as a separate layer from answer-level metrics;
  a retrieval score MUST NOT be treated as evidence of answer correctness.
- **FR-018**: The system MUST provide a failure-attribution procedure that
  classifies each failure as a retrieval problem or a generation/grounding
  problem based on whether the correct evidence was retrieved.
- **FR-019**: Conflicting evidence MUST be reported as a conflict in the
  answer (naming the differing sources) rather than merged into a single
  fact.

**Testing and documentation**

- **FR-020**: The test suite MUST cover: evidence model, answer schema
  parsing, citation validation (valid, invalid document, invalid chunk,
  unretrieved chunk, duplicates, missing), abstention, groundedness, answer
  evaluation, and grounded pipeline integration.
- **FR-021**: Every discovered failure MUST become a permanent regression
  test, including: unknown question abstains, invalid citation rejected,
  unretrieved citation rejected, supported answer carries citation,
  conflicting evidence reported, and answer does not use external
  knowledge.
- **FR-022**: Level 0 and Level 1 tests MUST continue to pass after all
  Level 2 changes.
- **FR-023**: Prompt-strategy experiments MUST be run and documented
  (simple RAG prompt; evidence-only; evidence-only + citation requirement;
  evidence-only + citation + abstention), measuring correctness,
  groundedness, citation validity, citation completeness, and abstention
  accuracy.
- **FR-024**: Experiment results and lessons learned MUST be documented in
  `docs/levels/level-02-grounded-rag/experiments.md` and
  `docs/levels/level-02-grounded-rag/lessons-learned.md`.
- **FR-025**: Hallucination scenarios MUST be explicitly tested: correct
  evidence, incorrect evidence, incomplete evidence, conflicting evidence,
  no evidence, and unknown question.

### Key Entities

- **Evidence**: An explicit representation of one retrieved chunk used to
  ground an answer; carries a stable evidence ID, originating document and
  chunk IDs, title, source, text, and retrieval score. The boundary
  between retrieval and generation.
- **Citation**: A reference from a claim in an answer to a specific
  document and chunk (optionally an evidence ID); validated for existence
  within the current retrieval result before the answer is returned.
- **Structured Answer**: The generated response as a validated object:
  answer text, citations, abstention indicator, and an evidence-sufficiency
  / groundedness indicator.
- **Evidence Sufficiency Decision**: The determination of whether
  retrieved evidence is sufficient to answer the question — distinct from
  whether retrieval succeeded.
- **Evaluation Case**: A dataset entry with question, answerable flag,
  expected answer, relevant documents, and relevant chunks; may be
  answerable, unanswerable, partial-evidence, or conflict type.
- **Claim Groundedness Verdict**: The per-claim classification of
  supported, unsupported, or partially supported relative to the retrieved
  evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of returned answers display their supporting sources,
  and 100% of displayed citations are validated against the actual
  retrieval result before display.
- **SC-002**: In 100% of the citation-hallucination test cases
  (nonexistent document, nonexistent chunk, unretrieved chunk), the
  invalid citation is detected and rejected or flagged.
- **SC-003**: On the evaluation dataset, the system abstains for at least
  90% of unanswerable questions while still answering at least 90% of
  answerable questions correctly.
- **SC-004**: Every test-case answer is scored on all five answer-level
  measures (correctness, groundedness, citation validity, citation
  completeness, abstention), with results reported as a complete matrix —
  no test case is left unmeasured.
- **SC-005**: Level 1 retrieval metrics (Recall@K, Precision@K, MRR)
  remain available and unchanged in meaning after the Level 2 upgrade, and
  are reported separately from answer-level metrics.
- **SC-006**: 100% of the pre-existing Level 0 and Level 1 test suite
  passes after all Level 2 changes, and every newly discovered failure has
  a regression test.
- **SC-007**: For 100% of evaluation failures, the team can state whether
  the root cause was retrieval or generation/grounding using the documented
  attribution procedure.
- **SC-008**: All six hallucination scenarios (correct, incorrect,
  incomplete, conflicting, no evidence, unknown question) have explicit
  automated tests with defined expected behavior.
- **SC-009**: Four prompt strategies are compared on the same dataset with
  all five answer-level measures, and the winning strategy is documented
  with its results.

## Assumptions

- The feature builds on the existing Level 1 system; ingestion, chunking,
  embedding, vector storage, retrieval configuration, and retrieval metrics
  are reused unchanged rather than replaced.
- The synthetic Telco markdown corpus remains the knowledge base; no new
  documents are required beyond what is needed for conflict and
  partial-evidence test cases.
- The same LLM gateway used in Level 1 is used for generation, structured
  answer output, and (where needed) structured assessment of evidence
  sufficiency and claim groundedness.
- Answer-level evaluation logic is written directly in the repository with
  transparent rules; where a model-based judge is used for groundedness, it
  is treated as an external dependency and isolated from deterministic
  unit tests.
- The command-line interface remains the only user interface; no web UI,
  REST API, or agent behavior is introduced.
- Prompt-strategy experiments may require live model calls; their results
  are recorded in documentation, while automated tests assert behavior
  through deterministic logic and controlled fixtures.
- Level 2 does not introduce new frameworks, evaluation products, or
  infrastructure beyond the existing stack, and does not add advanced
  retrieval techniques (hybrid search, reranking, query rewriting) —
  consistent with the constitution's framework and out-of-scope rules.
- Citation format starts as `document_id:chunk_id` identifiers and MAY be
  refined later without changing the requirement that citations map to real
  retrieved evidence.
