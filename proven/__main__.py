"""CLI entry point: python -m proven"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import dafny as dafny_tool
from .config import load_config
from .pipeline import run_pipeline, resume_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="proven",
        description="LLM-driven stepwise refinement with Dafny verification",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run the pipeline on a requirements file")
    run_parser.add_argument("requirements_file", type=Path, help="Path to requirements (.md)")
    run_parser.add_argument("--model", default=None, help="LLM model (overrides LLM_MODEL env var)")
    run_parser.add_argument(
        "--mode", choices=["assisted", "autonomous", "semi"], default="assisted",
        help="Interaction mode (default: assisted)",
    )
    run_parser.add_argument("--max-retries", type=int, default=3, help="Max retries per stage")
    run_parser.add_argument(
        "--target", choices=["py", "cs", "go", "java", "js"], default="py",
        help="Dafny compilation target (default: py)",
    )
    run_parser.add_argument("--workspace-dir", type=Path, default=None, help="Override workspace root")
    run_parser.add_argument("--verbose", action="store_true", help="Print LLM prompts and responses")
    run_parser.add_argument(
        "--mentor-budget", type=int, default=3,
        help="Max mentor interventions per run (0 to disable, default: 3)",
    )
    run_parser.add_argument(
        "--no-decompose", action="store_true",
        help="Disable deterministic spec decomposition before Stage 3",
    )
    run_parser.add_argument(
        "--rollback-budget", type=int, default=1,
        help="Max rollbacks to Stage 2 (0 to disable, default: 1)",
    )
    run_parser.add_argument(
        "--best-of-n", type=int, default=3,
        help="Fresh samples after adaptive retries exhaust (0 to disable, default: 3)",
    )
    run_parser.add_argument(
        "--strategy", choices=["full", "light", "iterative", "auto"], default="auto",
        help="Pipeline strategy: full (all scaffolding), light (simplified decomposition), "
             "iterative (generate-verify-fix), auto (select from model). Default: auto",
    )

    # --- resume ---
    resume_parser = subparsers.add_parser("resume", help="Resume a pipeline from an existing workspace")
    resume_parser.add_argument("workspace_dir", type=Path, help="Path to existing workspace")
    resume_parser.add_argument("--from-stage", type=int, choices=[1, 2, 3, 4, 5], default=None)
    resume_parser.add_argument("--model", default=None, help="LLM model (overrides LLM_MODEL env var)")
    resume_parser.add_argument("--mode", choices=["assisted", "autonomous", "semi"], default="assisted")
    resume_parser.add_argument("--max-retries", type=int, default=3)
    resume_parser.add_argument("--target", choices=["py", "cs", "go", "java", "js"], default="py")
    resume_parser.add_argument("--verbose", action="store_true")
    resume_parser.add_argument("--mentor-budget", type=int, default=3)
    resume_parser.add_argument("--no-decompose", action="store_true")
    resume_parser.add_argument("--rollback-budget", type=int, default=1)
    resume_parser.add_argument("--best-of-n", type=int, default=3)
    resume_parser.add_argument(
        "--strategy", choices=["full", "light", "iterative", "auto"], default="auto",
    )

    # --- check ---
    subparsers.add_parser("check", help="Check that Dafny is installed")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "check":
        return _check_dafny()

    config = load_config(
        mode=args.mode,
        max_retries=args.max_retries,
        target=args.target,
        verbose=getattr(args, "verbose", False),
        workspace_dir=getattr(args, "workspace_dir", None),
        mentor_budget=getattr(args, "mentor_budget", 3),
        decompose_enabled=not getattr(args, "no_decompose", False),
        rollback_budget=getattr(args, "rollback_budget", 1),
        best_of_n=getattr(args, "best_of_n", 3),
        model=getattr(args, "model", None),
    )

    # Apply adaptive strategy based on model profile
    from .strategy import resolve_profile, apply_strategy
    strategy_override = getattr(args, "strategy", "auto")
    profile = resolve_profile(config.llm_model, strategy_override)
    config = apply_strategy(config, profile)

    if args.command == "run":
        return run_pipeline(config, args.requirements_file)
    elif args.command == "resume":
        return resume_pipeline(config, args.workspace_dir, args.from_stage)

    return 1


def _check_dafny() -> int:
    """Verify Dafny is installed and working."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    dafny_path = os.environ.get("DAFNY_PATH", "dafny")
    print(f"Checking Dafny at: {dafny_path}")
    result = dafny_tool.check_installed(dafny_path)
    if result.success:
        print(f"Dafny version: {result.stdout.strip()}")
        print("Ready.")
        return 0
    else:
        print(f"Error: {result.error_message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
