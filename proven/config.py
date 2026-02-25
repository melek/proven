"""Configuration loading from .env, environment variables, and CLI args."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    # LLM
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    # Pipeline
    mode: str  # "assisted" | "autonomous" | "semi"
    max_retries: int
    target: str  # Dafny compilation target
    verbose: bool

    # Mentor
    mentor_budget: int  # Max mentor interventions per run (0 to disable)

    # Decomposition
    decompose_enabled: bool  # Run deterministic spec simplification before Stage 3
    rollback_budget: int  # Max rollbacks to Stage 2 (0 to disable)

    # Retry strategy
    best_of_n: int  # Fresh samples after adaptive retries (0 to disable)

    # Paths
    workspace_root: Path
    dafny_path: str

    # Strategy (set by apply_strategy, not directly by user)
    skip_stage1: bool = False           # Skip Stage 1 requirements capture
    merge_spec_impl: bool = False       # Merge Stages 2+3 into single generation
    light_stage1: bool = False          # Simplified Stage 1 (max 3 operations)
    max_output_tokens: int = 8192       # LLM completion token limit
    include_dafny_reference: bool = True  # Include Dafny syntax guide in prompts
    strategy_name: str = "full"         # For logging/display


def load_config(
    mode: str = "assisted",
    max_retries: int = 3,
    target: str = "py",
    verbose: bool = False,
    workspace_dir: Path | None = None,
    mentor_budget: int = 3,
    decompose_enabled: bool = True,
    rollback_budget: int = 1,
    best_of_n: int = 3,
    model: str | None = None,
) -> Config:
    """Load config from .env + env vars, with explicit args taking priority."""
    from dotenv import load_dotenv

    load_dotenv()

    return Config(
        llm_base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        llm_model=model or os.environ.get("LLM_MODEL", "claude-sonnet-4-6"),
        mode=mode,
        max_retries=max_retries,
        target=target,
        verbose=verbose,
        mentor_budget=mentor_budget,
        decompose_enabled=decompose_enabled,
        rollback_budget=rollback_budget,
        best_of_n=best_of_n,
        workspace_root=workspace_dir or Path("./runs"),
        dafny_path=os.environ.get("DAFNY_PATH", "dafny"),
    )
