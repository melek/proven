# Experiment 003: Full Matrix -- Model Capability x Pipeline Strategy x Difficulty

## Research Question

How do model capability, pipeline strategy, and benchmark difficulty interact across a wider difficulty range? Does the pipeline extend the verification frontier for strong models on harder problems, or does model capability dominate?

## Hypothesis

H1: Model capability dominates -- a strong model without the pipeline outperforms a weak model with the pipeline on most benchmarks.
H2: The pipeline provides substantial lift for weak models, turning zero-success into partial-success across difficulty levels.
H3: On hard+ and expert problems, even the strong model with full pipeline cannot succeed, establishing a current difficulty ceiling.

## Method

Four conditions across 6 new benchmarks at hard+ and expert difficulty, plus cross-condition comparison on the original 9 benchmarks. The hard+ and expert problems were not used in the ablation (Experiment 001), providing a check against overfitting.

| Condition | Method | Model |
|-----------|--------|-------|
| P-sonnet | Proven pipeline (full) | Claude Sonnet 4.6 |
| P-local | Proven pipeline (full) | qwen2.5-coder:14b |
| B-sonnet | Baseline generate-verify-fix | Claude Sonnet 4.6 |
| T-local | TDD test-first | qwen2.5-coder:14b |

New benchmarks: compositional_pipeline (hard+), extended_gcd (hard+), insertion_sort with permutation proof (hard+), red_black_tree (expert), compositional_triple (expert), topological_sort (expert).

## Variables

- Independent: condition (4 levels), benchmark problem (6 hard+/expert problems)
- Dependent: verification success (binary), compilation success (binary), wall-clock time, highest stage reached
- Controlled: pipeline configuration (full for Proven conditions), retry budgets, Dafny version

## Data Collection

One run per (condition, benchmark) cell. Pipeline instrumentation records stage status, wall time, and exit code. N=1 per cell (no variance data -- this is a frontier exploration, not a controlled trial).

## Analysis Plan

- Success rate by condition across the 6 hard+/expert benchmarks
- Compare against Experiment 001 results on the original 9 benchmarks to assess difficulty scaling
- Identify the difficulty ceiling for each condition
- Qualitative failure mode analysis: which stage fails, and why

## Null Result Protocol

If no condition succeeds on expert problems, report the difficulty ceiling. If the pipeline provides no lift over baseline on hard+ problems, this challenges the upstream-intervention thesis at higher difficulty levels.

## Status

complete

## Results Summary

N=24 runs (4 conditions x 6 benchmarks, 1 trial each).

| Condition | Verified | Compiled |
|-----------|----------|----------|
| P-sonnet (Proven + Sonnet) | 2/6 | 1/6 |
| P-local (Proven + Local) | 0/6 | 0/6 |
| B-sonnet (Baseline + Sonnet) | 3/6 | 3/6 |
| T-local (TDD + Local) | -- | 2/6 |

Model capability dominates at higher difficulty. Baseline Sonnet (no pipeline) outperforms Proven + Sonnet on hard+/expert problems (3/6 compiled vs 1/6). The pipeline's preprocessing rules, designed for the original benchmark patterns, do not cover the verification challenges at this level (nonlinear arithmetic, ghost multiset tracking, rotation invariants).

The local 14B model fails all 6 problems with the pipeline (0/6), confirming the difficulty ceiling. TDD + Local produces 2/6 compilable outputs (compositional_pipeline, topological_sort), reinforcing that TDD always produces code but with empirical rather than formal guarantees.

Expert problems (red_black_tree, compositional_triple, topological_sort) resist all formal verification conditions, establishing the current frontier. Extended_gcd (hard+) is the standout: Proven + Sonnet verified and compiled it via a recovered Stage 3 attempt, demonstrating the pipeline's value on problems requiring loop invariant guidance.
