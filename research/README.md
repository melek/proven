# Proven Research

This directory contains literature reviews, experiments, and shared analysis tools for the Proven project.

## Structure

```
research/
├── paper-outline.md           # Working paper draft
├── lit-reviews/               # Literature reviews by topic
├── experiments/               # Numbered experiment directories
│   ├── NNN-short-name/
│   │   ├── DESIGN.md          # Required: hypothesis, method, analysis plan
│   │   ├── *.py               # Experiment scripts
│   │   └── results/           # Output data
├── oracle_tests/              # Independent test suite (cross-experiment)
└── shared/                    # Utilities used across experiments
```

## Experiment Conventions

- **Naming:** `NNN-short-name/` (zero-padded, sequential)
- **Required:** Every experiment has a `DESIGN.md` following the template below
- **Results:** Go in `results/` subdirectory, never at experiment root
- **Self-contained:** Each experiment should be runnable independently
- **Shared utilities:** Cross-experiment scripts live in `shared/`

## DESIGN.md Template

```markdown
# Experiment NNN: Title

## Research Question
## Hypothesis
## Method
## Variables
- Independent:
- Dependent:
- Controlled:
## Data Collection
## Analysis Plan
## Null Result Protocol
## Status
planned | running | complete
## Results Summary
(if complete)
```
