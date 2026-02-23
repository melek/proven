"""Evaluate formal and TDD implementations against independent oracle tests.

Runs each oracle test suite against both formal (Dafny-compiled) and TDD outputs,
producing a comparison table showing pass rates and defect gaps.

Usage:
    python research/evaluate_oracle.py \
        --formal-dir runs/h2h/sonnet_freestyle \
        --tdd-dir runs/tdd/local \
        --oracle-dir research/oracle_tests

    # Single problem:
    python research/evaluate_oracle.py \
        --formal-dir runs/h2h/sonnet_freestyle \
        --tdd-dir runs/tdd/local \
        --problem ring_buffer
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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


def run_oracle_single(
    oracle_dir: Path,
    problem: str,
    condition: str,
    impl_dir: Path,
) -> dict:
    """Run oracle tests for one problem/condition combination.

    Returns:
        {
            "problem": str,
            "condition": str,  # "formal" or "tdd"
            "passed": int,
            "failed": int,
            "errors": int,
            "total": int,
            "status": "PASS" | "FAIL" | "SKIP" | "ERROR",
            "details": str,
        }
    """
    test_file = oracle_dir / f"test_oracle_{problem}.py"
    if not test_file.exists():
        return {
            "problem": problem,
            "condition": condition,
            "passed": 0, "failed": 0, "errors": 0, "total": 0,
            "status": "SKIP",
            "details": f"No oracle test file: {test_file.name}",
        }

    # Build pytest command: run only the fixture param matching this condition
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v", "--tb=short", "--no-header",
        f"-k", condition,
        f"--formal-dir={impl_dir}" if condition == "formal" else f"--formal-dir=.",
        f"--tdd-dir={impl_dir}" if condition == "tdd" else f"--tdd-dir=.",
    ]

    # Set up both dirs so conftest doesn't complain
    if condition == "formal":
        cmd.extend([f"--tdd-dir=."])
    else:
        cmd.extend([f"--formal-dir=."])

    # Remove duplicate flags
    seen = set()
    deduped = []
    for arg in cmd:
        key = arg.split("=")[0] if "=" in arg else arg
        if key.startswith("--formal-dir") or key.startswith("--tdd-dir"):
            if key.split("=")[0] not in seen:
                seen.add(key.split("=")[0])
                deduped.append(arg)
        else:
            deduped.append(arg)
    cmd = deduped

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(oracle_dir),
        )
    except subprocess.TimeoutExpired:
        return {
            "problem": problem,
            "condition": condition,
            "passed": 0, "failed": 0, "errors": 0, "total": 0,
            "status": "ERROR",
            "details": "TIMEOUT",
        }
    except Exception as e:
        return {
            "problem": problem,
            "condition": condition,
            "passed": 0, "failed": 0, "errors": 0, "total": 0,
            "status": "ERROR",
            "details": str(e),
        }

    output = result.stdout + "\n" + result.stderr

    # Parse pytest summary line: "X passed, Y failed, Z errors"
    passed = 0
    failed = 0
    errors = 0

    # Check for "no tests ran" (skipped)
    if "no tests ran" in output or "deselected" in output and "passed" not in output:
        # Check if ALL tests were deselected/skipped
        m = re.search(r"(\d+) deselected", output)
        if m and "passed" not in output and "failed" not in output:
            return {
                "problem": problem,
                "condition": condition,
                "passed": 0, "failed": 0, "errors": 0, "total": 0,
                "status": "SKIP",
                "details": "All tests skipped (no impl found)",
            }

    m_passed = re.search(r"(\d+) passed", output)
    m_failed = re.search(r"(\d+) failed", output)
    m_errors = re.search(r"(\d+) error", output)

    if m_passed:
        passed = int(m_passed.group(1))
    if m_failed:
        failed = int(m_failed.group(1))
    if m_errors:
        errors = int(m_errors.group(1))

    total = passed + failed + errors

    if total == 0:
        status = "SKIP"
    elif failed == 0 and errors == 0:
        status = "PASS"
    else:
        status = "FAIL"

    return {
        "problem": problem,
        "condition": condition,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": total,
        "status": status,
        "details": "",
    }


def check_self_criterion(run_dir: Path, problem: str, mode: str) -> str:
    """Check if the self-criterion passed (dafny verify / pytest)."""
    state_file = run_dir / problem / "run_state.json"

    # Also check versioned directories
    if not state_file.exists():
        candidates = list(run_dir.glob(f"{problem}_v*/run_state.json"))
        # Also check nested timestamp dirs
        candidates += list(run_dir.glob(f"{problem}/*/run_state.json"))
        candidates += list(run_dir.glob(f"{problem}_v*/*/run_state.json"))
        if candidates:
            state_file = max(candidates, key=lambda p: p.stat().st_mtime)

    if not state_file.exists():
        return "N/A"

    try:
        state = json.loads(state_file.read_text())
        stage_status = state.get("stage_status", {})
        # Stage 4 = verification/test pass
        if stage_status.get("4") == "completed" or stage_status.get(4) == "completed":
            return "PASS"
        return "FAIL"
    except Exception:
        return "N/A"


def print_results(results: list[dict], formal_dir: Path | None, tdd_dir: Path | None):
    """Print comparison table."""
    print(f"\n{'=' * 95}")
    print(f"  Oracle Test Evaluation")
    print(f"{'=' * 95}")

    # Header
    print(f"\n  {'Benchmark':<24}", end="")
    if formal_dir:
        print(f"{'F-self':<8} {'F-oracle':<12}", end="")
    if tdd_dir:
        print(f"{'T-self':<8} {'T-oracle':<12}", end="")
    if formal_dir and tdd_dir:
        print(f"{'Defect gap':<12}", end="")
    print()
    print(f"  {'-' * 90}")

    for problem in BENCHMARKS:
        row = f"  {problem:<24}"

        formal_result = None
        tdd_result = None

        for r in results:
            if r["problem"] == problem and r["condition"] == "formal":
                formal_result = r
            if r["problem"] == problem and r["condition"] == "tdd":
                tdd_result = r

        if formal_dir:
            if formal_result:
                self_crit = check_self_criterion(formal_dir, problem, "formal")
                oracle_str = (
                    f"{formal_result['passed']}/{formal_result['total']}"
                    if formal_result["total"] > 0
                    else formal_result["status"]
                )
                row += f"{self_crit:<8} {oracle_str:<12}"
            else:
                row += f"{'—':<8} {'—':<12}"

        if tdd_dir:
            if tdd_result:
                self_crit = check_self_criterion(tdd_dir, problem, "tdd")
                oracle_str = (
                    f"{tdd_result['passed']}/{tdd_result['total']}"
                    if tdd_result["total"] > 0
                    else tdd_result["status"]
                )
                row += f"{self_crit:<8} {oracle_str:<12}"
            else:
                row += f"{'—':<8} {'—':<12}"

        if formal_dir and tdd_dir and formal_result and tdd_result:
            if formal_result["total"] > 0 and tdd_result["total"] > 0:
                gap = formal_result["passed"] - tdd_result["passed"]
                gap_str = f"+{gap}" if gap > 0 else str(gap)
                row += f"{gap_str:<12}"
            else:
                row += f"{'—':<12}"

        print(row)

    # Summary
    print(f"\n  {'-' * 90}")
    for condition_name, impl_dir in [("Formal", formal_dir), ("TDD", tdd_dir)]:
        if impl_dir is None:
            continue
        cond = "formal" if condition_name == "Formal" else "tdd"
        cond_results = [r for r in results if r["condition"] == cond]
        if not cond_results:
            continue
        total_passed = sum(r["passed"] for r in cond_results)
        total_tests = sum(r["total"] for r in cond_results)
        full_pass = sum(1 for r in cond_results if r["status"] == "PASS")
        total_problems = sum(1 for r in cond_results if r["total"] > 0)
        print(f"  {condition_name}: {total_passed}/{total_tests} tests passed "
              f"({full_pass}/{total_problems} benchmarks fully correct)")

    print(f"{'=' * 95}")


def main():
    parser = argparse.ArgumentParser(description="Oracle evaluation: formal vs TDD")
    parser.add_argument("--formal-dir", type=Path, default=None,
                        help="Root directory with formal (Dafny-compiled) outputs")
    parser.add_argument("--tdd-dir", type=Path, default=None,
                        help="Root directory with TDD outputs")
    parser.add_argument("--oracle-dir", type=Path, default=Path("research/oracle_tests"),
                        help="Directory containing oracle test files")
    parser.add_argument("--problem", default=None,
                        help="Evaluate a single problem only")
    parser.add_argument("--output", type=Path, default=None,
                        help="Write results to JSON file")

    args = parser.parse_args()

    if not args.formal_dir and not args.tdd_dir:
        print("Error: specify at least one of --formal-dir or --tdd-dir")
        return 1

    benchmarks = [args.problem] if args.problem else BENCHMARKS

    all_results: list[dict] = []

    for problem in benchmarks:
        if args.formal_dir:
            print(f"  Evaluating formal/{problem}...", end=" ", flush=True)
            r = run_oracle_single(args.oracle_dir, problem, "formal", args.formal_dir)
            all_results.append(r)
            print(r["status"])

        if args.tdd_dir:
            print(f"  Evaluating tdd/{problem}...", end=" ", flush=True)
            r = run_oracle_single(args.oracle_dir, problem, "tdd", args.tdd_dir)
            all_results.append(r)
            print(r["status"])

    print_results(all_results, args.formal_dir, args.tdd_dir)

    if args.output:
        args.output.write_text(json.dumps(all_results, indent=2))
        print(f"\n  Results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
