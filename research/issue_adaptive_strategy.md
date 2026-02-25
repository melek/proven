## Motivation

In experiments across 15 benchmarks and 5 conditions, the Proven pipeline underperforms the baseline (simple generate-verify-fix loop) on Hard+ and Expert problems when using strong models. Specifically, Baseline + Sonnet compiled 3/6 new benchmarks while Proven + Sonnet compiled only 1/6.

Forensic analysis of the three problems where the pipeline failed but the baseline succeeded reveals three architectural failure modes:

1. **Spec over-commitment** (compositional_pipeline): Stage 2 locked in an `{:axiom}` ghost function that verified but could not compile. The baseline generated an imperative method that compiled on first attempt with 13x fewer tokens.

2. **Over-decomposition cascade** (insertion_sort): Stage 1 split a single algorithm into 4 operations (including inner/outer loop bodies as separate methods). Stage 2 could not produce a parseable spec for this decomposition -- 7 attempts, all failed at `dafny resolve`. The baseline used 2 operations with inline invariants and succeeded.

3. **Output token truncation** (compositional_triple): Implementation + proofs required ~600 lines. Every Stage 3/4 attempt hit the 8192 completion token max, producing truncated files. ~485,000 tokens consumed before timeout. The baseline built incrementally in 1.5-2k token chunks.

Meanwhile, the pipeline scaffolding *does* help weaker models -- qwen 14B compiled 5/9 original benchmarks with the pipeline vs. the expected lower rate without it. **The problem is not the pipeline itself, but that it applies the same strategy regardless of model capability.**

### Training data interaction

Many Hard+/Expert benchmarks (insertion sort, extended GCD, red-black tree) have verified Dafny implementations in training data. The baseline iterative approach lets strong models leverage recall + adaptation -- generating something close to a known solution, then fixing details via verification feedback. The pipeline spec-first path actively prevents this by forcing a decomposition that does not match any training example.

## Proposal: Adaptive Strategy Selection

### 1. Model Capability Profiles

Define a `ModelProfile` dataclass with scored capabilities:

```python
@dataclass
class ModelProfile:
    model_name: str

    # Capability scores (0.0 - 1.0)
    dafny_syntax: float      # Can it produce parseable Dafny?
    dafny_verification: float # Can it produce verifiable Dafny?
    reasoning_depth: float    # Multi-step proof / invariant quality

    # Hard constraints
    context_window: int       # Total tokens (input + output)
    max_output_tokens: int    # Completion token limit

    # Behavioral traits
    benefits_from_scaffolding: bool  # Does decomposition help or hurt?
    benefits_from_examples: bool     # Does few-shot Dafny reference help?
```

### 2. Three-Layer Capability Detection

**Layer 1: Static table for known models**

```python
KNOWN_PROFILES = {
    "claude-sonnet-4-6": ModelProfile(
        dafny_syntax=0.9, dafny_verification=0.7, reasoning_depth=0.8,
        context_window=200000, max_output_tokens=8192,
        benefits_from_scaffolding=False, benefits_from_examples=False,
    ),
    "claude-opus-4-6": ModelProfile(
        dafny_syntax=0.95, dafny_verification=0.85, reasoning_depth=0.95,
        context_window=200000, max_output_tokens=8192,
        benefits_from_scaffolding=False, benefits_from_examples=False,
    ),
    "qwen2.5-coder:14b": ModelProfile(
        dafny_syntax=0.5, dafny_verification=0.3, reasoning_depth=0.4,
        context_window=32768, max_output_tokens=4096,
        benefits_from_scaffolding=True, benefits_from_examples=True,
    ),
}
```

**Layer 2: User-defined profiles**

Allow users to define custom profiles in `.env` or a config file for local/fine-tuned models:

```toml
[model_profile]
dafny_syntax = 0.6
dafny_verification = 0.4
context_window = 16384
max_output_tokens = 4096
benefits_from_scaffolding = true
```

**Layer 3: Structured capability probe**

For unknown models, run 1-2 quick Dafny tasks at startup to estimate capabilities:

- **Probe 1 -- Syntax** (~10s): "Write a Dafny method that returns the maximum of two integers with pre/postconditions." Run `dafny resolve`. Score = resolved on attempt 1? 2? Failed?
- **Probe 2 -- Verification** (~30s): "Write a verified Dafny binary search with loop invariant." Run `dafny verify`. Score = verified? How many errors?

These probes cost <5k tokens and give a reliable signal for pipeline strategy selection. Cache results per model name to avoid re-probing.

### 3. Strategy Selection

Based on the profile, select one of three pipeline strategies:

#### Full Pipeline (weak models: dafny_syntax < 0.6)
Current behavior. All 5 stages, full preprocessing, detailed Dafny syntax injection in prompts, mentor system active, best-of-N sampling.

#### Light Pipeline (medium models: 0.6 <= dafny_syntax < 0.85)
- Stage 1: Requirements capture (simplified -- max 3 operations, no algorithm-internal decomposition)
- Stage 2: Specification (but allow method bodies, not just signatures)
- Stage 2.5: Preprocessing (keep -- it is free and does not hurt)
- Stage 3-4: Implementation + verification (standard)
- Stage 5: Compilation

#### Iterative Mode (strong models: dafny_syntax >= 0.85)
Closer to the baseline generate-verify-fix loop, but with pipeline benefits:
- Skip Stage 1 decomposition (let the model decide the architecture)
- Stage 2: Generate full spec+implementation in one pass
- Stage 2.5: Preprocessing (still free, still useful for syntax edge cases)
- Stage 3-4: Iterative verification fixes (not batch -- respond to specific errors)
- Stage 5: Compilation

### 4. Progressive Context Injection

Currently, all prompts include the same Dafny reference material regardless of model or attempt number. Instead, gate context injection on capability score AND retry count:

```
Attempt 1 (any model):
  - Requirements only
  - No Dafny reference material for strong models
  - Full Dafny syntax guide for weak models

Attempt 2-3 (after first failure):
  - Add specific error context
  - Strong models: still no reference injection
  - Weak models: add relevant Dafny patterns (loop invariants if invariant error, etc.)

Attempt 4+ (stuck):
  - ALL models: inject targeted Dafny reference for the specific stuck pattern
  - Strong models: trigger mentor system
  - Weak models: mentor + example solutions for similar problems
```

This extends the existing mentor system stuck detection. Instead of only providing "perspective shift" advice, it escalates by injecting progressively more context.

### 5. Dynamic Token Management

Use `max_output_tokens` from the profile to prevent truncation:

- **Estimate output size** before Stage 3: count operations, postconditions, lemmas in the spec. If estimated implementation > 70% of `max_output_tokens`, switch to incremental mode.
- **Incremental Stage 3**: Generate method-by-method instead of all-at-once. Each call produces one method + its lemmas. Concatenate results.
- **Context window budgeting**: For models with small context windows (e.g., 16k), summarize previous attempts instead of including full conversation history.

### 6. Retry Escalation

Instead of fixed retry behavior, escalate strategy on failure:

```
Strong model, attempt 1: Iterative mode (no scaffolding)
Strong model, attempt 3: Add Dafny reference injection
Strong model, attempt 5: Switch to Light Pipeline mode
Strong model, attempt 7: Switch to Full Pipeline mode (last resort)

Weak model, attempt 1: Full Pipeline (all scaffolding)
Weak model, attempt 3: Increase mentor budget
Weak model, attempt 5: Best-of-N with higher N
Weak model, attempt 7: Rollback to Stage 2 with guidance
```

This creates a natural escalation: try the model preferred strategy first, then progressively add more structure if it fails.

## Implementation Plan

### Phase 1: ModelProfile + Static Table
- Add `ModelProfile` dataclass to `proven/config.py`
- Add `KNOWN_PROFILES` lookup table
- Wire profile into `load_config()` based on `LLM_MODEL`

### Phase 2: Strategy Selection
- Add strategy enum: `full`, `light`, `iterative`
- Modify `pipeline.py` to select strategy based on profile
- Implement iterative Stage 3 (method-by-method generation)

### Phase 3: Progressive Context Injection
- Refactor `prompts.py` to accept capability scores
- Gate Dafny reference material on `dafny_syntax` score + attempt number
- Integrate with existing mentor stuck detection

### Phase 4: Capability Probe
- Implement 2-task probe in `proven/probe.py`
- Cache results in workspace
- Fall back to probe when model not in static table

### Phase 5: Token Management
- Add output size estimation before Stage 3
- Implement incremental Stage 3 for large implementations
- Add context window budgeting for small-context models

## Success Criteria

- Proven + Sonnet on Hard+ benchmarks should match or exceed baseline success rate (3/6)
- Proven + qwen 14B should not regress from current 5/9 on original benchmarks
- Pipeline should automatically select appropriate strategy without user intervention
- No single strategy should be strictly worse than the baseline for any model tier

## Data

### Full results matrix (new 6 benchmarks)

| Problem | Proven+Sonnet | Proven+Local | Baseline+Sonnet | TDD+Local | TDD+Sonnet |
|---------|:---:|:---:|:---:|:---:|:---:|
| compositional_pipeline (Hard+) | VERIFIED | FAIL | **PASS** | **PASS** | FAIL |
| extended_gcd (Hard+) | **PASS** | FAIL | FAIL | FAIL | **PASS** |
| insertion_sort (Hard+) | FAIL | FAIL | **PASS** | FAIL | **PASS** |
| red_black_tree (Expert) | FAIL | FAIL | FAIL | FAIL | FAIL |
| compositional_triple (Expert) | FAIL | FAIL | **PASS** | FAIL | **PASS** |
| topological_sort (Expert) | FAIL | FAIL | FAIL | **PASS** | -- |

### Failure mode breakdown

| Problem | Pipeline failure stage | Root cause | Baseline approach |
|---------|----------------------|------------|-------------------|
| compositional_pipeline | Stage 5 (compilation) | `{:axiom}` ghost function is un-compilable | Imperative method, 18s |
| insertion_sort | Stage 2 (spec resolution) | Over-decomposition into 4 operations | 2 operations, inline invariants |
| compositional_triple | Stage 3-4 (token truncation) | 600 lines > 8192 token limit | Incremental 1.5k-token fixes |

## References

- Forensic analysis: see conversation history for full comparison of pipeline vs baseline Dafny artifacts
- Full benchmark results: `research/sonnet_full_results.json`, `research/full_matrix_results.json`
- DafnyComp (arXiv 2509.23061): compositional verification cliff at 3% for frontier models
- AlgoVeri: near-zero LLM success on graph algorithms and advanced data structures
