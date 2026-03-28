# Experiment 004: Methodology Transfer Through an AI Advisory Skill

## Research Question

Does formal verification methodology translate effectively through an AI advisory skill? Specifically: do users who receive `/proven:advise` output subsequently take actions consistent with strengthening code guarantees, and does this pattern persist over time?

## Operationalization

"Translates effectively" is operationalized as: users who receive advise output subsequently take actions consistent with strengthening code guarantees (editing code, committing changes, asking follow-up questions about guarantees), and this pattern persists or increases across repeated invocations. The null hypothesis is that action rates are constant across invocations — users do not change behavior based on accumulated exposure to verification-informed analysis.

## Method

Single-group longitudinal observational study with within-subject comparisons. There is no control group — the study observes natural usage of the advise skill and tests whether behavior changes with exposure.

Data collection is opt-in, observation-only. The plugin's behavior is identical for participants and non-participants. Observations are structured counts and enum categories collected locally and submitted to GitHub by the user's explicit choice.

## Variables

### Independent

- **Skill invocation count** — ordinal position of each invocation for a given installation (1st, 2nd, 3rd, ...). The primary independent variable for the within-subject comparison.
- **Code pattern type** — what the advise skill identified (state machines, bounded resources, security boundaries, data integrity). Categorical.
- **Gap count** — number of unenforced assumptions the skill identified. Integer.

### Dependent

- **Action taken** — what the user did after receiving advise output. Enum: `edited` (modified code), `committed` (committed changes), `no-action` (no observable action), `asked-followup` (continued the conversation about guarantees).
- **Re-invocation rate** — whether the user invokes advise again in subsequent sessions. Binary per session.

### Controlled (by schema design)

- **Schema is fixed-enum.** Fields accept only predefined categories or integer counts.
- **No user content.** No source code, file paths, conversation text, or error messages are collected.
- **Observation granularity.** One observation per skill invocation — not per session or per day.

## Observation Schema

```json
{
  "skill": "advise",
  "patterns_found": 3,
  "gaps": 2,
  "options": 1,
  "language": "python",
  "loc": "200-1000",
  "action": "edited",
  "timestamp": "2026-03-27T14:30:00Z"
}
```

Fields:

| Field | Type | Values |
|-------|------|--------|
| `skill` | enum | `advise`, `survey` |
| `patterns_found` | integer | Count of guarantee patterns identified |
| `gaps` | integer | Count of unenforced assumptions |
| `options` | integer | Count of strengthening options presented |
| `language` | enum | Programming language of analyzed code |
| `loc` | enum | `<50`, `50-200`, `200-1000`, `1000+` |
| `action` | enum | `edited`, `committed`, `no-action`, `asked-followup` |
| `timestamp` | ISO 8601 | When the observation was recorded |

Validation rules: no value may contain `/` (file path indicator), no value may exceed 100 characters, `skill` must be in the enum set, `loc` must be in the enum set, `action` must be in the enum set.

## Threshold-Based Analysis

The study uses threshold-based analysis rather than a fixed sample size or timeline. Different analyses become possible as data accumulates. At each threshold, if the data shows no signal, we report descriptively and continue collecting.

### N=1: Proof of concept

- Schema validation: confirm the observation pipeline produces well-formed data
- End-to-end test: enable, collect, preview, submit
- Identify any instrumentation problems before wider use

### N=5: Descriptive statistics

- Distribution of actions across invocations
- Distribution of code pattern types and languages
- Most common gap counts and option counts
- Baseline action rate (proportion of invocations leading to edits or commits)

### N=15: Within-subject comparison

- **Primary test:** McNemar test on action rate, comparing 1st-2nd invocations (early) vs. 3rd+ invocations (later) within subjects who have at least 3 invocations
- Effect size: odds ratio for taking action after early vs. later invocations
- If McNemar test is not significant: report the observed action rates descriptively, note the sample size limitation, continue collecting

### N=30: Trajectory clustering

- Group installations by action trajectory (e.g., "consistently edits", "initially no-action then edits", "no-action throughout")
- k-means or hierarchical clustering on the sequence of actions per installation
- Descriptive characterization of cluster types
- If clusters are not distinguishable: report that trajectories are homogeneous, which is itself informative

### N=50: Pattern-specific analysis

- Action rates stratified by code pattern type (state machines vs. bounded resources vs. security boundaries)
- Chi-square test for independence between pattern type and action taken
- Gap count as predictor: logistic regression with action (binary: edited/committed vs. no-action) as outcome, gap count as predictor
- If no pattern-specific effects: report that the methodology transfers (or fails to transfer) uniformly across pattern types

## Null Result Protocol

At each threshold, if the expected signal is absent, we report the null result descriptively rather than abandoning the study. Specific null results and their interpretations:

- **Constant action rate across invocations (N=15):** The methodology does not accumulate — users respond the same way to their 10th advise output as their 1st. This is informative: it suggests the skill provides situation-specific value (or not) rather than building transferred understanding.
- **No trajectory clusters (N=30):** All users follow similar patterns. If the pattern is high-action, the skill is broadly useful. If low-action, the methodology may not transfer through this medium.
- **No pattern-specific effects (N=50):** The skill's impact (or lack thereof) is uniform across code patterns. This constrains future work: improving transfer requires improving the skill overall, not targeting specific code patterns.

## Ethical Considerations

- **Informed consent.** The `/proven:contribute` skill walks through a conversational consent flow explaining what is collected, what is not, and how data is used, before enabling collection.
- **Voluntariness.** The plugin functions identically without participation. No functionality is gated.
- **Transparency.** All collected data can be previewed before submission. The full schema is disclosed during consent.
- **Right to withdraw.** Users can disable collection, purge local data, and request deletion of submitted GitHub issues.
- **Public data.** Submissions are GitHub issues — public and potentially permanent. Users are informed of this during the consent and submission flows.
- **Minimal data.** The schema was designed to answer the research question with the least possible data. No user content is collected.

## Limitations

- **Self-selection bias.** Users who opt in to observation collection may already be interested in formal verification, biasing action rates upward.
- **Observation effect.** Knowing that actions are observed may change behavior (Hawthorne effect). Mitigated by the fact that observation categories are coarse — users cannot "perform" for the observer in any meaningful way.
- **Action attribution.** The `action` field captures what happened after advise output, not whether advise caused it. Users may have edited for unrelated reasons.
- **Single instrument.** All observations come from the same skill. We cannot compare methodology transfer through different media (e.g., documentation vs. advisory skill).
- **No control group.** Within-subject comparison (early vs. late invocations) partially addresses this, but we cannot compare to users who never use the skill.

## Deferred

Pipeline execution observations (model family, difficulty tier, verification success) are deferred to a future version. The current schema covers skill invocations only.

## Status

Planned.
