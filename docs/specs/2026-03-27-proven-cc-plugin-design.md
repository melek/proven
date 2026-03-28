# Proven CC Plugin Design

## What This Is

A Claude Code plugin that brings formal-verification-informed thinking into everyday development. Not a pipeline wrapper — a methodology lens. Three skills, no hooks, no ambient injection. Complements existing workflows (superpowers, TDD, whatever the user already has).

Much of what this plugin offers is well-established design-by-contract thinking (Meyer, 1988; Dijkstra, 1976). The contribution is not methodological novelty but accessibility — an LLM that can read your code and apply these principles in context, using your vocabulary, scaled to your codebase. The Proven experiment adds specific findings about specification form (Section 3 of the methodology), but the advisory skill's core value is making existing ideas available at the point of use.

## Motivation

Most software carries no formal guarantees about its behavior. Formal verification has historically been too expensive for anything outside aerospace, defense, and cryptography. LLM-driven specification may change this — the Proven experiment explored whether structured inference can lower the barrier to producing verified software.

The Proven pipeline (N=216 ablation study) demonstrates that deterministic specification preprocessing combined with LLM-driven implementation produces correct code. Every implementation produced — across all conditions — passes 100% of independent tests; the methods differ in production rate, not correctness. The novel finding: specification quality is an optimizable parameter — the *form* of a specification affects LLM success independently of its semantic content.

This plugin doesn't wrap the pipeline. It distills the methodology — the thinking patterns, the tradeoff analysis, the assurance vocabulary — into something Claude Code can apply during ordinary development work.

## Design Principles

### Complementary, not competing

The plugin adds a lens, not a workflow. If someone is using TDD, Proven doesn't say "do formal verification instead." It offers a perspective on what guarantees exist, what's missing, and what it would take to strengthen them. It integrates with whatever the user already does.

### Skill-driven, not ambient

No SessionStart hooks. No context injected into every session. The methodology loads on-demand when a skill is invoked — either by Claude when it recognizes an opportunity, or by the user explicitly. Zero token overhead in sessions that don't need it. This follows the superpowers pattern (skill invocation, not hook injection) and is lighter on the model's cognitive ergonomics. Once a skill is invoked, its methodology content remains in the session context — this is by design, so subsequent questions in the same session benefit from the verification lens without re-invocation.

### Descriptive, not prescriptive

The plugin presents verification-informed thinking with its evidence, including what new affordances AI development brings to verification economics. It presents tradeoffs realistically, including costs, limitations, and current state. The plugin does not frame formal verification as something the user should adopt.

The voice is adaptive to context. If the user's code already uses assertions, contracts, or type-level guarantees, the plugin uses that vocabulary. If not, it speaks in terms of promises, guarantees, assumptions, and risks. Formal terminology is introduced progressively — plain language on first encounter, formal terms in parentheses when the concept recurs, formal terms used directly once the user has engaged with the concept. Even many professional programmers may not know what a postcondition is — the plugin meets users where they are and builds vocabulary from there.

### Ideas stand on their own

The plugin does not argue for formal verification. It does not "subtly convince" or use persuasive framing. It presents what the code guarantees, what it doesn't, what strengthening those guarantees would look like, and what it would cost. Tradeoff analysis references deployment context — where and how the software is intended to be deployed determines the appropriate assurance level. The user evaluates the merit of the ideas themselves.

## Skills

### `/proven:about`

**Skill description:** "Introduction to Proven — what it is, what the research found, and optionally how to install the CLI and Dafny. Use when the user asks about Proven, wants to understand the research, or needs to set up the pipeline."

**argument-hint:** (none)

Replaces the current `/proven:setup` skill. Explains what Proven is: an experiment in using LLMs to produce formally verified software via Dafny.

**Content:**

- The research question: can structured inference make formal verification accessible beyond safety-critical domains?
- The pipeline architecture (5 stages: requirements, specification, preprocessing, implementation, compilation) and the novel contribution (Stage 2.5: deterministic specification preprocessing)
- Research results, presented in plain language first (preprocessing doubled success rate for smaller models; every produced implementation was functionally correct). Statistical details (p=0.067, Cohen's h=0.49, confidence intervals) available if asked, not foregrounded.
- Current state: research prototype, not production tool
- Honest about limits:
  - The pipeline's input is requirements, not existing code — it produces new verified implementations, it doesn't annotate existing ones
  - Hard problems (ring buffer, red-black tree) still fail for smaller models even with preprocessing
  - The rewrite rules were designed on the same benchmark suite used for evaluation — generalization is unknown
- Optional: walks through installing Proven CLI and/or Dafny if the user wants, but doesn't presume they should

**Output shape:** A structured overview (2-4 paragraphs covering what it is, what was found, current state). If the user wants installation, transitions to an interactive walkthrough (same flow as the current setup skill).

### `/proven:advise`

**Skill description:** "Analyze code through a verification lens — identify what it guarantees, what enforces those guarantees, and where gaps exist. Use when working with state machines, security boundaries, data integrity, bounded resources, financial logic, or any code where implicit guarantees need to be identified and evaluated."

**argument-hint:** "[file path or module name]"

The core skill. When invoked, reads the code in context and applies the Proven methodology as a lens. Operates as a perspective within existing workflows — if brainstorming or TDD is active, advise supplements rather than replaces.

**Behavior:**

1. Reads the code or module in context (or the file/module specified by argument)
2. Identifies structures that have implicit guarantees — state machines, bounded collections, security boundaries, data integrity invariants, resource lifecycle management
3. Describes what the code currently guarantees and what enforces those guarantees (types, runtime checks, tests, nothing)
4. Identifies gaps — guarantees that are assumed but not enforced
5. When relevant, describes what strengthening a guarantee would look like, in the user's language and codebase (not in Dafny)
6. Frames tradeoffs realistically, informed by deployment context and what AI development changes about verification economics
7. When a module is a strong candidate for formal verification, notes that the Proven pipeline exists and how to run it — not as a recommendation, but as information about what's available

**Adaptive voice:**

- Before generating output, scans the code in context for formal specification patterns (assertions, contracts, invariants, pre/postconditions, type-level constraints). If present, uses formal vocabulary. If the user uses formal terms in their message, matches that register. Otherwise, defaults to plain language: promises, guarantees, assumptions, risks.
- Progressive vocabulary: on first encounter of a concept, uses plain language. When the concept recurs, introduces the formal term in parentheses. Uses formal terms directly once the user has engaged with them.
- Scales depth to the target. A simple data class with bounds gets a sentence. A state machine governing user sessions gets a thorough analysis.
- Generative when the suggestion is small and actionable (e.g., a concrete assertion or type constraint). Analytical when the recommendation is architectural.
- Explains what drew attention to each finding (the pattern), not just the finding itself. The goal is to demonstrate a way of looking at code, not just to report conclusions.

**Output shape:** Structured analysis with sections:
- **What this code guarantees** — what's enforced and by what mechanism
- **Gaps** — guarantees that are assumed but not enforced, with specific code references
- **Options** — what strengthening would look like, framed as tradeoffs not recommendations

Length scaled to complexity: 10-15 lines for a simple module, several paragraphs with code references for a complex state machine. One-shot analysis with conversational follow-up available.

**Does not:**

- Generate Dafny code
- Run the Proven pipeline or any prover
- Require Dafny to be installed
- Prescribe — observes, explains, answers when asked

### `/proven:survey`

**Skill description:** "Scan a codebase and identify where stronger guarantees would matter most — ranks modules by implicit invariants, unenforced assumptions, and state complexity. Use when starting work on a new codebase, planning where to invest in reliability, or triaging technical risk."

**argument-hint:** "[directory path]"

Project-scoped triage. Scans a codebase or subtree and ranks modules by how much they would benefit from verification-informed thinking.

**Behavior:**

1. Explores the codebase structure (or the user-specified subtree/directory)
2. Identifies modules with implicit invariants, state transitions, safety-critical logic, or data integrity requirements
3. Produces a prioritized assessment (targets the 5-10 highest-leverage modules, not an exhaustive report):
   - High value: "This state machine governs user sessions and has no enforced transition invariants"
   - Medium value: "This bounded buffer has runtime checks but the bounds aren't captured in the type system"
   - Low value: mentioned only in summary ("12 modules are pure data mappers with no invariants to enforce")
4. For high-value targets, briefly describes what stronger guarantees would look like
5. Suggests invoking `/proven:advise` on specific high-value modules for detailed analysis

For projects under ~10 modules, suggests using `/proven:advise` on specific files instead.

**Output shape:** A priority-ranked list of modules with one-line descriptions and value assessment. High-value targets get a brief paragraph explaining why. Typically fits in one screen. For larger codebases, may take a minute to scan — the skill notes this upfront.

**Subagent behavior:** When dispatched as a subagent (e.g., from a plan or another skill), survey scans modules sequentially without spawning nested subagents, and returns a structured result rather than conversational output.

**Does not:**

- Modify any code
- Run verification tools
- Produce exhaustive reports

## Methodology Content

These principles guide how `/proven:advise` structures its analysis. They are not presented to the user as instructions — the skill applies them internally and presents its observations in descriptive terms.

Distilled from the literature reviews, the paper (N=216 ablation study), and the SLR-informed issues spec.

### 1. Work backwards from what must be true

Before analyzing how code works, identify what it must guarantee. If a function transfers money, the guarantee is: balances stay non-negative, the total is conserved. Start there. This is Dijkstra's weakest precondition calculus: start with the postcondition, derive the precondition through systematic predicate transformation. The program structure follows from the calculation.

### 2. Identify and reason about invariants

The most important question about any loop is not "what does it do?" but "what is true every time execution reaches the top?" Loop invariants are where most correctness reasoning fails, because identifying what is *preserved* across iterations requires understanding the inductive structure. For stateful objects, the analogous question is "what must be true about this object's state between any two method calls?" These invariants — loop invariants, class invariants, state machine invariants — are the primary targets for the advise skill's analysis.

### 3. The shape of a specification matters

For LLM-driven verification, two ways of expressing the same guarantee can be dramatically different in how verifiable they are. The Proven ablation study found that deterministic rewriting of specifications — without changing their meaning — more than doubled verification success rates for a 14B model (p=0.067, not yet reaching conventional significance). The effect was model- and difficulty-dependent: strong for smaller models on medium problems, negligible for frontier models in isolation. The underlying principle — prefer direct checks over indirect ones, separate independent guarantees rather than combining them — applies more broadly to assertions and test expectations, though the experimental evidence is specific to LLM + SMT verification.

### 4. Guarantees exist on a spectrum

SPARK Ada's industrial adoption framework (28 years, deployed in C-130J flight controls, NVIDIA ADAS) defines five incremental levels: syntactic restrictions, data flow properties, absence of runtime errors, key functional properties, full proof. The Proven SLR's analysis of 98 papers suggests a similar spectrum: proven, validated, monitored, tested.

Most production code relies on testing alone. Each step up the spectrum adds enforcement but also specification effort. A runtime assertion that was implicit in a comment becomes an enforced check. A type that was `int` becomes a bounded range. These are incremental improvements. Note, however, that the gap between "tested" and "proven" is qualitative, not just quantitative — formal proof covers all inputs, while testing covers a finite sample.

### 5. Incremental adoption works

Start with "what could go wrong?" (identify risks). Move to "what does this promise?" (name the guarantees). Then "how is that promise enforced?" (find the mechanism — types, tests, assertions, nothing). The first three steps can be applied without any formal tools. They structure the analysis that a formal tool would build on.

### 6. Existing code can benefit, with realistic expectations

Adding assertions to code that wasn't designed around them captures the guarantees you can identify, not structural guarantees the code was derived from. On existing codebases, the highest-value moves are: identifying state machines with unenforced transition invariants, finding bounds that are checked at runtime but not captured in types, and spotting implicit assumptions that nothing enforces. These are real improvements. Specifications written alongside new code can capture deeper structural invariants — when writing new modules or extending existing ones, thinking about guarantees from the start captures more.

## What the Plugin Does NOT Do

- Inject context into every session (no hooks)
- Compete with or replace existing workflows
- Require Dafny or any prover to be installed
- Omit costs, limitations, or current state when presenting potential benefits
- Generate Dafny code or run the pipeline (that's the CLI's job)
- Use persuasive or advocacy framing — ideas are presented with evidence and justification; the user evaluates their merit

## Grounding

### Supported by the Proven experiment

- Specification preprocessing shows a medium effect size for weaker models (N=216, p=0.067, Cohen's h=0.49 — suggestive but not yet reaching conventional significance). The rewrite rules were designed after observing failure patterns on the same benchmarks, so generalization to unseen specifications is unknown.
- All produced implementations pass 100% of independent tests (129 tests across 9 benchmarks) regardless of method. This confirms correctness of produced code but reflects benchmark difficulty — these are well-understood data structure problems.
- The pipeline's failure mode is non-production, not incorrect production
- Specification quality is an optimizable parameter (paper Section 7.1)

### Grounded in literature

- Dijkstra's weakest precondition calculus (*A Discipline of Programming*, 1976)
- SPARK Ada's five-level adoption framework (Lockheed Martin C-130J, NVIDIA ADAS, 28 years deployed). SPARK demonstrates that incremental adoption of formal thinking is industrially viable. This plugin applies the same incremental philosophy at the advisory level rather than the tool level.
- Assurance spectrum analysis from Proven's SLR of 98 papers (novel classification, not an established taxonomy)
- Kleppmann's observation: proof checkers reject hallucinations deterministically, providing a different failure mode than test suites, which can pass despite specification violations
- AWS Cedar: Dafny-verified authorization engine, 1 billion invocations/second, deployed 2024

### Not yet validated

- The mentor system's stuck categories (never fired in 108 runs — designed but untested)
- Trace-informed rewrite rule discovery (proposed in SLR spec, not implemented)
- Quantifier complexity metrics (well-motivated, not built)
- Whether the methodology translates effectively through an advisory skill (this plugin is itself an experiment)

## Technical Details

### Plugin structure

```
proven/
├── .claude-plugin/
│   ├── plugin.json          # Update: bump version, no hooks needed
│   └── marketplace.json     # Update: reflect new skills
├── skills/
│   ├── about/SKILL.md       # Replaces setup/
│   ├── advise/SKILL.md      # Core methodology lens
│   └── survey/SKILL.md      # Project-scoped triage
├── proven/                  # Existing pipeline (unchanged)
├── examples/                # Existing benchmarks (unchanged)
└── research/                # Existing research (unchanged)
```

### Skill allowed-tools

- **about**: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, ToolSearch
- **advise**: Read, Bash, Glob, Grep, Agent, ToolSearch (read-only exploration + subagents for deeper analysis)
- **survey**: Read, Bash, Glob, Grep, Agent, ToolSearch (read-only exploration + subagents for parallel module scanning)

### No new runtime dependencies

The skills are pure methodology — instructions for Claude, not code to execute. No Python scripts, no hooks, no MCP servers. The existing pipeline remains available via the CLI for users who want to run it directly.

## Migration

- Replace `skills/setup/SKILL.md` content with a redirect: "This skill has been renamed to `/proven:about`. Invoke `/proven:about` instead." Remove the redirect in the following version bump.
- Create `skills/about/SKILL.md`, `skills/advise/SKILL.md`, `skills/survey/SKILL.md`
- Update `.claude-plugin/plugin.json` version to 0.4.0 (breaking change: removed skill, added three new skills)
- Update `.claude-plugin/marketplace.json` description
