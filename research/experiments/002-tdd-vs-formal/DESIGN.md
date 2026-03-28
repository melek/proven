# Experiment 002: TDD vs. Formal Verification Correctness Comparison

## Research Question

Do TDD and formal verification produce differently correct code? When both methods produce output, does one yield more functionally correct implementations than the other?

## Hypothesis

H1: Formal verification and TDD produce equally correct code on well-understood data structure benchmarks -- the methods differ in production rate and guarantee strength, not functional correctness.
H2: Formal verification's failure mode is non-production (cannot discharge proof), while TDD's failure mode is silent incorrectness (passes self-generated tests but fails independent oracle).

## Method

Five conditions run across 9 benchmarks, evaluated against an independent test suite of 129 tests written separately from both formal specs and TDD tests.

| Condition | Method | Model |
|-----------|--------|-------|
| Proven + Local | 5-stage pipeline | qwen2.5-coder:14b |
| Proven + Sonnet | 5-stage pipeline | Claude Sonnet 4.6 |
| Baseline + Sonnet | Generate-verify-fix loop | Claude Sonnet 4.6 |
| TDD + Local | Test-first development | qwen2.5-coder:14b |
| TDD + Sonnet | Test-first development | Claude Sonnet 4.6 |

TDD agent writes pytest tests from requirements (never revised), then iterates on implementation until tests pass. Proven pipeline uses full configuration (decompose + mentor + rollback). Baseline uses minimal prompt with no Dafny syntax guide or preprocessing.

Independent oracle: 129 pytest tests across 9 benchmarks exercising public API only, written independently of both formal specs and TDD-generated tests.

## Variables

- Independent: verification method (Proven pipeline, baseline Dafny, TDD), model (qwen 14B, Sonnet)
- Dependent: independent test pass rate, production rate (compiled output produced), self-assessment accuracy (TDD self-pass vs oracle-pass)
- Controlled: benchmark suite (9 problems), retry budgets (6 for Proven, 10 for TDD/baseline)

## Data Collection

Each condition produces compiled output (or fails). Compiled outputs are run against the independent test suite. Results recorded as pass/fail per test per condition.

## Analysis Plan

- Per-condition: count of independent tests passed / total applicable tests
- Production rate: benchmarks producing compiled output per condition
- Self-assessment reliability: compare TDD self-reported pass/fail against oracle results to detect false negatives (correct code rejected by buggy LLM-generated tests)
- Qualitative analysis of failure modes by method

## Null Result Protocol

If both methods produce identical correctness on all benchmarks, report this as the primary finding: the methods are indistinguishable on functional correctness for these problems. The meaningful distinction becomes production rate and guarantee strength.

## Status

complete

## Results Summary

**Zero independent test failures across all conditions.** Every implementation that was produced -- whether through formal verification, baseline, or TDD -- passes 100% of applicable independent tests.

| Condition | Compiled | Independent Tests |
|-----------|----------|-------------------|
| Proven + Local | 5/9 | 69/69 |
| Proven + Sonnet | 7/9 | 93/93 |
| Baseline + Sonnet | 9/9 | 129/129 |
| TDD + Local | 9/9 | 129/129 |
| TDD + Sonnet | 9/9 | 129/129 |

The methods differ in production rate, not correctness. Formal verification's failure mode is non-production (cannot compile). TDD + qwen 14B self-reports 5/9 pass despite 9/9 oracle pass -- LLM-generated tests are unreliable for weaker models. Formal verification produces no false negatives: if it compiles, it satisfies its specification.
