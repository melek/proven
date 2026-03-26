# SLR-Informed Issues for Proven

## Context

A systematic literature review on *formal verification and runtime monitoring of operational procedures in safety-critical systems* (98 papers, 6 themes) was completed via Stepwise on 2026-03-25. The review identified several gaps that Proven directly addresses — and areas where the literature suggests Proven's novel contribution (specification quality optimization) can deepen.

**Proven's role:** Reference prototype and idea store for UIDI's proof factory. These issues strengthen Proven's research value rather than expanding it into a production tool.

**Filtering axioms:** All accepted issues must be deterministic-first, not add inference points, be compatible with the resumable pipeline, and extend the "specification quality is optimizable" thesis or apply Proven's own methodology to itself.

## Accepted Issues

### A. Quantifier Complexity Metric for Spec Quality Measurement

**SLR grounding:** Theme 3.2.6 (specification engineering). The review finds "evaluation of specification quality beyond syntactic correctness is underdeveloped."

**Problem:** `decompose.py` applies rewrites but doesn't measure the resulting spec quality. Success is determined downstream when Z3 either proves or doesn't. There is no way to correlate spec features with verification outcomes without re-running the full pipeline.

**Proposal:** A lightweight, deterministic metric computed before and after Stage 2.5: quantifier depth, existential count, clause redundancy score, total specification surface area. Emitted alongside the preprocessed spec.

**Axiom alignment:**
- Zero LLM calls — pure static analysis of Dafny AST
- Extends "spec quality is optimizable" with measurability
- Produces artifacts UIDI's proof factory can inherit as quality signals

### B. Trace-Informed Rewrite Rule Discovery

**SLR grounding:** Theme 3.2.6 (automated specification synthesis). Raha et al. on SMT-based synthesis from traces; Gaglione et al. on inferring LTL from noisy data.

**Problem:** The ~21 rewrite functions in `decompose.py` were hand-authored. The 216 ablation runs contain a corpus of "what went wrong" — Z3 failure patterns, stuck detection triggers, verification error messages — that hasn't been systematically mined.

**Proposal:** An analysis pass over existing `interaction_log.jsonl` files from failed verification attempts. Identify recurring Z3 failure patterns and propose candidate deterministic rewrite rules. The analysis itself may use inference; the resulting rules must be deterministic.

**Axiom alignment:**
- Output is deterministic rewrite rules (same as existing decompose.py)
- Extends the core thesis: specification quality is optimizable, and the optimization surface is discoverable
- Uses existing pipeline artifacts (interaction logs), no new infrastructure

### C. Assurance-Level Taxonomy for Pipeline Output

**SLR grounding:** Section 4.1 (the assurance spectrum). SQ3 answer: the corpus reveals proven/validated/monitored/tested as a spectrum, not a binary.

**Problem:** Proven currently has a binary outcome: Stage 4 succeeds (all methods verified) or fails. But partial success is real — a spec might verify 6/8 methods. Downstream consumers (including UIDI) get no structured signal about what was and wasn't proved.

**Proposal:** Emit a structured assurance report after Stage 4: per-method verification status, which postconditions were discharged, which failed, and the assurance level (proven, partially-proven, unverified). Derived entirely from Dafny's verification output.

**Axiom alignment:**
- Deterministic — parsed from Dafny's own error/success output
- Resumable — enriches run_state.json with finer-grained status
- Feeds UIDI's proof factory with per-contract assurance signals

### D. Postcondition Assertions on Stage Transitions

**SLR grounding:** Theme 3.2.1 (model checking of procedural logic). Section 4.1 granularity gap finding: step-level verification of operational procedures is underrepresented.

**Problem:** `pipeline.py` sequences stages but doesn't formally assert the contract between them. Stage 2 promises "valid Dafny spec with no method bodies." Stage 2.5 promises "semantically equivalent spec with fewer verification obstacles." Stage 3 promises "same spec signatures, bodies added." These properties are assumed, not checked.

**Proposal:** Python assertions after each stage transition that verify the output conforms to the stage's contract:
- Post-Stage 2: spec parses, no method bodies present
- Post-Stage 2.5: same method signatures as input, spec still parses
- Post-Stage 3: same method signatures as spec, bodies present
- Post-Stage 4: all methods verified or failure recorded with per-method status
- Post-Stage 5: output file exists and compiles in target language

**Axiom alignment:**
- Eat your own cooking — Proven enforcing procedural correctness on itself
- Deterministic — structural checks on Dafny source text
- Step-level verification of Proven's own operational procedure

### E. Spec Drift Detection as a Formal Pipeline Invariant

**SLR grounding:** Section 4.1 (convergence toward hybrid approaches). Assurance case literature on through-life safety argument maintenance (Denney & Pai, Calinescu et al.).

**Problem:** The mentor system detects spec drift as a stuck-detection heuristic in Stage 4 ("model removed specification clauses"). But spec drift can occur at any LLM-touching stage (2, 3, 4), and the detection is reactive rather than preventive.

**Proposal:** Promote spec drift detection to a pipeline-wide invariant: the set of `requires`/`ensures` clauses is captured after Stage 2 and monotonically checked across all subsequent stages. Any clause removal must be explicitly justified (e.g., mentor-recommended relaxation with logged rationale). Silent contract disappearance fails the pipeline.

**Axiom alignment:**
- Contracts don't silently disappear — same discipline Proven asks Dafny to enforce
- Deterministic — clause set comparison via text/AST matching (note: shares parsing concerns with Issue A; coordinate to avoid duplicate AST work)
- Strengthens audit trail for UIDI inheritance

## Excluded Ideas

These ideas emerged from the SLR analysis but fall outside Proven's axioms or scope. Filed as a single tracking issue to preserve the reasoning.

### Runtime Monitoring of Compiled Output

The SLR's strongest cross-cutting finding is that hybrid approaches (static proof + runtime monitoring) are the most practical path to verified procedural execution. Emitting runtime assertions in Stage 5 output (e.g., precondition checks at module boundaries in compiled Python/Go) would extend Dafny's guarantees to the boundary where they end — external inputs, network calls, filesystem interactions.

**Why excluded:** Changes downstream artifacts that belong to the user's requirements, not Proven's. Dafny's compilation guarantees semantic preservation; adding assertions to the output is a feature of the *consuming system*, not the pipeline.

**Where it belongs:** UIDI's proof factory, where the consuming system is controlled. Or as an opt-in Stage 5.5 in a future Proven version if there's demand.

### Pattern Extraction for UIDI

Each of Proven's architectural patterns (bounded retry with stuck detection, deterministic preprocessing before inference, mentor as perspective shift, rollback with guidance) could be evaluated against SLR evidence and tagged for UIDI adoption/adaptation/discard.

**Why excluded:** This is UIDI work wearing a Proven hat. The issues belong in UIDI's tracker as Phase 4 decision points.

**Where it belongs:** UIDI Phase 4 planning, informed by the SLR briefing already filed.

### Verification-as-a-Service Organizational Pattern

The CERN PLCverif model (formal verification expertise provided externally to teams that lack it) maps to what Proven does: non-experts write English, Proven handles verification machinery.

**Why excluded:** Organizational/deployment concern, not a code issue. Proven already *is* this pattern — the issue would be documentation, not implementation.

**Where it belongs:** Proven's README or paper framing. Cite Lopez-Miguel et al. 2025 for positioning.

### LLM-Assisted Specification Improvements

The SLR cites Endres et al. (LLMs translating informal specs to formal postconditions) and Ma et al. (Req2LTL at 88.4% accuracy). Improving Stage 2's LLM prompts based on this literature could raise spec quality at the inference layer.

**Why excluded:** Adds or modifies inference points. Proven's thesis is that deterministic preprocessing (Stage 2.5) is the higher-leverage intervention. Prompt improvements are legitimate but should be evaluated empirically against new decompose.py rules (Issue B) to avoid conflating effects.

**Where it belongs:** Research experiment — a new ablation condition testing improved Stage 2 prompts vs. new Stage 2.5 rewrites, to measure where the quality gain actually comes from.
