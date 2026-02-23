# CLAUDE.md — Proven: LLM-Driven Stepwise Refinement

## What This Is

**Proven** is a 5-stage pipeline that uses LLMs to produce formally verified software via Dafny. Natural-language requirements go in; verified, compiled code comes out. The pipeline separates concerns that existing generate-and-verify loops conflate: specification authoring, specification preprocessing, implementation, proof discharge, and code generation.

The project includes the pipeline tool (`proven/`), a benchmark suite of 9 problems (`examples/`), and a research experiment comparing formal verification against TDD (`research/`).

## Philosophy

Edsger Dijkstra argued that writing a program and then proving it correct is fundamentally backwards. Instead:

> Start with what must be true (postcondition) → calculate what must be true before (weakest precondition) → the program structure emerges from the proof.

Proven operationalizes this: requirements are formalized into Dafny specifications, specifications are deterministically simplified, and only then does the LLM implement and prove. The verifier is not a test oracle — it's a structural guarantee.

## Tool Selection

**Dafny** was selected as the verification language because:
- Pre/postconditions and loop invariants are first-class language constructs
- Z3 SMT solver discharges proof obligations automatically (no manual proof scripts)
- Compiles to Python, C#, Go, Java, JavaScript, and Rust
- Most accessible entry point for LLM-driven verification
- Active ecosystem with dedicated POPL workshops (2024-2026) and industrial deployment (AWS Cedar)

## Pipeline Architecture

```
Stage 1: Requirements Capture
    NL requirements → structured JSON (operations, invariants, pre/postconditions)

Stage 2: Formal Specification
    Structured JSON → Dafny spec (signatures + contracts, no method bodies)
    Validated: dafny resolve (parsing + type-checking)

Stage 2.5: Specification Preprocessing (deterministic, zero LLM calls)
    Rewrites: existential→membership, redundant ensures removal,
    ensures reordering, syntax fixes (generic brackets, quantifier ranges)
    Validated: dafny resolve on preprocessed spec

Stage 3: Implementation
    Preprocessed spec → Dafny implementation (method bodies + proof annotations)
    Validated: dafny verify (full verification)

Stage 4: Proof Discharge
    Retry loop with adaptive temperature, stuck detection, mentor advisor
    Can trigger rollback to Stage 2 with guidance

Stage 5: Code Generation
    Verified Dafny → target language via dafny build
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `proven/pipeline.py` | Orchestrator — runs stages sequentially with mode-based interaction |
| `proven/stages.py` | Stage 1-5 implementations |
| `proven/decompose.py` | 14 deterministic rewrite functions for spec preprocessing |
| `proven/mentor.py` | Stuck detection (5 categories) + perspective-shift advisor |
| `proven/prompts.py` | All LLM prompt templates + temperature strategies |
| `proven/dafny.py` | Dafny CLI wrapper (resolve, verify, build) |
| `proven/workspace.py` | RunState persistence + interaction logging |

## Research Results

Experiments across 9 benchmarks, 5 conditions:

| Condition | Compiled | Oracle Pass |
|-----------|----------|-------------|
| Proven + Local (qwen 14B) | 5/9 | 69/69 |
| Proven + Sonnet | 7/9 | 93/93 |
| Freestyle Dafny + Sonnet | 9/9 | 129/129 |
| TDD + Local (qwen 14B) | 9/9 | 129/129 |
| TDD + Sonnet | 9/9 | 129/129 |

Key finding: **zero oracle test failures across all conditions.** All produced implementations are functionally correct. The difference between methods is production rate, not correctness. See `research/paper-outline.md` for the full paper draft.

## Commands

```bash
# Run pipeline on a benchmark
python -m proven run examples/bounded_counter.md --mode autonomous

# Resume a paused run
python -m proven resume runs/path/to/workspace --from-stage 3

# Check Dafny installation
python -m proven check
```

## Configuration

Copy `.env.example` to `.env` and set:
- `LLM_BASE_URL` — OpenAI-compatible API endpoint
- `LLM_API_KEY` — API key
- `LLM_MODEL` — Model name (e.g., `qwen2.5-coder:14b`, `claude-sonnet-4-6`)
- `DAFNY_PATH` — Path to Dafny executable (or `dafny` if on PATH)

## Key References

- Dijkstra, E.W. — *A Discipline of Programming* (1976)
- Leino, K.R.M. — "Dafny: An Automatic Program Verifier for Functional Correctness" (2010)
- DafnyPro [POPL 2026] — Inference-time framework for Dafny annotation generation
- MIDSPIRAL / dafny-replay [Harvard 2025] — Closest prior work to Proven's vision

## Session History

- **2026-02-21**: Initial research. Explored formal verification landscape, Dijkstra's methodology, modern tool ecosystem.
- **2026-02-22**: Built the pipeline. Implemented all 5 stages, decomposition engine (14 rewrite rules), mentor system, adaptive temperature. Ran head-to-head experiments (Proven local vs freestyle).
- **2026-02-23**: TDD vs Formal experiment. Built TDD agent, 129 oracle tests across 9 benchmarks. Ran Proven+Sonnet condition (7/9). All conditions produce correct code — zero oracle failures.
