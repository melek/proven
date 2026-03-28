---
name: survey
description: "Scan a codebase and identify where stronger guarantees would matter most — ranks modules by implicit invariants, unenforced assumptions, and state complexity. Use when starting work on a new codebase, planning where to invest in reliability, or triaging technical risk."
argument-hint: "[directory path]"
allowed-tools: "Read, Bash, Glob, Grep, Agent, ToolSearch"
---

# Proven: Codebase Survey

SUBAGENT-STOP: If you were dispatched as a subagent to execute a specific task, do not spawn further subagents. Scan modules sequentially and return a structured result.

## Procedure

### 1. Determine Scan Target

If an argument was provided, use that directory path. Otherwise, use the current working directory. Verify the path exists before proceeding.

For larger codebases (estimated >50 source files), note upfront: "This may take a minute to scan."

### 2. Explore Codebase Structure

Map the project layout:

- Use Glob to find source files (`**/*.py`, `**/*.ts`, `**/*.js`, `**/*.go`, `**/*.java`, `**/*.rs`, `**/*.cs`, `**/*.dfy`, etc. — adapt to whatever languages are present)
- Use Bash to count files and get a sense of scale: `find <target> -name '*.py' -o -name '*.ts' | wc -l` (adapt extensions)
- Read key structural files: package manifests, module __init__.py files, directory listings of src/ or lib/ directories
- Identify the module boundaries (directories, packages, namespaces, or individual files depending on project structure)

For projects under ~10 modules, note that `/proven:advise` on specific files would be more useful than a survey, but proceed with the scan if the user asked for it.

### 3. Identify High-Value Targets

Read module entry points and key files. Look for these patterns:

**State machines and transitions:**
- Explicit state enums, status fields, phase tracking
- Methods that change object state with implicit ordering constraints
- Workflow or lifecycle management (user sessions, order processing, deployment pipelines)

**Implicit invariants:**
- Bounds that are checked at runtime but not captured in types (array indices, collection sizes, numeric ranges)
- Relationships between fields that must hold but are not enforced (e.g., `start < end`, `balance >= 0`, `items.length == count`)
- Data structures with consistency requirements (trees must be balanced, graphs must be acyclic, caches must not exceed capacity)

**Safety-critical logic:**
- Authentication, authorization, permission checks
- Financial calculations, currency handling
- Cryptographic operations, key management
- Resource lifecycle (open/close, acquire/release, connect/disconnect)

**Data integrity:**
- Serialization/deserialization boundaries
- Database schema assumptions
- API contract enforcement (input validation, output shape guarantees)
- Migration or transformation logic where data loss is possible

**Concurrency and shared state:**
- Locks, mutexes, atomic operations
- Shared mutable state across threads or processes
- Event ordering assumptions

### 4. Assess and Rank

For each identified module, assess:

- **Severity of failure:** What happens if an invariant is violated? Data corruption vs. UI glitch.
- **Current enforcement:** What mechanisms exist? Types, assertions, tests, runtime checks, nothing.
- **Complexity:** How many states, transitions, or invariants are involved?
- **Leverage:** Would strengthening guarantees here protect downstream consumers?

Classify each as high, medium, or low value.

### 5. Produce Output

Structure the output as a priority-ranked assessment:

**High value targets (5-10 max):** Each gets a paragraph explaining:
- What the module does
- What implicit guarantees it carries
- What enforcement exists today
- Why stronger guarantees would matter here

**Medium value targets:** Each gets one line describing the module and what was observed.

**Low value summary:** A single line noting how many modules were scanned and found to have minimal invariant complexity (e.g., "14 modules are pure data mappers, serializers, or configuration with no complex invariants to enforce").

**Recommendation:** For each high-value target, suggest: "Run `/proven:advise <module path>` for detailed analysis."

## Output Constraints

- Target one screen of output (roughly 40-60 lines). Prioritize the most important findings.
- Do not produce exhaustive reports. The survey is a triage tool, not an audit.
- Do not modify any code.
- Do not run verification tools, linters, or test suites.
- Do not generate Dafny code or specifications.
- Present findings descriptively. Do not advocate for formal verification or any particular methodology. State what was observed and what the tradeoffs are.
