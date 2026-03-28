"""Freestyle Dafny verification agent — generate-and-verify loop.

No pipeline stages, no decomposition, no mentor, no preprocessing.
Just: read requirements -> generate Dafny -> verify -> fix errors -> repeat.

This is the "Claude Code freestyle" baseline for head-to-head comparison
with the Proven pipeline.

Usage:
    python research/freestyle_agent.py examples/bounded_counter.md \
        --model qwen2.5-coder:14b \
        --base-url http://localhost:11434/v1 \
        --max-attempts 10 \
        --output-dir runs/h2h/freestyle_local/bounded_counter
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path so we can import proven modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from proven.dafny import verify, build, resolve
from proven.llm import LLMClient
from proven.prompts import strip_code_fences


# Deliberately minimal — no Dafny syntax guide, no decomposition hints
FREESTYLE_SYSTEM = """\
You are an expert Dafny programmer. Given natural language requirements, \
write a complete Dafny program with:
- Class or datatype definitions
- Method signatures with requires (preconditions) and ensures (postconditions)
- Complete method bodies with loop invariants and decreases clauses
- All code necessary to pass `dafny verify`

Output ONLY the Dafny code. No markdown fences, no explanation."""


FREESTYLE_RETRY = """\
The previous Dafny code failed verification.

Previous code:
{previous_code}

Dafny errors:
{errors}

Fix all errors and output the COMPLETE corrected Dafny file.
Do NOT remove or weaken any specifications — preserve all requires/ensures clauses.
Output ONLY the Dafny code. No markdown fences, no explanation."""


def run_freestyle(
    requirements_file: Path,
    output_dir: Path,
    llm: LLMClient,
    max_attempts: int = 10,
    dafny_path: str = "dafny",
    target: str = "py",
    verbose: bool = False,
) -> dict:
    """Run the freestyle generate-and-verify loop.

    Returns a results dict compatible with analyze_runs.py.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    attempts_dir = output_dir / "attempts"
    attempts_dir.mkdir(exist_ok=True)

    requirements_text = requirements_file.read_text(encoding="utf-8")
    problem = requirements_file.stem

    # Interaction log (same format as Proven pipeline)
    log_file = output_dir / "interaction_log.jsonl"
    log_entries: list[dict] = []

    def log_event(event: dict):
        event["ts"] = datetime.now(timezone.utc).isoformat()
        log_entries.append(event)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    start_time = time.time()
    total_tokens = 0
    llm_calls = 0
    verified = False
    full_success = False
    highest_stage = 0  # 0 = nothing, 3 = has implementation, 5 = compiled

    # Build conversation
    initial_prompt = (
        f"Write a complete Dafny program implementing the following requirements. "
        f"Include all type definitions, method signatures with requires/ensures, "
        f"and complete method bodies with loop invariants and decreases clauses.\n\n"
        f"Requirements:\n{requirements_text}"
    )

    conversation: list[dict] = [
        {"role": "user", "content": initial_prompt},
    ]

    current_code = ""
    impl_file = output_dir / "implementation.dfy"

    for attempt in range(max_attempts):
        # LLM call
        temperature = 0.2 if attempt == 0 else min(0.2 + attempt * 0.1, 0.7)

        log_event({
            "event": "llm_request",
            "stage": 4 if attempt > 0 else 3,
            "attempt": attempt,
            "messages_count": len(conversation),
        })

        if verbose:
            print(f"  Attempt {attempt + 1}/{max_attempts} (temp={temperature:.1f})...")

        try:
            resp = llm.complete_with_history(
                FREESTYLE_SYSTEM, conversation, temperature=temperature,
            )
        except Exception as e:
            print(f"  LLM call failed: {e}")
            log_event({"event": "llm_error", "error": str(e)})
            break

        llm_calls += 1
        total_tokens += resp.usage.get("total_tokens", 0)

        log_event({
            "event": "llm_response",
            "stage": 4 if attempt > 0 else 3,
            "attempt": attempt,
            "content_length": len(resp.content),
            "usage": resp.usage,
        })

        current_code = strip_code_fences(resp.content)
        conversation.append({"role": "assistant", "content": current_code})

        # Save attempt
        attempt_file = attempts_dir / f"attempt_{attempt + 1:02d}.dfy"
        attempt_file.write_text(current_code, encoding="utf-8")
        impl_file.write_text(current_code, encoding="utf-8")
        highest_stage = max(highest_stage, 3)

        # Verify
        result = verify(impl_file, dafny_path=dafny_path)

        log_event({
            "event": "tool_call",
            "stage": 4 if attempt > 0 else 3,
            "command": result.command,
            "exit_code": result.exit_code,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:2000],
        })

        if result.success:
            verified = True
            highest_stage = 4
            if verbose:
                print(f"  VERIFIED on attempt {attempt + 1}!")

            # Try to compile
            compiled_dir = output_dir / "compiled"
            compiled_dir.mkdir(exist_ok=True)
            build_result = build(
                impl_file, target=target, output_dir=compiled_dir,
                dafny_path=dafny_path,
            )
            if build_result.success:
                full_success = True
                highest_stage = 5
                if verbose:
                    print(f"  Compiled to {target}!")

            break

        # Failed — prepare retry
        errors = result.error_message
        (attempts_dir / f"attempt_{attempt + 1:02d}_errors.txt").write_text(
            errors, encoding="utf-8"
        )

        if verbose:
            # Extract verified count from error output
            match = re.search(r"(\d+)\s+verified,\s+(\d+)\s+error", errors)
            if match:
                print(f"  {match.group(1)} verified, {match.group(2)} errors")
            else:
                first_error = ""
                for line in errors.splitlines():
                    if "Error:" in line:
                        first_error = line.strip()[:100]
                        break
                print(f"  Failed: {first_error or errors[:100]}")

        if attempt < max_attempts - 1:
            retry_prompt = FREESTYLE_RETRY.format(
                previous_code=current_code,
                errors=errors[:3000],
            )
            conversation.append({"role": "user", "content": retry_prompt})

    elapsed = time.time() - start_time

    # Write run_state.json (compatible with analyze_runs.py)
    run_state = {
        "run_id": output_dir.name,
        "workspace_path": str(output_dir),
        "current_stage": highest_stage,
        "mode": "freestyle",
        "stage_status": {
            "1": "skipped",  # No requirements capture stage
            "2": "skipped",  # No specification stage
            "3": "completed" if highest_stage >= 3 else "pending",
            "4": "completed" if verified else ("failed" if highest_stage >= 3 else "pending"),
            "5": "completed" if full_success else ("failed" if verified else "pending"),
        },
        "retry_counts": {
            "1": 0,
            "2": 0,
            "3": 1,
            "4": max(0, llm_calls - 1),
            "5": 1 if verified else 0,
        },
        "requirements_file": str(requirements_file),
        "config_snapshot": {
            "llm_model": llm.model,
            "target": target,
            "max_retries": max_attempts,
            "condition": "freestyle",
        },
    }
    (output_dir / "run_state.json").write_text(
        json.dumps(run_state, indent=2), encoding="utf-8"
    )

    # Write proof report (compatible with analyze_runs.py)
    proof_report = {
        "status": "verified" if verified else "failed",
        "attempts": llm_calls,
        "last_errors": "" if verified else (result.error_message[:2000] if not verified else ""),
        "warnings": [],
        "mentor_interventions": 0,
    }
    (output_dir / "04_proof_report.json").write_text(
        json.dumps(proof_report, indent=2), encoding="utf-8"
    )

    # Summary
    status = "PASS" if full_success else ("VERIFY" if verified else "FAIL")
    print(f"\n  [{problem}] {status} — {llm_calls} attempts, "
          f"{total_tokens} tokens, {elapsed:.0f}s")

    return {
        "problem": problem,
        "verified": verified,
        "full_success": full_success,
        "attempts": llm_calls,
        "total_tokens": total_tokens,
        "wall_time_sec": round(elapsed, 1),
        "highest_stage": highest_stage,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Freestyle Dafny verification agent (no pipeline)",
    )
    parser.add_argument("requirements_file", type=Path, help="Path to requirements .md")
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--base-url", default=None, help="LLM API base URL")
    parser.add_argument("--api-key", default=None, help="LLM API key")
    parser.add_argument("--max-attempts", type=int, default=10, help="Max iterations")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory")
    parser.add_argument("--target", default="py", help="Dafny build target")
    parser.add_argument("--dafny-path", default=None, help="Path to dafny binary")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    # Load .env for defaults
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    model = args.model or os.environ.get("LLM_MODEL", "qwen2.5-coder:14b")
    base_url = args.base_url or os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key = args.api_key or os.environ.get("LLM_API_KEY", "ollama")
    dafny_path = args.dafny_path or os.environ.get("DAFNY_PATH", "dafny")

    output_dir = args.output_dir or Path(
        f"runs/h2h/freestyle_{model.replace(':', '-').replace('/', '-')}"
        f"/{args.requirements_file.stem}"
    )

    if not args.requirements_file.exists():
        print(f"Error: {args.requirements_file} not found")
        return 1

    print(f"Freestyle Agent — {model}")
    print(f"Problem: {args.requirements_file.stem}")
    print(f"Max attempts: {args.max_attempts}")
    print(f"Output: {output_dir}")

    llm = LLMClient(base_url, api_key, model)
    result = run_freestyle(
        args.requirements_file,
        output_dir,
        llm,
        max_attempts=args.max_attempts,
        dafny_path=dafny_path,
        target=args.target,
        verbose=args.verbose,
    )

    return 0 if result["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
