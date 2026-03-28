---
name: contribute
description: "Opt in to anonymized observation collection, preview accumulated data, and submit to the Proven research project via GitHub."
allowed-tools: Read, Bash, Glob, Grep, AskUserQuestion, ToolSearch
---

# Proven Research Participation

Conversational interface to the research data collection system for Experiment 004 (Methodology Transfer). This skill explains the study, handles informed consent, and manages the observation lifecycle. All execution goes through the shell script — this skill explains and guides.

**Plugin root:** `${CLAUDE_PLUGIN_ROOT}`
**Shell script:** `${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh`
**Research statement:** `${CLAUDE_PLUGIN_ROOT}/docs/RESEARCH.md`

## Procedure

### Determine state

First, check whether the user has already enabled observation collection:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh" status
```

This tells you whether observations are enabled, how many exist, and the date range. Branch based on the result.

---

### Branch A: First-time invocation (not yet enabled)

Walk through the consent flow conversationally. Do not present this as a wall of text — have a dialogue.

**1. Explain the research question.**

The Proven project includes a research component studying whether formal verification methodology translates effectively through an AI advisory skill. The `/proven:advise` skill applies verification-informed thinking to code — the research question is whether that analysis leads to users taking actions that strengthen code guarantees, and whether this pattern persists over time.

**2. Explain what is collected.**

Observations are structured counts and categories. Show the schema:

```
skill: "advise"
patterns_found: 3
gaps: 2
options: 1
language: "python"
loc: "200-1000"
action: "edited"
invocation_number: 7
```

Emphasize: these are counts and enum values. The fields are:
- `skill` — which skill was invoked (advise, survey)
- `patterns_found`, `gaps`, `options` — integer counts from skill output
- `language` — programming language of the analyzed code
- `loc` — lines-of-code bucket (enum: <50, 50-200, 200-1000, 1000+)
- `action` — what the user did after (enum: edited, committed, no-action, asked-followup)
- `invocation_number` — how many times this installation has recorded an observation (resets if data is purged)

**3. Explain what is NOT collected.**

Be explicit about exclusions:
- No source code, file paths, or file contents
- No conversation text or prompts
- No error messages or compiler output
- No project names, repository URLs, or directory structures
- No system information beyond what's in the schema

**4. Explain submission mechanics.**

Submission is via GitHub issue on the melek/proven repository. This means:
- The user's GitHub identity is attached to the submission (via `gh` CLI)
- The data is public and permanent once submitted
- Submissions use a hashed installation ID for longitudinal linking — GitHub identity is visible but the hash prevents cross-referencing between submissions without the local salt

**5. Note voluntariness.**

The plugin works identically with or without participation. Observations are collected locally and only submitted when the user explicitly chooses. The full research statement is at `${CLAUDE_PLUGIN_ROOT}/docs/RESEARCH.md`.

**6. Ask for consent.**

Ask the user whether they want to enable observation collection. If yes:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh" enable
```

The script creates the observation directory and writes a consent record with timestamp.

If the user declines, acknowledge and move on. No further prompting.

---

### Branch B: Already enabled (subsequent invocations)

Show the status output from the initial check. Then offer the available actions:

**Preview accumulated data:**

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh" preview
```

Shows all pending observations with validation results. Writes a preview file to /tmp for inspection. Always offer preview before submit.

**Submit to GitHub:**

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh" submit
```

The script handles the full flow: preview, identity confirmation, consent confirmation, issue creation, and flushing submitted observations. Requires `gh` CLI to be authenticated.

**Disable collection:**

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh" disable
```

Stops future collection. Does not delete existing observations.

**Purge all data:**

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh" purge
```

Deletes all local observations (pending and submitted). The script confirms before acting.

**Rotate installation ID:**

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/proven-research.sh" rotate-id
```

Generates a new installation UUID. Warn the user that this breaks longitudinal linking between submissions.

---

## Key Constraints

- **The skill explains and guides. The shell script executes.** Never replicate the script's logic — always call the script.
- **Never file GitHub issues directly.** Always use the submit subcommand.
- **Present the consent flow as a conversation**, not a disclosure document. Ask one thing at a time.
- **Reference `docs/RESEARCH.md`** when the user wants the full research statement — do not try to reproduce it from memory.
- **Do not prompt for participation** outside this skill. The contribute skill is invoked intentionally; it never interrupts other workflows.
