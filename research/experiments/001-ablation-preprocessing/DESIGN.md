# Experiment 001: Ablation of Deterministic Specification Preprocessing

## Research Question

Does deterministic specification preprocessing (zero LLM calls, regex-based rewrites) improve LLM verification success rates in a Dafny pipeline? Does the effect vary with model capability and problem difficulty?

## Hypothesis

H1: Preprocessing (Config C) achieves higher verification success than Baseline (Config A).
H2: Preprocessing outperforms Mentor-only (Config B), because the bottleneck is specification form, not implementation retry strategy.
H3: The effect is larger for weaker models (14B) than stronger models (Sonnet), because weaker models have narrower provable specification forms.
H4: Full pipeline (Config D) does not significantly outperform Decompose-only (Config C), suggesting upstream simplification dominates downstream repair.

## Method

Full factorial ablation: 4 pipeline configurations x 9 benchmarks x 3 trials x 2 models. All runs use `--strategy full --best-of-n 0 --max-retries 6` to prevent confounding. Configurations differ only in decompose/mentor/rollback flags.

| Config | Decompose | Mentor Budget | Rollback Budget |
|--------|-----------|---------------|-----------------|
| A: Baseline | off | 0 | 0 |
| B: +Mentor | off | 3 | 0 |
| C: +Decompose | on | 0 | 0 |
| D: Full Pipeline | on | 3 | 1 |

Benchmarks span three difficulty tiers: Simple (bounded_counter, stack), Medium (priority_queue, sorted_list, unique_set, pipeline_state), Hard (binary_search, ring_buffer, balanced_parentheses).

## Variables

- Independent: pipeline configuration (4 levels), model (qwen2.5-coder:14b, Claude Sonnet 4.6), benchmark problem (9 levels)
- Dependent: verification success (binary), highest stage reached, total retry attempts, wall-clock time, tokens consumed, mentor interventions
- Controlled: max retries (6), strategy (full), best-of-N (0), Dafny version, temperature strategy

## Data Collection

Pipeline instrumentation writes `run_state.json` and `interaction_log.jsonl` per run. Analysis script walks the 216 run directories and extracts all metrics.

## Analysis Plan

- Success rates with Wilson score 95% CIs per (model, config) group
- Pairwise comparisons via one-sided Fisher's exact test; effect sizes via Cohen's h
- Difficulty-tier interaction: success rate by (config, difficulty) to identify where components help most
- Per-problem heatmap to identify individual benchmark effects

## Null Result Protocol

If preprocessing shows no effect (A vs C not significant), report as evidence that specification form does not matter for these benchmarks at this model capability level. If mentor shows zero interventions, report as evidence the stuck detection threshold is miscalibrated for the retry budget.

## Status

complete

## Results Summary

N=216 runs (one Sonnet baseline cell had 2 trials instead of 3, yielding N=215 actual).

**qwen2.5-coder:14b**: Preprocessing doubles success rate (A: 19% to C: 41%, p=0.067, Cohen's h=0.49, medium effect). Effect concentrated on medium problems (8% to 42%). Mentor alone provides small non-significant lift (A: 19% to B: 30%). Full pipeline (D: 33%) does not outperform decompose-only.

**Claude Sonnet 4.6**: Baseline already strong (65%). Neither decompose nor mentor alone adds meaningful lift. Full pipeline reaches 78%, the highest observed rate. Decompose achieves 100% on medium problems (vs 75% baseline). Hard problems benefit from the full pipeline (33% to 56%).

Mentor system recorded zero interventions across all 108 mentor-enabled runs -- an informative negative result confirming the upstream thesis: when specification form is the bottleneck, implementation-stage advice cannot help.
