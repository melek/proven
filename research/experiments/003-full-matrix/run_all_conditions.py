"""Run all 5 conditions on the new Hard+/Expert benchmarks.

Conditions:
    P-sonnet  = Proven pipeline + Sonnet     (ALREADY DONE — reads from runs/sonnet_full)
    P-local   = Proven pipeline + local qwen
    B-sonnet  = Baseline Dafny agent + Sonnet
    T-local   = TDD agent + local qwen
    T-sonnet  = TDD agent + Sonnet

Usage:
    python research/run_all_conditions.py [--conditions all] [--benchmarks new]
    python research/run_all_conditions.py --conditions B-sonnet,T-sonnet --benchmarks all
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


NEW_BENCHMARKS = [
    "compositional_pipeline",
    "extended_gcd",
    "insertion_sort",
    "red_black_tree",
    "compositional_triple",
    "topological_sort",
]

ORIGINAL_BENCHMARKS = [
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

ALL_BENCHMARKS = ORIGINAL_BENCHMARKS + NEW_BENCHMARKS

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

# API configs
LOCAL_CONFIG = {
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "model": "qwen2.5-coder:14b",
}

SONNET_CONFIG = {
    "base_url": "https://api.anthropic.com/v1",
    "api_key": os.environ.get("LLM_API_KEY", ""),
    "model": "claude-sonnet-4-6",
}


def get_dafny_path():
    from dotenv import load_dotenv
    load_dotenv()
    return os.environ.get("DAFNY_PATH", "dafny")


def run_proven(problem: str, config: dict, output_dir: Path, verbose: bool = False) -> dict:
    """Run Proven pipeline."""
    req_file = Path("examples") / f"{problem}.md"
    if not req_file.exists():
        return {"problem": problem, "error": f"Missing {req_file}"}

    env = os.environ.copy()
    env["LLM_BASE_URL"] = config["base_url"]
    env["LLM_API_KEY"] = config["api_key"]
    env["LLM_MODEL"] = config["model"]

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

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1
    elapsed = time.time() - start

    verified, compiled = parse_run_state(output_dir)

    return {
        "problem": problem,
        "verified": verified,
        "compiled": compiled,
        "wall_time_sec": round(elapsed, 1),
        "exit_code": exit_code,
    }


def run_baseline(problem: str, config: dict, output_dir: Path, verbose: bool = False) -> dict:
    """Run baseline Dafny agent (no pipeline)."""
    req_file = Path("examples") / f"{problem}.md"
    if not req_file.exists():
        return {"problem": problem, "error": f"Missing {req_file}"}

    cmd = [
        sys.executable, "research/freestyle_agent.py", str(req_file),
        "--max-attempts", "10",
        "--output-dir", str(output_dir),
        "--model", config["model"],
        "--base-url", config["base_url"],
        "--api-key", config["api_key"],
    ]
    if verbose:
        cmd.append("--verbose")

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1
    elapsed = time.time() - start

    verified, compiled = parse_run_state(output_dir)

    return {
        "problem": problem,
        "verified": verified,
        "compiled": compiled,
        "wall_time_sec": round(elapsed, 1),
        "exit_code": exit_code,
    }


def run_tdd(problem: str, config: dict, output_dir: Path, verbose: bool = False) -> dict:
    """Run TDD agent."""
    req_file = Path("examples") / f"{problem}.md"
    if not req_file.exists():
        return {"problem": problem, "error": f"Missing {req_file}"}

    cmd = [
        sys.executable, "research/tdd_agent.py", str(req_file),
        "--max-attempts", "10",
        "--output-dir", str(output_dir),
        "--model", config["model"],
        "--base-url", config["base_url"],
        "--api-key", config["api_key"],
    ]
    if verbose:
        cmd.append("--verbose")

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1
    elapsed = time.time() - start

    # TDD uses "tests_pass" instead of "verified"
    state_file = output_dir / "run_state.json"
    tests_pass = False
    if state_file.exists():
        state = json.loads(state_file.read_text())
        stage_status = {str(k): v for k, v in state.get("stage_status", {}).items()}
        tests_pass = stage_status.get("4") == "completed"

    return {
        "problem": problem,
        "tests_pass": tests_pass,
        "compiled": tests_pass,  # TDD: passing tests = success
        "wall_time_sec": round(elapsed, 1),
        "exit_code": exit_code,
    }


def parse_run_state(output_dir: Path) -> tuple[bool, bool]:
    """Parse run_state.json from output dir (may be in timestamped subdir)."""
    for state_file in sorted(output_dir.rglob("run_state.json")):
        state = json.loads(state_file.read_text())
        stage_status = {int(k): v for k, v in state.get("stage_status", {}).items()}
        verified = stage_status.get(4) == "completed"
        compiled = stage_status.get(5) == "completed"
        return verified, compiled
    return False, False


CONDITION_DEFS = {
    "P-local": {
        "label": "Proven + Local",
        "runner": run_proven,
        "config": LOCAL_CONFIG,
        "output_prefix": "runs/full_matrix/proven_local",
    },
    "P-sonnet": {
        "label": "Proven + Sonnet",
        "runner": None,  # Already done — reads from existing results
        "config": SONNET_CONFIG,
        "output_prefix": "runs/sonnet_full",
    },
    "B-sonnet": {
        "label": "Baseline + Sonnet",
        "runner": run_baseline,
        "config": SONNET_CONFIG,
        "output_prefix": "runs/full_matrix/baseline_sonnet",
    },
    "T-local": {
        "label": "TDD + Local",
        "runner": run_tdd,
        "config": LOCAL_CONFIG,
        "output_prefix": "runs/full_matrix/tdd_local",
    },
    "T-sonnet": {
        "label": "TDD + Sonnet",
        "runner": run_tdd,
        "config": SONNET_CONFIG,
        "output_prefix": "runs/full_matrix/tdd_sonnet",
    },
}


def load_existing_proven_sonnet(benchmarks: list[str]) -> list[dict]:
    """Load results from the already-completed Proven+Sonnet run."""
    results_file = Path("research/sonnet_full_results.json")
    if not results_file.exists():
        return []
    all_results = json.loads(results_file.read_text())
    return [r for r in all_results if r["problem"] in benchmarks]


def print_matrix(all_results: dict[str, list[dict]], benchmarks: list[str]):
    """Print a full condition x problem matrix."""
    conditions = list(all_results.keys())

    print(f"\n{'='*90}")
    print(f"  Full Condition Matrix — Results")
    print(f"{'='*90}")

    header = f"  {'Problem':<24} {'Diff':<8}"
    for c in conditions:
        label = CONDITION_DEFS.get(c, {}).get("label", c)
        header += f" {label:<16}"
    print(header)
    print(f"  {'-'*86}")

    for problem in benchmarks:
        row = f"  {problem:<24} {DIFFICULTY.get(problem, '?'):<8}"
        for c in conditions:
            results = all_results[c]
            match = [r for r in results if r["problem"] == problem]
            if match:
                r = match[0]
                if r.get("compiled") or r.get("tests_pass"):
                    status = "PASS"
                elif r.get("verified"):
                    status = "VERIFIED"
                elif r.get("error"):
                    status = "ERROR"
                else:
                    status = "FAIL"
                row += f" {status:<16}"
            else:
                row += f" {'—':<16}"
        print(row)

    # Summary row
    print(f"  {'-'*86}")
    row = f"  {'TOTAL':<24} {'':8}"
    for c in conditions:
        results = all_results[c]
        total = len(results)
        passed = sum(1 for r in results if r.get("compiled") or r.get("tests_pass"))
        row += f" {passed}/{total:<14}"
    print(row)
    print(f"{'='*90}")


def main():
    parser = argparse.ArgumentParser(description="Run all conditions on benchmarks")
    parser.add_argument(
        "--conditions", default="P-local,B-sonnet,T-local,T-sonnet",
        help="Conditions to run (P-sonnet is loaded from existing results). Default: P-local,B-sonnet,T-local,T-sonnet",
    )
    parser.add_argument(
        "--benchmarks", default="new",
        help="'new' (6 Hard+/Expert), 'all' (15), or comma-separated names",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    conditions = [c.strip() for c in args.conditions.split(",")]
    if args.benchmarks == "new":
        benchmarks = NEW_BENCHMARKS
    elif args.benchmarks == "all":
        benchmarks = ALL_BENCHMARKS
    else:
        benchmarks = [b.strip() for b in args.benchmarks.split(",")]

    # Always include P-sonnet from existing results
    if "P-sonnet" not in conditions:
        conditions.insert(0, "P-sonnet")

    # Load API key from .env if not in environment
    from dotenv import load_dotenv
    load_dotenv()
    if not SONNET_CONFIG["api_key"]:
        SONNET_CONFIG["api_key"] = os.environ.get("LLM_API_KEY", "")

    print(f"Full Condition Matrix Run")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Benchmarks: {len(benchmarks)} problems")
    print(f"{'='*60}")

    all_results: dict[str, list[dict]] = {}

    for condition in conditions:
        cdef = CONDITION_DEFS.get(condition)
        if not cdef:
            print(f"Unknown condition: {condition}")
            continue

        print(f"\n{'='*60}")
        print(f"  Condition: {cdef['label']}")
        print(f"{'='*60}")

        if condition == "P-sonnet":
            results = load_existing_proven_sonnet(benchmarks)
            if results:
                print(f"  Loaded {len(results)} results from previous run")
            else:
                print(f"  No existing results found — skipping")
            all_results[condition] = results
            continue

        results = []
        for problem in benchmarks:
            output_dir = Path(cdef["output_prefix"]) / problem
            print(f"\n  [{cdef['label']}] {problem} ({DIFFICULTY.get(problem, '?')})")

            result = cdef["runner"](
                problem, cdef["config"], output_dir, verbose=args.verbose
            )
            result["condition"] = condition
            result["difficulty"] = DIFFICULTY.get(problem, "?")
            results.append(result)

            status = "PASS" if result.get("compiled") or result.get("tests_pass") else (
                "VERIFIED" if result.get("verified") else "FAIL"
            )
            print(f"  Result: {status} ({result.get('wall_time_sec', 0):.0f}s)")

        all_results[condition] = results

        # Save intermediate results
        results_file = Path("research/full_matrix_results.json")
        # Flatten for JSON
        flat = []
        for c, rs in all_results.items():
            for r in rs:
                flat.append({**r, "condition": c, "label": CONDITION_DEFS[c]["label"]})
        results_file.write_text(json.dumps(flat, indent=2))

    print_matrix(all_results, benchmarks)

    # Final save
    results_file = Path("research/full_matrix_results.json")
    flat = []
    for c, rs in all_results.items():
        for r in rs:
            flat.append({**r, "condition": c, "label": CONDITION_DEFS[c]["label"]})
    results_file.write_text(json.dumps(flat, indent=2))
    print(f"\n  Results saved to: {results_file}")


if __name__ == "__main__":
    main()
