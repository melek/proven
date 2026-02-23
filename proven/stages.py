"""The five pipeline stages. Each is a function with a common signature."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from . import dafny as dafny_tool
from .config import Config
from .llm import LLMClient
from .workspace import RunState, InteractionLog
from .prompts import (
    STAGE1_SYSTEM, STAGE1_USER,
    STAGE2_SYSTEM, STAGE2_USER, STAGE2_RETRY_USER, STAGE2_ROLLBACK_USER,
    STAGE3_SYSTEM, STAGE3_USER,
    STAGE4_RETRY_USER, STAGE4_RETRY_USER_WITH_MENTOR,
    strip_code_fences, extract_json, check_spec_integrity,
    get_retry_temperature, get_adaptive_temperature, BEST_OF_N_TEMP,
)
from .decompose import decompose_spec, fix_dafny_syntax
from .mentor import MentorState, record_attempt, detect_stuck, get_mentor_directive, _parse_verified_count


class StageOutcome(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    outcome: StageOutcome
    output_file: Path | None
    message: str
    attempts: int
    rollback_target: int | None = None
    rollback_guidance: str | None = None


def _llm_call(
    llm: LLMClient,
    log: InteractionLog,
    stage: int,
    attempt: int,
    system: str,
    user: str,
    temperature: float = 0.2,
    verbose: bool = False,
) -> str:
    """Make an LLM call and log it."""
    messages = [{"role": "user", "content": user}]
    log.log_llm_request(stage, attempt, messages)
    if verbose:
        print(f"\n  [LLM] Calling model (temp={temperature})...")
    resp = llm.complete(system, user, temperature=temperature)
    log.log_llm_response(stage, attempt, resp.content, resp.usage)
    if verbose:
        print(f"  [LLM] Got {len(resp.content)} chars, {resp.usage.get('total_tokens', '?')} tokens")
    return resp.content


def _llm_call_with_history(
    llm: LLMClient,
    log: InteractionLog,
    stage: int,
    attempt: int,
    system: str,
    messages: list[dict],
    temperature: float = 0.2,
    verbose: bool = False,
) -> str:
    """Make an LLM call with conversation history and log it."""
    log.log_llm_request(stage, attempt, messages)
    if verbose:
        print(f"\n  [LLM] Calling model with history ({len(messages)} msgs, temp={temperature})...")
    resp = llm.complete_with_history(system, messages, temperature=temperature)
    log.log_llm_response(stage, attempt, resp.content, resp.usage)
    if verbose:
        print(f"  [LLM] Got {len(resp.content)} chars, {resp.usage.get('total_tokens', '?')} tokens")
    return resp.content


# ─────────────────────────────────────────────────────────────
# Stage 1: Requirements Capture
# ─────────────────────────────────────────────────────────────

def stage_1_requirements(
    state: RunState, config: Config, llm: LLMClient, log: InteractionLog
) -> StageResult:
    """Natural language requirements -> structured JSON."""
    req_path = Path(state.requirements_file)
    requirements_text = req_path.read_text(encoding="utf-8")

    prompt = STAGE1_USER.format(requirements_text=requirements_text)

    for attempt in range(config.max_retries + 1):
        raw = _llm_call(
            llm, log, stage=1, attempt=attempt,
            system=STAGE1_SYSTEM, user=prompt,
            temperature=get_retry_temperature(attempt),
            verbose=config.verbose,
        )

        try:
            parsed = extract_json(raw)
        except ValueError:
            print(f"  Attempt {attempt + 1}: invalid JSON, retrying...")
            continue

        output_file = state.workspace_path / "01_requirements.json"
        output_file.write_text(json.dumps(parsed, indent=2), encoding="utf-8")

        log.log_stage_complete(1, "success", str(output_file))
        return StageResult(
            outcome=StageOutcome.SUCCESS,
            output_file=output_file,
            message=f"Structured {len(parsed.get('operations', []))} operations, "
                    f"{len(parsed.get('data_structures', []))} data structures",
            attempts=attempt + 1,
        )

    return StageResult(
        outcome=StageOutcome.FAILED,
        output_file=None,
        message="Failed to produce valid JSON after all retries",
        attempts=config.max_retries + 1,
    )


# ─────────────────────────────────────────────────────────────
# Stage 2: Formal Specification
# ─────────────────────────────────────────────────────────────

def stage_2_specification(
    state: RunState, config: Config, llm: LLMClient, log: InteractionLog
) -> StageResult:
    """Structured requirements -> Dafny specification (no bodies)."""
    req_json = (state.workspace_path / "01_requirements.json").read_text(encoding="utf-8")

    # Check for rollback guidance from mentor
    rollback_guidance = getattr(state, 'rollback_guidance', None)
    if rollback_guidance:
        existing_spec_file = state.workspace_path / "02_specification.dfy"
        previous_spec = existing_spec_file.read_text(encoding="utf-8") if existing_spec_file.exists() else ""
        prompt = STAGE2_ROLLBACK_USER.format(
            requirements_json=req_json,
            previous_spec=previous_spec,
            mentor_guidance=rollback_guidance,
        )
        state.rollback_guidance = None  # Consume
        print(f"  [Rollback] Using mentor guidance for specification rewrite")
    else:
        prompt = STAGE2_USER.format(requirements_json=req_json)

    last_attempt_code = None
    last_errors = None

    for attempt in range(config.max_retries + 1):
        if attempt == 0:
            raw = _llm_call(
                llm, log, stage=2, attempt=attempt,
                system=STAGE2_SYSTEM, user=prompt,
                temperature=get_retry_temperature(attempt),
                verbose=config.verbose,
            )
        else:
            retry_prompt = STAGE2_RETRY_USER.format(
                previous_attempt=last_attempt_code,
                errors=last_errors,
            )
            raw = _llm_call(
                llm, log, stage=2, attempt=attempt,
                system=STAGE2_SYSTEM, user=retry_prompt,
                temperature=get_retry_temperature(attempt),
                verbose=config.verbose,
            )

        dafny_code = strip_code_fences(raw)

        # Fix common LLM syntax errors before resolve
        fixed_code, syntax_fixes = fix_dafny_syntax(dafny_code)
        if syntax_fixes:
            dafny_code = fixed_code
            for fix in syntax_fixes:
                print(f"  [Syntax Fix] {fix}")

        output_file = state.workspace_path / "02_specification.dfy"
        output_file.write_text(dafny_code, encoding="utf-8")

        # Check with dafny resolve
        result = dafny_tool.resolve(output_file, dafny_path=config.dafny_path)
        log.log_tool(2, result.command, result.exit_code, result.stdout, result.stderr)

        if result.success:
            log.log_stage_complete(2, "success", str(output_file))
            return StageResult(
                outcome=StageOutcome.SUCCESS,
                output_file=output_file,
                message=f"Specification passes dafny resolve ({attempt + 1} attempt(s))",
                attempts=attempt + 1,
            )

        print(f"  Attempt {attempt + 1}: dafny resolve failed, retrying...")
        if config.verbose:
            print(f"  Errors: {result.error_message[:500]}")
        last_attempt_code = dafny_code
        last_errors = result.error_message

    return StageResult(
        outcome=StageOutcome.FAILED,
        output_file=state.workspace_path / "02_specification.dfy",
        message=f"Specification failed dafny resolve after {config.max_retries + 1} attempts",
        attempts=config.max_retries + 1,
    )


# ─────────────────────────────────────────────────────────────
# Stage 3: Implementation
# ─────────────────────────────────────────────────────────────

def stage_3_implementation(
    state: RunState, config: Config, llm: LLMClient, log: InteractionLog
) -> StageResult:
    """Fill in method bodies with invariants and termination measures."""
    spec_code = (state.workspace_path / "02_specification.dfy").read_text(encoding="utf-8")

    # Run deterministic decomposition on the spec before implementation
    if config.decompose_enabled:
        decomposed, changes = decompose_spec(spec_code)
        if changes:
            print(f"  [Decompose] Applied {len(changes)} simplifications:")
            for c in changes:
                print(f"    - {c}")
            decomposed_file = state.workspace_path / "02_specification_decomposed.dfy"
            decomposed_file.write_text(decomposed, encoding="utf-8")
            # Re-verify the decomposed spec
            resolve_result = dafny_tool.resolve(decomposed_file, dafny_path=config.dafny_path)
            log.log_tool(3, resolve_result.command, resolve_result.exit_code,
                         resolve_result.stdout, resolve_result.stderr)
            if resolve_result.success:
                spec_code = decomposed
                print(f"  [Decompose] Decomposed spec passes dafny resolve")
            else:
                print(f"  [Decompose] Decomposed spec failed resolve, using original")
                if config.verbose:
                    print(f"  [Decompose] Errors: {resolve_result.error_message[:300]}")

    prompt = STAGE3_USER.format(specification_dfy=spec_code)

    raw = _llm_call(
        llm, log, stage=3, attempt=0,
        system=STAGE3_SYSTEM, user=prompt,
        temperature=get_retry_temperature(0),
        verbose=config.verbose,
    )

    dafny_code = strip_code_fences(raw)

    # Fix common syntax errors in implementation bodies
    fixed_code, syntax_fixes = fix_dafny_syntax(dafny_code)
    if syntax_fixes:
        dafny_code = fixed_code
        for fix in syntax_fixes:
            print(f"  [Syntax Fix] {fix}")

    output_file = state.workspace_path / "03_implementation.dfy"
    output_file.write_text(dafny_code, encoding="utf-8")

    # Try verification
    result = dafny_tool.verify(output_file, dafny_path=config.dafny_path)
    log.log_tool(3, result.command, result.exit_code, result.stdout, result.stderr)

    if result.success:
        log.log_stage_complete(3, "success", str(output_file))
        return StageResult(
            outcome=StageOutcome.SUCCESS,
            output_file=output_file,
            message="Implementation verified on first attempt",
            attempts=1,
        )

    # Verification failed — stage 4 will handle retries
    log.log_stage_complete(3, "needs_retry", str(output_file))
    return StageResult(
        outcome=StageOutcome.FAILED,
        output_file=output_file,
        message=f"Verification failed: {result.error_message[:200]}",
        attempts=1,
    )


# ─────────────────────────────────────────────────────────────
# Stage 4: Proof Discharge (retry loop)
# ─────────────────────────────────────────────────────────────

def stage_4_proof_discharge(
    state: RunState, config: Config, llm: LLMClient, log: InteractionLog
) -> StageResult:
    """Retry loop: fix verification errors, strengthen invariants."""
    impl_file = state.workspace_path / "03_implementation.dfy"
    # Use the decomposed spec for integrity checks if it exists,
    # since that's what the model was actually prompted with
    decomposed_file = state.workspace_path / "02_specification_decomposed.dfy"
    spec_file = decomposed_file if decomposed_file.exists() else (
        state.workspace_path / "02_specification.dfy"
    )

    current_code = impl_file.read_text(encoding="utf-8")
    original_spec = spec_file.read_text(encoding="utf-8")

    # Check if it already verifies (stage 3 succeeded)
    result = dafny_tool.verify(impl_file, dafny_path=config.dafny_path)
    if result.success:
        report = {"status": "verified", "attempts": 0, "warnings": [], "mentor_interventions": 0}
        report_file = state.workspace_path / "04_proof_report.json"
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log.log_stage_complete(4, "success", str(report_file))
        return StageResult(
            outcome=StageOutcome.SUCCESS,
            output_file=report_file,
            message="Already verified (no retries needed)",
            attempts=0,
        )

    # Create retry attempts directory
    attempts_dir = state.workspace_path / "03_verify_attempts"
    attempts_dir.mkdir(exist_ok=True)

    # Build conversation history for the retry loop
    conversation: list[dict] = [
        {"role": "user", "content": STAGE3_USER.format(specification_dfy=original_spec)},
        {"role": "assistant", "content": current_code},
    ]

    all_warnings: list[str] = []

    # Initialize mentor
    mentor_state = MentorState(budget_remaining=config.mentor_budget)
    active_directive_text: str | None = None

    for attempt in range(1, config.max_retries + 1):
        errors = result.error_message

        # Save failed attempt
        attempt_file = attempts_dir / f"attempt_{attempt:02d}.dfy"
        attempt_file.write_text(current_code, encoding="utf-8")
        (attempts_dir / f"attempt_{attempt:02d}_errors.txt").write_text(
            errors, encoding="utf-8"
        )

        # Record attempt and check for stuck pattern
        spec_warnings = check_spec_integrity(original_spec, current_code)
        record_attempt(mentor_state, attempt, errors, spec_warnings)

        stuck_pattern = detect_stuck(mentor_state)
        if stuck_pattern and mentor_state.budget_remaining > 0:
            directive = get_mentor_directive(
                mentor_state, stuck_pattern, original_spec,
                llm, log, verbose=config.verbose,
            )
            if directive:
                if directive.action == "rollback" and directive.rollback_target:
                    # Signal rollback to pipeline
                    report = {
                        "status": "rollback",
                        "attempts": attempt,
                        "last_errors": errors[:2000],
                        "warnings": all_warnings,
                        "mentor_interventions": len(mentor_state.interventions),
                        "rollback_target": directive.rollback_target,
                    }
                    report_file = state.workspace_path / "04_proof_report.json"
                    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
                    log.log_stage_complete(4, "rollback", str(report_file))
                    return StageResult(
                        outcome=StageOutcome.FAILED,
                        output_file=report_file,
                        message=f"Mentor recommends rollback to Stage {directive.rollback_target}",
                        attempts=attempt,
                        rollback_target=directive.rollback_target,
                        rollback_guidance=directive.rollback_guidance,
                    )
                else:
                    active_directive_text = directive.content

        # Choose adaptive temperature based on stuck diagnosis
        stuck_cat_str = stuck_pattern.category.value if stuck_pattern else None
        temperature = get_adaptive_temperature(attempt, stuck_cat_str)

        print(f"  Retry {attempt}/{config.max_retries} (temp={temperature:.1f}"
              f"{f', stuck={stuck_cat_str}' if stuck_cat_str else ''})...")

        # Choose prompt template based on mentor directive
        if active_directive_text:
            retry_prompt = STAGE4_RETRY_USER_WITH_MENTOR.format(
                mentor_directive=active_directive_text,
                previous_attempt=current_code,
                errors=errors,
            )
            active_directive_text = None  # Consume after one use
        else:
            retry_prompt = STAGE4_RETRY_USER.format(
                previous_attempt=current_code,
                errors=errors,
            )

        conversation.append({"role": "user", "content": retry_prompt})

        raw = _llm_call_with_history(
            llm, log, stage=4, attempt=attempt,
            system=STAGE3_SYSTEM, messages=conversation,
            temperature=temperature,
            verbose=config.verbose,
        )

        new_code = strip_code_fences(raw)

        # Fix common syntax errors in retry output
        fixed_code, syntax_fixes = fix_dafny_syntax(new_code)
        if syntax_fixes:
            new_code = fixed_code
            for fix in syntax_fixes:
                print(f"  [Syntax Fix] {fix}")

        conversation.append({"role": "assistant", "content": new_code})

        # Check spec integrity
        warnings = check_spec_integrity(original_spec, new_code)
        if warnings:
            all_warnings.extend(warnings)
            print(f"  WARNING: LLM may have modified specifications:")
            for w in warnings:
                print(f"    {w}")

        # Write and verify
        impl_file.write_text(new_code, encoding="utf-8")
        current_code = new_code

        result = dafny_tool.verify(impl_file, dafny_path=config.dafny_path)
        log.log_tool(4, result.command, result.exit_code, result.stdout, result.stderr)

        if result.success:
            report = {
                "status": "verified",
                "attempts": attempt,
                "warnings": all_warnings,
                "mentor_interventions": len(mentor_state.interventions),
            }
            report_file = state.workspace_path / "04_proof_report.json"
            report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
            log.log_stage_complete(4, "success", str(report_file))
            return StageResult(
                outcome=StageOutcome.SUCCESS,
                output_file=report_file,
                message=f"Verified after {attempt} retry(ies)"
                        + (f" ({len(all_warnings)} warnings)" if all_warnings else "")
                        + (f" ({len(mentor_state.interventions)} mentor interventions)"
                           if mentor_state.interventions else ""),
                attempts=attempt,
            )

    # ── Best-of-N fallback: fresh samples without conversation history ──
    if config.best_of_n > 0:
        print(f"\n  [Best-of-N] Adaptive retries exhausted. Generating {config.best_of_n} fresh samples...")
        best_code: str | None = None
        best_verified = -1
        best_errors = ""

        bon_dir = state.workspace_path / "03_best_of_n"
        bon_dir.mkdir(exist_ok=True)

        for sample in range(config.best_of_n):
            sample_prompt = STAGE3_USER.format(specification_dfy=original_spec)

            raw = _llm_call(
                llm, log, stage=4, attempt=config.max_retries + 1 + sample,
                system=STAGE3_SYSTEM, user=sample_prompt,
                temperature=BEST_OF_N_TEMP,
                verbose=config.verbose,
            )
            sample_code = strip_code_fences(raw)

            # Fix common syntax errors in fresh sample
            fixed_code, syntax_fixes = fix_dafny_syntax(sample_code)
            if syntax_fixes:
                sample_code = fixed_code
                for fix in syntax_fixes:
                    print(f"  [Syntax Fix] {fix}")

            # Write and verify
            sample_file = bon_dir / f"sample_{sample + 1:02d}.dfy"
            sample_file.write_text(sample_code, encoding="utf-8")

            sample_result = dafny_tool.verify(sample_file, dafny_path=config.dafny_path)
            log.log_tool(4, sample_result.command, sample_result.exit_code,
                         sample_result.stdout, sample_result.stderr)

            if sample_result.success:
                # Found a fully verified sample — use it immediately
                impl_file.write_text(sample_code, encoding="utf-8")
                total_attempts = config.max_retries + sample + 1
                report = {
                    "status": "verified",
                    "attempts": total_attempts,
                    "strategy": f"best-of-{config.best_of_n} (sample {sample + 1})",
                    "warnings": all_warnings,
                    "mentor_interventions": len(mentor_state.interventions),
                }
                report_file = state.workspace_path / "04_proof_report.json"
                report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
                log.log_stage_complete(4, "success", str(report_file))
                print(f"  [Best-of-N] Sample {sample + 1} verified!")
                return StageResult(
                    outcome=StageOutcome.SUCCESS,
                    output_file=report_file,
                    message=f"Verified via best-of-{config.best_of_n} (sample {sample + 1}, "
                            f"{total_attempts} total attempts)"
                            + (f" ({len(mentor_state.interventions)} mentor interventions)"
                               if mentor_state.interventions else ""),
                    attempts=total_attempts,
                )

            # Track best partial result
            verified, errors_count = _parse_verified_count(sample_result.error_message)
            print(f"  [Best-of-N] Sample {sample + 1}: {verified} verified, {errors_count} errors")

            if verified > best_verified:
                best_verified = verified
                best_code = sample_code
                best_errors = sample_result.error_message

        # No sample fully verified — use the best one as the final state
        if best_code is not None:
            impl_file.write_text(best_code, encoding="utf-8")
            print(f"  [Best-of-N] No sample verified. Best: {best_verified} verified conditions")

    # Exhausted all strategies
    total_attempts = config.max_retries + config.best_of_n
    last_err = result.error_message
    bon_best = None
    if config.best_of_n > 0:
        last_err = best_errors or result.error_message
        bon_best = best_verified
    report = {
        "status": "failed",
        "attempts": total_attempts,
        "last_errors": last_err[:2000],
        "warnings": all_warnings,
        "mentor_interventions": len(mentor_state.interventions),
        "best_of_n_tried": config.best_of_n,
        "best_of_n_best_verified": bon_best,
    }
    report_file = state.workspace_path / "04_proof_report.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.log_stage_complete(4, "failed", str(report_file))
    return StageResult(
        outcome=StageOutcome.FAILED,
        output_file=report_file,
        message=f"Verification failed after {config.max_retries} retries"
                + (f" + {config.best_of_n} fresh samples" if config.best_of_n > 0 else "")
                + (f" ({len(mentor_state.interventions)} mentor interventions)"
                   if mentor_state.interventions else ""),
        attempts=total_attempts,
    )


# ─────────────────────────────────────────────────────────────
# Stage 5: Code Generation
# ─────────────────────────────────────────────────────────────

def stage_5_code_generation(
    state: RunState, config: Config, llm: LLMClient, log: InteractionLog
) -> StageResult:
    """Compile verified Dafny to target language."""
    impl_file = state.workspace_path / "03_implementation.dfy"
    output_dir = state.workspace_path / "05_compiled"
    output_dir.mkdir(exist_ok=True)

    result = dafny_tool.build(
        impl_file,
        target=config.target,
        output_dir=output_dir,
        dafny_path=config.dafny_path,
    )
    log.log_tool(5, result.command, result.exit_code, result.stdout, result.stderr)

    if result.success:
        log.log_stage_complete(5, "success", str(output_dir))
        return StageResult(
            outcome=StageOutcome.SUCCESS,
            output_file=output_dir,
            message=f"Compiled to {config.target} in {output_dir}",
            attempts=1,
        )

    return StageResult(
        outcome=StageOutcome.FAILED,
        output_file=output_dir,
        message=f"Compilation failed: {result.error_message[:200]}",
        attempts=1,
    )
