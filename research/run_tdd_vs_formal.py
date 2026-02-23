"""Orchestration: run TDD conditions across all benchmarks.

Formal results already exist. This script runs the TDD condition(s) and
optionally triggers oracle evaluation.

Usage:
    # Run TDD with local model (qwen 14B):
    python research/run_tdd_vs_formal.py --conditions T-local

    # Run TDD with Sonnet:
    python research/run_tdd_vs_formal.py --conditions T-sonnet

    # Run both:
    python research/run_tdd_vs_formal.py --conditions T-local,T-sonnet

    # Specific benchmarks:
    python research/run_tdd_vs_formal.py --conditions T-local --benchmarks ring_buffer,stack
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


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

# Condition configs
CONDITIONS = {
    "T-local": {
        "label": "TDD + Local (qwen 14B)",
        "model": None,        # uses env defaults
        "base_url": None,
        "api_key": None,
        "output_prefix": "runs/tdd/local",
    },
    "T-sonnet": {
        "label": "TDD + Sonnet",
        "model": "claude-sonnet-4-6",
        "base_url": "https://api.anthropic.com/v1",
        "api_key": None,      # uses ANTHROPIC_API_KEY env var
        "output_prefix": "runs/tdd/sonnet",
    },
}


def run_tdd_condition(
    problem: str,
    condition: str,
    max_attempts: int = 10,
    verbose: bool = False,
) -> dict:
    """Run TDD agent for one problem under one condition."""
    config = CONDITIONS[condition]
    examples_dir = Path("examples")
    req_file = examples_dir / f"{problem}.md"

    if not req_file.exists():
        return {
            "problem": problem,
            "condition": condition,
            "label": config["label"],
            "tests_pass": False,
            "full_success": False,
            "error": f"Missing {req_file}",
        }

    output_dir = Path(config["output_prefix"]) / problem

    cmd = [
        sys.executable, "research/tdd_agent.py", str(req_file),
        "--max-attempts", str(max_attempts),
        "--output-dir", str(output_dir),
    ]

    if config["model"]:
        cmd.extend(["--model", config["model"]])
    if config["base_url"]:
        cmd.extend(["--base-url", config["base_url"]])
    if config["api_key"]:
        cmd.extend(["--api-key", config["api_key"]])
    if verbose:
        cmd.append("--verbose")

    print(f"\n  [{condition}] {config['label']}: {problem}")
    start = time.time()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print(f"  [{condition}] {problem}: TIMEOUT")
        return {
            "problem": problem,
            "condition": condition,
            "label": config["label"],
            "tests_pass": False,
            "full_success": False,
            "wall_time_sec": 600,
            "error": "TIMEOUT",
        }

    elapsed = time.time() - start

    # Parse run_state.json
    state_file = output_dir / "run_state.json"
    tests_pass = False
    if state_file.exists():
        state = json.loads(state_file.read_text())
        stage_status = {str(k): v for k, v in state.get("stage_status", {}).items()}
        tests_pass = stage_status.get("4") == "completed"

    status = "PASS" if tests_pass else "FAIL"
    print(f"  [{condition}] {problem}: {status} ({elapsed:.0f}s)")

    return {
        "problem": problem,
        "condition": condition,
        "label": config["label"],
        "tests_pass": tests_pass,
        "full_success": tests_pass,
        "wall_time_sec": round(elapsed, 1),
        "exit_code": result.returncode,
    }


def print_comparison(results: list[dict]):
    """Print comparison table across TDD conditions."""
    print(f"\n{'=' * 80}")
    print(f"  TDD vs Formal — Results")
    print(f"{'=' * 80}")

    conditions = sorted(set(r["condition"] for r in results))
    cond_labels = {r["condition"]: r.get("label", r["condition"]) for r in results}

    header = f"  {'Problem':<24} {'Difficulty':<10}"
    for c in conditions:
        header += f" {cond_labels.get(c, c):<20}"
    print(header)
    print(f"  {'-' * 76}")

    for problem in BENCHMARKS:
        row = f"  {problem:<24} {DIFFICULTY.get(problem, '?'):<10}"
        for c in conditions:
            matches = [r for r in results if r["problem"] == problem and r["condition"] == c]
            if matches:
                r = matches[0]
                status = "PASS" if r["full_success"] else "FAIL"
                time_str = f" ({r.get('wall_time_sec', 0):.0f}s)" if r.get("wall_time_sec") else ""
                row += f" {status + time_str:<20}"
            else:
                row += f" {'—':<20}"
        print(row)

    # Summary
    print(f"\n  {'Summary':<24} {'—':<10}", end="")
    for c in conditions:
        c_results = [r for r in results if r["condition"] == c]
        total = len(c_results)
        passed = sum(1 for r in c_results if r["full_success"])
        avg_time = sum(r.get("wall_time_sec", 0) for r in c_results) / total if total else 0
        summary = f"{passed}/{total} pass ({avg_time:.0f}s avg)"
        print(f" {summary:<20}", end="")
    print(f"\n{'=' * 80}")


def main():
    parser = argparse.ArgumentParser(
        description="Run TDD conditions for TDD vs Formal comparison",
    )
    parser.add_argument(
        "--conditions", default="T-local",
        help="Comma-separated conditions: T-local, T-sonnet (default: T-local)",
    )
    parser.add_argument(
        "--benchmarks", default="all",
        help="Comma-separated benchmark names or 'all'",
    )
    parser.add_argument("--max-attempts", type=int, default=10,
                        help="Max implementation iterations per problem")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    conditions = [c.strip() for c in args.conditions.split(",")]
    benchmarks = BENCHMARKS if args.benchmarks == "all" else [
        b.strip() for b in args.benchmarks.split(",")
    ]

    # Validate conditions
    for c in conditions:
        if c not in CONDITIONS:
            print(f"Error: unknown condition '{c}'. Available: {', '.join(CONDITIONS)}")
            return 1

    print(f"TDD vs Formal Experiment")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Benchmarks: {len(benchmarks)} problems")
    print(f"Max attempts: {args.max_attempts}")
    print(f"{'=' * 80}")

    all_results: list[dict] = []

    for problem in benchmarks:
        for condition in conditions:
            result = run_tdd_condition(
                problem, condition,
                max_attempts=args.max_attempts,
                verbose=args.verbose,
            )
            all_results.append(result)

    print_comparison(all_results)

    # Save results
    results_file = Path("research/tdd_results.json")
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\n  Results saved to: {results_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
