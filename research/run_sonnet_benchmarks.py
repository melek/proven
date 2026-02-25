"""Run all benchmarks through the Proven pipeline with Claude Sonnet.

Usage:
    python research/run_sonnet_benchmarks.py [--benchmarks all] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


ALL_BENCHMARKS = [
    # Original 9 (Simple → Hard)
    "bounded_counter",
    "stack",
    "priority_queue",
    "sorted_list",
    "unique_set",
    "pipeline_state",
    "binary_search",
    "ring_buffer",
    "balanced_parentheses",
    # New 6 (Hard+ → Expert)
    "compositional_pipeline",
    "extended_gcd",
    "insertion_sort",
    "red_black_tree",
    "compositional_triple",
    "topological_sort",
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
    "compositional_pipeline": "hard+",
    "extended_gcd": "hard+",
    "insertion_sort": "hard+",
    "red_black_tree": "expert",
    "compositional_triple": "expert",
    "topological_sort": "expert",
}

OUTPUT_ROOT = Path("runs/sonnet_full")


def run_benchmark(problem: str, verbose: bool = False) -> dict:
    """Run Proven pipeline on a single benchmark."""
    req_file = Path("examples") / f"{problem}.md"
    output_dir = OUTPUT_ROOT / problem

    if not req_file.exists():
        return {"problem": problem, "error": f"Missing {req_file}"}

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

    print(f"\n{'='*60}")
    print(f"  [{DIFFICULTY.get(problem, '?').upper()}] {problem}")
    print(f"{'='*60}")

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        exit_code = result.returncode
        if result.stdout:
            # Print last 20 lines of output for progress visibility
            lines = result.stdout.strip().split("\n")
            for line in lines[-20:]:
                print(f"  {line}")
        if result.returncode != 0 and result.stderr:
            for line in result.stderr.strip().split("\n")[-10:]:
                print(f"  [stderr] {line}")
    except subprocess.TimeoutExpired:
        exit_code = -1
        print(f"  TIMEOUT (900s)")

    elapsed = time.time() - start

    # Find the workspace (may be timestamped subdir)
    verified = False
    full_success = False
    stage_status = {}

    # Check for run_state.json in output_dir or its subdirectories
    for state_file in sorted(output_dir.rglob("run_state.json")):
        state = json.loads(state_file.read_text())
        stage_status = {int(k): v for k, v in state.get("stage_status", {}).items()}
        verified = stage_status.get(4) == "completed"
        full_success = stage_status.get(5) == "completed"
        break  # Use most recent

    if full_success:
        status = "COMPILED"
    elif verified:
        status = "VERIFIED"
    else:
        # Check how far it got
        max_stage = max((s for s, v in stage_status.items() if v == "completed"), default=0)
        status = f"STAGE {max_stage}" if max_stage > 0 else "FAIL"

    print(f"\n  Result: {status} ({elapsed:.0f}s)")

    return {
        "problem": problem,
        "difficulty": DIFFICULTY.get(problem, "?"),
        "verified": verified,
        "compiled": full_success,
        "stage_status": {str(k): v for k, v in stage_status.items()},
        "wall_time_sec": round(elapsed, 1),
        "exit_code": exit_code,
    }


def print_summary(results: list[dict]):
    """Print results table."""
    print(f"\n{'='*70}")
    print(f"  Proven + Sonnet — Full Benchmark Results")
    print(f"{'='*70}")
    print(f"  {'Problem':<26} {'Difficulty':<10} {'Result':<12} {'Time':>8}")
    print(f"  {'-'*66}")

    for r in results:
        if r.get("compiled"):
            status = "COMPILED"
        elif r.get("verified"):
            status = "VERIFIED"
        elif r.get("error"):
            status = "ERROR"
        else:
            stages = r.get("stage_status", {})
            max_done = max((int(s) for s, v in stages.items() if v == "completed"), default=0)
            status = f"STAGE {max_done}" if max_done > 0 else "FAIL"
        time_str = f"{r.get('wall_time_sec', 0):.0f}s"
        print(f"  {r['problem']:<26} {r.get('difficulty', '?'):<10} {status:<12} {time_str:>8}")

    compiled = sum(1 for r in results if r.get("compiled"))
    verified = sum(1 for r in results if r.get("verified"))
    total = len(results)
    total_time = sum(r.get("wall_time_sec", 0) for r in results)

    print(f"  {'-'*66}")
    print(f"  Compiled: {compiled}/{total}   Verified: {verified}/{total}   Total time: {total_time:.0f}s")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description="Run all benchmarks with Sonnet")
    parser.add_argument(
        "--benchmarks", default="all",
        help="Comma-separated benchmark names or 'all' (default: all)",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.benchmarks == "all":
        benchmarks = ALL_BENCHMARKS
    else:
        benchmarks = [b.strip() for b in args.benchmarks.split(",")]

    print(f"Proven + Sonnet — Full Benchmark Run")
    print(f"Model: claude-sonnet-4-6")
    print(f"Benchmarks: {len(benchmarks)} problems")
    print(f"Output: {OUTPUT_ROOT}")
    print(f"{'='*60}")

    all_results = []
    for problem in benchmarks:
        result = run_benchmark(problem, verbose=args.verbose)
        all_results.append(result)

        # Save intermediate results after each benchmark
        results_file = Path("research/sonnet_full_results.json")
        results_file.write_text(json.dumps(all_results, indent=2))

    print_summary(all_results)
    print(f"\n  Results saved to: research/sonnet_full_results.json")


if __name__ == "__main__":
    main()
