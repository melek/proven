# Literature Review: Proof-First & Requirements-Based Software Development Frameworks

*A survey of formal-methods-based alternatives to test-driven development, evaluated by maturity and industrial track record.*

*Compiled: 2026-02-21*

---

## 1. Introduction

Test-driven development (TDD) treats testing as the primary quality gate: write a failing test, write code to pass it, refactor. This is fundamentally reactive — bugs are found, not prevented.

An alternative tradition, rooted in Edsger Dijkstra's *A Discipline of Programming* (1976), inverts the process: **derive programs from specifications and proofs, so correctness is structural rather than empirical.** Requirements are formalized. Proof obligations are discharged. Code emerges from the proof, not the other way around.

This review surveys 18 frameworks and tools in this tradition, organized into three categories:

1. **Refinement-based methods** — Abstract specifications refined stepwise into implementations
2. **Verification-aware programming languages** — Languages where proofs are first-class
3. **Methodological frameworks** — Process-level approaches to correct-by-construction development

Each is evaluated on: origin and institutional backing, industrial adoption, community activity, documentation quality, learning curve, code output, and notable successes. The goal is to identify which are **most proven and mature** — not just theoretically sound, but battle-tested in production.

---

## 2. Refinement-Based Methods

These methods follow the classical formal development chain: abstract specification → stepwise refinement → executable code. Each refinement step generates proof obligations.

### 2.1 B-Method / Atelier B

**Origin:** Jean-Raymond Abrial, late 1980s. Industrialized by CLEARSY (founded 2001). Based on set theory and first-order predicate logic.

**Industrial track record:** The strongest of any refinement method.

- **Paris Metro Line 14 (Meteor):** Fully automated driverless metro, operational since October 1998. Safety-critical software proven correct with Atelier B. Of 27,800 lemmas, ~90% discharged automatically. **Zero defects found in 25+ years of continuous operation** — not during validation, integration, on-site testing, or revenue service. The software remained at version 1.0 through at least 2007.
- **Paris Metro Lines 1, 4, 13:** Subsequent automation projects.
- **Railway signaling worldwide:** Adopted by Alstom, Siemens, RATP — from Meteor (1998) to Octys (2016).
- **Semiconductor certification:** ATMEL, STMicroelectronics (Common Criteria).
- Applied across automotive, banking, space, and nuclear domains.

**Active development:** Atelier B has T2 certification for railway applications. CLEARSY presented at FMICS 2024 (29th International Conference on Formal Methods for Industrial Critical Systems). A 2024 paper documents the current state: *Formal Methods in Industry* (CLEARSY).

**Code output:** Generates C and Ada from proven specifications.

**Learning curve:** Steep. Requires set theory, predicate logic, and refinement concepts. Community is historically French-speaking.

**Assessment:** The Paris Metro Line 14 result — zero defects over 25 years — is arguably the single most compelling data point in all of formal methods. No other methodology can point to a comparable deployed outcome.

### 2.2 Event-B / Rodin Platform

**Origin:** Jean-Raymond Abrial (successor to B-Method). Shifts focus from software refinement to system-level modeling. Rodin Platform developed through EU projects: Rodin (2004–2007), Deploy (2008–2012), ADVANCE (2011–2014). Based at University of Southampton and ETH Zurich.

**Industrial adoption:**

- **Railway:** Siemens Transportation (train control/signaling), Systerel (railway, aerospace)
- **Automotive:** Bosch (cruise control, start-stop systems)
- **Aerospace:** Space Systems Finland (BepiColombo space probe — Attitude and Orbit Control System)
- **Medical:** QNX Software Systems (medical device software, safety case evidence)

**Active development:** Rodin 3.10 is current. The 12th Rodin Workshop was held in June 2025. The ABZ conference series (covering ASM, B, and Z methods) held its 10th edition in 2024 (Bergamo, Italy). Rodin is extensible via plugins for UML modeling, model-checking, simulation, requirements traceability, and code generation.

**Documentation:** Multiple tutorials, a comprehensive wiki, and Abrial's textbook *Modeling in Event-B: System and Software Engineering* (Cambridge University Press, 2010).

**Code output:** Code generation available through plugins, though less mature than Atelier B's direct generation. More oriented toward system-level modeling and proof.

**Learning curve:** Moderate to steep. Eclipse-based IDE adds some accessibility.

**Assessment:** Inherits B-Method credibility. The BepiColombo space probe and Siemens railway work are notable. Stronger for system modeling than direct code production.

### 2.3 Abstract State Machines (ASM)

**Origin:** Yuri Gurevich (University of Michigan, 1980s–1990s). Methodologically championed by Egon Börger (University of Pisa). Definitive text: *Abstract State Machines: A Method for High-Level System Design and Analysis* (Börger and Stärk, Springer 2003).

**Industrial adoption:** Applied to specifying semantics of Java and C#, hardware verification, protocol verification, and business process modeling. Less broadly adopted than B-Method or SPARK.

**Active development:** The ASMETA tool suite supports Eclipse IDE integration, specification editing, simulation, and verification. Asmeta2Java (2024) enables automatic translation to executable Java. CoreASM provides an open-source execution engine.

**Code output:** Java via Asmeta2Java. Less industrially mature than alternatives.

**Assessment:** Solid theoretical foundations and useful for specification work, but lacks a dramatic industrial success story. Primarily academic.

### 2.4 Vienna Development Method (VDM)

**Origin:** IBM Vienna Laboratory, 1970s, for specifying the PL/I language. One of the oldest formal methods. VDM-SL standardized as ISO/IEC 13817-1 (1996). VDM++ adds object-oriented constructs.

**Active development:** The Overture Tool (open-source Eclipse IDE) saw updates in late 2025. A VS Code extension is available. The INTO-CPS project uses VDM for co-simulation of cyber-physical systems.

**Code output:** VDM specifications can be animated and executed. Overture supports Java code generation. FMI interface enables simulation integration.

**Assessment:** Historically significant but lacks a single compelling modern success story. The INTO-CPS co-simulation work represents the most active current application. Declining industrial adoption relative to newer tools.

### 2.5 Z Notation

**Origin:** Oxford University Programming Research Group, early 1980s. Developed by Jean-Raymond Abrial (before B-Method), C.A.R. Hoare, and others. Based on Zermelo-Fraenkel set theory. Standardized as ISO/IEC 13568:2002.

**Notable applications:**

- **IBM CICS:** Customer Information Control System specified in Z (not mechanically verified).
- **Mondex Smart Card:** Electronic purse formally verified to ITSEC Level E6, requiring ~200 pages of proofs. Found implementation bugs in original design.

**Active development:** Low. Community Z Tools (CZT) exists but tool support is identified as a major adoption barrier.

**Code output:** Primarily a specification language. Refinement to code is manual.

**Assessment:** Important historically and pedagogically. The Mondex verification is notable. But Z has been largely superseded by tools with better automation and code generation. Not recommended for new projects.

---

## 3. Verification-Aware Programming Languages

These are programming languages where specifications, proofs, and executable code coexist in the same artifact. The specification-implementation gap is eliminated or minimized.

### 3.1 Dafny

**Origin:** K. Rustan M. Leino, Microsoft Research, 2008. Successor to ESC/Modula-3, ESC/Java, and Spec#. Uses Boogie intermediate verification language and Z3 SMT solver. Development support shifted to Amazon's Automated Reasoning group (~2022–2023), with Leino continuing at AWS.

**Industrial adoption — the strongest evidence for any verification-aware language:**

- **AWS Authorization Engine:** Invoked **1 billion times per second**, rewritten and formally verified in Dafny over four years, deployed in 2024 without incident. Customers saw 3x performance improvement. (*Formally Verified Cloud-Scale Authorization*, Amazon Science, 2024.)
- **Cedar Authorization Language:** AWS's open-source authorization policy language, implementation built in Dafny. Now a CNCF Sandbox project.
- **AWS Encryption Libraries:** Security-critical cryptographic code verified in Dafny.
- **smithy-dafny:** Dafny integrated with AWS's Smithy API framework.

**Active development:** Very active. ~3,300 GitHub stars. Dedicated workshops at POPL 2024, 2025, and planned 2026. Frequent releases. The dafny-annotator tool (2025) uses LLMs to automatically add logical annotations to Dafny methods.

**Code output:** Compiles to **C#, Go, Python, Java, and JavaScript**, with an **experimental Rust backend** under active development. This breadth of targets is unmatched among verification-aware languages.

**Documentation:** Excellent. Comprehensive tutorials, reference manual, blog, examples, and a free online textbook at dafny.org.

**Learning curve:** **The lowest of any verification-aware language.** Syntax resembles familiar imperative/OOP languages. Pre/postconditions and loop invariants are first-class. Z3 automates most proof obligations, reducing manual proof burden.

**Assessment:** The AWS authorization engine at 1 billion calls/second is the most significant industrial deployment of a verification-aware language at scale. Combined with the lowest learning curve, broadest compilation targets, excellent documentation, and active corporate backing (Amazon), Dafny is the most practical entry point for proof-first development today.

### 3.2 F* (F-star)

**Origin:** Microsoft Research and INRIA Paris. Features "Dijkstra monads" that compute weakest preconditions for effectful programs — literally named after Dijkstra. High-level, multi-paradigm, inspired by ML/OCaml with dependent types and effects.

**Industrial adoption — deployed on billions of devices:**

- **HACL\*:** Formally verified cryptographic library written in F*, compiled to C. Verified for memory safety, functional correctness, and secret independence. Deployed in:
  - **Mozilla Firefox**
  - **The Linux kernel**
  - **mbedTLS**
  - **Tezos blockchain**
  - **ElectionGuard voting SDK**
  - **WireGuard VPN**
- **EverCrypt:** Verified cryptographic provider combining HACL* and Vale (verified assembly).
- **StarMalloc** (SPLASH 2024): Verified concurrent memory allocator, drop-in replacement.
- **Verified OCaml garbage collector** (JAR 2025).

**Active development:** ~2,400 GitHub stars, 228 forks. Active research publication pipeline (PLDI 2025, SPLASH 2024, JAR 2025). PulseCore (PLDI 2025) adds concurrent separation logic. FStar Dataset v2.0 released for AI-assisted proof training.

**Code output:** Compiles to **C** (via Low*/KaRaMeL), **OCaml**, and **F#**. The C extraction is production-quality — HACL* demonstrates this.

**Learning curve:** Steep. Requires understanding of dependent types, effects, monads, and separation logic. Best suited for developers with strong PL theory backgrounds.

**Assessment:** HACL* in Firefox and the Linux kernel means F*-generated code runs on billions of devices — the broadest deployment footprint of any formally verified library. The Dijkstra monad connection makes it theoretically closest to Dijkstra's methodology. But the learning curve is significant.

### 3.3 Lean 4

**Origin:** Leonardo de Moura, Microsoft Research. Lean 4 (2021) is a complete reimplementation. The Lean Focused Research Organization (Lean FRO) was formed in 2023. De Moura moved to AWS.

**Industrial adoption:**

- **AWS Cedar:** Amazon uses Lean to formally verify the Cedar authorization policy language. Executable formal models in Lean are ~10x smaller than production Rust code. Millions of random inputs used for differential testing.
- **Mathematics:** "Unparalleled adoption in the mathematical community," surpassing all previous formal mathematics systems.

**Community:** **Largest among theorem provers.** ~7,300 GitHub stars. Mathlib: 210,000+ formalized theorems, 100,000+ definitions, 1.58 million lines of code, 300+ contributors. Won the 2025 ACM SIGPLAN Programming Languages Software Award. DeepSeek-Prover-V2 (April 2025) targets Lean 4 theorem proving.

**Code output:** Compiles to C, then native code. Efficient reference-counted memory management.

**Learning curve:** Steep for full theorem proving, but Lean 4 has invested heavily in usability. Excellent documentation including multiple free online textbooks.

**Assessment:** The largest and most active formal methods community. AWS Cedar verification is a strong industrial reference. However, Lean's strength is in mathematics and theorem proving — it's less directly oriented toward the specification→code pipeline than Dafny or SPARK.

### 3.4 Coq / Rocq

**Origin:** INRIA, 1989 (originally "Coq" after Thierry Coquand). **Renamed to The Rocq Prover** with Rocq 9.0 in March 2025. 200+ contributing researchers.

**Industrial adoption — some of the most significant verified artifacts in existence:**

- **CompCert:** Verified C compiler (ARM, PowerPC, RISC-V, x86). **Won the 2021 ACM Software System Award.** Version 3.16 supports Rocq 9.0.
- **CertiKOS:** Verified operating system kernel.
- **FSCQ:** Verified file system.
- **Four-Color Theorem** and **Feit-Thompson Theorem**: Formally verified via the Mathematical Components library.

**Community:** ~5,400 GitHub stars, 200+ contributors. Active development (Rocq 9.0, March 2025). Standard library split into Corelib and Stdlib. Regular community events. Extensive ecosystem via awesome-coq/awesome-rocq.

**Documentation:** Excellent. *Software Foundations* (Pierce et al.) is one of the most widely used free CS textbooks. *Certified Programming with Dependent Types* (Chlipala) provides advanced treatment.

**Code output:** Extracts to **OCaml, Haskell, and Scheme** (with type and proof erasure).

**Learning curve:** Steep. Requires learning Gallina, Ltac/Ltac2 tactic languages, and the Calculus of Inductive Constructions.

**Assessment:** CompCert winning the ACM Software System Award validates Coq/Rocq as a vehicle for producing real, deployed verified software. The prover is mature, the community is large, and the ecosystem is rich. However, the extraction pipeline targets functional languages, and the learning curve is substantial.

### 3.5 Isabelle/HOL

**Origin:** Lawrence Paulson (Cambridge, 1986), with Tobias Nipkow and Makarius Wenzel (TU Munich). Higher-Order Logic instantiation.

**Industrial adoption:**

- **seL4 Microkernel:** **First formal proof of functional correctness of a general-purpose OS kernel.** 200,000+ lines of proof script verifying 8,700 lines of C and 600 lines of assembler (per the SOSP 2009 paper). Now nearly 1 million lines of proof. seL4 Summit 2025 continues to drive adoption.
- **Intel and AMD:** Processor verification.
- **Cryptographic protocol verification.**

**Community:** Isabelle2025-2 is the latest release (with dark mode and VS Code support). The Archive of Formal Proofs (AFP) at isa-afp.org contains 500+ entries of formalized theories. Sledgehammer automates proof search via external provers.

**Code output:** Generates **SML, OCaml, Haskell, and Scala.** Mature code generation framework.

**Learning curve:** Steep but well-supported. The Isar proof language is relatively readable. *Concrete Semantics* (Nipkow and Klein) is a free online textbook.

**Assessment:** seL4 is a landmark result — the most complete OS kernel verification ever performed. The Archive of Formal Proofs is a substantial body of reusable verified work. Isabelle is a premier theorem prover with strong tool automation.

### 3.6 ACL2

**Origin:** Matt Kaufmann and J Strother Moore, University of Texas at Austin. Successor to Boyer-Moore theorem prover (1972). Based on a subset of Common Lisp. **Won the 2005 ACM Software System Award.**

**Industrial adoption — the strongest in hardware verification:**

- **AMD:** Used since 1995 to verify floating-point operations (motivated by the Pentium FDIV bug). Proved correctness of AMD K5 floating-point division and AMD Athlon floating-point adder.
- **Centaur Technology:** ACL2 specification of a subset of the x86 ISA, validated against Intel, AMD, and Centaur hardware.
- **IBM, Intel, Rockwell Collins, Motorola/Freescale, Oracle, Kestrel Institute.**

**Active development:** ACL2 v8.6. 19th International ACL2 Workshop held May 2025.

**Code output:** ACL2 specifications **are** executable Common Lisp programs — no extraction step. However, Common Lisp is not a mainstream deployment target.

**Assessment:** Decades of sustained industrial use, particularly in hardware verification. The AMD relationship (preventing another Pentium FDIV-class bug) demonstrates concrete economic value. Less relevant for general software development due to the Common Lisp ecosystem.

### 3.7 Why3

**Origin:** Toccata team, INRIA Saclay / Université Paris-Saclay / CNRS. Reimplementation of the former Why platform. Provides WhyML (specification + programming language) and interfaces to numerous external provers.

**Industrial adoption:** Primarily as infrastructure:

- **Backend for SPARK Ada** — provides deductive verification
- **Backend for Frama-C** (Jessie plugin) — deductive verification of C programs
- **Alt-Ergo SMT solver** is also used by Atelier B

**Active development:** Why3 1.8.2 (2025). INRIA-backed, ensuring institutional stability.

**Code output:** WhyML extracts to OCaml.

**Assessment:** Why3's significance is as **infrastructure powering other tools.** The fact that both SPARK and Frama-C chose it as their verification backend validates its design. Not typically used directly by end users.

### 3.8 SPARK Ada

**Origin:** University of Southampton, 1980s. Commercialized by Praxis High Integrity Systems → Altran → now managed by AdaCore. Current generation (SPARK 2014/2024) integrates with GNAT Ada compiler, uses Why3 and CVC5/Z3 for automated proof.

**Industrial adoption — one of the strongest in all of formal methods:**

- **Lockheed Martin C-130J:** Flight control software since 1997 (U.S. military, UK Royal Air Force).
- **NVIDIA:** Rewriting safety-critical ADAS and autonomous driving firmware from C to Ada/SPARK for **ISO 26262** compliance. Published an open-source SPARK reference process in 2025.
- **Tokeneer:** NSA-funded security demonstrator, EAL 5+ Gold certification, released as open source (2008).
- **SHOLIS:** Military helicopter landing system, DEFSTAN 00-55 SIL4.
- **Thales:** Joint SPARK adoption guidelines.
- Widely deployed in avionics (DO-178C), defense, air traffic management, medical devices, and industrial automation.

**Active development:** AdaCore provides commercial backing. GNAT Community Edition free for open-source/academic use. Active Ada Forum community. Multiple webinars, training courses, and certification support.

**Five-level adoption framework:**

| Level | Name | What's Verified |
|---|---|---|
| Stone | SPARK subset | Code restrictions only |
| Bronze | Data flow | No uninitialized variables, no unused assignments |
| Silver | Absence of runtime errors | No buffer overflows, no division by zero, etc. |
| Gold | Key properties | Functional properties of critical components |
| Platinum | Full functional proof | Complete specification and proof |

This incremental adoption pathway is unique and highly practical.

**Code output:** SPARK programs **are** valid Ada programs. There is no extraction gap — the verified code is the deployed code. This is the most direct connection between proof and executable artifact of any tool surveyed.

**Learning curve:** Moderate. Ada is readable and strongly typed. The five-level framework allows teams to start with simple restrictions and add formal verification incrementally.

**Assessment:** The combination of industrial track record (C-130J since 1997), modern momentum (NVIDIA in 2025), incremental adoption, and zero extraction gap makes SPARK the most mature and practical tool for proof-first development in safety-critical domains. The NVIDIA partnership signals expansion beyond traditional defense/aerospace into automotive.

### 3.9 Idris 2

**Origin:** Edwin Brady, University of St Andrews, Scotland. Redesigned around Quantitative Type Theory (QTT). Self-hosting.

**Industrial adoption:** None significant. Primarily academic and enthusiast use.

**Community:** ~2,800 GitHub stars. Active development (2025 updates). Yaffle core redesign (POPL 2024).

**Assessment:** Research language exploring practical dependent types. No industrial track record. Interesting theoretically but not mature for production use.

### 3.10 Agda

**Origin:** Ulf Norell, Chalmers University, Sweden. Extension of Martin-Löf's type theory.

**Industrial adoption:** None significant. Primary value is in formalized mathematics (especially homotopy type theory via Cubical Agda).

**Community:** ~2,500 GitHub stars. Standard Library v2.0 released 2025. *Programming Language Foundations in Agda* (PLFA) is widely used in education.

**Assessment:** Excellent for type theory research and education. Not suitable for production software development.

---

## 4. Methodological Frameworks

These are process-level approaches rather than specific languages or tools.

### 4.1 SCADE (Safety-Critical Application Development Environment)

**Origin:** Based on Lustre synchronous dataflow language (VERIMAG, Grenoble, 1984). Esterel Technologies merged Lustre with the Esterel language. Acquired by ANSYS in 2012. Now Ansys SCADE Suite.

**Industrial adoption — arguably the most commercially successful formal-methods tool by deployment scale:**

- **Airbus:** A318 Elite, A320 NEO, A340, A380, A350 flight control and display systems.
- **Boeing:** 737 SWA, 737 MAX, 787, 747-8.
- **Dassault Aviation:** Rafale fighter (Esterel for flight control).
- **Nuclear:** Power plant control software.
- **Railways:** Hong Kong subway signaling.
- **Automotive:** ADAS and safety systems.
- Certified at **DO-178C Level A** (aerospace), **IEC 61508 SIL 3** (industrial), **EN 50128** (railway).

**Code output:** **Qualified/certified automatic C code generation.** The code generator itself is certified at DO-178C Level A and IEC 61508 SIL 3. This eliminates the need to verify generated code — the generator is the verified artifact.

**Learning curve:** Moderate for control systems engineers. Graphical/diagrammatic interface is intuitive. However, SCADE is specialized for embedded systems — not a general-purpose programming environment.

**Assessment:** SCADE-generated code is running in essentially every major commercial aircraft flying today. By deployment scale and commercial impact, it is the most successful formal methods tool in existence. However, it is a specialized embedded systems tool, not a general-purpose development framework.

### 4.2 Cleanroom Software Engineering

**Origin:** Harlan Mills, IBM, mid-1980s. Combines formal methods, incremental development, and statistical quality control.

**Historical results:**

- IBM Flight Control Project: 2.3 errors/KLOC
- FAA Air Traffic Control: 3.5 errors/KLOC
- 85,000-line PL/I application: 10x defect reduction, 5x productivity improvement

**Current status:** Inactive. Mills died in 1996 and the community dispersed. No modern tooling or active community.

**Assessment:** Historically impressive results, but the methodology has not survived as a living practice. Of archival interest only.

### 4.3 Correctness-by-Construction (CbyC) — Praxis/Altran

**Origin:** Praxis High Integrity Systems (UK). Articulated in Anthony Hall's manifesto *Correctness by Construction: A Manifesto for High-Integrity Software*.

**Core principles:** (1) Expect requirements to change; (2) Know why you are testing; (3) Eliminate errors before testing; (4) Write software that is easy to verify; (5) Develop incrementally; (6) Some aspects of software development are hard; (7) Software is not useful by itself.

**Notable application:** Tokeneer (NSA, SPARK Ada, EAL 5+).

**Current status:** CbyC as a distinct methodology is closely tied to SPARK Ada. Academic research continues at IMDEA (Madrid) and KIT Karlsruhe. A 2023 paper (*Flexible Correct-by-Construction Programming*) extends the approach.

**Assessment:** Sound principles that influenced SPARK Ada's methodology. The Tokeneer case study remains a canonical reference. Not independently active outside of SPARK.

---

## 5. Maturity Assessment

### Tier 1: Battle-Proven at Scale

These have deployed verified software in production for years or decades, with measurable outcomes:

| Framework | Key Evidence | Scale | Years in Production |
|---|---|---|---|
| **SCADE** | Airbus A380, Boeing 787 flight controls | Every major commercial aircraft | 20+ years |
| **B-Method** | Paris Metro Line 14 — zero defects, 25 years | Millions of daily passengers | 25+ years |
| **SPARK Ada** | C-130J military aircraft; NVIDIA ADAS (2025) | Military fleets; automotive | 28+ years |
| **ACL2** | AMD processor verification (since 1995) | Every AMD processor | 30+ years |
| **F\*** | HACL* in Firefox, Linux kernel, WireGuard | Billions of devices | 5+ years |
| **Dafny** | AWS authorization engine (1B calls/sec) | AWS global infrastructure | 1+ years (deployed 2024) |

### Tier 2: Landmark Verified Artifacts

These have produced individually significant verified systems, even if deployment is narrower:

| Framework | Key Artifact | Significance |
|---|---|---|
| **Coq / Rocq** | CompCert verified C compiler | ACM Software System Award 2021 |
| **Isabelle/HOL** | seL4 verified microkernel | First verified OS kernel |
| **Lean 4** | AWS Cedar verification; Mathlib | ACM SIGPLAN Award 2025; largest math library |

### Tier 3: Mature with Niche Adoption

| Framework | Status |
|---|---|
| **Event-B / Rodin** | Active development, industrial applications in railway/aerospace |
| **VDM** | Historically significant, active in co-simulation (INTO-CPS) |
| **Why3** | Critical infrastructure (powers SPARK and Frama-C backends) |
| **ASM (ASMETA)** | Active academic tool, limited industrial deployment |

### Tier 4: Research / Emerging

| Framework | Status |
|---|---|
| **Idris 2** | Research language, no industrial deployment |
| **Agda** | Mathematics formalization, no industrial deployment |

### Tier 5: Historical / Inactive

| Framework | Status |
|---|---|
| **Z Notation** | Largely superseded; tool support stagnant |
| **Cleanroom** | Inactive since Mills' death (1996) |
| **CbyC (Praxis)** | Subsumed into SPARK Ada practice |

---

## 6. Comparative Matrix

| Tool | Industrial Maturity | Active Dev | Learning Curve | Code Targets | Dijkstra Alignment | Best For |
|---|---|---|---|---|---|---|
| **SCADE** | Highest | Yes (Ansys) | Moderate | Certified C | Indirect | Embedded safety-critical |
| **B-Method** | Very High | Yes (CLEARSY) | Steep | C, Ada | High (refinement) | Railway, transport |
| **SPARK Ada** | Very High | Yes (AdaCore) | Moderate | Ada (native) | High | Safety-critical, defense |
| **ACL2** | Very High | Yes (UT Austin) | Moderate-Steep | Common Lisp | Moderate | Hardware verification |
| **Dafny** | High | Very Active (AWS) | **Lowest** | C#, Go, Py, Java, JS, Rust | High (WP calculus) | General-purpose verified software |
| **F\*** | High | Very Active (MSR/INRIA) | Steep | C, OCaml, F# | **Highest** (Dijkstra monads) | Verified systems/crypto |
| **Coq/Rocq** | High | Very Active | Steep | OCaml, Haskell | High | Verified compilers, kernels |
| **Isabelle/HOL** | High | Very Active | Steep | SML, OCaml, Haskell, Scala | High | OS verification, proofs |
| **Lean 4** | High | Very Active | Steep | C (native) | High | Mathematics, policy verification |
| **Event-B** | Medium-High | Active | Steep | Plugins | High (refinement) | System modeling |
| **Why3** | Medium-High | Active | Moderate | OCaml | High (WP) | Verification infrastructure |

---

## 7. Conclusions and Recommendations for Proven

### Which frameworks are most proven and mature?

By **deployment scale**, SCADE leads — its verified code is in the flight controls of nearly every major commercial aircraft. But SCADE is a specialized embedded systems tool, not a general-purpose development framework.

By **longevity and zero-defect evidence**, the B-Method is unmatched — 25 years, zero defects on Paris Metro Line 14.

By **breadth of industrial adoption in safety-critical software**, SPARK Ada has the most diverse track record across defense, aerospace, automotive, and security domains, with the additional advantage of an incremental adoption pathway.

By **scale of modern deployment in general-purpose computing**, Dafny leads — AWS's authorization engine at 1 billion calls per second, deployed 2024.

By **deployment footprint** (number of devices running verified code), F* leads via HACL* in Firefox and the Linux kernel.

### For the Proven project specifically

The Proven project aims to build an LLM context management engine using Dijkstra-style proof-first development. The most relevant tools are:

1. **Dafny** (recommended starting point): Lowest learning curve, broadest code targets (including Python and JavaScript), direct support for preconditions/postconditions/invariants, automated proof via Z3, and proven at AWS scale. The workflow of Requirements → Formal Spec → Proof → Derived Code maps directly to Dafny's design.

2. **F\***: Theoretically closest to Dijkstra's methodology (Dijkstra monads compute weakest preconditions). Produces verified C. The HACL* success demonstrates production-quality output. But the learning curve is significantly steeper.

3. **SPARK Ada**: Most mature methodology with the best incremental adoption story. The code IS the verified artifact (no extraction gap). But Ada is not a mainstream target for an LLM context engine.

4. **Lean 4**: Largest community and strongest AI-assisted proving ecosystem. AWS Cedar verification provides industrial credibility. But oriented more toward theorem proving than the spec-to-code pipeline.

### Suggested evaluation approach

Build the same small component — a priority queue with proven ordering invariants (as proposed in the project CLAUDE.md) — in Dafny, F*, and one of Lean 4 or SPARK Ada. Evaluate based on:

- Time from specification to proven, executable code
- Readability of specifications and proofs
- Quality and usability of generated code
- Debugging experience when proofs fail
- How naturally the tool supports Dijkstra's weakest-precondition workflow

---

## References

### Primary Texts
- Dijkstra, E.W. *A Discipline of Programming* (1976)
- Dijkstra, E.W. & Scholten, C.S. *Predicate Calculus and Program Semantics* (1989)
- Abrial, J.-R. *Modeling in Event-B: System and Software Engineering* (2010)
- Börger, E. & Stärk, R. *Abstract State Machines* (2003)

### Industrial Evidence
- CLEARSY. *Formal Methods in Industry* (2024). https://www.atelierb.eu/wp-content/uploads/2024/11/Formal-Methods-in-Industry.pdf
- CLEARSY. *Extension of Line 14 — Over 25 Years of Reliability.* https://www.clearsy.com/en/the-tools/extension-of-line-14-of-the-paris-metro-over-25-years-of-reliability-thanks-to-the-b-formal-method/
- Amazon Science. *Formally Verified Cloud-Scale Authorization* (2024). https://www.amazon.science/publications/formally-verified-cloud-scale-authorization
- AdaCore/NVIDIA. *Ada and SPARK Enter the Automotive ISO 26262 Market* (2025). https://www.adacore.com/press/ada-and-spark-enter-the-automotive-iso-26262-market-with-nvidia
- NVIDIA. *SPARK Reference Process.* https://nvidia.github.io/spark-process/

### Tools and Documentation
- Dafny: https://dafny.org
- F*: https://fstar-lang.org
- HACL*: https://hacl-star.github.io
- Lean 4: https://lean-lang.org
- Rocq Prover (Coq): https://rocq-prover.org
- Isabelle: https://isabelle.in.tum.de
- ACL2: https://www.cs.utexas.edu/~moore/acl2/
- Why3: https://www.why3.org
- SPARK Ada: https://www.adacore.com/languages/spark
- Atelier B: https://www.atelierb.eu/en/
- Event-B: https://www.event-b.org
- Ansys SCADE: https://www.ansys.com/products/embedded-software/ansys-scade-suite
- Overture (VDM): https://into-cps-association.github.io/constituent-model-development/overture/
- ASMETA: https://asmeta.github.io

### Research
- Hall, A. *Correctness by Construction: A Manifesto for High-Integrity Software.* https://www.researchgate.net/publication/228922389
- *Flexible Correct-by-Construction Programming* (2023). https://lmcs.episciences.org/11444/pdf
- IMDEA CbyC Group: https://wp.software.imdea.org/cbc/
- ACL2 Industrial Use: https://royalsocietypublishing.org/doi/10.1098/rsta.2015.0399
- seL4 Summit 2025: https://sel4.systems/Summit/2025/abstracts2025.html
- CompCert: https://compcert.org

### Community Resources
- Awesome Formal Verification: https://github.com/ElNiak/awesome-formal-verification
- Archive of Formal Proofs (Isabelle): https://www.isa-afp.org
- Mathlib (Lean): https://github.com/leanprover-community/mathlib4
- Awesome Coq/Rocq: https://github.com/rocq-community/awesome-coq
- SPARK Adoption Guidance: https://www.adacore.com/books/implementation-guidance-spark
