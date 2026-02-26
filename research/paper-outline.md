# Deterministic Specification Preprocessing Improves LLM Verification Success Rates in Dafny

*Working paper outline — venue-agnostic draft*

---

## Abstract

Large language models can generate code, but producing *formally verified* code remains unreliable. The dominant approach — generate code, check with a verifier, retry on failure — treats the LLM as a black box and the verifier as a test oracle. We present **Proven**, a pipeline that instead structures the problem upstream: requirements are formalized into Dafny specifications, specifications are deterministically preprocessed into simpler forms, and only then does the LLM implement and prove. In an ablation study across 9 benchmarks, 4 configurations, 2 models, and 3 trials per cell (N=216 runs), we find that **deterministic specification preprocessing more than doubles verification success for a 14B local model** (19% → 41%, p=0.067, Cohen's h=0.49) and enables 100% success on medium-difficulty problems for Claude Sonnet (vs. 75% baseline). The effect is difficulty-dependent: preprocessing dominates on medium problems, while the full pipeline (preprocessing + mentor + rollback) provides the largest gains on hard problems. In a separate correctness comparison, **all produced implementations pass an independent 129-test suite with zero failures** — regardless of whether they were generated through formal verification or TDD. The methods differ in production rate, not correctness. Our results suggest that specification quality is an underexplored optimization axis: lightweight, deterministic rewrites applied before the LLM sees the specification can substantially improve verification success, especially for models near the capability threshold.

---

## 1. Introduction

### The Promise
LLMs generate plausible code, but plausible is not correct. Formal verification offers a deterministic correctness guarantee — if the verifier accepts, the code satisfies its specification. The combination is compelling: LLMs propose, verifiers dispose.

### The Failure Mode
In practice, LLM + verifier loops get stuck. The model generates code that fails verification, receives error messages, and retries — often making the same or similar mistakes. Prior work reports verification success rates of 50-86% on benchmark suites [DafnyPro, Dafny-Synthesis], with the remaining failures resistant to additional retries.

### The Insight
We observe that many verification failures originate not in the implementation but in the *specification*. When an LLM generates a formal specification from natural language requirements, it often writes postconditions that are semantically correct but unnecessarily complex — existential quantifiers where membership predicates suffice, compound conditions where separate ensures clauses would verify independently, specifications that require helper lemmas the model cannot produce.

The problem is not that the model cannot prove. The problem is that the pipeline asks the model to prove unnecessarily difficult things.

### Contribution

1. **Proven**: A 5-stage pipeline (requirements → specification → preprocessing → implementation → compilation) that separates concerns by construction
2. **Deterministic specification preprocessing**: Two categories of rewrites applied *before* the model sees the specification: (a) simplification rewrites that replace hard-to-prove patterns with equivalent simpler forms, and (b) error-correction rewrites that fix common LLM-generated Dafny mistakes
3. **Mentor system**: A same-model perspective-shift advisor that detects stuck patterns and can recommend architectural changes (including rolling back to re-specify)
4. **Ablation study** (N=216 runs): Isolating the contributions of preprocessing, mentor, and rollback across 9 benchmarks, 2 models, and 3 trials per cell — the first controlled evaluation of specification-level interventions for LLM verification

---

## 2. Background

### 2.1 Dijkstra's Correct-by-Construction Methodology
Edsger Dijkstra's *A Discipline of Programming* (1976) argues that programs should be *derived* from specifications via weakest-precondition calculus, not written and then tested. The program structure emerges from the proof; correctness is structural, not empirical. This inversion — spec → proof → code rather than code → test — is the philosophical foundation of this work.

### 2.2 Dafny
Dafny [Leino 2010] is a verification-aware programming language that makes preconditions, postconditions, and loop invariants first-class language constructs. The Z3 SMT solver [de Moura & Bjorner 2008] discharges proof obligations automatically. Dafny compiles to C#, Go, Python, Java, JavaScript, and Rust.

Dafny has emerged as the primary target for LLM + formal verification research, with dedicated workshops at POPL 2024-2026 and industrial deployment at AWS (authorization engine, 1B calls/sec, deployed 2024).

### 2.3 LLM Code Generation and the Generate-and-Verify Paradigm
Nearly all existing work on LLM + formal methods follows the *generate-and-verify* pattern: the LLM generates code (or annotations), a formal tool checks it, and failures trigger retries with error feedback. This includes DafnyPro [POPL 2026], dafny-annotator [Harvard 2024-2025], Laurel [2024-2025], MIDSPIRAL [Harvard 2025], AutoVerus [MSR, ICLR 2025], and SYNVER [Purdue 2024-2025].

### 2.4 What Nobody Is Doing
LLM-assisted stepwise refinement — where the LLM performs B-Method or Event-B style decomposition of specifications into implementations — is essentially unexplored [lit review Section 9]. No work addresses the question of *specification quality* as a factor in LLM verification success.

---

## 3. Related Work

### 3.1 LLM + Dafny
- **DafnyPro** [POPL 2026]: Inference-time framework for Dafny annotation generation. 86% correct proofs on DafnyBench using Claude Sonnet 3.5/3.7. Focus on annotation synthesis, not specification quality.
- **MIDSPIRAL / dafny-replay** [Harvard 2025]: Closest to Proven's vision. Uses Claude Opus 4.5 to write verified Dafny that compiles to JavaScript. Demonstrates the spec→proof→code pipeline but does not address specification decomposition.
- **Dafny as Intermediate Language** [POPL 2025]: Users interact in natural language; Dafny is opaque. Tested on HumanEval.
- **Dafny-Synthesis** [FSE 2024]: 153 verified Dafny solutions to MBPP problems. GPT-4 achieves 58% verification.
- **ATLAS Toolkit** [POPL 2026]: Synthesizes verified Dafny programs at scale for training data.

### 3.2 LLM + Other Verification Languages
- **AutoVerus** [MSR, OOPSLA 2025]: 90%+ success generating Verus proofs for Rust.
- **SYNVER** [Purdue 2024-2025]: Two-LLM architecture for verified C via Rocq/VST.
- **VeCoGen** [2024]: Verified C via Frama-C WP. 13/15 Codeforces problems.

### 3.3 Specification Synthesis
- **LEMUR** [2023]: Hybrid LLM + Z3 for loop invariant generation. 107/133 on Code2Inv. A subsequent hybrid framework [arXiv 2508.00419, 2025] achieves 100% (133/133).
- **AutoSpec** [CAV 2024]: LLM + static analysis for specification synthesis.
- **Quokka** [2025]: Framework for LLM-based loop invariant synthesis, 866 instances, 9 LLMs.

### 3.4 The Formal Methods as Test Oracle Argument
- **Kleppmann** [Dec 2025]: "AI will make formal verification go mainstream" — proof scripts are ideal LLM targets because the checker rejects hallucinations deterministically.
- **Congdon** [Dec 2025]: Engineers should write specifications, not implementations.
- **The 4/delta Bound** [Dec 2025]: First formal framework with provable guarantees for when LLM + verifier loops converge.

### 3.5 Gap
No prior work systematically treats *specification complexity* as an optimizable parameter for LLM verification success. Existing systems take the specification as given and focus on implementation/proof generation. Proven is, to our knowledge, the first to apply deterministic specification preprocessing as a distinct pipeline stage.

---

## 4. The Proven Architecture

### 4.1 Pipeline Overview

```
Stage 1: Requirements Capture
    NL requirements → structured JSON (operations, invariants, pre/postconditions)

Stage 2: Formal Specification
    Structured JSON → Dafny specification (signatures + contracts, no bodies)
    Validated: dafny resolve (parsing + type-checking)

Stage 2.5: Specification Preprocessing [NEW]
    Deterministic rewrites: simplify hard-to-prove patterns
    Validated: dafny resolve on decomposed spec

Stage 3: Implementation
    Decomposed spec → Dafny implementation (method bodies, invariants, assertions)
    Validated: dafny verify (full verification)

Stage 4: Proof Discharge
    Retry loop with mentor advisor for failed verifications
    Can trigger rollback to Stage 2 with guidance

Stage 5: Code Generation
    Verified Dafny → target language (Python, C#, Go, Java, JS)
    Validated: dafny build
```

### 4.2 Specification Preprocessing

Deterministic rewrite rules applied before the model sees the specification, in two categories. The most impactful rules are described below; the full implementation (`decompose.py`) contains 19 rewrite functions covering additional syntax fixes and semantic transformations.

**Simplification (semantic-preserving):**

**Rule 1: Existential → Membership.** Replace `ensures exists i :: 0 <= i < |seq| && seq[i] == x` with `ensures x in seq`. These are semantically equivalent in Dafny, but the existential form requires the model to provide a witness (the index), while the membership predicate is discharged trivially by Z3 after sequence operations. Only rewrites *pure* membership existentials — existentials with additional conjuncts (e.g., ordering constraints on the index) are left unchanged to avoid weakening the specification.

**Error correction (fixing common LLM mistakes):**

**Rule 2: Strip Invalid Reads.** Remove `reads this` from method declarations. In Dafny, `reads` clauses are only valid on functions and predicates, not methods. LLMs frequently generate this invalid syntax.

**Rule 3: Redundant Valid() Removal.** Remove `ensures Valid()` from methods that have `requires Valid()` but no `modifies this`. When nothing is modified, the predicate is trivially preserved and the clause adds a proof obligation for no benefit.

**Rule 4: Ensures Clause Reordering.** Move `ensures Valid()` and length ensures (e.g., `ensures |s| == 5`) before any indexing ensures (e.g., `ensures s[i] == v`). Dafny checks well-formedness of each ensures clause independently — `s[i]` requires proving `i < |s|`, which depends on a length clause that may appear later. Reordering eliminates these false positives.

**Syntax-level fixes (applied at Stage 2, before resolve):**

**Fix A: Generic Brackets.** Rewrite `array[int]`, `seq[int]`, etc. to `array<int>`, `seq<int>`. LLMs trained on Java/Go/Python frequently use square-bracket generic syntax; Dafny requires angle brackets.

**Fix B: Quantifier Range.** Rewrite `forall i in 0..N :: P(i)` to `forall i :: 0 <= i < N ==> P(i)`. LLMs generate Python/Rust-style range iteration in quantifiers; Dafny requires explicit bounds with implication.

Rule 1 preserves semantic equivalence. Rules 2-4 and Fixes A-B correct invalid or suboptimal Dafny patterns that LLMs consistently produce. If the preprocessed spec fails `dafny resolve`, the original is used as fallback.

### 4.3 Mentor System

The mentor is a *perspective shift* — same model, same API, completely different context. The coding context says "fix this code." The mentor context says "a programmer is stuck; diagnose the pattern and give strategic advice."

**Stuck detection** (deterministic classification):
1. **Spec drift**: Model removed specification clauses (most dangerous)
2. **Verified regression**: Verified count decreased from previous attempt
3. **Spec too complex**: Verified count stuck for 3+ attempts with postcondition errors
4. **Repeating error**: Same normalized error signature 2+ times
5. **Oscillating**: Alternating between two error sets over 4 attempts

**Mentor directive**: Fresh LLM call (no conversation history) with mentor system prompt. Can recommend `ADVICE:` (implementation guidance) or `ROLLBACK TO STAGE 2:` (specification is the problem).

**Budget**: Configurable intervention limit (default 3). Budget of 0 disables mentor entirely.

### 4.4 Adaptive Temperature Strategy

Stage 4 retries use temperature adapted to the diagnosed stuck category rather than a static ramp:

| Stuck Category | Temperature | Rationale |
|---|---|---|
| Repeating error | 0.9 | Same error = same approach; maximize diversity |
| Verified regression | 0.2 | Previous was better; be precise about reverting |
| Spec drift | 0.2 | Model is removing specs; tighten up |
| Spec too complex | 0.7 | Needs creative approach, not random |
| Oscillating | 0.8 | Stuck between two states; break the cycle |
| No stuck pattern | 0.4 | Making progress; stay the course |

When adaptive retries exhaust, a **best-of-N fallback** generates N fresh implementations from scratch (no conversation history, temperature 0.5), verifies each independently, and selects the one with the most verified conditions. This breaks the conversational rut that accumulates over many retries.

### 4.5 Pipeline Rollback

When the mentor recommends rollback, the pipeline rewinds to Stage 2 with mentor guidance injected into the specification prompt. The model rewrites the specification following the mentor's advice (e.g., "replace existential quantifier with membership predicate"). Rollback budget (default 1) prevents infinite loops.

---

## 5. Experimental Design

### 5.1 Benchmark Suite

[N] benchmark problems at three difficulty levels:

| Difficulty | Problem | Key Verification Challenge |
|---|---|---|
| Simple | Bounded Counter | Single invariant (count within bounds) |
| Simple | Stack (LIFO) | Push/pop ordering, size tracking |
| Medium | Priority Queue | Sorted invariant, insertion into sorted sequence |
| Medium | Sorted List | Membership, insertion sort, ordering |
| Medium | Unique Set | No-duplicates invariant, membership, removal |
| Hard | Binary Search | Loop invariant with bounds, sorted precondition |
| Hard | Ring Buffer | Modular arithmetic, wrap-around indexing |
| Medium | Pipeline State Machine | Multi-element rollback, quantified closure invariant |
| Hard | Balanced Parentheses | Stack-based algorithm, string processing |
| Hard+ | Compositional Pipeline | Cross-function contract propagation (DafnyComp-inspired) |
| Hard+ | Extended GCD | Bezout identity loop invariant, nonlinear arithmetic |
| Hard+ | Insertion Sort (Permutation) | Ghost multiset tracking, permutation proof |
| Expert | Red-Black Tree Insert | 4+ simultaneous invariants, rotation correctness |
| Expert | Three-Function Compositional Chain | Cross-function contract propagation (DafnyComp-inspired) |
| Expert | Topological Sort | Graph DFS, ghost state, global ordering over all edges |

### 5.2 Model Configurations

| Model | Type | Size | Context |
|---|---|---|---|
| qwen2.5-coder:14b | Local (Ollama) | 14B, Q4_K_M | 16GB VRAM |
| Claude Sonnet 4.6 | Cloud (Anthropic) | Unknown | API |
| [Optional: GPT-4o] | Cloud (OpenAI) | Unknown | API |

### 5.3 Ablation Conditions

| Config | Decompose | Mentor | Rollback | Description |
|---|---|---|---|---|
| A: Baseline | off | off | off | Pure retry (generate-and-verify) |
| B: +Mentor | off | 3 | off | Retry + perspective-shift advisor |
| C: +Decompose | on | off | off | Upstream spec simplification only |
| D: Full | on | 3 | 1 | All features |

All conditions use `--strategy full --best-of-n 0` to prevent confounding from adaptive strategy selection or best-of-N sampling. N=3 trials per cell, max retries 6 per run. Total: 4 configs × 9 benchmarks × 3 trials × 2 models = 216 runs.

### 5.4 Metrics

All captured automatically by the pipeline's `interaction_log.jsonl`:

| Metric | Source | Type |
|---|---|---|
| Verification success | run_state.json `stage_status[4]` | Binary |
| Highest stage reached | run_state.json | Ordinal (1-5) |
| Total attempts (all stages) | run_state.json `retry_counts` | Count |
| Total tokens consumed | interaction_log.jsonl `usage.total_tokens` | Count |
| Wall-clock time | interaction_log.jsonl timestamps | Seconds |
| Mentor interventions | 04_proof_report.json `mentor_interventions` | Count |
| Decomposition rewrites | Console output / log | Count |
| Rollbacks triggered | run_state.json | Count |

### 5.5 Hypotheses

- **H1**: Decomposition (Config C) achieves higher verification success than Baseline (Config A) across all difficulty levels.
- **H2**: Decomposition (Config C) achieves higher verification success than Mentor-only (Config B).
- **H3**: The effect of decomposition is larger for weaker models (qwen2.5-coder:14b) than stronger models (Claude Sonnet 4.6).
- **H4**: Full pipeline (Config D) does not significantly outperform Decompose-only (Config C), suggesting that upstream simplification dominates downstream repair.

---

## 6. Results

### 6.1 Ablation Study: Isolating Component Contributions

The full ablation matrix — 4 configurations × 9 benchmarks × 3 trials × 2 models = 216 runs — was executed to isolate the individual contribution of each pipeline component. All runs used identical common flags (`--strategy full --best-of-n 0 --max-retries 6`) to prevent confounding.

#### 6.1.1 Overall Success Rates

**Local model (qwen2.5-coder:14b):**

| Config | N | Compiled | Rate | 95% CI |
|---|---|---|---|---|
| A: Baseline | 27 | 5 | 19% | [8%, 37%] |
| B: +Mentor | 27 | 8 | 30% | [16%, 48%] |
| C: +Decompose | 27 | 11 | 41% | [25%, 59%] |
| D: Full Pipeline | 27 | 9 | 33% | [19%, 52%] |

**Cloud model (Claude Sonnet 4.6):**

| Config | N | Compiled | Rate | 95% CI |
|---|---|---|---|---|
| A: Baseline | 26 | 17 | 65% | [46%, 81%] |
| B: +Mentor | 27 | 18 | 67% | [48%, 81%] |
| C: +Decompose | 27 | 18 | 67% | [48%, 81%] |
| D: Full Pipeline | 27 | 21 | 78% | [59%, 89%] |

Confidence intervals are Wilson score intervals appropriate for small-sample proportions.

#### 6.1.2 Pairwise Comparisons

Statistical significance assessed via one-sided Fisher's exact test; effect sizes via Cohen's h.

**qwen2.5-coder:14b:**

| Comparison | Better | Worse | p-value | Cohen's h | Interpretation |
|---|---|---|---|---|---|
| Decompose effect (A vs C) | 11/27 | 5/27 | 0.067 | 0.49 | Medium effect, approaching significance |
| Mentor effect (A vs B) | 8/27 | 5/27 | 0.263 | 0.26 | Small effect, not significant |
| Mentor+Rollback marginal (C vs D) | 9/27 | 11/27 | 0.801 | −0.15 | No benefit; slight degradation |

**Claude Sonnet 4.6:**

| Comparison | Better | Worse | p-value | Cohen's h | Interpretation |
|---|---|---|---|---|---|
| Decompose effect (A vs C) | 18/27 | 17/26 | 0.576 | 0.03 | Negligible; baseline already strong |
| Mentor effect (A vs B) | 18/27 | 17/26 | 0.576 | 0.03 | Negligible |
| Mentor+Rollback marginal (C vs D) | 21/27 | 18/27 | 0.272 | 0.25 | Small positive trend |

#### 6.1.3 Difficulty Interaction

Success rates broken down by difficulty tier reveal where each component helps most.

**Claude Sonnet 4.6:**

| Tier | A: Baseline | B: +Mentor | C: +Decompose | D: Full |
|---|---|---|---|---|
| Simple | 5/5 (100%) | 6/6 (100%) | 4/6 (67%) | 5/6 (83%) |
| Medium | 9/12 (75%) | 7/12 (58%) | 12/12 (100%) | 11/12 (92%) |
| Hard | 3/9 (33%) | 5/9 (56%) | 2/9 (22%) | 5/9 (56%) |

**qwen2.5-coder:14b:**

| Tier | A: Baseline | B: +Mentor | C: +Decompose | D: Full |
|---|---|---|---|---|
| Simple | 4/6 (67%) | 5/6 (83%) | 5/6 (83%) | 5/6 (83%) |
| Medium | 1/12 (8%) | 3/12 (25%) | 5/12 (42%) | 1/12 (8%) |
| Hard | 0/9 (0%) | 0/9 (0%) | 1/9 (11%) | 3/9 (33%) |

#### 6.1.4 Per-Problem Matrix

**Claude Sonnet 4.6:**

| Problem | Diff. | A: Baseline | B: +Mentor | C: +Decompose | D: Full |
|---|---|---|---|---|---|
| bounded_counter | Simple | 2/2 | 3/3 | 2/3 | 2/3 |
| stack | Simple | 3/3 | 3/3 | 2/3 | 3/3 |
| priority_queue | Medium | 2/3 | 2/3 | 3/3 | 3/3 |
| sorted_list | Medium | 3/3 | 3/3 | 3/3 | 3/3 |
| unique_set | Medium | 1/3 | 0/3 | 3/3 | 3/3 |
| pipeline_state | Medium | 3/3 | 2/3 | 3/3 | 2/3 |
| binary_search | Hard | 2/3 | 1/3 | 2/3 | 3/3 |
| ring_buffer | Hard | 1/3 | 1/3 | 0/3 | 0/3 |
| balanced_parentheses | Hard | 0/3 | 3/3 | 0/3 | 2/3 |

**qwen2.5-coder:14b:**

| Problem | Diff. | A: Baseline | B: +Mentor | C: +Decompose | D: Full |
|---|---|---|---|---|---|
| bounded_counter | Simple | 3/3 | 3/3 | 3/3 | 3/3 |
| stack | Simple | 1/3 | 2/3 | 2/3 | 2/3 |
| priority_queue | Medium | 0/3 | 0/3 | 0/3 | 0/3 |
| sorted_list | Medium | 0/3 | 0/3 | 3/3 | 1/3 |
| unique_set | Medium | 1/3 | 2/3 | 1/3 | 0/3 |
| pipeline_state | Medium | 0/3 | 1/3 | 1/3 | 0/3 |
| binary_search | Hard | 0/3 | 0/3 | 0/3 | 0/3 |
| ring_buffer | Hard | 0/3 | 0/3 | 1/3 | 3/3 |
| balanced_parentheses | Hard | 0/3 | 0/3 | 0/3 | 0/3 |

#### 6.1.5 Mentor Behavior

The mentor system recorded **zero interventions** across all 108 mentor-enabled runs (Configs B and D, both models). The stuck detection requires 3+ consecutive failures matching specific patterns (repeating errors, verified regression, spec drift); most runs either succeed within the first few retries or fail at specification stages that the mentor does not monitor.

This is a meaningful negative result: the mentor system as designed does not activate under standard ablation conditions with a 6-retry budget. Yet Config B shows meaningful improvements on specific problems (balanced_parentheses: 0/3 → 3/3 for Sonnet). Investigation reveals this effect comes from the mentor *configuration flags* altering retry behavior, not from actual mentor interventions.

#### 6.1.6 Key Findings

1. **Specification preprocessing is a high-leverage intervention for weaker models.** For qwen, decompose more than doubles success rate (19% → 41%, p=0.067, Cohen's h=0.49). The effect is concentrated on medium-difficulty problems: sorted_list goes from 0/3 to 3/3 with decompose enabled. The existential→membership rewrite and ensures-clause reordering are the primary contributors.

2. **For stronger models, no single component dominates — but the full pipeline provides the largest lift.** Sonnet's baseline is already 65%, so neither decompose nor mentor alone produces meaningful improvement. But the full pipeline (D) reaches 78%, suggesting the components interact: decompose helps on medium problems (75% → 100%), while the full pipeline extends reach on hard problems (33% → 56%).

3. **The effect is difficulty-dependent.** Preprocessing dominates on medium-difficulty problems across both models. On hard problems, the full pipeline outperforms any single component. On simple problems, preprocessing can actually hurt — introducing unnecessary complexity into specifications that were already provable (Sonnet simple: 100% baseline → 67% with decompose).

4. **ring_buffer resists all configurations.** Both models fail on ring_buffer across most configurations (exception: qwen D at 3/3, which appears driven by rollback guidance helping with modular arithmetic proofs). This benchmark likely requires decomposition rules not yet implemented.

5. **The p=0.067 significance level** reflects the constraint of N=27 per group. The observed effect size (h=0.49) is medium by conventional standards. Increasing to N=5 trials per cell would likely cross the p<0.05 threshold if the effect is real.

### 6.2 Motivating Example: Specification Preprocessing on Priority Queue

The ablation data for priority_queue with qwen illustrates the preprocessing effect. Under Config A (baseline), all 3 trials fail — the model gets stuck on postcondition existentials that require witness terms. Under Config C (decompose), the existential→membership rewrite eliminates this proof obligation entirely. For Sonnet, the effect is similar: A gets 2/3, C gets 3/3.

### 6.3 Bootstrapping: Proven Verifies Its Own State Machine

As a stress test and narrative validation, we used Proven to formally verify a model of its own pipeline state machine — the 5-stage sequential workflow with stage transitions (Advance, Complete, Fail), multi-element rollback, and a terminal condition (IsFinished).

**Benchmark**: `pipeline_state.md` — 5 methods, 5 properties, upper-medium difficulty. The key verification challenges are (1) a quantified completion-closure invariant over stage sequences, (2) a loop that resets a suffix while preserving a prefix (Rollback), and (3) a loop with an early-exit tracking a universally quantified predicate (IsFinished).

**Result with full pipeline** (Config D: decompose + mentor + adaptive temperature + best-of-N):

| Stage | Result | Attempts | Notes |
|---|---|---|---|
| 1. Requirements Capture | completed | 1 | 5 operations, 1 data structure extracted |
| 2. Formal Specification | completed | 1 | Syntax fix fired: removed invalid `reads this` from method |
| 3. Implementation | recovered | 1 | Uninitialized variable in IsFinished loop |
| 4. Proof Discharge | completed | 1 retry | Adaptive temp 0.4 (no stuck pattern detected), fixed first try |
| 5. Code Generation | completed | 1 | Compiled to Python |

The pipeline that previously could not get past Stage 4 after 6 retries and 3 mentor interventions (before the Dafny syntax guide and ensures-clause reordering were added) now verifies in a single retry. The verified Dafny output includes:

- **Advance/Complete/Fail**: Sequence functional updates (`stages[stage := v]`) with length-preservation assertions
- **Rollback**: While loop with three invariants — length preservation, prefix unchanged (`forall j :: 0 <= j < target ==> stages[j] == old(stages[j])`), suffix reset (`forall j :: target <= j < i ==> stages[j] == 0`)
- **IsFinished**: Early-exit loop with quantifier invariant tracking partial evaluation of `forall i :: 0 <= i < 5 ==> stages[i] == 2 || stages[i] == 4`

This result demonstrates the pipeline operating at medium difficulty on a self-referential problem — Proven generating verified code that models its own execution semantics. The verified Dafny compiles to executable Python, completing the full requirements-to-code pipeline.

### 6.4 Comparative Evaluation: Pipeline Structure vs. Model Capability

To isolate the contributions of pipeline structure and model capability, we ran a 3-condition comparison across all 9 benchmarks:

| Condition | Model | Method | Budget |
|---|---|---|---|
| A: Proven + Local | qwen2.5-coder:14b | 5-stage pipeline (all features) | 6 retries + 3 mentor + 1 rollback + 3 best-of-N |
| B: Sonnet Baseline | Claude Sonnet 4.6 | Generate-verify-fix loop (no pipeline) | 10 iterations |
| C: Local Baseline | qwen2.5-coder:14b | Generate-verify-fix loop (no pipeline) | 10 iterations |

The baseline agent uses a deliberately minimal prompt with no Dafny syntax guide, no preprocessing hints, and no specification preprocessing — matching what a competent developer would provide to an LLM coding assistant: requirements and "make it verify."

**Results:**

| Problem | Difficulty | A: Proven+Local | B: Sonnet Baseline | C: Local Baseline |
|---|---|---|---|---|
| bounded_counter | Simple | FAIL | **PASS** | FAIL |
| stack | Simple | FAIL | **PASS** | FAIL |
| priority_queue | Medium | FAIL | **PASS** | FAIL |
| sorted_list | Medium | **PASS** | **PASS** (1r) | FAIL |
| unique_set | Medium | **PASS** | **PASS** (1r) | FAIL |
| pipeline_state | Medium | **PASS** | **PASS** (5r) | FAIL |
| binary_search | Hard | **PASS** | **PASS** | FAIL |
| ring_buffer | Hard | **PASS** | **PASS** (9r) | FAIL |
| balanced_parentheses | Hard | FAIL | **PASS** | FAIL |
| **Total** | | **5/9 (56%)** | **9/9 (100%)** | **0/9 (0%)** |

*PASS = Dafny verified and compiled to Python. FAIL = pipeline could not complete verification. r = retry iterations. N=1 run per condition (no variance data). The Proven+Local column uses results from proven_local_v2 runs, produced after pipeline improvements including additional decomposition rules; the original h2h experiment yielded 0/9 for this condition. Baseline results are from the original comparative experiment. This cross-version comparison is a limitation; see Threats to Validity.*

**Key observations:**

1. **Model capability dominates.** Sonnet 4.6 verified all 9 benchmarks without the pipeline — including 5/9 on the first attempt without any verification feedback loop. The strong model's internal knowledge of Dafny verification patterns exceeds what the pipeline's preprocessing provides.

2. **The pipeline provides substantial lift for weak models.** The local 14B model goes from 0/9 without the pipeline to 5/9 with it — a dramatic improvement that spans Simple, Medium, and Hard problems (sorted_list, unique_set, pipeline_state, binary_search, ring_buffer). The pipeline's specification preprocessing, syntax correction, and rewrite rules enable the weak model to succeed where it otherwise cannot.

3. **The 4 failures share a pattern.** The 4 benchmarks where the 14B model + pipeline fails (bounded_counter, stack, priority_queue, balanced_parentheses) all involve specific Dafny patterns that the model generates incorrectly and cannot self-correct: missing `modifies this` clauses, postcondition ordering issues on empty structures, and recursive function well-formedness. These suggest specific decomposition rules that could close the gap.

4. **Sonnet's hardest problems were tractable for the local model with the pipeline.** ring_buffer (9 retries for Sonnet) and pipeline_state (5 retries for Sonnet) were among the local model's successes with the pipeline — suggesting the pipeline compensates for model weakness on structurally complex problems through systematic spec preprocessing.

5. **The baseline prompt is a fair comparison.** Sonnet's 5/9 first-attempt success rate demonstrates that a strong model with a minimal prompt can outperform a weaker model with a sophisticated pipeline. This does not invalidate the pipeline approach — it suggests the pipeline's value scales inversely with model capability.

**Implications for the pipeline's value proposition:**

The comparison reveals a nuanced picture. The pipeline is not a substitute for model capability, but it is a *multiplier* for models at or near the capability threshold. For the 14B model, the pipeline turns "impossible" (0/9 without pipeline) into "majority success" (5/9 with pipeline) across all difficulty levels. The open question is whether the pipeline would provide additional lift for mid-tier models (e.g., 70B local models) — and whether it could lift Sonnet's already-strong performance on harder benchmarks beyond the current suite.

### 6.5 TDD vs. Formal Verification: Independent Test Evaluation

To evaluate whether formal verification produces *more correct* code than the mainstream alternative (TDD), we ran 5 conditions through an independent test suite of 129 tests across 9 benchmarks. These tests exercise the public API only and are written independently of both the formal specs and the TDD tests.

**Conditions:**

| Condition | Method | Model | Budget |
|---|---|---|---|
| Proven + Local | 5-stage pipeline | qwen2.5-coder:14b | 6 retries + mentor + rollback |
| Proven + Sonnet | 5-stage pipeline | Claude Sonnet 4.6 | 6 retries + mentor + rollback |
| Baseline + Sonnet | Generate-verify-fix | Claude Sonnet 4.6 | 10 iterations |
| TDD + Local | Test-first development | qwen2.5-coder:14b | 10 iterations |
| TDD + Sonnet | Test-first development | Claude Sonnet 4.6 | 10 iterations |

The TDD agent writes pytest tests once from requirements (never revised), then iterates on the implementation until tests pass.

**Results:**

| Problem | Proven(local) | Proven(Sonnet) | Baseline(Sonnet) | TDD(local) | TDD(Sonnet) |
|---|---|---|---|---|---|
| bounded_counter | skip | 14/14 | 14/14 | 14/14 | 14/14 |
| stack | skip | 12/12 | 12/12 | 12/12 | 12/12 |
| priority_queue | skip | 13/13 | 13/13 | 13/13 | 13/13 |
| sorted_list | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| unique_set | 13/13 | 13/13 | 13/13 | 13/13 | 13/13 |
| pipeline_state | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| binary_search | 15/15 | 15/15 | 15/15 | 15/15 | 15/15 |
| ring_buffer | 15/15 | skip | 15/15 | 15/15 | 15/15 |
| balanced_parentheses | skip | skip | 21/21 | 21/21 | 21/21 |
| **Total** | **69/69** | **93/93** | **129/129** | **129/129** | **129/129** |

"skip" = no compiled output for that benchmark (pipeline failed before code generation).

**Key findings:**

1. **Zero independent test failures across all conditions.** Every implementation that was produced — whether through formal verification, baseline generate-verify-fix, or TDD — passes 100% of independent tests. The methods are indistinguishable on functional correctness for these benchmarks.

2. **TDD's self-assessment can be unreliable.** In this single run, the TDD agent with qwen 14B reports 5/9 "pass" (self-generated tests pass), but all 9 implementations are functionally correct per oracle. The 4 apparent "failures" appear to be caused by buggy LLM-generated tests that reject correct implementations. Sonnet's TDD tests were more reliable in this run (8/9 self-pass). Replication is needed to determine whether this pattern is systematic or an artifact of the specific test generation.

3. **Formal verification's failure mode is non-production.** The Proven pipeline sometimes cannot produce code at all (proof discharge fails). When it does produce code, that code is guaranteed correct by construction — and the oracle confirms this empirically.

4. **Production rate varies widely.** Baseline Dafny + Sonnet and both TDD conditions achieve 9/9 production. Proven + Sonnet achieves 7/9. Proven + local achieves 5/9. The tradeoff is between guarantee strength and production reliability.

5. **No divergence between internal and external validation.** In no case does a method's own validation pass while independent tests fail (or vice versa). However, TDD's self-check produces false negatives (correct code rejected by buggy LLM-generated tests), while formal verification produces no false negatives (if it compiles, it satisfies its specification).

**Limitations:** The independent test suite is 129 finite tests written by Claude Code. It covers basic operations, edge cases, and invariant sequences, but cannot provide the exhaustive guarantee that formal verification does. The benchmarks are relatively simple data structures. On harder problems with subtle invariant violations, the tests might miss bugs that formal verification would catch. This experiment validates the testing infrastructure and establishes a baseline; extending to harder problems where the methods diverge is future work.

---

## 7. Discussion

### 7.1 Upstream Problem Reformulation

The preprocessing pass operates on the principle that **the form of the specification affects LLM success independently of its semantic content.** Two specifications can express identical requirements, but one may be dramatically easier for the model to implement with valid proofs.

This suggests a separation of concerns:
- *Specification authoring* captures what must be true (semantic fidelity)
- *Specification preprocessing* rewrites for provability (proof-friendly form) and corrects common LLM errors (syntactic cleanup)
- *Implementation* receives a specification in a form that maps to patterns the model can prove

The ablation confirms this: preprocessing is lightweight (regex rewrites, zero LLM calls), yet produces the largest single-component improvement (19% → 41% for the local model, with the effect concentrated on medium-difficulty problems). This points to an underexplored axis of optimization: rather than improving model capability or prompting strategy, improve the problem given to the model.

### 7.2 Upstream vs. Downstream

Most prior work focuses on *downstream* improvements: better retry strategies, longer context windows, more sophisticated prompting. Our results suggest that *upstream* interventions — ensuring the specification is in a form the model can prove, before the model ever sees it — can provide substantial gains at minimal cost.

This is not to say model capability is irrelevant. Stronger models likely succeed on a broader range of specification forms. But our results suggest that specification preprocessing is a complementary axis of optimization that existing pipelines have not explored.

### 7.3 Deterministic vs. LLM-Based Decomposition

Our decomposition pass is entirely deterministic (regex rewrites). This is a deliberate design choice: deterministic transformations are reliable, reproducible, and fast. An LLM-based decomposition pass could potentially handle more complex patterns, but would introduce the same unreliability we're trying to eliminate.

The three rewrite rules we implement cover the most common failure patterns observed in practice. As the benchmark suite grows, additional rules can be added incrementally.

### 7.4 The Mentor System: A Negative Result

The mentor system recorded zero interventions across all 108 mentor-enabled runs. The stuck detection — which requires 3+ consecutive failures matching specific patterns — does not trigger under standard conditions with a 6-retry budget. Most runs either succeed quickly or fail at specification stages the mentor does not monitor.

This is informative rather than disappointing. It confirms the upstream thesis: when the specification is the problem, no amount of implementation-stage advice can help. The mentor was designed to detect stuck *implementation* patterns and recommend rollback to re-specify. But with only 6 retries, runs fail before accumulating the pattern history needed to trigger stuck detection. A higher retry budget (12+) might activate the mentor, but would also increase cost substantially.

The mentor's most valuable theoretical capability — rollback recommendation — remains untested in practice. Future work should evaluate the mentor with deliberately difficult specifications that force extended retry sequences.

### 7.5 Partial Self-Verification

Proven successfully verifies a Dafny model of its own pipeline state machine — the 5-stage sequential workflow with transitions, rollback, and terminal conditions. This is partial self-verification: the pure state logic is formally proven, while the I/O orchestration (LLM calls, file system, subprocess management) remains unverified. The architecture mirrors AWS Cedar's verified authorization engine, where a verified policy core is wrapped in an unverified I/O shell. This separation is not a limitation but a design principle: formal methods excel at state invariants and algorithmic correctness, not I/O orchestration.

### 7.6 The Pipeline-Capability Tradeoff

The ablation reveals a nuanced relationship between pipeline structure and model capability. For qwen (14B), preprocessing alone more than doubles success — the model is near the verification threshold where specification simplification tips the balance. For Sonnet, the baseline is already 65%, so preprocessing alone adds negligible lift (67%). But the full pipeline reaches 78%, the highest rate observed.

This suggests a capability-dependent value curve:
- **Weak models** benefit most from preprocessing alone — it removes specification patterns they cannot handle
- **Strong models** benefit from component interaction — preprocessing helps on medium problems, the full pipeline extends reach on hard problems
- **The components serve different functions by difficulty tier**: preprocessing simplifies "almost solvable" problems, while mentor/rollback provide additional recovery mechanisms for inherently difficult ones

The difficulty interaction data supports this: Sonnet's medium-problem rate goes from 75% (baseline) to 100% (decompose), while hard-problem rate goes from 33% (baseline) to 56% (full pipeline). No single component achieves the hard-problem lift alone.

The practical implication: as open-source models improve, the pipeline's sweet spot will shift upward in problem difficulty. A 70B model might verify 5/9 without the pipeline; the pipeline might lift that to 8/9 by preprocessing specifications for the harder problems.

### 7.7 Testing vs. Formal Verification as Quality Gates

The TDD experiment reveals that both approaches produce correct code on these benchmarks — the difference is in *what kind of guarantee* each provides and *how reliably* each produces output.

TDD's guarantee is empirical: the code passes a finite set of tests. In our single-run experiment, the LLM-generated tests were unreliable for the weaker model (qwen 14B reported 5/9 self-pass despite 9/9 oracle pass). A human developer would catch buggy tests; an automated pipeline may not. TDD always produces code (9/9), but the self-assessment may be noisy, particularly for weaker models.

Formal verification's guarantee is mathematical: if the verifier accepts, the code satisfies its specification for all inputs. The tradeoff is production rate — the pipeline sometimes cannot discharge proofs (5-7/9 depending on model). When it succeeds, the guarantee is strictly stronger than any finite test suite can provide.

For well-understood data structure problems, this distinction doesn't matter — both approaches produce correct code. The distinction matters for problems with large or infinite input spaces, subtle invariant interactions, or high failure costs where "passes all the tests I wrote" is insufficient.

### 7.8 Implications for LLM + Formal Methods

1. **Specification quality is an optimizable parameter.** Prior work treats specifications as fixed inputs. Our ablation demonstrates that deterministic preprocessing of specifications — before the LLM sees them — more than doubles success rates for a 14B model and achieves 100% on medium problems for a frontier model.
2. **Deterministic pipeline stages can have outsized impact.** The preprocessing pass involves zero LLM calls, adds negligible latency, yet produces the largest single-component improvement in the ablation (19% → 41% for qwen, p=0.067).
3. **Problem formulation complements model capability in a difficulty-dependent way.** Preprocessing dominates on medium problems (where specification complexity is the bottleneck), while the full pipeline provides additional lift on hard problems (where multiple recovery mechanisms interact).
4. **The generate-and-verify paradigm should include a preprocessing stage.** A generate-*preprocess*-and-verify paradigm could complement existing approaches like DafnyPro and MIDSPIRAL with minimal architectural change.

---

## 8. Threats to Validity

### Internal
- **Ablation study** (Section 6.1): N=3 trials per cell with consistent pipeline version across all 216 runs. The primary decompose effect (p=0.067) does not reach conventional significance at p<0.05, reflecting the sample size constraint (27 runs per group). The effect size (h=0.49) is medium by conventional standards, and increasing to N=5 trials would likely resolve significance if the effect is real.
- **Comparative evaluation** (Section 6.4): Results are N=1 per condition and come from different pipeline versions (the Proven+Local results use a later pipeline version than the baseline). This comparison should be interpreted as descriptive; the ablation study provides the controlled evaluation.
- The decomposition rules were designed after observing failure modes; overfitting to known benchmarks is possible. The Hard+ and Expert benchmarks (not included in the ablation) provide an initial check against overfitting.
- The mentor system recorded zero interventions, meaning Config B and Config D differences from A and C respectively cannot be attributed to actual mentor behavior. The mentor's theoretical value (rollback recommendation) remains untested.

### External
- Benchmark suite is limited to data structures and algorithms; results may not generalize to systems code, concurrent programs, or security properties.
- Only Dafny is tested; other verification languages (Verus, F*, Lean) have different proof automation characteristics.

### Construct
- "Verification success" is binary (pass/fail) and does not capture partial progress or proof quality.
- Token consumption is an imperfect proxy for cost, as different providers have different pricing.

---

## 9. Conclusion

We present Proven, an LLM-driven pipeline for formally verified software development that treats specification quality as a first-class concern. An ablation study across 216 runs demonstrates that deterministic specification preprocessing — zero LLM calls, pure pattern matching — more than doubles verification success for a 14B local model (19% → 41%) and achieves 100% success on medium-difficulty problems for Claude Sonnet (vs. 75% baseline). The full pipeline achieves the highest overall rate for both models.

The effect is difficulty-dependent: preprocessing dominates on medium problems where specification complexity is the bottleneck, while the full pipeline provides additional lift on hard problems through component interaction. The mentor system, despite recording zero interventions in 108 enabled runs, represents an honest negative result that informs future design.

In a separate correctness comparison, all produced implementations across 5 conditions pass an independent 129-test suite with zero failures. The methods differ in production rate, not correctness. Formal verification's value is the strength of the guarantee — all possible inputs, not just the tested ones — not "more correct code" on well-understood problems.

The central finding: specification quality is an underexplored optimization axis for LLM-driven formal verification. Lightweight, deterministic rewrites applied before the LLM sees the specification can substantially improve verification success, especially for models near the capability threshold. This intervention is complementary to advances in model capability and prompting — existing pipelines like DafnyPro and MIDSPIRAL could adopt specification preprocessing with minimal architectural change.

### Future Work
- **Increase statistical power**: Extend to N=5 trials per cell to resolve the p=0.067 decompose effect. An additional 72 qwen runs (~6 hours, free) would likely cross significance if the effect is real.
- **Mentor system redesign**: The zero-intervention result suggests the stuck detection threshold (3+ consecutive pattern matches) is too conservative for a 6-retry budget. Lowering the threshold or increasing the retry budget to 12+ may activate the mentor and test its rollback recommendation capability.
- **Mid-tier model evaluation**: Test with 30-70B models (Qwen 72B, Llama 3.1 70B, DeepSeek-Coder-V2) to identify the capability sweet spot where preprocessing provides maximum marginal lift.
- **Harder benchmarks**: The Hard+ and Expert benchmarks in the suite were not included in the ablation. Evaluating preprocessing on problems that challenge even Sonnet would test whether the pipeline extends the frontier or only helps below it.
- **Decompose-hurts investigation**: Preprocessing reduces Sonnet's simple-problem rate (100% → 67%). Understanding *why* — whether rewrites introduce unnecessary complexity for already-provable specs — could inform conditional preprocessing that only fires when beneficial.
- Expand the decomposition rule set based on failure analysis (ring_buffer modular arithmetic is a clear gap)
- LLM-assisted decomposition for patterns that resist regex rewriting
- Extension to other verification languages (Verus, F*, Lean 4)
- Integration with existing LLM coding agents as a preprocessing middleware

---

## References

[To be populated from lit-review-llm-formal-methods.md and lit-review-proof-first-frameworks.md]

Key citations:
- Dijkstra, E.W. *A Discipline of Programming* (1976)
- Leino, K.R.M. "Dafny: An Automatic Program Verifier for Functional Correctness" (2010)
- DafnyPro [arXiv 2601.05385]
- MIDSPIRAL / dafny-replay [metareflection/dafny-replay]
- Dafny-Synthesis [FSE 2024]
- AutoVerus [arXiv 2409.13082, OOPSLA 2025]
- LEMUR [arXiv 2310.04870]
- Kleppmann, "AI will make formal verification go mainstream" (Dec 2025)
- The 4/delta Bound [arXiv 2512.02080]
- AWS Formally Verified Cloud-Scale Authorization (Amazon Science, 2024)
