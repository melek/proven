"""Run ablation study: isolate decompose, mentor, and rollback effects.

4 configurations × 9 benchmarks × 3 trials × 2 models = 216 runs.
All runs use --strategy full --best-of-n 0 to prevent confounding.

Usage:
    # Full run (one model)
    python research/run_ablation.py --models qwen2.5-coder-14b

    # Pilot (4 cells)
    python research/run_ablation.py \
        --models qwen2.5-coder-14b \
        --configs A_baseline,C_decompose \
        --problems bounded_counter,priority_queue \
        --trials 1

    # Preview without executing
    python research/run_ablation.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ─────────────────────────────────────────────────────────────
# Experiment definitions
# ─────────────────────────────────────────────────────────────

BENCHMARKS = [
    "bounded_counter",
    "stack",
    "priority_queue",
    "sorted_list",
    "unique_set",
    "pipeline_state",
    "binary_search",
    "ring_buffer",
    "balanced_parentheses",
]

DIFFICULTY = {
    "bounded_counter": "simple",
    "stack": "simple",
    "priority_queue": "medium",
    "sorted_list": "medium",
    "unique_set": "medium",
    "pipeline_state": "medium",
    "binary_search": "hard",
    "ring_buffer": "hard",
    "balanced_parentheses": "hard",
}

# Ablation configurations: the independent variable
CONFIGS = {
    "A_baseline": {
        "label": "A: Baseline",
        "flags": [
            "--no-decompose",
            "--mentor-budget", "0",
            "--rollback-budget", "0",
        ],
    },
    "B_mentor": {
        "label": "B: +Mentor",
        "flags": [
            "--no-decompose",
            "--mentor-budget", "3",
            "--rollback-budget", "0",
        ],
    },
    "C_decompose": {
        "label": "C: +Decompose",
        "flags": [
            "--mentor-budget", "0",
            "--rollback-budget", "0",
        ],
    },
    "D_full": {
        "label": "D: Full Pipeline",
        "flags": [
            "--mentor-budget", "3",
            "--rollback-budget", "1",
        ],
    },
}

# Common flags for ALL configs (prevents confounding)
COMMON_FLAGS = [
    "--mode", "autonomous",
    "--max-retries", "6",
    "--strategy", "full",   # Prevents auto-strategy from overriding ablation flags
    "--best-of-n", "0",     # Disabled to avoid confounding
]

MODEL_CONFIGS = {
    "qwen2.5-coder-14b": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "qwen2.5-coder:14b",
    },
    "claude-sonnet": {
        "base_url": "https://api.anthropic.com/v1",
        "api_key": "",  # loaded from env
        "model": "claude-sonnet-4-6",
    },
}

RUN_TIMEOUT = 900  # 15 minutes per run


# ─────────────────────────────────────────────────────────────
# Workspace and result management
# ─────────────────────────────────────────────────────────────

def workspace_dir(model_slug: str, config_name: str, problem: str, trial: int) -> Path:
    return Path("runs/ablation") / model_slug / config_name / problem / f"trial_{trial}"


def cell_has_result(ws_dir: Path) -> bool:
    for _ in ws_dir.rglob("run_state.json"):
        return True
    return False


def parse_run_state(output_dir: Path) -> tuple[bool, bool]:
    """Parse run_state.json (may be in timestamped subdir)."""
    for state_file in sorted(output_dir.rglob("run_state.json")):
        state = json.loads(state_file.read_text())
        stage_status = {int(k): v for k, v in state.get("stage_status", {}).items()}
        verified = stage_status.get(4) == "completed"
        compiled = stage_status.get(5) == "completed"
        return verified, compiled
    return False, False


# ─────────────────────────────────────────────────────────────
# Execution
# ─────────────────────────────────────────────────────────────

def run_single_cell(
    model_slug: str,
    model_config: dict,
    config_name: str,
    ablation_config: dict,
    problem: str,
    trial: int,
    verbose: bool = False,
) -> dict:
    """Execute a single pipeline run for one cell of the ablation matrix."""
    ws_dir = workspace_dir(model_slug, config_name, problem, trial)
    req_file = Path("examples") / f"{problem}.md"

    env = os.environ.copy()
    env["LLM_BASE_URL"] = model_config["base_url"]
    env["LLM_API_KEY"] = model_config["api_key"]
    env["LLM_MODEL"] = model_config["model"]

    cmd = [
        sys.executable, "-m", "proven", "run", str(req_file),
        *COMMON_FLAGS,
        *ablation_config["flags"],
        "--workspace-dir", str(ws_dir),
    ]
    if verbose:
        cmd.append("--verbose")

    start = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=RUN_TIMEOUT, env=env,
        )
        exit_code = result.returncode
        stdout = result.stdout
    except subprocess.TimeoutExpired:
        exit_code = -1
        stdout = ""
    elapsed = time.time() - start

    verified, compiled = parse_run_state(ws_dir)

    return {
        "model": model_slug,
        "config": config_name,
        "config_label": ablation_config["label"],
        "problem": problem,
        "trial": trial,
        "difficulty": DIFFICULTY.get(problem, "?"),
        "verified": verified,
        "compiled": compiled,
        "wall_time_sec": round(elapsed, 1),
        "exit_code": exit_code,
    }


def build_run_queue(
    models: list[str],
    configs: list[str],
    problems: list[str],
    trials: int,
    skip_existing: bool = True,
) -> list[tuple[str, str, str, int]]:
    """Build the list of (model, config, problem, trial) cells to run."""
    queue = []
    skipped = 0
    for model_slug in models:
        for config_name in configs:
            for problem in problems:
                for trial in range(1, trials + 1):
                    ws = workspace_dir(model_slug, config_name, problem, trial)
                    if skip_existing and cell_has_result(ws):
                        skipped += 1
                        continue
                    queue.append((model_slug, config_name, problem, trial))
    return queue, skipped


def print_progress(results: list[dict], models: list[str], configs: list[str]):
    """Print intermediate progress table."""
    print(f"\n  {'-' * 60}")
    print(f"  Progress: {len(results)} runs completed")
    print(f"  {'-' * 60}")

    for model in models:
        model_results = [r for r in results if r["model"] == model]
        if not model_results:
            continue
        print(f"\n  {model}:")
        for config in configs:
            cfg_results = [r for r in model_results if r["config"] == config]
            if not cfg_results:
                continue
            total = len(cfg_results)
            passed = sum(1 for r in cfg_results if r["compiled"])
            verified = sum(1 for r in cfg_results if r["verified"])
            label = CONFIGS[config]["label"]
            print(f"    {label:<22} {passed}/{total} compiled, {verified}/{total} verified")
    print(f"  {'-' * 60}")


def print_final_matrix(results: list[dict], models: list[str], configs: list[str], problems: list[str]):
    """Print the full result matrix."""
    print(f"\n{'=' * 90}")
    print(f"  Ablation Study Results")
    print(f"{'=' * 90}")

    for model in models:
        model_results = [r for r in results if r["model"] == model]
        if not model_results:
            continue

        print(f"\n  Model: {model}")
        header = f"  {'Problem':<24} {'Diff':<8}"
        for config in configs:
            label = CONFIGS[config]["label"]
            header += f" {label:<16}"
        print(header)
        print(f"  {'-' * 80}")

        for problem in problems:
            row = f"  {problem:<24} {DIFFICULTY.get(problem, '?'):<8}"
            for config in configs:
                cell = [r for r in model_results
                        if r["config"] == config and r["problem"] == problem]
                if cell:
                    passed = sum(1 for r in cell if r["compiled"])
                    total = len(cell)
                    row += f" {passed}/{total:<14}"
                else:
                    row += f" {'—':<16}"
            print(row)

        # Summary row
        print(f"  {'-' * 80}")
        row = f"  {'TOTAL':<24} {'':8}"
        for config in configs:
            cfg_results = [r for r in model_results if r["config"] == config]
            total = len(cfg_results)
            passed = sum(1 for r in cfg_results if r["compiled"])
            if total > 0:
                pct = 100 * passed / total
                row += f" {passed}/{total} ({pct:.0f}%)     "
            else:
                row += f" {'—':<16}"
        print(row)

    print(f"{'=' * 90}")


def save_results(results: list[dict], output_path: Path):
    """Save results atomically."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    tmp_path.replace(output_path)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run ablation study: isolate decompose, mentor, and rollback effects",
    )
    parser.add_argument(
        "--models", default="qwen2.5-coder-14b",
        help="Comma-separated model slugs (default: qwen2.5-coder-14b)",
    )
    parser.add_argument(
        "--configs", default="A_baseline,B_mentor,C_decompose,D_full",
        help="Comma-separated config names (default: all four)",
    )
    parser.add_argument(
        "--problems", default=None,
        help="Comma-separated problem names (default: all 9 original benchmarks)",
    )
    parser.add_argument(
        "--trials", type=int, default=3,
        help="Number of trials per cell (default: 3)",
    )
    parser.add_argument(
        "--no-skip", action="store_true",
        help="Re-run cells even if results already exist",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the run queue without executing",
    )
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    configs = [c.strip() for c in args.configs.split(",")]
    problems = [p.strip() for p in args.problems.split(",")] if args.problems else BENCHMARKS

    # Validate inputs
    for m in models:
        if m not in MODEL_CONFIGS:
            print(f"Error: unknown model '{m}'. Available: {', '.join(MODEL_CONFIGS)}")
            return 1
    for c in configs:
        if c not in CONFIGS:
            print(f"Error: unknown config '{c}'. Available: {', '.join(CONFIGS)}")
            return 1
    for p in problems:
        req_file = Path("examples") / f"{p}.md"
        if not req_file.exists():
            print(f"Error: benchmark not found: {req_file}")
            return 1

    # Load API key from .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    for slug, mcfg in MODEL_CONFIGS.items():
        if not mcfg["api_key"]:
            mcfg["api_key"] = os.environ.get("LLM_API_KEY", "")

    # Build queue
    queue, skipped = build_run_queue(
        models, configs, problems, args.trials,
        skip_existing=not args.no_skip,
    )
    total_cells = len(models) * len(configs) * len(problems) * args.trials

    print(f"Ablation Study")
    print(f"Models:  {', '.join(models)}")
    print(f"Configs: {', '.join(configs)}")
    print(f"Problems: {len(problems)} benchmarks")
    print(f"Trials:  {args.trials}")
    print(f"Total cells: {total_cells}, skipped: {skipped}, to run: {len(queue)}")
    print(f"{'=' * 60}")

    if args.dry_run:
        print(f"\nDry run — would execute {len(queue)} cells:")
        for model, config, problem, trial in queue:
            print(f"  {model} / {config} / {problem} / trial_{trial}")
        return 0

    if not queue:
        print("\nAll cells already have results. Use --no-skip to re-run.")
        return 0

    # Load existing results
    results_path = Path("research/ablation_results.json")
    results: list[dict] = []
    if results_path.exists():
        try:
            results = json.loads(results_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            results = []

    # Run
    for i, (model_slug, config_name, problem, trial) in enumerate(queue):
        label = CONFIGS[config_name]["label"]
        print(f"\n[{i + 1}/{len(queue)}] {model_slug} / {label} / {problem} / trial_{trial}")

        result = run_single_cell(
            model_slug, MODEL_CONFIGS[model_slug],
            config_name, CONFIGS[config_name],
            problem, trial,
            verbose=args.verbose,
        )
        results.append(result)

        status = "PASS" if result["compiled"] else ("VERIFY" if result["verified"] else "FAIL")
        print(f"  -> {status} ({result['wall_time_sec']:.0f}s)")

        # Save after every run
        save_results(results, results_path)

        # Progress every 9 runs (one full problem set)
        if (i + 1) % 9 == 0:
            print_progress(results, models, configs)

    # Final summary
    print_final_matrix(results, models, configs, problems)
    save_results(results, results_path)
    print(f"\nResults saved to: {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
