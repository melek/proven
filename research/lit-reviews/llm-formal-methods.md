# Literature Review: LLM-Driven Software Development with Formal Methods

*A survey of projects combining large language models with formal verification, proof-first development, and correct-by-construction approaches.*

*Compiled: 2026-02-21*

---

## 1. Overview

The convergence of LLMs and formal methods is happening fast. What was theoretical in 2023 has become a rich ecosystem of tools, benchmarks, startups, and research programs by early 2026. However, nearly all work falls into one of two patterns:

- **LLM → code → verify** (generate code, then check it with a formal tool)
- **LLM generates annotations** (add invariants/proofs to existing code)

Almost nobody is doing the Dijkstra-style pipeline:

- **Spec → proof → code** (derive the program from the specification)

And nobody is doing LLM-assisted stepwise refinement (B-Method style). This represents a significant white space.

---

## 2. LLM + Dafny (Most Active Ecosystem)

Dafny has become the primary target for LLM + formal verification research, with dedicated workshops at POPL 2024, 2025, and 2026.

### dafny-replay / MIDSPIRAL (2025) — Closest to Proven's Vision

Harvard (Nada Amin's metareflection group) + a React developer. Uses Claude Code (Opus 4.5) to write verified Dafny code that compiles to JavaScript for web applications. The workflow: specify intent → translate to formal property → LLM generates Dafny implementation → Dafny verifies → compile to JS.

This is the closest existing project to a practical "LLM coding agent with formal methods."

- Maturity: Open-source prototype
- GitHub: [metareflection/dafny-replay](https://github.com/metareflection/dafny-replay)
- Blog: [midspiral.com](https://midspiral.com/blog/from-intent-to-proof-dafny-verification-for-web-apps/)

### Dafny as Verification-Aware Intermediate Language (POPL 2025)

Users guide LLMs to generate code in Dafny as an opaque intermediate representation. Dafny verifies correctness against specifications, then compiles to the target language. Users never see Dafny code — all interaction is in natural language. Closest to a spec → proof → code workflow.

- Maturity: Prototype, tested on HumanEval
- Paper: [arXiv 2501.06283](https://arxiv.org/abs/2501.06283)

### DafnyPro (Dafny Workshop at POPL 2026)

Inference-time framework for generating verification annotations in Dafny. Uses Claude Sonnet 3.5/3.7. Achieves 86% correct proofs on DafnyBench.

- Maturity: Research prototype
- Paper: [arXiv 2601.05385](https://arxiv.org/abs/2601.05385)

### dafny-annotator (2024–2025)

From Harvard/metareflection. Uses LLMs and search to add logical annotations (assertions, invariants, decreases clauses) to Dafny methods. Fine-tuned LLaMa 8B reaches 50.6% annotation success.

- GitHub: [metareflection/dafny-annotator](https://github.com/metareflection/dafny-annotator)
- Paper: [arXiv 2411.15143](https://arxiv.org/abs/2411.15143)

### Laurel (2024–2025)

Automatically generates assertions using LLMs to unblock Dafny's SMT solver. 56.6% success on real-world Dafny lemmas.

- Paper: [arXiv 2405.16792](https://arxiv.org/abs/2405.16792)

### ATLAS Toolkit (Dafny Workshop at POPL 2026)

Automated pipeline that synthesizes verified Dafny programs at scale to address the training data bottleneck.

- Paper: [arXiv 2512.10173](https://arxiv.org/abs/2512.10173)

### Dafny-Synthesis (FSE 2024)

153 verified Dafny solutions to MBPP problems. GPT-4 generated verified methods for 58% of problems.

- GitHub: [Mondego/dafny-synthesis](https://github.com/Mondego/dafny-synthesis)

### Formalizing Requirements into Dafny Specifications with LLMs (2025)

Uses LLMs to transform natural language requirements into Dafny formal specifications.

- Paper: [Springer](https://link.springer.com/chapter/10.1007/978-981-95-4213-0_6)

### PREFACE (2025)

Trains a small RL agent to steer a frozen general-purpose LLM toward generating formally verified Dafny code, without LLM fine-tuning.

- Conference: [ACM GLSVLSI 2025](https://dl.acm.org/doi/10.1145/3716368.3735300)

### Benchmarks

| Benchmark | Size | What It Tests |
|---|---|---|
| DafnyBench | 782 programs | Annotation synthesis |
| Dafny-Synthesis | 153 problems | Code synthesis from specs |
| MINIF2F-Dafny | Math benchmark | First math benchmark in Dafny |
| Vericoding | 782 tasks | Cross-language (Lean/Verus/Dafny) |

---

## 3. LLM + Verus (Verified Rust)

### AutoVerus (Microsoft Research, OOPSLA 2025)

LLM agents that automatically generate correctness proofs for Rust code using Verus. Mimics human expert proof construction in three phases. 90%+ success, with over half solved in under 30 seconds.

- GitHub: [microsoft/verus-proof-synthesis](https://github.com/microsoft/verus-proof-synthesis)
- Paper: [arXiv 2409.13082](https://arxiv.org/abs/2409.13082)

### SAFE (Microsoft Research, 2024)

Fine-tunes DeepSeekCoder to synthesize specifications and proofs for Rust. Produced 19,017 formal specifications and 9,706 verified Rust functions.

### VeriStruct (2025)

Extends AI-assisted verification to complete data structure modules in Verus. 99.2% success (128/129 functions).

- Paper: [arXiv 2510.25015](https://arxiv.org/html/2510.25015)

---

## 4. LLM + Lean 4 (Math Proofs, Not Software Engineering)

Lean 4 dominates the LLM + formal reasoning space, but almost all work targets **mathematical theorem proving**, not software engineering.

### DeepSeek-Prover-V2 (April 2025)

671B parameter model. 88.9% on MiniF2F-test, 49/658 on PutnamBench. Uses recursive decomposition.

- GitHub: [deepseek-ai/DeepSeek-Prover-V2](https://github.com/deepseek-ai/DeepSeek-Prover-V2)

### Seed-Prover 1.5 (ByteDance, 2025)

11/12 Putnam 2025 problems, 5/6 IMO 2025 problems. Large-scale RL training.

- GitHub: [ByteDance-Seed/Seed-Prover](https://github.com/ByteDance-Seed/Seed-Prover)

### AlphaProof (Google DeepMind, Nature November 2025)

RL-based system, silver medal at 2024 IMO. AlphaZero-inspired architecture.

- Paper: [Nature](https://www.nature.com/articles/s41586-025-09833-y)

### Apple Hilbert (2025)

Hierarchical agent bridging formal and informal reasoning. 99.2% on miniF2F, 70.0% on PutnamBench (20 points above previous SOTA).

- Paper: [Apple ML Research](https://machinelearning.apple.com/research/hilbert)

### LeanDojo / LeanCopilot (2025)

Open-source framework for AI-assisted theorem proving. VS Code extension for proof automation.

- Website: [leandojo.org](https://leandojo.org/)
- GitHub: [lean-dojo/LeanCopilot](https://github.com/lean-dojo/LeanCopilot)

**Gap:** Nobody is using Lean 4 for verified software engineering in the way Dafny and Verus are being used.

---

## 5. LLM + Coq/Rocq

### SYNVER (Purdue, 2024–2025)

Synthesizes formally verified C programs using two LLMs: one generates candidate C programs from specifications, the other constructs machine-checked proofs in Rocq using the Verified Software Toolchain (VST). Takes separation logic specifications as input.

- Paper: [arXiv 2410.14835](https://arxiv.org/abs/2410.14835)
- Website: [Purdue SynVer](https://www.cs.purdue.edu/homes/bendy/SynVer/index.html)

### AutoRocq (November 2025)

First LLM agent for program verification in Rocq. Learns on-the-fly. Tested on SV-COMP benchmarks and Linux kernel modules.

- Paper: [arXiv 2511.17330](https://arxiv.org/abs/2511.17330)

### CoqPilot (ASE 2024)

VS Code extension for automated Coq proof generation.

- Conference: [ACM ASE 2024](https://dl.acm.org/doi/10.1145/3691620.3695357)

### Formal Land (2025)

Building an integrated Rocq coding assistant in VS Code. EU/Erasmus funded.

- Website: [formal.land](https://formal.land/blog/2025/01/21/designing-a-coding-assistant-for-rocq)

---

## 6. LLM + C Verification (Frama-C)

### VeCoGen (November 2024)

Generates formally verified C programs using Frama-C WP plugin. Solves 13/15 Codeforces problems.

- GitHub: [ASSERT-KTH/Vecogen](https://github.com/ASSERT-KTH/Vecogen)

### AutoICE (December 2025)

LLM-driven evolutionary search for verified C code. 90.36% verification rate.

- Paper: [arXiv 2512.07501](https://arxiv.org/abs/2512.07501)

---

## 7. LLM + Specification Synthesis

### AutoSpec (CAV 2024)

LLMs + static analysis to synthesize satisfiable and adequate specifications for full proof.

- Paper: [Springer CAV 2024](https://link.springer.com/chapter/10.1007/978-3-031-65630-9_16)

### LEMUR (2023)

Hybrid framework combining LLMs with Z3 SMT solver for loop invariant generation. Achieved 107/133 on Code2Inv benchmark.

- Paper: [arXiv 2310.04870](https://arxiv.org/abs/2310.04870)

### Hybrid LLM + SMT Loop Invariant Framework (2025)

Combines reasoning-optimised LLMs (O1, O3-mini) with Z3 SMT solver. 100% coverage (133/133) on Code2Inv benchmark.

- Paper: [arXiv 2508.00419](https://arxiv.org/abs/2508.00419)

### Quokka (September 2025)

Framework for LLM-based loop invariant synthesis. Evaluated on 866 instances across 9 LLMs.

- Paper: [arXiv 2509.21629](https://arxiv.org/abs/2509.21629)

### ClassInvGen (2025)

Co-generates executable class invariants and test inputs for C++. Perfect accuracy with test co-generation.

- Paper: [arXiv 2502.18917](https://arxiv.org/abs/2502.18917)

---

## 8. LLM + SPARK Ada

### Marmaragan (February 2025)

Explores LLM-generated annotations for SPARK 2014 Ada. Demonstrates feasibility, proposes future direction of LLMs generating pre/postconditions.

- Paper: [arXiv 2502.07728](https://arxiv.org/abs/2502.07728)

---

## 9. LLM + Stepwise Refinement

**This is the thinnest area — essentially unexplored.**

No direct work on LLMs performing B-Method or Event-B style stepwise refinement was found. The closest:

- **SR-Eval** (September 2025) — Evaluates LLMs on code generation under stepwise *requirement* refinement, but this is requirements refinement, not formal refinement in the B-Method sense. [arXiv 2509.18808](https://arxiv.org/html/2509.18808)
- **Formal requirements engineering + LLMs** (2025) — Roadmap paper. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0950584925000369)

**Assessment:** B-Method / Event-B style refinement with LLMs is a significant white space and differentiated research opportunity.

---

## 10. The Argument for Formal Methods as "Test Oracle" for AI

This argument is gaining serious mainstream traction.

### Martin Kleppmann (December 2025)

"Prediction: AI will make formal verification go mainstream." Core argument: proof scripts are ideal for LLMs because the proof checker rejects invalid proofs — hallucinations don't matter. AI creates both the supply (cheaper proofs) and demand (need to verify AI-generated code).

- URL: [martin.kleppmann.com](https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html)

### Ben Congdon (December 2025)

"The Coming Need for Formal Specification." Engineers should transition from writing implementation to writing specifications. Proposes: English specs → TLA+ models → formal proofs for critical paths → LLM audits for the rest.

- URL: [benjamincongdon.me](https://benjamincongdon.me/blog/2025/12/12/The-Coming-Need-for-Formal-Specification/)

### Atlas Computing

Proposes a modular AI-assisted FV toolchain with components: GenerateAndCheck, CorrectByConstruction, ProgramRepair, ProgramEquivalence. Argues AI could enable widespread FV use "in years not decades."

- URL: [atlascomputing.org](https://atlascomputing.org/ai-assisted-fv-toolchain.pdf)

### The 4/δ Bound (December 2025)

First formal framework with provable guarantees for termination in multi-stage LLM-verifier pipelines. Mathematical basis for when LLM + verifier loops converge.

- Paper: [arXiv 2512.02080](https://arxiv.org/abs/2512.02080)

---

## 11. Startups and Organizations

### Well-Funded

| Company | Funding | Focus | Tool |
|---|---|---|---|
| **Harmonic** | $120M Series C, $1.45B valuation (Nov 2025) | Mathematical superintelligence | Lean 4 |
| **Logical Intelligence** | Undisclosed, Yann LeCun on board (Jan 2026) | Code → proof verification | Aleph (proprietary) |

### Emerging (from FMxAI 2025 at SRI)

Eight new organizations founded in the past year at the FM + AI intersection:

- Math Inc.
- Theorem Labs
- Sigil Logic
- Principia Labs
- Axiom Math
- Safer-AI
- Ulyssean
- genproof.ai

### Nonprofit / Research

| Organization | Focus |
|---|---|
| **Atlas Computing** | AI safety through formal verification; Specification IDE |
| **Formal Land** | Rocq/Coq coding assistant (EU funded) |

---

## 12. Major Lab Involvement

| Lab | Projects | Focus |
|---|---|---|
| **Microsoft Research** | AutoVerus, Verus, SAFE | Verified Rust |
| **Amazon / AWS** | Cedar + Dafny, Bedrock Guardrails AR checks | Verified authorization, LLM output checking |
| **Google DeepMind** | AlphaProof | Math theorem proving (Lean) |
| **Apple** | Hilbert | Math theorem proving (Lean) |
| **ByteDance** | Seed-Prover | Math theorem proving (Lean) |
| **INRIA** | LLM4Code, FORMAL, FRAIME (with Mitsubishi) | Verified code assistants, ML in Lean |
| **NSF** | AIMing program (NSF 24-554) | Funding for AI + formal methods research |

Meta FAIR is notably quiet in this specific intersection.

---

## 13. Amazon/AWS Specifically

AWS has the deepest industrial integration of formal methods and is beginning to combine with LLMs:

**Current FM infrastructure (production):**
- Cedar authorization language — designed for automated reasoning, implemented in Dafny
- AWS authorization engine — modeled as Dafny functions with proven properties
- Over a decade of automated reasoning applied to cloud infrastructure

**LLM integration:**
- Automated Reasoning Checks in Amazon Bedrock Guardrails — uses formal verification to validate LLM outputs against domain knowledge. Claims up to 99% accuracy at detecting correct LLM responses. This is formal methods *checking* LLM outputs, not LLMs *generating* formal proofs.

**Assessment:** No public evidence of AWS using LLMs to generate Dafny code/proofs internally, but given their investment in both areas, this seems likely to be happening privately.

---

## 14. What Nobody Is Doing (White Spaces)

1. **LLM-assisted stepwise refinement.** No work on B-Method or Event-B style refinement with LLMs. The most systematic end-to-end formal development process has zero LLM tooling.

2. **LLM-driven correct-by-construction derivation.** Nobody is using LLMs to perform Dijkstra-style program derivation (postcondition → weakest precondition → program emerges). The CorC tool exists but has no LLM integration.

3. **Requirements → formal spec → proof → code (fully automated).** The closest is the POPL 2025 "Dafny as intermediate language" paper and MIDSPIRAL, but neither covers the full pipeline systematically.

4. **LLM + F\*.** Despite F*'s Dijkstra monads and HACL* success, no one is building LLM tools for it.

5. **LLM-assisted choice of refinement strategy.** The human decisions in B-Method (choosing invariants, decompositions, data representations) are exactly the kind of constrained choices LLMs could propose and rank, but nobody is working on this.

---

## 15. Implications for Proven

The landscape validates the Proven project's direction but reveals that the specific approach — Dijkstra-style derivation with LLM assistance — is largely unexplored. Key observations:

1. **Dafny is the right ecosystem.** It has the most LLM tooling, the most active research community (POPL workshops), and the MIDSPIRAL project demonstrates the closest existing analog to what Proven envisions.

2. **The "generate and verify" pattern dominates** but is not what Proven is about. Most tools do LLM → code → verify. Proven's spec → proof → code is differentiated.

3. **Refinement is the biggest opportunity.** Nobody is combining LLMs with stepwise refinement. An LLM that proposes refinement steps (and a formal tool that checks them) would be novel.

4. **The argument for this approach is gaining mainstream support.** Kleppmann, Congdon, and Atlas Computing are all publicly arguing that formal specification should replace testing as the primary quality mechanism for AI-generated code. The intellectual climate is favorable.

5. **The economics work.** Martin Kleppmann's key insight: proof scripts are ideal LLM targets because the checker rejects hallucinations deterministically. Retry is cheap. This makes the LLM + formal verifier loop fundamentally more reliable than the LLM + test suite loop.

---

## References

### Key Papers
- DafnyPro: [arXiv 2601.05385](https://arxiv.org/abs/2601.05385)
- Dafny as Intermediate Language: [arXiv 2501.06283](https://arxiv.org/abs/2501.06283)
- dafny-annotator: [arXiv 2411.15143](https://arxiv.org/abs/2411.15143)
- Laurel: [arXiv 2405.16792](https://arxiv.org/abs/2405.16792)
- AutoVerus (OOPSLA 2025): [arXiv 2409.13082](https://arxiv.org/abs/2409.13082)
- SYNVER: [arXiv 2410.14835](https://arxiv.org/abs/2410.14835)
- AutoRocq: [arXiv 2511.17330](https://arxiv.org/abs/2511.17330)
- VeCoGen: [arXiv 2411.19275](https://arxiv.org/abs/2411.19275)
- DeepSeek-Prover-V2: [arXiv 2504.21801](https://arxiv.org/abs/2504.21801)
- AlphaProof: [Nature](https://www.nature.com/articles/s41586-025-09833-y)
- LEMUR: [arXiv 2310.04870](https://arxiv.org/abs/2310.04870)
- Hybrid LLM+SMT Loop Invariants: [arXiv 2508.00419](https://arxiv.org/abs/2508.00419)
- The 4/δ Bound: [arXiv 2512.02080](https://arxiv.org/abs/2512.02080)
- AI + Formal Methods Survey: [arXiv 2411.14870](https://arxiv.org/abs/2411.14870)
- Marmaragan (SPARK): [arXiv 2502.07728](https://arxiv.org/abs/2502.07728)
- ATLAS Toolkit: [arXiv 2512.10173](https://arxiv.org/abs/2512.10173)
- MINIF2F-Dafny: [arXiv 2512.10187](https://arxiv.org/abs/2512.10187)
- Vericoding: [arXiv 2509.22908](https://arxiv.org/abs/2509.22908)
- Requirements to Dafny Specs: [Springer](https://link.springer.com/chapter/10.1007/978-981-95-4213-0_6)
- Formal Requirements + LLMs Roadmap: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0950584925000369)

### Key Blog Posts and Reports
- Kleppmann: [AI will make formal verification go mainstream](https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html)
- Congdon: [The Coming Need for Formal Specification](https://benjamincongdon.me/blog/2025/12/12/The-Coming-Need-for-Formal-Specification/)
- Atlas Computing: [AI-Assisted FV Toolchain](https://atlascomputing.org/ai-assisted-fv-toolchain.pdf)
- MIDSPIRAL: [From Intent to Proof](https://midspiral.com/blog/from-intent-to-proof-dafny-verification-for-web-apps/)
- Dafny Blog: [dafny-annotator](https://dafny.org/blog/2025/06/21/dafny-annotator/)

### GitHub Repositories
- [metareflection/dafny-replay](https://github.com/metareflection/dafny-replay)
- [metareflection/dafny-annotator](https://github.com/metareflection/dafny-annotator)
- [microsoft/verus-proof-synthesis](https://github.com/microsoft/verus-proof-synthesis)
- [deepseek-ai/DeepSeek-Prover-V2](https://github.com/deepseek-ai/DeepSeek-Prover-V2)
- [ByteDance-Seed/Seed-Prover](https://github.com/ByteDance-Seed/Seed-Prover)
- [lean-dojo/LeanCopilot](https://github.com/lean-dojo/LeanCopilot)
- [ASSERT-KTH/Vecogen](https://github.com/ASSERT-KTH/Vecogen)
- [Mondego/dafny-synthesis](https://github.com/Mondego/dafny-synthesis)

### Organizations
- [Atlas Computing](https://atlascomputing.org/projects/)
- [Formal Land](https://formal.land/)
- [Harmonic](https://harmonic.fun/)
- [NSF AIMing](https://www.nsf.gov/funding/opportunities/aiming-artificial-intelligence-formal-methods-mathematical/nsf24-554/solicitation)
- [INRIA LLM4Code](https://www.inria.fr/en/llm4code)
