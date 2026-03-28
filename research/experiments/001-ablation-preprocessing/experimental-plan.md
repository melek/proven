# Experimental Plan

## Research Question

**Primary:** Does upstream specification decomposition in an LLM-driven formal verification pipeline improve verification success rates compared to downstream retry strategies?

**Secondary:**
- Does the effect of decomposition vary with model capability?
- Does mentor-guided rollback provide additional benefit beyond static decomposition?
- What is the relationship between specification complexity and verification success?

---

## Independent Variables

### 1. Pipeline Configuration (4 levels)

| Config | Decompose | Mentor Budget | Rollback Budget | CLI Flags |
|--------|-----------|---------------|-----------------|-----------|
| **A: Baseline** | off | 0 | 0 | `--no-decompose --mentor-budget 0 --rollback-budget 0` |
| **B: +Mentor** | off | 3 | 0 | `--no-decompose --mentor-budget 3 --rollback-budget 0` |
| **C: +Decompose** | on | 0 | 0 | `--mentor-budget 0 --rollback-budget 0` |
| **D: Full** | on | 3 | 1 | `--mentor-budget 3 --rollback-budget 1` |

All configs: `--mode autonomous --max-retries 6`

### 2. Model (2-3 levels)

| Model | Endpoint | Notes |
|-------|----------|-------|
| qwen2.5-coder:14b | `http://localhost:11434/v1` (Ollama) | 14B params, Q4_K_M, local GPU |
| Claude Sonnet 4.6 | `https://api.anthropic.com/v1` | Cloud, requires API key |
| GPT-4o (optional) | `https://api.openai.com/v1` | Cloud, requires API key |

To switch models: update `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` in `.env`.

### 3. Problem (8 levels)

See benchmark suite below. Graded by difficulty.

---

## Dependent Variables

All captured automatically by the existing pipeline instrumentation.

| Metric | Source | Extraction |
|--------|--------|------------|
| **Verification success** | `run_state.json` → `stage_status["4"]` or `["3"]` == "completed" | Binary |
| **Highest stage reached** | `run_state.json` → max stage with status != "pending" | 1-5 |
| **Total retry attempts** | `run_state.json` → sum of `retry_counts` | Integer |
| **Total tokens consumed** | `interaction_log.jsonl` → sum of `usage.total_tokens` | Integer |
| **Wall-clock time** | `interaction_log.jsonl` → last ts minus first ts | Seconds |
| **Mentor interventions** | `04_proof_report.json` → `mentor_interventions` | Integer |
| **Decomposition rewrites** | `02_specification_decomposed.dfy` existence + diff | Count + type |
| **Rollbacks triggered** | `run_state.json` → presence of rollback events in log | Integer |
| **Stage 2 attempts** | `run_state.json` → `retry_counts["2"]` | Integer |
| **Stage 4 attempts** | `run_state.json` → `retry_counts["4"]` | Integer |

---

## Benchmark Suite

### Difficulty Grading Criteria

| Level | Invariants | Methods | Verification Challenge |
|-------|-----------|---------|----------------------|
| Simple | 1 | 2-3 | Single loop invariant or no loops |
| Medium | 2-3 | 3-5 | Multiple interacting invariants, sorted sequences |
| Hard | 3+ | 5+ | Complex invariants, modular arithmetic, needs lemmas |

### Problems

| # | Problem | Difficulty | File | Key Challenge |
|---|---------|-----------|------|---------------|
| 1 | Bounded Counter | Simple | `examples/bounded_counter.md` | Value within [min, max] bounds |
| 2 | Stack (LIFO) | Simple | `examples/stack.md` | Push/pop ordering, LIFO property |
| 3 | Priority Queue | Medium | `examples/priority_queue.md` | Sorted invariant, insertion |
| 4 | Sorted List | Medium | `examples/sorted_list.md` | Insert-in-order, membership, ordering |
| 5 | Unique Set | Medium | `examples/unique_set.md` | No-duplicates invariant, membership, removal |
| 6 | Binary Search | Hard | `examples/binary_search.md` | Loop invariant with narrowing bounds |
| 7 | Ring Buffer | Hard | `examples/ring_buffer.md` | Modular arithmetic, capacity invariant |
| 8 | Balanced Parentheses | Hard | `examples/balanced_parentheses.md` | Stack-based algorithm, string processing |
| 9 | Pipeline State Machine | Medium | `examples/pipeline_state.md` | Meta-benchmark: Proven verifying its own stage transitions |

---

## Execution Protocol

### Per Run

```bash
# Template command
python -m proven run examples/{problem}.md \
  --mode autonomous \
  --max-retries 6 \
  --verbose \
  {config_flags} \
  --workspace-dir runs/experiment/{model}/{config}/{problem}/{trial}
```

### Full Matrix

```
For each model in [qwen2.5-coder:14b, claude-sonnet-4-6]:
  For each config in [A, B, C, D]:
    For each problem in [bounded_counter, stack, priority_queue, sorted_list, unique_set, binary_search, ring_buffer, balanced_parentheses]:
      For trial in [1, 2, 3]:
        Run pipeline with config flags
        Record: run_state.json, interaction_log.jsonl, 04_proof_report.json
```

Total runs per model: 4 configs x 8 problems x 3 trials = **96 runs**
Total runs (2 models): **192 runs**
Estimated time per run (local 14B): 2-10 minutes → ~3-16 hours for local model

### Workspace Organization

```
runs/experiment/
  qwen2.5-coder-14b/
    baseline/
      bounded_counter/trial_1/
      bounded_counter/trial_2/
      bounded_counter/trial_3/
      stack/trial_1/
      ...
    mentor/
      ...
    decompose/
      ...
    full/
      ...
  claude-sonnet-4-6/
    ...
```

---

## Analysis Plan

### Primary Analysis: Verification Success Rate

For each (model, config) pair, compute:
- Success rate = # verified runs / total runs
- 95% confidence interval (Wilson score interval for proportions)
- Compare configs pairwise (Fisher's exact test or McNemar's test for matched pairs)

### Secondary Analyses

1. **Difficulty interaction**: Success rate by (config, difficulty_tier). Does decomposition help more on harder problems?
2. **Efficiency**: Mean tokens consumed for successful runs by config. Does decomposition reduce total cost even when baseline eventually succeeds?
3. **Mentor behavior**: What stuck categories are detected? How often does mentor fire? Does rollback occur? What is the success rate after rollback?
4. **Decomposition coverage**: How many rewrites per problem? Which rules fire most? Correlation between rewrite count and success improvement?
5. **Model interaction**: Plot success rate by (model, config). Does the gap between configs shrink for stronger models?

### Figures

1. **Bar chart**: Verification success rate by config (grouped by model)
2. **Heatmap**: Success rate by (problem, config) — shows which problems benefit from which interventions
3. **Box plot**: Total tokens consumed by config (for successful runs)
4. **Timeline**: Example run showing stages, retries, mentor interventions (narrative figure)
5. **Stacked bar**: Stuck categories detected across all runs

---

## Pilot Data

Already collected from development runs (all qwen2.5-coder:14b, priority queue):

| Run ID | Config (approx) | Result | Stage 4 Attempts | Mentor | Notes |
|--------|-----------------|--------|-------------------|--------|-------|
| 2026-02-22T18-58-45 | ~Baseline | FAIL | 5 | 0 | No mentor, no decompose |
| 2026-02-22T19-17-57 | ~B (+Mentor) | FAIL | 6 | 3 | Mentor fired; model couldn't act on advice |
| 2026-02-22T19-56-24 | ~C (+Decompose) | PASS | 0 | 0 | 1st attempt success after decomposition |

This pilot data already demonstrates the core finding: decomposition turned a consistent failure into a first-attempt success.

---

## Automation Script

`research/analyze_runs.py` will:

1. Walk `runs/experiment/` directory tree
2. Parse `run_state.json` and `interaction_log.jsonl` from each run
3. Extract all dependent variables
4. Output:
   - `research/results.csv` — one row per run, all metrics
   - `research/summary.csv` — aggregated by (model, config, problem)
   - Terminal: formatted summary table

---

## Prerequisites

Before running the full experiment:

1. All 8 benchmark problems must pass Stage 2 (dafny resolve) with at least one model
2. The analysis script must work on existing pilot data
3. Cloud model API keys must be configured (for non-local runs)
4. Sufficient disk space for ~192 run directories (~500KB each = ~100MB total)

---

## Timeline

| Phase | What | Estimated Effort |
|-------|------|-----------------|
| 1 | Write benchmark problems, validate with dafny resolve | 1 session |
| 2 | Run full experiment with local model (96 runs) | 1-2 sessions (mostly waiting) |
| 3 | Run full experiment with cloud model (96 runs) | 1 session |
| 4 | Analyze results, generate figures | 1 session |
| 5 | Write paper draft | 2-3 sessions |
