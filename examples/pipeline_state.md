# Pipeline State Machine

## Data Structure
A state machine tracking the status of 5 sequential pipeline stages.
Each stage has an integer status code: 0 = Pending, 1 = InProgress, 2 = Completed, 3 = Failed, 4 = Skipped.
The stages are stored as a sequence of exactly 5 integers (like seq<int> of length 5).
All values in the sequence must be valid status codes between 0 and 4 inclusive.

## Operations
1. **Advance(stage)**: Set the given stage (index 0-4) to InProgress (1). The stage must currently be Pending (0), and every stage before it must be Completed (2) or Skipped (4).
2. **Complete(stage)**: Set the given stage to Completed (2). The stage must currently be InProgress (1).
3. **Fail(stage)**: Set the given stage to Failed (3). The stage must currently be InProgress (1).
4. **Rollback(target)**: Reset the stage at index target and all later stages to Pending (0). Target must be between 0 and 4 inclusive.
5. **IsFinished()**: Return whether every stage is Completed (2) or Skipped (4).

## Properties to Prove
- **Completion closure**: If any stage is Completed (2), then every stage before it is Completed (2) or Skipped (4).
- **Forward progress**: Advance requires all prior stages to be Completed or Skipped before a stage can start.
- **Rollback scope**: After Rollback(target), stages before target are unchanged and stages from target onward are Pending (0).
- **Terminal correctness**: IsFinished returns true if and only if every stage is Completed (2) or Skipped (4).
- **IsFinished is read-only**: IsFinished does not modify the pipeline state.
