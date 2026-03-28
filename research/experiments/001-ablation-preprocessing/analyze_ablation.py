"""Analyze ablation study results: success rates, pairwise comparisons, effects.

Usage:
    # Primary analysis (success rate table + pairwise comparisons)
    python research/analyze_ablation.py

    # Full analysis with all secondary metrics
    python research/analyze_ablation.py --full

    # Write CSV files + LaTeX table
    python research/analyze_ablation.py --full --csv --latex

    # Read from JSON instead of walking run directories
    python research/analyze_ablation.py --results-json research/ablation_results.json
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

CONFIG_ORDER = ["A_baseline", "B_mentor", "C_decompose", "D_full"]
CONFIG_LABELS = {
    "A_baseline": "A: Baseline",
    "B_mentor": "B: +Mentor",
    "C_decompose": "C: +Decompose",
    "D_full": "D: Full",
}


# ─────────────────────────────────────────────────────────────
# Data collection
# ─────────────────────────────────────────────────────────────

def collect_from_dirs(ablation_root: Path) -> list[dict]:
    """Walk the ablation directory tree and parse all run results."""
    from analyze_runs import parse_run

    results = []
    for state_file in sorted(ablation_root.rglob("run_state.json")):
        run_dir = state_file.parent
        try:
            parts = run_dir.relative_to(ablation_root).parts
            # parts = (model, config, problem, trial_n, timestamp)
            if len(parts) < 4:
                continue
            model_slug = parts[0]
            config_name = parts[1]
            problem_name = parts[2]
            trial_str = parts[3]  # "trial_1"
        except (ValueError, IndexError):
            continue

        metrics = parse_run(run_dir)
        if metrics:
            metrics["model_slug"] = model_slug
            metrics["ablation_config"] = config_name
            metrics["config_label"] = CONFIG_LABELS.get(config_name, config_name)
            try:
                metrics["trial"] = int(trial_str.split("_")[1])
            except (IndexError, ValueError):
                metrics["trial"] = 0
            metrics["difficulty"] = DIFFICULTY.get(metrics.get("problem", ""), "?")
            results.append(metrics)

    return results


def collect_from_json(json_path: Path) -> list[dict]:
    """Load results from the JSON saved by run_ablation.py."""
    text = json_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    # Normalize field names
    for r in data:
        if "config" in r and "ablation_config" not in r:
            r["ablation_config"] = r["config"]
        if "config_label" not in r:
            r["config_label"] = CONFIG_LABELS.get(r.get("ablation_config", ""), "?")
        if "model" in r and "model_slug" not in r:
            r["model_slug"] = r["model"]
        if "difficulty" not in r:
            r["difficulty"] = DIFFICULTY.get(r.get("problem", ""), "?")
        # Normalize success metric: prefer "compiled", fall back to "full_success"
        if "compiled" not in r:
            r["compiled"] = r.get("full_success", False)
    return data


# ─────────────────────────────────────────────────────────────
# Statistical functions
# ─────────────────────────────────────────────────────────────

def wilson_score_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score confidence interval for a proportion.

    Returns (point_estimate, lower_bound, upper_bound).
    """
    if total == 0:
        return 0.0, 0.0, 0.0

    p_hat = successes / total
    denom = 1 + z ** 2 / total
    center = (p_hat + z ** 2 / (2 * total)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z ** 2 / (4 * total)) / total) / denom

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return p_hat, lower, upper


def fishers_exact(a: int, b: int, c: int, d: int) -> float:
    """Fisher's exact test p-value (one-sided, tests if row 1 > row 2).

    2x2 table: [[a, b], [c, d]]
    Row 1 = condition expected to be better (e.g., +Decompose)
    Row 2 = condition expected to be worse (e.g., Baseline)
    """
    try:
        from scipy.stats import fisher_exact as _fisher
        _, p = _fisher([[a, b], [c, d]], alternative="greater")
        return p
    except ImportError:
        # Manual hypergeometric calculation
        n = a + b + c + d
        r1 = a + b
        c1 = a + c
        # P(X >= a) under H0
        p_value = 0.0
        for x in range(a, min(r1, c1) + 1):
            y = r1 - x
            w = c1 - x
            v = n - r1 - c1 + x
            if y < 0 or w < 0 or v < 0:
                continue
            log_p = (
                _log_comb(r1, x) + _log_comb(n - r1, c1 - x) - _log_comb(n, c1)
            )
            p_value += math.exp(log_p)
        return min(p_value, 1.0)


def _log_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h for comparing two proportions."""
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


# ─────────────────────────────────────────────────────────────
# Primary analyses
# ─────────────────────────────────────────────────────────────

def success_rate_table(results: list[dict]):
    """Print success rate by (model, config) with Wilson CIs."""
    models = sorted(set(r["model_slug"] for r in results))
    configs = [c for c in CONFIG_ORDER if any(r["ablation_config"] == c for r in results)]

    print(f"\n{'=' * 80}")
    print(f"  Primary Analysis: Verification Success Rate")
    print(f"{'=' * 80}")

    for model in models:
        mr = [r for r in results if r["model_slug"] == model]
        print(f"\n  Model: {model}")
        print(f"  {'Config':<22} {'N':<5} {'Compiled':<10} {'Rate':<8} {'95% CI':<16} {'Verified':<10}")
        print(f"  {'-' * 70}")

        for config in configs:
            cr = [r for r in mr if r["ablation_config"] == config]
            n = len(cr)
            if n == 0:
                continue
            compiled = sum(1 for r in cr if r.get("compiled"))
            verified = sum(1 for r in cr if r.get("verified"))
            rate, lo, hi = wilson_score_ci(compiled, n)
            label = CONFIG_LABELS.get(config, config)
            print(f"  {label:<22} {n:<5} {compiled:<10} {rate:>5.0%}   [{lo:.0%}, {hi:.0%}]{'':<5} {verified}")

    print()


def pairwise_comparisons(results: list[dict]):
    """Run the three key pairwise comparisons."""
    models = sorted(set(r["model_slug"] for r in results))
    configs_present = set(r["ablation_config"] for r in results)

    comparisons = [
        ("A_baseline", "C_decompose", "Decompose effect (A vs C)"),
        ("A_baseline", "B_mentor", "Mentor effect (A vs B)"),
        ("C_decompose", "D_full", "Mentor+Rollback marginal (C vs D)"),
    ]

    print(f"\n{'=' * 80}")
    print(f"  Pairwise Comparisons (Fisher's exact test, one-sided)")
    print(f"{'=' * 80}")

    for model in models:
        mr = [r for r in results if r["model_slug"] == model]
        print(f"\n  Model: {model}")
        print(f"  {'Comparison':<35} {'Better':<10} {'Worse':<10} {'p-value':<10} {'h':<8} {'Sig?'}")
        print(f"  {'-' * 75}")

        for worse_cfg, better_cfg, label in comparisons:
            if worse_cfg not in configs_present or better_cfg not in configs_present:
                continue

            worse = [r for r in mr if r["ablation_config"] == worse_cfg]
            better = [r for r in mr if r["ablation_config"] == better_cfg]

            a = sum(1 for r in better if r.get("compiled"))  # better success
            b = len(better) - a                               # better fail
            c = sum(1 for r in worse if r.get("compiled"))   # worse success
            d = len(worse) - c                                # worse fail

            if len(better) == 0 or len(worse) == 0:
                continue

            p = fishers_exact(a, b, c, d)
            h = cohens_h(a / len(better) if len(better) > 0 else 0,
                         c / len(worse) if len(worse) > 0 else 0)
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""

            better_label = f"{a}/{len(better)}"
            worse_label = f"{c}/{len(worse)}"
            print(f"  {label:<35} {better_label:<10} {worse_label:<10} {p:<10.4f} {h:<8.2f} {sig}")

    print()


# ─────────────────────────────────────────────────────────────
# Secondary analyses
# ─────────────────────────────────────────────────────────────

def difficulty_interaction(results: list[dict]):
    """Success rate by (config, difficulty) for each model."""
    models = sorted(set(r["model_slug"] for r in results))
    configs = [c for c in CONFIG_ORDER if any(r["ablation_config"] == c for r in results)]
    tiers = ["simple", "medium", "hard"]

    print(f"\n{'=' * 80}")
    print(f"  Difficulty Interaction: Success Rate by Tier")
    print(f"{'=' * 80}")

    for model in models:
        mr = [r for r in results if r["model_slug"] == model]
        print(f"\n  Model: {model}")
        header = f"  {'Tier':<10}"
        for config in configs:
            header += f" {CONFIG_LABELS.get(config, config):<16}"
        print(header)
        print(f"  {'-' * 70}")

        for tier in tiers:
            row = f"  {tier:<10}"
            for config in configs:
                cr = [r for r in mr
                      if r["ablation_config"] == config and r.get("difficulty") == tier]
                if not cr:
                    row += f" {'—':<16}"
                else:
                    passed = sum(1 for r in cr if r.get("compiled"))
                    n = len(cr)
                    row += f" {passed}/{n} ({100 * passed / n:.0f}%)     "
            print(row)

    print()


def token_efficiency(results: list[dict]):
    """Compare token consumption across configs."""
    models = sorted(set(r["model_slug"] for r in results))
    configs = [c for c in CONFIG_ORDER if any(r["ablation_config"] == c for r in results)]

    print(f"\n{'=' * 80}")
    print(f"  Token Efficiency")
    print(f"{'=' * 80}")

    for model in models:
        mr = [r for r in results if r["model_slug"] == model]
        print(f"\n  Model: {model}")
        print(f"  {'Config':<22} {'Successes':<12} {'Mean tokens':<14} {'Mean time':<12}")
        print(f"  {'-' * 58}")

        for config in configs:
            cr = [r for r in mr if r["ablation_config"] == config]
            if not cr:
                continue

            succeeded = [r for r in cr if r.get("compiled")]
            label = CONFIG_LABELS.get(config, config)

            if succeeded:
                # Use total_tokens if available (from dir analysis), else wall_time
                tokens = [r.get("total_tokens", 0) for r in succeeded]
                times = [r.get("wall_time_sec", 0) for r in succeeded]
                mean_tok = sum(tokens) / len(tokens) if any(tokens) else 0
                mean_time = sum(times) / len(times)
                print(f"  {label:<22} {len(succeeded):<12} {mean_tok:<14.0f} {mean_time:<12.0f}s")
            else:
                print(f"  {label:<22} {'0':<12} {'—':<14} {'—'}")

    print()


def mentor_analysis(results: list[dict]):
    """Analyze mentor intervention patterns."""
    models = sorted(set(r["model_slug"] for r in results))

    print(f"\n{'=' * 80}")
    print(f"  Mentor Behavior (Configs B and D only)")
    print(f"{'=' * 80}")

    for model in models:
        mr = [r for r in results if r["model_slug"] == model]
        print(f"\n  Model: {model}")

        for config in ["B_mentor", "D_full"]:
            cr = [r for r in mr if r["ablation_config"] == config]
            if not cr:
                continue

            label = CONFIG_LABELS.get(config, config)
            total = len(cr)
            with_mentor = [r for r in cr if r.get("mentor_interventions", 0) > 0]
            mentor_then_pass = [r for r in with_mentor if r.get("compiled")]

            print(f"\n  {label}:")
            print(f"    Total runs: {total}")
            print(f"    Runs with mentor interventions: {len(with_mentor)}")
            if with_mentor:
                mean_interventions = sum(r.get("mentor_interventions", 0) for r in with_mentor) / len(with_mentor)
                print(f"    Mean interventions per mentored run: {mean_interventions:.1f}")
                print(f"    Success after mentor: {len(mentor_then_pass)}/{len(with_mentor)}")

            rollbacks = [r for r in cr if r.get("rollback_events", 0) > 0]
            if rollbacks:
                rb_pass = [r for r in rollbacks if r.get("compiled")]
                print(f"    Runs with rollback: {len(rollbacks)}")
                print(f"    Success after rollback: {len(rb_pass)}/{len(rollbacks)}")

    print()


def per_problem_matrix(results: list[dict]):
    """Full problem × config matrix for each model."""
    models = sorted(set(r["model_slug"] for r in results))
    configs = [c for c in CONFIG_ORDER if any(r["ablation_config"] == c for r in results)]
    problems = sorted(set(r.get("problem", "") for r in results),
                       key=lambda p: ["simple", "medium", "hard"].index(DIFFICULTY.get(p, "hard")))

    print(f"\n{'=' * 90}")
    print(f"  Full Problem × Config Matrix")
    print(f"{'=' * 90}")

    for model in models:
        mr = [r for r in results if r["model_slug"] == model]
        print(f"\n  Model: {model}")
        header = f"  {'Problem':<24} {'Diff':<8}"
        for config in configs:
            header += f" {CONFIG_LABELS.get(config, config):<14}"
        print(header)
        print(f"  {'-' * 80}")

        for problem in problems:
            row = f"  {problem:<24} {DIFFICULTY.get(problem, '?'):<8}"
            for config in configs:
                cell = [r for r in mr
                        if r["ablation_config"] == config and r.get("problem") == problem]
                if cell:
                    passed = sum(1 for r in cell if r.get("compiled"))
                    total = len(cell)
                    row += f" {passed}/{total:<12}"
                else:
                    row += f" {'—':<14}"
            print(row)

    print()


# ─────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────

def write_csv_files(results: list[dict], output_dir: Path):
    """Write per-run and summary CSVs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Per-run CSV
    run_csv = output_dir / "ablation_results.csv"
    fieldnames = [
        "model_slug", "ablation_config", "config_label", "problem", "trial",
        "difficulty", "verified", "compiled", "total_tokens", "wall_time_sec",
        "total_attempts", "mentor_interventions", "rollback_events", "decompose_applied",
    ]
    with open(run_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in sorted(results, key=lambda x: (
            x.get("model_slug", ""), x.get("ablation_config", ""),
            x.get("problem", ""), x.get("trial", 0),
        )):
            writer.writerow(r)
    print(f"  Per-run CSV: {run_csv}")

    # Summary CSV
    summary_csv = output_dir / "ablation_summary.csv"
    models = sorted(set(r["model_slug"] for r in results))
    configs = [c for c in CONFIG_ORDER if any(r["ablation_config"] == c for r in results)]
    problems = sorted(set(r.get("problem", "") for r in results))

    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "config", "problem", "difficulty", "n", "compiled", "verified", "rate"])
        for model in models:
            for config in configs:
                for problem in problems:
                    cell = [r for r in results
                            if r["model_slug"] == model
                            and r["ablation_config"] == config
                            and r.get("problem") == problem]
                    if not cell:
                        continue
                    n = len(cell)
                    compiled = sum(1 for r in cell if r.get("compiled"))
                    verified = sum(1 for r in cell if r.get("verified"))
                    rate = compiled / n if n > 0 else 0
                    writer.writerow([model, config, problem,
                                     DIFFICULTY.get(problem, "?"),
                                     n, compiled, verified, f"{rate:.2f}"])
    print(f"  Summary CSV: {summary_csv}")


def print_latex_table(results: list[dict]):
    """Print LaTeX-formatted table for the paper."""
    models = sorted(set(r["model_slug"] for r in results))
    configs = [c for c in CONFIG_ORDER if any(r["ablation_config"] == c for r in results)]

    print(f"\n{'=' * 80}")
    print(f"  LaTeX Table")
    print(f"{'=' * 80}")

    n_models = len(models)
    col_spec = "l" + "rrr" * n_models
    print(f"\\begin{{tabular}}{{{col_spec}}}")
    print("\\toprule")

    # Header
    header = "Config"
    for model in models:
        short = model.replace("qwen2.5-coder-14b", "qwen 14B").replace("claude-sonnet", "Sonnet")
        header += f" & \\multicolumn{{3}}{{c}}{{{short}}}"
    header += " \\\\"
    print(header)

    subheader = ""
    for _ in models:
        subheader += " & Rate & 95\\% CI & N"
    subheader += " \\\\"
    print(subheader)
    print("\\midrule")

    for config in configs:
        label = CONFIG_LABELS.get(config, config)
        row = label
        for model in models:
            cr = [r for r in results
                  if r["model_slug"] == model and r["ablation_config"] == config]
            n = len(cr)
            if n == 0:
                row += " & -- & -- & 0"
            else:
                compiled = sum(1 for r in cr if r.get("compiled"))
                rate, lo, hi = wilson_score_ci(compiled, n)
                row += f" & {rate:.0%} & [{lo:.0%}, {hi:.0%}] & {n}"
        row += " \\\\"
        print(row)

    print("\\bottomrule")
    print("\\end{tabular}")
    print()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze ablation study results")
    parser.add_argument(
        "--runs-dir", type=Path, default=Path("runs/ablation"),
        help="Root directory for ablation runs (default: runs/ablation)",
    )
    parser.add_argument(
        "--results-json", type=Path, default=None,
        help="Read from JSON instead of walking run directories",
    )
    parser.add_argument("--csv", action="store_true", help="Write CSV files")
    parser.add_argument("--latex", action="store_true", help="Print LaTeX table")
    parser.add_argument("--full", action="store_true", help="Run all secondary analyses")
    args = parser.parse_args()

    # Collect data
    if args.results_json and args.results_json.exists():
        results = collect_from_json(args.results_json)
        print(f"Loaded {len(results)} results from {args.results_json}")
    elif args.runs_dir.exists():
        results = collect_from_dirs(args.runs_dir)
        print(f"Collected {len(results)} results from {args.runs_dir}")
    else:
        print(f"Error: no results found at {args.runs_dir} or {args.results_json}")
        return 1

    if not results:
        print("No results to analyze.")
        return 1

    # Primary analyses (always run)
    success_rate_table(results)
    pairwise_comparisons(results)
    per_problem_matrix(results)

    # Secondary analyses (--full flag)
    if args.full:
        difficulty_interaction(results)
        token_efficiency(results)
        mentor_analysis(results)

    # Output files
    if args.csv:
        write_csv_files(results, Path("research"))

    if args.latex:
        print_latex_table(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
