# Scholar Postconditions — Phase 2 (Screening)

## Data Structure
Pure validation functions over parsed workspace data.

Input types:
- `candidate`: record with `id` (string)
- `screening_entry`: record with `paper_id` (string) and `decision` (string: "include", "exclude", or "flag_for_full_text")
- `included_paper`: record with `id` (string)

## Operations
1. **CheckAllCandidatesScreened(candidates, screening_log)**: For every candidate, there exists at least one screening_entry with matching paper_id AND decision in {"include", "exclude"}. Papers initially flagged have two entries; only the final include/exclude decision matters. Returns (satisfied, failures) listing unscreened candidate ids.
2. **CheckIncludedConsistency(included, screening_log)**: Every included paper has a corresponding screening_entry with decision == "include". Returns (satisfied, failures) listing inconsistent paper ids.
3. **CheckNoOrphanInclusions(included, candidates)**: Every included paper id exists in the candidates sequence. Returns (satisfied, failures) listing orphan paper ids.
4. **CheckPhase2All(candidates, screening_log, included)**: Runs checks 1–3. Returns (satisfied, failures) where satisfied is true only if all three pass.

## Properties to Prove
- **Soundness**: If CheckPhase2All returns satisfied == true, then all three individual checks return satisfied == true.
- **Completeness**: If any individual check returns satisfied == false, then CheckPhase2All returns satisfied == false and failures is non-empty.
- **Determinism**: Same inputs produce the same output.
- **All operations are read-only**: No operation modifies its inputs.
