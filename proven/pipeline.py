"""Main pipeline orchestrator."""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .llm import LLMClient
from .workspace import RunState, InteractionLog
from .interaction import InteractionHandler
from .stages import (
    StageOutcome,
    stage_1_requirements,
    stage_2_specification,
    stage_3_implementation,
    stage_4_proof_discharge,
    stage_5_code_generation,
)

STAGES = [
    (1, "Requirements Capture", stage_1_requirements),
    (2, "Formal Specification", stage_2_specification),
    (3, "Implementation", stage_3_implementation),
    (4, "Proof Discharge", stage_4_proof_discharge),
    (5, "Code Generation", stage_5_code_generation),
]


def run_pipeline(config: Config, requirements_file: Path) -> int:
    """Execute the full pipeline from scratch. Returns 0 on success, 1 on failure."""
    # Validate requirements file
    if not requirements_file.exists():
        print(f"Error: requirements file not found: {requirements_file}")
        return 1

    # Validate LLM config
    if not config.llm_api_key:
        print("Error: LLM_API_KEY not set. Copy .env.example to .env and fill it in.")
        return 1

    llm = LLMClient(config.llm_base_url, config.llm_api_key, config.llm_model)
    state = RunState.create(
        config.workspace_root,
        requirements_file,
        config.mode,
        config_snapshot={
            "llm_model": config.llm_model,
            "target": config.target,
            "max_retries": config.max_retries,
            "strategy": config.strategy_name,
        },
    )
    log = InteractionLog(state.workspace_path)
    interaction = InteractionHandler(config.mode)

    print(f"Proven v0.1.0 — LLM-driven stepwise refinement")
    print(f"Workspace: {state.workspace_path}")
    print(f"Mode: {config.mode} | Model: {config.llm_model} | Target: {config.target}")
    print(f"Strategy: {config.strategy_name} | Max retries: {config.max_retries}")

    return _execute_stages(state, config, llm, log, interaction)


def resume_pipeline(config: Config, workspace_dir: Path, from_stage: int | None) -> int:
    """Resume a pipeline from an existing workspace."""
    if not workspace_dir.exists():
        print(f"Error: workspace not found: {workspace_dir}")
        return 1

    state = RunState.load(workspace_dir)
    log = InteractionLog(state.workspace_path)

    # Override mode if specified
    if config.mode != "assisted":  # only override if explicitly set
        state.mode = config.mode

    # Reset stages if resuming from a specific point
    if from_stage is not None:
        for i in range(from_stage, 6):
            state.stage_status[i] = "pending"
            state.retry_counts[i] = 0
        state.save()

    llm = LLMClient(config.llm_base_url, config.llm_api_key, config.llm_model)
    interaction = InteractionHandler(state.mode)

    print(f"Proven v0.1.0 — Resuming from {workspace_dir}")
    print(f"Mode: {state.mode}")

    return _execute_stages(state, config, llm, log, interaction)


def _execute_stages(
    state: RunState,
    config: Config,
    llm: LLMClient,
    log: InteractionLog,
    interaction: InteractionHandler,
) -> int:
    """Walk through stages with mode-based interaction and rollback support."""
    stage_idx = 0
    rollback_count = 0

    while stage_idx < len(STAGES):
        stage_num, stage_name, stage_fn = STAGES[stage_idx]

        status = state.stage_status.get(stage_num, "pending")
        if status in ("completed", "recovered"):
            print(f"\n  Stage {stage_num} ({stage_name}): already completed, skipping")
            stage_idx += 1
            continue
        if status == "skipped":
            print(f"\n  Stage {stage_num} ({stage_name}): skipped")
            stage_idx += 1
            continue

        # Skip Stage 1 in iterative mode (model chooses its own decomposition)
        if stage_num == 1 and config.skip_stage1:
            state.stage_status[1] = "skipped"
            state.save()
            print(f"\n  Stage 1 (Requirements Capture): skipped ({config.strategy_name} strategy)")
            stage_idx += 1
            continue

        # Stage 4 auto-skips if stage 3 succeeded
        if stage_num == 4 and state.stage_status.get(3) == "completed":
            impl_file = state.workspace_path / "03_implementation.dfy"
            if impl_file.exists():
                from . import dafny as dafny_tool
                check = dafny_tool.verify(impl_file, dafny_path=config.dafny_path)
                if check.success:
                    state.stage_status[4] = "completed"
                    state.save()
                    print(f"\n  Stage 4 (Proof Discharge): implementation already verified, skipping")
                    stage_idx += 1
                    continue

        print(f"\n{'=' * 60}")
        print(f"  Stage {stage_num}: {stage_name}")
        print(f"{'=' * 60}")

        state.current_stage = stage_num
        state.stage_status[stage_num] = "in_progress"
        state.save()

        result = stage_fn(state, config, llm, log)
        state.retry_counts[stage_num] = result.attempts

        if result.outcome == StageOutcome.SUCCESS:
            state.stage_status[stage_num] = "completed"
            print(f"\n  -> SUCCESS: {result.message}")
            # Stage 4 success means Stage 3's implementation was fixed
            if stage_num == 4 and state.stage_status.get(3) == "failed":
                state.stage_status[3] = "recovered"
        elif result.outcome == StageOutcome.FAILED:
            state.stage_status[stage_num] = "failed"
            print(f"\n  -> FAILED: {result.message}")
        elif result.outcome == StageOutcome.SKIPPED:
            state.stage_status[stage_num] = "skipped"

        state.save()

        # Handle rollback from Stage 4
        if (result.rollback_target is not None
                and rollback_count < config.rollback_budget):
            rollback_count += 1
            target_stage = result.rollback_target
            target_idx = next(
                i for i, (n, _, _) in enumerate(STAGES) if n == target_stage
            )

            # Store rollback guidance for the target stage
            state.rollback_guidance = result.rollback_guidance

            # Reset stages from target onward
            for i in range(target_idx, len(STAGES)):
                n = STAGES[i][0]
                state.stage_status[n] = "pending"
                state.retry_counts[n] = 0
            state.save()

            print(f"\n  [Rollback] Rewinding to Stage {target_stage} "
                  f"({rollback_count}/{config.rollback_budget} rollbacks used)")
            stage_idx = target_idx
            continue

        # Mode-based interaction
        if interaction.should_pause(result.outcome.value, result.attempts):
            while True:
                action = interaction.prompt_user(
                    stage_num, stage_name, result.outcome.value,
                    result.message, result.output_file,
                )
                log.log_user_decision(stage_num, action)

                if action == "approve":
                    break
                elif action == "abort":
                    print("\n  Pipeline aborted by user.")
                    return 1
                elif action == "skip":
                    state.stage_status[stage_num] = "skipped"
                    state.save()
                    break
                elif action == "retry":
                    # Re-run the stage
                    state.stage_status[stage_num] = "pending"
                    result = stage_fn(state, config, llm, log)
                    state.retry_counts[stage_num] = result.attempts
                    if result.outcome == StageOutcome.SUCCESS:
                        state.stage_status[stage_num] = "completed"
                        print(f"\n  -> SUCCESS: {result.message}")
                    else:
                        state.stage_status[stage_num] = "failed"
                        print(f"\n  -> FAILED: {result.message}")
                    state.save()
                    # Loop back to prompt again
                elif action == "switch_mode":
                    new_mode = interaction.get_new_mode()
                    interaction = InteractionHandler(new_mode)
                    state.mode = new_mode
                    state.save()
                    print(f"  Mode switched to: {new_mode}")
                    # Re-evaluate whether to pause
                    if not interaction.should_pause(result.outcome.value, result.attempts):
                        break

        # Stop on failure in autonomous mode — but stage 3 failure flows to stage 4
        if result.outcome == StageOutcome.FAILED and config.mode == "autonomous":
            if stage_num == 3:
                print(f"\n  Stage 3 failed verification — proceeding to Stage 4 (proof discharge)...")
                stage_idx += 1
                continue
            break

        stage_idx += 1

    # Summary — always print, whether completed or stopped early
    all_succeeded = all(
        state.stage_status.get(n) in ("completed", "skipped", "recovered") for n, _, _ in STAGES
    )
    label = "Pipeline Complete" if all_succeeded else "Pipeline Summary"
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    for num, name, _ in STAGES:
        status = state.stage_status.get(num, "?")
        retries = state.retry_counts.get(num, 0)
        if status == "recovered":
            s4_retries = state.retry_counts.get(4, 0)
            detail = f" (failed -> fixed in Stage 4, {s4_retries} retry(ies))"
        elif retries > 1:
            detail = f" ({retries} attempts)"
        else:
            detail = ""
        print(f"  Stage {num} ({name}): {status}{detail}")
    if rollback_count > 0:
        print(f"  Rollbacks used: {rollback_count}")
    print(f"\n  Workspace: {state.workspace_path}")

    return 0 if all_succeeded else 1
