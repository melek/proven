# M00 Orchestrator State Machine

## Data Structure
A state machine for pipeline orchestration with 13 states. Each state is a named enum value: IDLE, AUTH_CHECK, INTAKE, TIER0_DIRECT, TIER1_ACK, TIER1_EXECUTE, TIER2_DECOMPOSE, TIER2_EXECUTE_LOOP, SCORING, HANDOFF, DELIVER, ERROR, COMPLETE.
Transitions are guarded by conditions: a tier classification (enum: Tier0, Tier1, Tier2), a boolean store_unlocked, a boolean subtasks_remaining, and a boolean recoverable.
A transition event records: from_state, to_state, tier, store_unlocked, subtasks_remaining, recoverable, and an audit_event_id string that must be non-empty.
A trace is a sequence of transition events.

## Operations
1. **ExecuteTransition(current_state, tier, store_unlocked, subtasks_remaining, recoverable, audit_event_id)**: Return the next state according to the guarded-command rules. Requires current_state is not COMPLETE. Requires audit_event_id is non-empty. The transition rules are: IDLE goes to AUTH_CHECK. AUTH_CHECK goes to INTAKE if store_unlocked, ERROR if not. INTAKE goes to TIER0_DIRECT if Tier0, TIER1_ACK if Tier1, TIER2_DECOMPOSE if Tier2. TIER0_DIRECT goes to COMPLETE. TIER1_ACK goes to TIER1_EXECUTE. TIER1_EXECUTE goes to SCORING. TIER2_DECOMPOSE goes to TIER2_EXECUTE_LOOP. TIER2_EXECUTE_LOOP goes to itself if subtasks_remaining, SCORING if not. SCORING goes to HANDOFF. HANDOFF goes to DELIVER. DELIVER goes to COMPLETE. ERROR goes to IDLE if recoverable, COMPLETE if not.
2. **IsValidTransition(from_state, to_state, tier, store_unlocked, subtasks_remaining, recoverable)**: Return whether a transition from from_state to to_state is valid under the given conditions.
3. **IsValidTrace(trace)**: Return whether every event in the trace is a valid transition and every event has a non-empty audit_event_id.
4. **IsConsistentTrace(trace)**: Return whether consecutive events are state-consistent: each event's to_state matches the next event's from_state.
5. **IsCompleteTrace(trace)**: Return whether the trace is non-empty and the last event's to_state is COMPLETE.

## Properties to Prove
- **Terminal correctness**: COMPLETE is terminal. No valid transition has COMPLETE as its from_state.
- **Determinism**: For any given (current_state, tier, store_unlocked, subtasks_remaining, recoverable), ExecuteTransition produces exactly one next_state.
- **Audit invariant**: ExecuteTransition requires a non-empty audit_event_id. Every event in a valid trace has a non-empty audit_event_id.
- **Tier 0 reachability**: A trace starting at IDLE with store_unlocked=true and tier=Tier0 reaches COMPLETE in exactly 4 transitions (5 states: IDLE, AUTH_CHECK, INTAKE, TIER0_DIRECT, COMPLETE).
- **Tier 1 reachability**: A trace starting at IDLE with store_unlocked=true and tier=Tier1 reaches COMPLETE in exactly 8 transitions (9 states: IDLE, AUTH_CHECK, INTAKE, TIER1_ACK, TIER1_EXECUTE, SCORING, HANDOFF, DELIVER, COMPLETE).
- **No dead states**: Every non-COMPLETE state has at least one valid outbound transition.
- **Error recovery**: From ERROR with recoverable=true, the system returns to IDLE. From ERROR with recoverable=false, the system reaches COMPLETE.
- **Monotonic progress for self-loops**: The only state that can transition to itself is TIER2_EXECUTE_LOOP (when subtasks_remaining is true). No other state has a self-loop.
