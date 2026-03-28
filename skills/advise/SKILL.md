---
name: advise
description: Analyze code through a verification lens — identify what it guarantees, what enforces those guarantees, and where gaps exist. Use when working with state machines, security boundaries, data integrity, bounded resources, financial logic, or any code where implicit guarantees need to be identified and evaluated.
argument-hint: "[file path or module name]"
allowed-tools: "Read, Bash, Glob, Grep, Agent, ToolSearch"
---

# Proven Advise

Analyze code through a verification lens. Identify what it guarantees, what enforces those guarantees, and where gaps exist.

<SUBAGENT-STOP>
If you were dispatched as a subagent, skip the workflow preamble and go directly to analysis.
</SUBAGENT-STOP>

## How This Skill Works

This skill operates as a **perspective within existing workflows**. If brainstorming, TDD, or another methodology is active, advise supplements it — it does not replace it. If TDD is active, focus on what the tests should guarantee, not on replacing the test-first discipline.

## Procedure

### 1. Identify the target

If an argument was provided, read that file or module. Otherwise, use whatever code is in the current conversation context. If no code is available, ask the user what they'd like analyzed.

### 2. Detect vocabulary level

Before generating output, scan the code for formal specification patterns:
- Assertions (`assert`, `require`, `ensure`, `invariant`)
- Contract libraries (Design by Contract decorators, `@pre`, `@post`)
- Type-level constraints (bounded types, newtypes, branded types)
- Pre/postcondition comments or docstrings

If present, use formal vocabulary (precondition, postcondition, invariant, loop invariant).
If the user uses formal terms in their message, match that register.
Otherwise, default to plain language: promises, guarantees, assumptions, risks.

**Progressive vocabulary:** On first encounter of a concept, use plain language. When the concept recurs, introduce the formal term in parentheses. Use formal terms directly once the user has engaged with them.

### 3. Analyze the code

Apply these principles internally to structure your analysis. Do not present them as a list or framework to the user — present your observations in descriptive terms.

**Work backwards from what must be true.** Before analyzing how code works, identify what it must guarantee. If a function transfers money, the guarantee is: balances stay non-negative, the total is conserved. Start with the postcondition, derive the precondition through systematic predicate transformation.

**Identify invariants.** The most important question about any loop: "what is true every time execution reaches the top?" For stateful objects: "what must be true about this object's state between any two method calls?" These — loop invariants, class invariants, state machine invariants — are the primary analysis targets.

**Consider specification shape.** Prefer direct checks over indirect ones. Separate independent guarantees rather than combining them. Two ways of expressing the same guarantee can differ dramatically in how verifiable, testable, and auditable they are.

**Place guarantees on the spectrum.** Most code relies on testing alone. Each step up adds enforcement: runtime assertion, type constraint, formal proof. Note the qualitative gap between tested and proven — formal proof covers all inputs, testing covers a finite sample.

**Assess incrementally.** What could go wrong? What does this code promise? How is that promise enforced (types, tests, assertions, nothing)? The first three questions can be answered without any formal tools.

**Be realistic about existing code.** Assertions added to code that wasn't designed around them capture the guarantees you can identify, not structural guarantees the code was derived from. On existing codebases, the highest-value moves are: finding state machines with unenforced transition invariants, bounds checked at runtime but not in types, and implicit assumptions that nothing enforces.

### 4. Present findings

Structure your output as:

**What this code guarantees** — What's enforced and by what mechanism. Be specific: name the function, the check, the type.

**Gaps** — Guarantees that are assumed but not enforced. Reference specific code locations. Explain what drew your attention to each gap — the pattern you recognized — before describing the gap itself. The goal is to demonstrate a way of looking at code, not just report conclusions.

**Options** — What strengthening would look like, framed as tradeoffs. For each option, describe what it would cost (effort, complexity) and what it would provide (what class of bugs it prevents, what guarantee it adds). Frame in terms of deployment context — where and how the software is intended to be deployed determines the appropriate level.

### 5. Scale and adapt

- A simple data class with bounds: a few lines.
- A complex state machine: several paragraphs with specific code references.
- Small, actionable suggestions (a concrete assertion, a type narrowing): include the code.
- Architectural recommendations: describe the approach without generating implementation.

### 6. Bridge to formal tools (when appropriate)

When a module is a strong candidate for formal verification — complex invariants, safety-critical logic, state machines with many transitions — note that the Proven pipeline exists and how to run it (`proven run requirements.md --mode autonomous`). Present this as information about what's available, not as a recommendation.

## Constraints

- Do NOT generate Dafny code
- Do NOT run the Proven pipeline or any prover
- Do NOT require Dafny to be installed
- Do NOT prescribe — observe, explain, answer when asked
- Do NOT present the methodology principles as a numbered list or framework
- Do NOT argue for formal verification. Present tradeoffs realistically, including costs and limitations.
