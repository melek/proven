# Proven Research Statement

## Study

**Title:** Does formal verification methodology translate effectively through an AI advisory skill?

**Researcher:** Lionel Di Giacomo, independent researcher

**Project:** Proven — LLM-Driven Stepwise Refinement (Experiment 004: Methodology Transfer)

**Full experiment design:** `research/experiments/004-methodology-transfer/DESIGN.md`

## Research Question

The Proven pipeline demonstrates that structured inference can produce formally verified software. The `/proven:advise` skill distills the methodology — verification-informed thinking, invariant identification, guarantee analysis — into an advisory tool for everyday development. This study asks: does that methodology actually transfer? When users receive advise output, do they subsequently take actions consistent with strengthening code guarantees, and does this pattern persist over time?

## What Is Collected

Observations are structured counts and enumerated categories. The complete schema:

| Field | Type | Description |
|-------|------|-------------|
| `skill` | enum | Which skill was invoked: `advise`, `survey` |
| `patterns_found` | integer | Number of guarantee patterns identified |
| `gaps` | integer | Number of unenforced assumptions found |
| `options` | integer | Number of strengthening options presented |
| `language` | enum | Programming language of analyzed code |
| `loc` | enum | Lines-of-code bucket: `<50`, `50-200`, `200-1000`, `1000+` |
| `action` | enum | User's subsequent action: `edited`, `committed`, `no-action`, `asked-followup` |
| `invocation_number` | integer | Nth observation by this installation (counts all pending + submitted) |
| `timestamp` | ISO 8601 | When the observation was recorded (truncated to hour, UTC) |

Each observation is a single JSON file stored locally at `~/.proven/observations/`.

## What Is NOT Collected

- No source code, file paths, or file contents
- No conversation text, prompts, or LLM responses
- No error messages or compiler output
- No project names, repository URLs, or directory structures
- No system information (OS, hardware, network)
- No behavioral telemetry, keystrokes, or timing data
- No information about other tools, plugins, or workflows

The schema is fixed-enum by design. Fields accept only predefined categories or integer counts. Values containing file path separators or exceeding 100 characters are rejected during validation.

## How Data Is Used

Submitted observations are analyzed in aggregate to answer the research question. Analysis focuses on:

- Whether users who receive advise output take actions consistent with strengthening guarantees
- Whether action rates change with repeated invocations (within-subject comparison)
- Whether certain code patterns (state machines, bounded resources) elicit stronger responses
- Trajectory clustering if sufficient data accumulates

Individual submissions are not singled out in reporting. Results are presented as group statistics (rates, distributions, statistical tests at predefined thresholds).

The experiment design specifies threshold-based analysis: different analyses become possible at N=5, N=15, N=30, and N=50 observations. There is no fixed timeline — analysis occurs when thresholds are reached.

## Risks

**Public visibility.** Submissions are GitHub issues on the melek/proven repository. Anyone can read them.

**GitHub identity.** Your GitHub username is attached to the issue you create. The observation data itself uses a hashed installation ID (first 8 characters of SHA-256 of a local UUID + salt), but your GitHub identity is visible on the issue.

**Permanence.** GitHub issues can be deleted by the repository owner, but data may persist in caches, forks, or third-party archives. Treat submissions as permanent.

**Longitudinal linking.** The hashed installation ID allows linking observations across submissions from the same installation. Rotating the installation ID (`proven-research.sh rotate-id`) breaks this link but also breaks longitudinal analysis for that installation.

## Voluntary Participation

The Proven plugin works identically whether or not you participate. The `/proven:advise` and `/proven:survey` skills produce the same output regardless of observation collection status. No functionality is gated behind participation.

Observations are collected locally and only submitted when you explicitly run the submit command. You can preview all accumulated data before submission.

## How to Withdraw

**Delete local data.** Run `proven-research.sh purge` to delete all local observations (pending and submitted records).

**Disable collection.** Run `proven-research.sh disable` to stop future observation collection.

**Request issue deletion.** To remove a submitted observation from GitHub, open an issue on the melek/proven repository requesting deletion. Include the hashed installation ID from your submission. The repository owner will delete the issue.

**Rotate installation ID.** Run `proven-research.sh rotate-id` to generate a new ID, preventing linkage between future submissions and past ones.

## References

- Full experiment design: `research/experiments/004-methodology-transfer/DESIGN.md`
- Proven pipeline and research: `CLAUDE.md`
- Ablation study results: `research/experiments/001-ablation-preprocessing/`
- Paper outline: `research/paper-outline.md`
