"""Head-to-head comparison: Proven pipeline vs freestyle agent.

Runs all conditions across all benchmarks and collects results.

Usage:
    python research/run_head_to_head.py [--conditions A,C] [--benchmarks all] [--verbose]

Conditions:
    A = Proven pipeline + local model (qwen2.5-coder:14b)
    C = Freestyle agent + local model (same model, no pipeline)
    B = Freestyle agent + Claude Sonnet (run separately via Task subagents)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


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


def run_proven(problem: str, output_dir: Path, verbose: bool = False) -> dict:
    """Run Condition A: Proven pipeline + local model."""
    examples_dir = Path("examples")
    req_file = examples_dir / f"{problem}.md"

    if not req_file.exists():
        return {"problem": problem, "condition": "A", "verified": False,
                "error": f"Missing {req_file}"}

    cmd = [
        sys.executable, "-m", "proven", "run", str(req_file),
        "--mode", "autonomous",
        "--max-retries", "6",
        "--mentor-budget", "3",
        "--rollback-budget", "1",
        "--best-of-n", "3",
        "--workspace-dir", str(output_dir),
    ]
    if verbose:
        cmd.append("--verbose")

    print(f"\n  [Condition A] Proven + local: {problem}")
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - start

    # Parse run_state.json from output dir
    state_file = output_dir / "run_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        stage_status = {int(k): v for k, v in state.get("stage_status", {}).items()}
        verified = stage_status.get(4) == "completed"
        full_success = stage_status.get(5) == "completed"
    else:
        verified = False
        full_success = False

    status = "PASS" if full_success else ("VERIFY" if verified else "FAIL")
    print(f"  [Condition A] {problem}: {status} ({elapsed:.0f}s)")

    return {
        "problem": problem,
        "condition": "A",
        "label": "Proven + Local",
        "verified": verified,
        "full_success": full_success,
        "wall_time_sec": round(elapsed, 1),
        "exit_code": result.returncode,
    }


def run_freestyle_local(problem: str, output_dir: Path, verbose: bool = False) -> dict:
    """Run Condition C: Freestyle agent + local model."""
    examples_dir = Path("examples")
    req_file = examples_dir / f"{problem}.md"

    if not req_file.exists():
        return {"problem": problem, "condition": "C", "verified": False,
                "error": f"Missing {req_file}"}

    cmd = [
        sys.executable, "research/freestyle_agent.py", str(req_file),
        "--max-attempts", "10",
        "--output-dir", str(output_dir),
    ]
    if verbose:
        cmd.append("--verbose")

    print(f"\n  [Condition C] Freestyle + local: {problem}")
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - start

    # Parse run_state.json from output dir
    state_file = output_dir / "run_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        stage_status = {int(k): v for k, v in state.get("stage_status", {}).items()}
        verified = stage_status.get(4) == "completed"
        full_success = stage_status.get(5) == "completed"
    else:
        verified = False
        full_success = False

    status = "PASS" if full_success else ("VERIFY" if verified else "FAIL")
    print(f"  [Condition C] {problem}: {status} ({elapsed:.0f}s)")

    return {
        "problem": problem,
        "condition": "C",
        "label": "Freestyle + Local",
        "verified": verified,
        "full_success": full_success,
        "wall_time_sec": round(elapsed, 1),
        "exit_code": result.returncode,
    }


def print_comparison(results: list[dict]):
    """Print a comparison table."""
    print(f"\n{'=' * 80}")
    print(f"  Head-to-Head Results")
    print(f"{'=' * 80}")

    # Group by problem
    problems = sorted(set(r["problem"] for r in results))
    conditions = sorted(set(r["condition"] for r in results))

    # Header
    cond_labels = {r["condition"]: r.get("label", r["condition"]) for r in results}
    header = f"  {'Problem':<22} {'Difficulty':<10}"
    for c in conditions:
        header += f" {cond_labels.get(c, c):<18}"
    print(header)
    print(f"  {'-' * 76}")

    for problem in problems:
        row = f"  {problem:<22} {DIFFICULTY.get(problem, '?'):<10}"
        for c in conditions:
            matches = [r for r in results if r["problem"] == problem and r["condition"] == c]
            if matches:
                r = matches[0]
                status = "PASS" if r["full_success"] else ("VERIFY" if r["verified"] else "FAIL")
                time_str = f" ({r['wall_time_sec']:.0f}s)" if r.get("wall_time_sec") else ""
                row += f" {status + time_str:<18}"
            else:
                row += f" {'—':<18}"
        print(row)

    # Summary per condition
    print(f"\n  {'Summary':<22} {'—':<10}", end="")
    for c in conditions:
        c_results = [r for r in results if r["condition"] == c]
        total = len(c_results)
        verified = sum(1 for r in c_results if r["verified"])
        full = sum(1 for r in c_results if r["full_success"])
        avg_time = (sum(r.get("wall_time_sec", 0) for r in c_results) / total) if total else 0
        print(f" {full}/{total} pass ({avg_time:.0f}s avg)", end="")
        print(" " * max(0, 18 - len(f"{full}/{total} pass ({avg_time:.0f}s avg)")), end="")
    print()
    print(f"{'=' * 80}")


def main():
    parser = argparse.ArgumentParser(description="Run head-to-head comparison")
    parser.add_argument(
        "--conditions", default="A,C",
        help="Comma-separated conditions to run (A=Proven, C=Freestyle local, default: A,C)",
    )
    parser.add_argument(
        "--benchmarks", default="all",
        help="Comma-separated benchmark names or 'all' (default: all)",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    conditions = [c.strip().upper() for c in args.conditions.split(",")]
    if args.benchmarks == "all":
        benchmarks = BENCHMARKS
    else:
        benchmarks = [b.strip() for b in args.benchmarks.split(",")]

    print(f"Head-to-Head Comparison")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Benchmarks: {len(benchmarks)} problems")
    print(f"{'=' * 80}")

    all_results: list[dict] = []

    for problem in benchmarks:
        for condition in conditions:
            if condition == "A":
                output_dir = Path(f"runs/h2h/proven_local/{problem}")
                result = run_proven(problem, output_dir, verbose=args.verbose)
                all_results.append(result)
            elif condition == "C":
                output_dir = Path(f"runs/h2h/freestyle_local/{problem}")
                result = run_freestyle_local(problem, output_dir, verbose=args.verbose)
                all_results.append(result)
            elif condition == "B":
                print(f"\n  [Condition B] Sonnet freestyle: run via Task subagents (separate)")
            else:
                print(f"\n  Unknown condition: {condition}")

    print_comparison(all_results)

    # Save results
    results_file = Path("research/h2h_results.json")
    results_file.write_text(json.dumps(all_results, indent=2))
    print(f"\n  Results saved to: {results_file}")


if __name__ == "__main__":
    main()
