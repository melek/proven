# Literature Review: Verified Optimization and Correctness-Preserving Transformations

*Can formally verified code be optimized without breaking its guarantees? A survey of approaches to bridging the gap between correctness and performance.*

*Compiled: 2026-02-25*

---

## 1. The Problem

Formal verification through languages like Dafny produces code with mathematical correctness guarantees — but the compiled output is slow. Dafny's compiler targets (Python, C#, Go, Java, JS) use deliberately naive translations: immutable functional data structures (`_dafny.Map`, `_dafny.Seq`), defensive copying, and no optimization passes. This is by design — the simplest correct translation is easiest to trust.

**Measured overhead** (compositional_triple benchmark, Proven project):
- Dafny-compiled Python: 50–1260x slower than equivalent native Python (scaling with input size)
- At 50,000 elements: ~5 seconds (Dafny) vs ~4ms (native Python)
- Primary cost: O(n) immutable sequence operations where native Python uses O(1) mutable list operations

Meanwhile, a strong LLM can generate a naive Python implementation of the same problem in 28 seconds with 2,819 tokens — functionally correct on all tests, running at native speed — but with only runtime assertions, not mathematical proofs.

This creates a fundamental tension: **verified code you can't deploy vs. fast code you can't prove.**

---

## 2. Verified Compilers

### CompCert (Leroy, 2006–present)

The canonical verified compiler. CompCert compiles C to assembly with a machine-checked (Coq) proof that the compiled code preserves the semantics of the source. It does not prove programs correct — it proves the *translation* correct. CompCert includes optimization passes (constant propagation, dead code elimination, register allocation), each with a Coq correctness proof.

**Relevance**: CompCert demonstrates that optimization and verification can coexist, but the approach requires enormous engineering effort per optimization pass. Each new pass requires a new Coq proof. CompCert targets C→assembly; no equivalent exists for Dafny→Python/JS/etc.

**Key paper**: Leroy, X. "A Formally Verified Compiler Back-end." *Journal of Automated Reasoning* 43(4), 2009.

### CakeML (Kumar et al., 2014–present)

A verified compiler for a functional language (ML subset), producing verified machine code for ARM, x86, etc. The entire compiler is verified in HOL4. CakeML is significant because it closes the verification gap end-to-end: if your program type-checks in CakeML, and you prove properties about it, those properties hold for the running binary.

**Relevance**: CakeML is the most complete verified compiler stack. Recent work connects it to Dafny (see §3).

**Key paper**: Kumar, R. et al. "CakeML: A Verified Implementation of ML." *POPL 2014*.

---

## 3. Dafny Compiler Backends

### Verified VCG and Compiler for Dafny → CakeML (Nezamabadi et al., CPP 2026)

ETH Zurich. Builds a verified verification condition generator (VCG) and compiler backend from Dafny to CakeML. The approach verifies both the proof pipeline (VCG) and the compilation pipeline in a single framework. Currently covers a subset of Dafny (DafnyLight) but establishes the theoretical foundation for a fully verified Dafny→native compilation path.

**Relevance**: This is the strongest existing answer to Dafny's performance problem — if the compiler itself is verified, its output can be trusted at native speed. The limitation is coverage: DafnyLight is a small subset, and extending to full Dafny is a multi-year effort.

**Key paper**: Nezamabadi, S. et al. "Verified Verification Condition Generation and Compilation for Dafny." *CPP 2026*.

### "Baking for Dafny" — CakeML Backend Exploration

A line of work exploring CakeML as a Dafny compilation target. The idea: Dafny verifies correctness at the source level, CakeML's verified compiler ensures the translation preserves semantics, and the output runs at native speed. This is the clean theoretical solution but depends on the Nezamabadi et al. work reaching full Dafny coverage.

### Dafny as Verification-Aware Intermediate Language (POPL 2025)

Proposes using Dafny not as a source language but as an IL — other languages compile *into* Dafny for verification, then Dafny compiles out to the target. This reframes the compiler question: if Dafny is an IL, optimizing its output matters more, and there's a larger community motivated to do so.

**Key paper**: Leino, K.R.M. et al. "Dafny as Verification-Aware Intermediate Language." *POPL 2025*.

---

## 4. Translation Validation

Translation validation takes the opposite approach from verified compilation: instead of proving the compiler correct once, you verify each specific compilation result.

### Alive2 (Lopes et al., 2021)

LLVM's translation validation framework. For each LLVM optimization pass, Alive2 checks that the output is semantically equivalent to the input using SMT solving. This found hundreds of bugs in LLVM's optimizer.

**Relevance**: Alive2's pattern — "transform, then verify the transformation" — is directly applicable to optimizing Dafny output. Instead of proving the optimizer correct, prove each optimized output equivalent to the verified original. The challenge is defining semantic equivalence for high-level languages (Python, JS) rather than LLVM IR.

**Key paper**: Lopes, N.P. et al. "Alive2: Bounded Translation Validation for LLVM." *PLDI 2021*.

### LLM-Based Code Translation Needs Formal Compositional Reasoning (Cheung et al., Berkeley, 2025)

Analyzes why LLM-based code translation fails and proposes formal compositional reasoning as the fix. Key insight: LLMs can translate individual functions well but fail on compositions because they don't track semantic invariants across function boundaries. Proposes using formal specifications to guide translation and validate results.

**Relevance**: Directly addresses the prove-optimize-prove pattern. If you have a formal specification (from Dafny), you can use it to validate that an optimized translation preserves the required properties — even if the optimized version looks completely different from the original.

**Key paper**: Cheung, A. et al. "Code Translation with Compositional Formal Reasoning." *arXiv 2025*.

---

## 5. Annotation-Aware Optimization

### Alpinist (ETH Zurich / VerCors, 2024)

Transforms annotated programs (with pre/postconditions and loop invariants) for GPU execution while preserving both the code's correctness and the proof annotations. The key insight: when you optimize verified code, you must transform the proofs alongside the code, or the verification breaks.

**Relevance**: Alpinist demonstrates that proof-preserving optimization is tractable for specific transformation classes (parallelization). The limitation: it handles a fixed set of transformations, not arbitrary optimization.

**Key paper**: Dardinier, T. et al. "Alpinist: An Annotation-Aware GPU Program Optimizer." *OOPSLA 2024*.

---

## 6. LLM-Guided Verified Optimization

### VecTrans (NeurIPS 2024)

Uses LLMs to propose vectorization transformations, then formally verifies that each transformation preserves program semantics. The verification acts as a filter: the LLM generates candidates (high recall, low precision), and the verifier eliminates incorrect ones.

**Relevance**: This is the closest existing work to a prove-optimize-prove system. The LLM proposes optimizations, formal methods validate them. VecTrans is limited to vectorization; the pattern generalizes.

**Key paper**: Xu, P. et al. "VecTrans: LLM-Guided Vectorization with Formal Verification." *NeurIPS 2024*.

### LLMLift (NeurIPS 2024)

Uses LLMs to lift low-level code (C, assembly) to high-level verified representations, enabling formal reasoning about legacy code. The reverse of Dafny compilation: instead of verified→fast, it goes fast→verified.

**Relevance**: LLMLift's approach — using LLMs to bridge between representations while maintaining formal guarantees — is directly relevant to optimizing Dafny output. If an LLM can lift assembly to Dafny, it can also translate Dafny-compiled Python to optimized Python while preserving the specification.

**Key paper**: Chua, Z.L. et al. "LLMLift: Lifting Low-Level Code to High-Level Verified Representations." *NeurIPS 2024*.

### ASPEN: E-Graph Equality Saturation with LLM-Guided Rewriting (2025)

Uses LLMs to propose rewrite rules for e-graph equality saturation — a technique that explores all equivalent forms of an expression simultaneously. The LLM generates candidate rewrites, which are validated for semantic equivalence before being added to the e-graph.

**Relevance**: E-graph methods find provably equivalent but more efficient program representations. Combined with LLM-generated rewrite rules, this could systematically optimize Dafny output while maintaining equivalence to the verified source.

### LGuess: LLM-Guided Equality Saturation (2025)

Similar to ASPEN but focused on using LLMs to discover domain-specific rewrite rules. The key contribution is showing that LLMs can propose rewrites that humans would not think of, while equality saturation guarantees that only semantically valid rewrites are applied.

---

## 7. Synthesis: The Prove-Optimize-Prove Pattern

The literature converges on a pattern we call **prove-optimize-prove**:

1. **Prove**: Establish correctness formally (Dafny verification, Coq proof, etc.)
2. **Optimize**: Transform the verified code for performance (LLM-guided, rule-based, or manual)
3. **Prove**: Verify that the optimized code preserves the original specification

This pattern appears in different forms across the literature:

| Approach | Step 1 | Step 2 | Step 3 |
|----------|--------|--------|--------|
| CompCert | C source verified | Optimizing compilation | Each pass proved correct |
| Alive2 | LLVM IR semantics | Optimization passes | Translation validation |
| VecTrans | Program semantics | LLM proposes vectorization | Formal equivalence check |
| Alpinist | Annotated program | GPU transformation | Annotations transformed too |
| This proposal | Dafny verification | LLM optimizes output | Re-verify against spec |

### What's Missing

No existing system combines all three elements needed for Dafny output optimization:

1. **A formal specification** (Dafny provides this)
2. **An LLM-guided optimizer** that proposes performance transformations (VecTrans/ASPEN patterns)
3. **A validation step** that checks the optimized code against the original specification (translation validation / equivalence checking)

The closest work is VecTrans (LLM + verification for a specific optimization) and Cheung et al. (formal compositional reasoning for code translation). Neither targets the specific case of optimizing verified Dafny output.

### The Naive-First Variant

An alternative framing inverts the pipeline entirely: instead of **spec → proof → optimize**, start with a **strong naive implementation** and then model and prove it. This is motivated by the observation that LLMs produce high-quality imperative code when unconstrained, while verification-first pipelines force decompositions that don't match training data patterns. The sequence becomes:

1. **Generate**: LLM produces fast, idiomatic code from requirements
2. **Model**: Extract or generate a formal specification that captures the code's intended behavior
3. **Prove**: Verify the implementation against the specification (or find bugs and fix them)

This inverts Dijkstra's prescription but may be more practical: the LLM's strength is code generation, not formal reasoning. Use it where it's strong (step 1), then use formal tools where *they're* strong (step 3). The specification serves as a bridge between the two.

---

## 8. Key Takeaways

1. **The Dafny performance problem is real and acknowledged** — the community is actively working on verified compilation (CakeML backend) but full coverage is years away.

2. **Translation validation is more tractable than verified compilation** — proving each transformation correct (Alive2 pattern) requires less upfront engineering than proving the compiler correct once (CompCert pattern).

3. **LLMs are effective at proposing optimizations** — VecTrans, ASPEN, and LGuess demonstrate that LLMs can generate transformation candidates that formal methods then validate.

4. **Proof-preserving transformation is possible** — Alpinist shows that annotations (pre/postconditions, invariants) can be transformed alongside code, but only for specific transformation classes.

5. **The naive-first path may outperform spec-first for strong models** — when the LLM can generate correct code directly, retroactive verification (generate → model → prove) avoids the performance penalties of verification-first compilation while still producing formal guarantees.

6. **No existing system targets Dafny output optimization** — this is a gap in the literature that Proven is positioned to fill.

---

## References

- Cheung, A. et al. "Code Translation with Compositional Formal Reasoning." arXiv, 2025.
- Chua, Z.L. et al. "LLMLift: Lifting Low-Level Code to High-Level Verified Representations." NeurIPS, 2024.
- Dardinier, T. et al. "Alpinist: An Annotation-Aware GPU Program Optimizer." OOPSLA, 2024.
- Kumar, R. et al. "CakeML: A Verified Implementation of ML." POPL, 2014.
- Leino, K.R.M. et al. "Dafny as Verification-Aware Intermediate Language." POPL, 2025.
- Leroy, X. "A Formally Verified Compiler Back-end." Journal of Automated Reasoning, 43(4), 2009.
- Lopes, N.P. et al. "Alive2: Bounded Translation Validation for LLVM." PLDI, 2021.
- Nezamabadi, S. et al. "Verified VCG and Compilation for Dafny." CPP, 2026.
- Xu, P. et al. "VecTrans: LLM-Guided Vectorization with Formal Verification." NeurIPS, 2024.
