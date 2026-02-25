"""Adaptive pipeline strategy selection based on model capability profiles.

Maps model names to pipeline strategies. Strong models get less scaffolding
(iterative generate-verify-fix); weak models get full pipeline support.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .config import Config


class Strategy(str, Enum):
    FULL = "full"            # All stages, all scaffolding (current behavior)
    LIGHT = "light"          # Simplified Stage 1, reduced mentor/retry budgets
    ITERATIVE = "iterative"  # Skip Stage 1, merge spec+impl, no mentor


@dataclass(frozen=True)
class ModelProfile:
    strategy: Strategy
    max_output_tokens: int
    context_window: int
    include_dafny_reference: bool


# Known model profiles — strategy assignment based on experiment data.
# Default to FULL (safe) for unknown models.
KNOWN_PROFILES: dict[str, ModelProfile] = {
    # Strong models: iterative mode (let them use training data recall)
    "claude-opus-4-6":       ModelProfile(Strategy.ITERATIVE, 16384, 200000, False),
    "claude-sonnet-4-6":     ModelProfile(Strategy.ITERATIVE, 16384, 200000, False),
    "claude-sonnet-4-5-20250514": ModelProfile(Strategy.ITERATIVE, 16384, 200000, False),
    # Medium models: light pipeline (some structure, less decomposition)
    "claude-haiku-4-5-20251001": ModelProfile(Strategy.LIGHT, 8192, 200000, True),
    "gpt-4o":                ModelProfile(Strategy.LIGHT, 16384, 128000, False),
    "gpt-4o-mini":           ModelProfile(Strategy.LIGHT, 8192, 128000, True),
    # Weak/local models: full pipeline (all scaffolding)
    "qwen2.5-coder:14b":    ModelProfile(Strategy.FULL, 4096, 32768, True),
    "qwen2.5-coder:7b":     ModelProfile(Strategy.FULL, 4096, 32768, True),
    "qwen2.5-coder:32b":    ModelProfile(Strategy.FULL, 4096, 32768, True),
}

DEFAULT_PROFILE = ModelProfile(Strategy.FULL, 8192, 32768, True)


def resolve_profile(
    model_name: str,
    strategy_override: str | None = None,
) -> ModelProfile:
    """Determine the model profile. CLI override > static table > default.

    Args:
        model_name: The LLM model name from config.
        strategy_override: CLI --strategy value. "auto" or None uses the table.
    """
    # Look up base profile from static table
    profile = KNOWN_PROFILES.get(model_name, DEFAULT_PROFILE)

    # CLI override replaces the strategy (keeps other profile properties)
    if strategy_override and strategy_override != "auto":
        strategy = Strategy(strategy_override)
        profile = replace(profile, strategy=strategy)

    return profile


def apply_strategy(config: Config, profile: ModelProfile) -> Config:
    """Return a new Config with strategy-appropriate parameter values.

    FULL strategy: preserves all current defaults (no changes).
    LIGHT strategy: simplified decomposition, reduced retry budgets.
    ITERATIVE strategy: skip Stage 1, merge spec+impl, minimal scaffolding.
    """
    if profile.strategy == Strategy.FULL:
        return replace(
            config,
            max_output_tokens=profile.max_output_tokens,
            include_dafny_reference=profile.include_dafny_reference,
            strategy_name=Strategy.FULL.value,
        )

    if profile.strategy == Strategy.LIGHT:
        return replace(
            config,
            light_stage1=True,
            mentor_budget=min(config.mentor_budget, 1),
            rollback_budget=0,
            best_of_n=min(config.best_of_n, 1),
            max_output_tokens=profile.max_output_tokens,
            include_dafny_reference=profile.include_dafny_reference,
            strategy_name=Strategy.LIGHT.value,
        )

    # ITERATIVE
    return replace(
        config,
        skip_stage1=True,
        merge_spec_impl=True,
        mentor_budget=0,
        rollback_budget=0,
        best_of_n=0,
        max_output_tokens=profile.max_output_tokens,
        include_dafny_reference=profile.include_dafny_reference,
        strategy_name=Strategy.ITERATIVE.value,
    )
