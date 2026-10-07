# Level 2 Grounded RAG — Lessons Learned (US6, T037)

Status: recorded after the deterministic experiment baseline
(`docs/levels/level-02-grounded-rag/experiments.md`, T036) and the named
regression + hallucination scenarios (T034/T035). Claims marked *"to be
measured live"* are not asserted by any test (R8): they require
`--oracle llm` and are recorded evidence, never assertions.

---

## 1. What causes an unsupported answer?

An answer claim is UNSUPPORTED when the claim's tokens are not covered by
the evidence retrieved for the question (lexical baseline) or when a model
judge disagrees. Two distinct failure origins, both already observable in
the deterministic setup:

1. **Missing evidence (retrieval problem).** The truth is in the corpus but
   the right chunk was not retrieved; no amount of prompt craft helps.
   Detectable by checking the relevant_chunks/documents of the case against
   the retrieved evidence.
2. **Generation drift (grounding problem).** The right evidence was
   retrieved but the generator added a sentence it can't support. The
   token-overlap baseline and the `GroundednessJudge` interface exist
   precisely to name this; `test_hallucination_scenario_unsupported_extra_claim_detected`
   pins the detector.

Deterministic baseline signal: with the extractive CopyOracle, 0
unsupported claims appeared, because the generator never invents text —
evidence-only generators cannot hallucinate by construction. Unsupported
claims are therefore a *generation* signature, not a retrieval one.

## 2. High score ≠ grounded

A high correctness score only means the expected answer's tokens appeared;
it says nothing about whether the model saw the evidence. Two cases from
the deterministic run illustrate the disambiguation:

- `lte_slow_troubleshooting` (partial): correctness 0.6 because the
  expected answer wants more than the retrieved evidence alone delivers —
  correctness and groundedness measure different things.
- An answer could be word-for-word correct *and* fully supported by
  evidence, yet still be a retrieval miss if the supporting chunk was never
  retrieved (the evidence came from a source that happens to agree).

Litmus test: **drop the evidence** and re-ask. If the answer survives, the
model used external knowledge — a grounding violation (FR-003/FR-021),
regardless of the score.

## 3. Citation-invention rate

Fabricated citations (nonexistent document, chunk under another document,
or a chunk that was never retrieved) are rejected by the validator
(`UNKNOWN_DOCUMENT` / `UNKNOWN_CHUNK` / `NOT_RETRIEVED`) with 100% coverage
in `test_citations.py` (SC-002). The *rate* at which a live model invents
them is a prompt-strategy effect that is **to be measured live** (R8):
strategy C/D explicitly forbid invented citations, so the delta between
B (say-nothing) and C/D is the observable prompt-only effect on
invention rate. Until that live run, the honest posture is: the validator
guarantees no invented citation is ever displayed, so the user-visible risk
is bounded regardless of the underlying rate.

## 4. Is prompt-only fix effectiveness real?

The four strategies A-D change only prompt emphasis; they change **no
enforcement**. In this build the actual grounding guarantees come from
enforced structure (schema + validation) and the citation validator, not
from appealing to the model. Deterministic baseline: delta between A-D is
0.00 on every measure — a scripted generator cannot be "convinced" by a
prompt. Any observable live-model delta between A-D is the genuine
prompt-only effect and **must be measured live** (SC-009); the reproducible
corollary is that prompt wording is the *weakest* lever in the stack.

## 5. False abstentions

Abstention is triggered by (a) zero/insufficient retrieval evidence or
(b) the model reporting insufficient evidence. False abstentions (the
answer was knowable) come from two places in this design:

- **Threshold tuning** (`min_evidence`, `sufficiency_threshold`): an overly
  aggressive sufficiency rule abstains even when good evidence exists. The
  `EvidenceSufficiencyDecision` exposes the explicit reason, so a false
  abstention is diagnosable at a glance (`--debug-grounding`).
- **Retrieval miss** (see #1): abstaining because the right chunk was never
  retrieved is a retrieval-class failure, not an abstention-logic failure.

The unanswerable case (`average_5g_speed_japan`, empty corpus scope) scores
abstention as 1.0 only when the system truly abstains — the eval dataset
keeps the *expected* behavior explicit, so false abstentions are tracked,
not assumed.

## 6. Incomplete citations

Flagged `INCOMPLETE_CITATIONS` whenever a factual (non-abstained) answer
carries fewer than one VALID citation. The deterministic oracle keeps
citation completeness at 1.00 (it cites every retrieved chunk by
construction); the regression suite pins the rule
(`test_hallucination_scenario_missing_citation_flagged`,
`test_supported_answer_has_citation`). Real-world incomplete citations are
therefore again a *generation* signature: proof that the generator produced
claims it did not associate with evidence.

## 7. Failure attribution: retrieval vs generation/grounding (FR-018)

**Procedure** — every failure is classified with this decision tree, based
on whether the correct evidence was retrieved (`relevant_chunks` /
`relevant_documents` are the ground truth):

```
Q: Was the correct evidence retrieved for this question?
  NO  -> RETRIEVAL PROBLEM
         Fix the corpus/embedder/retriever/top-K/threshold.
         Do NOT change the prompt or generator.
  YES -> Was the answer correct?
          YES -> Was it grounded (claims supported, citations VALID)?
                 YES -> no failure (case passes)
                 NO  -> GROUNDING PROBLEM (claims unsupported / citations
                        invalid): fix prompt grounding rules, generator,
                        or judge thresholds.
          NO  -> Is the answer an abstention?
                 YES -> FALSE ABSTENTION (abstention tuning / judge over-
                        strictness), a GROUNDING-class failure.
                 NO  -> GENERATION PROBLEM (wrong content despite right
                        evidence): prompt content, model choice, or
                        expected_answer too narrow.
```

Operational the debug blocks deliver the evidence for attribution:
`--debug-grounding` shows Retrieved Evidence, Evidence sufficiency,
Generated Answer, Citations + Validation, Conflicts, Final Response —
enough to locate which layer failed before touching any code.

**Classification rule (FR-018):** a failure is a *retrieval problem* when
the correct evidence was not retrieved; otherwise it is a
*generation/grounding problem*. The two-layer evaluation output enforces
this separation operationally (Principle XXII) by keeping the retrieval
block and the answer block as distinct labeled layers, so a low retrieval
score and a low answer score point at different owners.