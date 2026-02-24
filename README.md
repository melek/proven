# Proven

LLM-driven stepwise refinement with Dafny verification. Requirements go in, formally verified code comes out.

Proven is a 5-stage pipeline that separates concerns existing generate-and-verify loops conflate: specification authoring, deterministic spec preprocessing, implementation, proof discharge, and code generation. The key insight: **specification quality is an optimizable parameter** — deterministic rewrites applied before the LLM sees the spec can dramatically improve verification success, especially for weaker models.

## Results

In experiments across 9 benchmark problems and 5 conditions, every implementation that was produced passes an independent test suite — regardless of whether it was generated through formal verification or TDD:

| Condition | Compiled | Own check\* | Independent tests |
|-----------|----------|------------|-------------------|
| Proven + qwen 14B (local) | 5/9 | 5/5 | 69/69 |
| Proven + Claude Sonnet | 7/9 | 7/7 | 93/93 |
| Baseline Dafny + Claude Sonnet | 9/9 | 9/9 | 129/129 |
| TDD + qwen 14B (local) | 9/9 | 5/9 | 129/129 |
| TDD + Claude Sonnet | 9/9 | 8/9 | 129/129 |

\* "Own check" = each method's built-in validation (Dafny verifier for formal conditions, LLM-generated pytest for TDD).

**Zero independent test failures across all conditions.** The methods differ in production rate and self-check reliability, not in functional correctness. All benchmarks are data structure problems; N=1 run per condition. See `research/paper-outline.md` for the full analysis including caveats.

## Quick Start

### Prerequisites

- Python 3.10+
- [Dafny 4.x](https://github.com/dafny-lang/dafny/releases) (includes Z3 solver)
- An OpenAI-compatible LLM API (local [Ollama](https://ollama.ai) or cloud)

### Install

```bash
pip install -e .
```

### Configure

```bash
cp .env.example .env
# Edit .env with your LLM endpoint and Dafny path
```

### Run

```bash
# Verify a benchmark problem
python -m proven run examples/bounded_counter.md --mode autonomous

# Check that Dafny is installed
python -m proven check
```

## Pipeline

```
Stage 1: Requirements Capture
  NL requirements → structured JSON

Stage 2: Formal Specification
  JSON → Dafny spec (signatures + contracts, no bodies)
  Validated: dafny resolve

Stage 2.5: Specification Preprocessing (deterministic, zero LLM calls)
  Rewrites: existential→membership, redundant ensures removal,
  ensures reordering, generic bracket fixes, quantifier range fixes
  Validated: dafny resolve on preprocessed spec

Stage 3: Implementation
  Preprocessed spec → Dafny implementation (method bodies + proofs)
  Validated: dafny verify

Stage 4: Proof Discharge
  Retry loop with adaptive temperature, stuck detection, mentor advisor
  Can trigger rollback to Stage 2

Stage 5: Code Generation
  Verified Dafny → Python / C# / Go / Java / JS via dafny build
```

## CLI Reference

```bash
# Full pipeline run
python -m proven run <requirements.md> [options]

# Resume from a specific stage
python -m proven resume <workspace_dir> [--from-stage N]

# Check Dafny installation
python -m proven check
```

Key flags:
| Flag | Default | Description |
|------|---------|-------------|
| `--mode` | `assisted` | `assisted`, `semi`, or `autonomous` |
| `--max-retries` | `3` | Max retries per stage |
| `--mentor-budget` | `3` | Max mentor interventions (0 to disable) |
| `--rollback-budget` | `1` | Max rollbacks to Stage 2 (0 to disable) |
| `--best-of-n` | `3` | Fresh samples when stuck (0 to disable) |
| `--target` | `py` | Compilation target: `py`, `cs`, `go`, `java`, `js` |
| `--verbose` | off | Print LLM prompts and responses |

## Benchmarks

| Problem | Difficulty | Key verification challenge |
|---------|-----------|---------------------------|
| bounded_counter | Simple | Single interval invariant |
| stack | Simple | LIFO ordering, size tracking |
| priority_queue | Medium | Sorted invariant, insertion |
| sorted_list | Medium | Insert-in-order, membership |
| unique_set | Medium | No-duplicates invariant |
| pipeline_state | Medium | Multi-element rollback, quantified closure |
| binary_search | Hard | Loop invariant with narrowing bounds |
| ring_buffer | Hard | Modular arithmetic, wrap-around indexing |
| balanced_parentheses | Hard | Stack-based algorithm, string processing |
| compositional_pipeline | Hard+ | Cross-function contract propagation |
| extended_gcd | Hard+ | Bezout identity loop invariant |
| insertion_sort | Hard+ | Ghost multiset permutation proof |

## Research

The `research/` directory contains experiment infrastructure:

- `paper-outline.md` — Working paper draft
- `experimental-plan.md` — Full methodology
- `freestyle_agent.py` — Generate-verify-fix baseline agent (no pipeline structure)
- `tdd_agent.py` — TDD baseline agent
- `oracle_tests/` — 129 independent tests across 9 benchmarks (written separately from all generation methods)
- `run_head_to_head.py` — Comparative experiment orchestration
- `run_tdd_vs_formal.py` — TDD vs Formal comparison
- `evaluate_oracle.py` — Independent test evaluation script

### Reproducing experiments

```bash
# Run Proven pipeline on all benchmarks
python research/run_head_to_head.py --conditions A

# Run TDD agent on all benchmarks
python research/run_tdd_vs_formal.py --conditions T-local

# Run independent tests against outputs
python -m pytest research/oracle_tests/ \
    --formal-dir runs/h2h/proven_sonnet \
    --tdd-dir runs/tdd/sonnet
```

## License

[MIT](LICENSE)

## Author

Lionel Di Giacomo
