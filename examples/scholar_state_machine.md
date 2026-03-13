# Scholar Phase State Machine

## Data Structure
A state machine tracking a 6-phase systematic literature review (phases 0–5).
The state record contains:
- `current_phase`: integer in range [0, 5]
- `phase_status`: enum with values Pending, InProgress, Completed, Failed, NeedsProtocolRevision
- `feedback_iterations`: non-negative integer tracking Phase 4→3 feedback loops
- `retry_count`: non-negative integer tracking retries for the current phase
- `phase_completed`: a sequence of 6 booleans indicating whether each phase has been completed at least once

The state is initialized with current_phase = 0, phase_status = Pending, feedback_iterations = 0, retry_count = 0, and all phase_completed values set to false.

## Operations
1. **StartPhase(phase)**: Set phase_status to InProgress. Requires: phase == current_phase, phase_status == Pending.
2. **CompletePhase(phase)**: Set phase_status to Completed and mark phase_completed[phase] = true. Requires: phase == current_phase, phase_status == InProgress.
3. **FailPhase(phase)**: Set phase_status to Failed. Requires: phase == current_phase, phase_status == InProgress.
4. **TransitionToNext()**: Set current_phase to current_phase + 1, phase_status to Pending, retry_count to 0. Requires: phase_status == Completed, current_phase < 5.
5. **DiagnosticTransition()**: Set phase_status to NeedsProtocolRevision. Requires: current_phase == 2, phase_status == Completed. (Triggered when included corpus is empty after screening.)
6. **FeedbackLoop(max_iterations)**: Set current_phase to 3, phase_status to Pending, increment feedback_iterations by 1, reset retry_count to 0. Requires: current_phase == 4, phase_status == Completed, feedback_iterations < max_iterations.
7. **RetryPhase()**: Set phase_status to InProgress, increment retry_count by 1. Requires: phase_status == Failed, retry_count < 1.
8. **IsReviewComplete()**: Return whether current_phase == 5 and phase_status == Completed.

## Properties to Prove
- **Forward progress**: TransitionToNext can only advance to phase N+1 from completed phase N. After TransitionToNext, current_phase == old(current_phase) + 1.
- **No skipping**: If phase_completed[N] is true for N >= 1, then phase_completed[N-1] is also true. (Cannot complete phase 3 without having completed phases 0, 1, 2.)
- **Feedback bound**: feedback_iterations never exceeds max_iterations parameter. FeedbackLoop requires feedback_iterations < max_iterations before incrementing.
- **Retry bound**: retry_count never exceeds 1. RetryPhase requires retry_count < 1 before incrementing.
- **Terminal correctness**: IsReviewComplete returns true if and only if current_phase == 5 and phase_status == Completed.
- **Status validity**: phase_status is always one of the five defined enum values.
- **Phase range**: current_phase is always in [0, 5].
- **IsReviewComplete is read-only**: IsReviewComplete does not modify state.
