# Proven

**What if your AI-generated code came with a mathematical guarantee that it's correct?**

Proven is a pipeline that turns plain-English requirements into formally verified, compiled code. Instead of generating code and hoping tests catch the bugs, Proven writes a mathematical specification first, simplifies it so the prover can handle it, then generates an implementation that is *proven correct by construction*. If the verifier accepts it, the code satisfies its specification — not probably, not for the inputs you tested, but for all possible inputs.

## Why This Matters

LLMs generate plausible code. Tests catch some bugs. But formal verification provides a different kind of guarantee: if a sorted-list implementation passes the Dafny verifier, it maintains sort order after *every possible* insertion — not just the thousand cases your test suite tried.

The catch: getting LLMs to produce code that passes a formal verifier is hard. They write specifications that are correct but unnecessarily complex, then struggle to prove their own work. Proven's key insight is that **specification quality is an optimizable parameter**. Deterministic rewrites applied *before* the LLM sees the spec — converting existential quantifiers to membership checks, reordering postconditions, fixing common Dafny mistakes — can dramatically improve verification success.

## Results

### Ablation Study (N=216 runs)

How much does each pipeline component contribute? Tested across 9 benchmarks, 3 trials each, 2 models:

**Local model (qwen 14B) — where preprocessing matters most:**

| Config | Success Rate | What's enabled |
|--------|-------------|----------------|
| A: Baseline | 19% | Just the retry loop |
| B: +Mentor | 30% | + diagnostic advisor |
| C: +Decompose | 41% | + spec preprocessing |
| D: Full Pipeline | 33% | All components |

Spec preprocessing (A vs C) more than doubles success rate for the local model (p=0.067, medium effect size).

**Cloud model (Claude Sonnet) — where components interact:**

| Config | Success Rate | What's enabled |
|--------|-------------|----------------|
| A: Baseline | 65% | Just the retry loop |
| B: +Mentor | 67% | + diagnostic advisor |
| C: +Decompose | 67% | + spec preprocessing |
| D: Full Pipeline | 78% | All components |

Sonnet's baseline is already strong, so no single component shows a big lift alone — but the full pipeline achieves the highest rate. The components help on different problems: preprocessing dominates medium-difficulty benchmarks (75% → 100%), while the full pipeline extends reach on hard problems (33% → 56%).

### Correctness Comparison (N=5 conditions)

Every implementation produced — whether by formal verification or TDD — passes an independent 129-test suite:

| Condition | Compiled | Independent Tests |
|-----------|----------|-------------------|
| Proven + qwen 14B (local) | 5/9 | 69/69 |
| Proven + Claude Sonnet | 7/9 | 93/93 |
| Baseline Dafny + Claude Sonnet | 9/9 | 129/129 |
| TDD + qwen 14B (local) | 9/9 | 129/129 |
| TDD + Claude Sonnet | 9/9 | 129/129 |

**Zero independent test failures across all conditions.** The methods differ in production rate, not correctness. Formal verification's value is the *strength* of the guarantee, not that it produces "more correct" code on well-understood problems.

## How It Works

```
Requirements (English)
    ↓
Stage 1: Requirements Capture → structured JSON
    ↓
Stage 2: Formal Specification → Dafny contracts (no method bodies)
    ↓
Stage 2.5: Spec Preprocessing → deterministic rewrites (zero LLM calls)
    ↓
Stage 3: Implementation → Dafny code with proofs
    ↓
Stage 4: Proof Discharge → retry loop with adaptive strategies
    ↓
Stage 5: Code Generation → Python, C#, Go, Java, or JavaScript
```

Stage 2.5 is the novel part. It applies ~19 deterministic rewrite rules that transform the specification into a form the Z3 solver can handle more easily — without changing what the spec means. No LLM calls, no randomness, just pattern matching and rewriting.

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

## CLI Reference

```bash
# Full pipeline run
python -m proven run <requirements.md> [options]

# Resume from a specific stage
python -m proven resume <workspace_dir> [--from-stage N]

# Check Dafny installation
python -m proven check
```

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

| Problem | Difficulty | What's being verified |
|---------|-----------|----------------------|
| bounded_counter | Simple | Value stays within min/max bounds |
| stack | Simple | Last-in-first-out ordering, size tracking |
| priority_queue | Medium | Elements always come out sorted |
| sorted_list | Medium | List stays sorted after every insert |
| unique_set | Medium | No duplicate elements ever |
| pipeline_state | Medium | Multi-step rollback preserves consistency |
| binary_search | Hard | Search bounds narrow correctly every iteration |
| ring_buffer | Hard | Wrap-around indexing with modular arithmetic |
| balanced_parentheses | Hard | Parenthesis matching via stack algorithm |
| compositional_pipeline | Hard+ | Contracts propagate correctly across functions |
| extended_gcd | Hard+ | Bezout's identity holds through every loop iteration |
| insertion_sort | Hard+ | Output is a permutation of input AND sorted |
| red_black_tree | Expert | 4+ tree invariants maintained through rotations |
| compositional_triple | Expert | 3-function contract chain |
| topological_sort | Expert | Graph DFS produces valid global ordering |

## Research

The `research/` directory contains the full experiment infrastructure:

- `paper-outline.md` — Working paper draft
- `experiments/001-ablation-preprocessing/` — Ablation study (4 configs x 9 benchmarks x 3 trials x 2 models)
- `experiments/002-tdd-vs-formal/` — TDD vs formal verification comparison
- `experiments/003-full-matrix/` — Full-matrix evaluation across models and benchmarks
- `experiments/004-methodology-transfer/` — Methodology transfer through AI advisory skill
- `oracle_tests/` — 129 independent tests across 9 benchmarks
- `shared/` — Shared analysis tools and evaluation scripts

### Claude Code Plugin

The `skills/` directory provides Claude Code skills for verification-informed analysis. Run `/proven:contribute` to learn about optional research participation. See `docs/RESEARCH.md` for the full research statement.

### Reproducing the ablation study

```bash
# Run ablation with a local model
python research/experiments/001-ablation-preprocessing/run_ablation.py --models qwen2.5-coder-14b

# Analyze results
python research/experiments/001-ablation-preprocessing/analyze_ablation.py \
  --results-json research/experiments/001-ablation-preprocessing/results/ablation_results.json --full
```

## License

[MIT](LICENSE)

## Author

Lionel Di Giacomo
