"""Analyze Proven pipeline runs and extract metrics.

Usage:
    python research/analyze_runs.py [runs_dir]

Reads run_state.json and interaction_log.jsonl from each run directory.
Outputs a summary table to stdout and optionally writes results.csv.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_run(run_dir: Path) -> dict | None:
    """Extract metrics from a single run directory."""
    state_file = run_dir / "run_state.json"
    log_file = run_dir / "interaction_log.jsonl"
    report_file = run_dir / "04_proof_report.json"

    if not state_file.exists():
        return None

    state = json.loads(state_file.read_text())

    # Basic info
    run_id = state.get("run_id", run_dir.name)
    mode = state.get("mode", "unknown")
    config = state.get("config_snapshot", {})
    model = config.get("llm_model", "unknown")
    target = config.get("target", "unknown")
    max_retries = config.get("max_retries", 0)
    req_file = state.get("requirements_file", "unknown")

    # Extract problem name from requirements file path
    problem = Path(req_file).stem if req_file else "unknown"

    # Stage status
    stage_status = {int(k): v for k, v in state.get("stage_status", {}).items()}
    retry_counts = {int(k): v for k, v in state.get("retry_counts", {}).items()}

    # Determine highest stage reached
    highest_stage = 0
    for s in range(1, 6):
        if stage_status.get(s) in ("completed", "failed", "in_progress"):
            highest_stage = s

    # Verification success = stage 3 or 4 completed (implementation verified)
    verified = (
        stage_status.get(3) == "completed" and stage_status.get(4) == "completed"
    ) or (
        stage_status.get(4) == "completed"
    )

    # Full pipeline success = stage 5 completed
    full_success = stage_status.get(5) == "completed"

    # Total retry attempts
    total_attempts = sum(retry_counts.values())

    # Mentor interventions and proof report
    mentor_interventions = 0
    proof_status = "none"
    if report_file.exists():
        report = json.loads(report_file.read_text())
        mentor_interventions = report.get("mentor_interventions", 0)
        proof_status = report.get("status", "none")

    # Decomposition: check if decomposed spec exists
    decomposed_file = run_dir / "02_specification_decomposed.dfy"
    decompose_applied = decomposed_file.exists()

    # Parse interaction log for token usage and timing
    total_tokens = 0
    first_ts = None
    last_ts = None
    llm_calls = 0
    mentor_events = 0
    rollback_events = 0

    if log_file.exists():
        for line in log_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Timestamps
            ts_str = event.get("ts")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if first_ts is None or ts < first_ts:
                        first_ts = ts
                    if last_ts is None or ts > last_ts:
                        last_ts = ts
                except ValueError:
                    pass

            # Token usage
            if event.get("event") == "llm_response":
                llm_calls += 1
                usage = event.get("usage", {})
                total_tokens += usage.get("total_tokens", 0)

            # Mentor events
            if event.get("event") == "mentor_intervention":
                mentor_events += 1

            # Stage completion with rollback
            if event.get("event") == "stage_complete" and event.get("outcome") == "rollback":
                rollback_events += 1

    # Wall-clock time
    wall_time_sec = 0
    if first_ts and last_ts:
        wall_time_sec = (last_ts - first_ts).total_seconds()

    return {
        "run_id": run_id,
        "problem": problem,
        "model": model,
        "mode": mode,
        "max_retries": max_retries,
        "verified": verified,
        "full_success": full_success,
        "highest_stage": highest_stage,
        "proof_status": proof_status,
        "stage_1": stage_status.get(1, "pending"),
        "stage_2": stage_status.get(2, "pending"),
        "stage_3": stage_status.get(3, "pending"),
        "stage_4": stage_status.get(4, "pending"),
        "stage_5": stage_status.get(5, "pending"),
        "retries_s1": retry_counts.get(1, 0),
        "retries_s2": retry_counts.get(2, 0),
        "retries_s3": retry_counts.get(3, 0),
        "retries_s4": retry_counts.get(4, 0),
        "retries_s5": retry_counts.get(5, 0),
        "total_attempts": total_attempts,
        "total_tokens": total_tokens,
        "llm_calls": llm_calls,
        "wall_time_sec": round(wall_time_sec, 1),
        "mentor_interventions": mentor_interventions,
        "mentor_events": mentor_events,
        "decompose_applied": decompose_applied,
        "rollback_events": rollback_events,
    }


def print_summary(runs: list[dict]) -> None:
    """Print a formatted summary table."""
    if not runs:
        print("No runs found.")
        return

    print(f"\n{'=' * 100}")
    print(f"  Proven Run Analysis — {len(runs)} runs")
    print(f"{'=' * 100}")

    # Header
    print(f"\n{'Run ID':<24} {'Problem':<18} {'Model':<22} {'Result':<8} "
          f"{'Stage':<6} {'Attempts':<9} {'Tokens':<8} {'Time':<8} "
          f"{'Mentor':<7} {'Decomp':<7}")
    print("-" * 100)

    for r in sorted(runs, key=lambda x: x["run_id"]):
        result = "PASS" if r["full_success"] else ("VERIFY" if r["verified"] else "FAIL")
        decomp = "yes" if r["decompose_applied"] else "no"
        time_str = f"{r['wall_time_sec']:.0f}s" if r["wall_time_sec"] > 0 else "-"

        print(f"{r['run_id']:<24} {r['problem']:<18} {r['model']:<22} {result:<8} "
              f"{r['highest_stage']:<6} {r['total_attempts']:<9} {r['total_tokens']:<8} "
              f"{time_str:<8} {r['mentor_interventions']:<7} {decomp:<7}")

    # Aggregated stats
    print(f"\n{'=' * 100}")
    print(f"  Summary Statistics")
    print(f"{'=' * 100}")

    total = len(runs)
    verified = sum(1 for r in runs if r["verified"])
    full_success = sum(1 for r in runs if r["full_success"])
    with_decompose = [r for r in runs if r["decompose_applied"]]
    without_decompose = [r for r in runs if not r["decompose_applied"]]

    print(f"\n  Total runs:           {total}")
    print(f"  Verified:             {verified}/{total} ({100*verified/total:.0f}%)")
    print(f"  Full success (-> py): {full_success}/{total} ({100*full_success/total:.0f}%)")
    print(f"  Mean attempts:        {sum(r['total_attempts'] for r in runs)/total:.1f}")
    print(f"  Mean tokens:          {sum(r['total_tokens'] for r in runs)/total:.0f}")
    print(f"  Mean wall time:       {sum(r['wall_time_sec'] for r in runs)/total:.0f}s")

    if with_decompose:
        d_verified = sum(1 for r in with_decompose if r["verified"])
        print(f"\n  With decomposition:   {d_verified}/{len(with_decompose)} verified "
              f"({100*d_verified/len(with_decompose):.0f}%)")

    if without_decompose:
        nd_verified = sum(1 for r in without_decompose if r["verified"])
        print(f"  Without decomposition: {nd_verified}/{len(without_decompose)} verified "
              f"({100*nd_verified/len(without_decompose):.0f}%)")

    # Per-problem breakdown
    problems = sorted(set(r["problem"] for r in runs))
    if len(problems) > 1:
        print(f"\n  Per-Problem Breakdown:")
        print(f"  {'Problem':<20} {'Runs':<6} {'Verified':<10} {'Rate':<8}")
        print(f"  {'-'*44}")
        for p in problems:
            p_runs = [r for r in runs if r["problem"] == p]
            p_verified = sum(1 for r in p_runs if r["verified"])
            rate = 100 * p_verified / len(p_runs) if p_runs else 0
            print(f"  {p:<20} {len(p_runs):<6} {p_verified:<10} {rate:.0f}%")


def write_csv(runs: list[dict], output_path: Path) -> None:
    """Write run metrics to CSV."""
    if not runs:
        return

    fieldnames = list(runs[0].keys())
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(runs, key=lambda x: x["run_id"]))

    print(f"\n  CSV written to: {output_path}")


def main():
    runs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs")

    if not runs_dir.exists():
        print(f"Error: runs directory not found: {runs_dir}")
        sys.exit(1)

    # Find all run directories (contain run_state.json)
    runs = []
    for run_dir in sorted(runs_dir.rglob("run_state.json")):
        result = parse_run(run_dir.parent)
        if result:
            runs.append(result)

    print_summary(runs)

    # Write CSV
    csv_path = Path("research/results.csv")
    if csv_path.parent.exists():
        write_csv(runs, csv_path)


if __name__ == "__main__":
    main()
