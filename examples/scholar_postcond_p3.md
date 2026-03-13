# Scholar Postconditions — Phase 3 (Snowballing)

## Data Structure
Pure validation functions over parsed workspace data.

Input types:
- `snowball_entry`: record with `source_paper_id` (string), `direction` (string: "forward" or "backward"), `screening_decision` (string or null), `depth_level` (non-negative integer), `truncated` (boolean), `total_citations_available` (integer or null), `citations_retrieved` (integer or null), `discovered_paper_id` (string), `already_known` (boolean)
- `included_paper`: record with `id` (string)
- `candidate`: record with `id` (string)
- `phase_log_entry`: record with `event` (string), `saturation_metric` (rational or null), `phase` (integer)
- `max_snowball_depth`: non-negative integer (from protocol)
- `discovery_threshold`: rational (θ_d from protocol)

## Operations
1. **CheckTerminationCondition(max_depth_reached, saturation_below_threshold, max_depth)**: Returns satisfied = true if max_depth_reached >= max_depth OR saturation_below_threshold is true. Returns (satisfied, failures) where failures contains a single string if neither condition holds.
2. **CheckAllSeedsExamined(seed_count, seeds_with_forward, seeds_with_backward)**: Returns satisfied = true if seeds_with_forward == seed_count AND seeds_with_backward == seed_count. Returns (satisfied, failures) with failure count.
3. **CheckTruncationLogged(truncated_count, truncated_with_counts)**: Returns satisfied = true if truncated_count == truncated_with_counts. Returns (satisfied, failures).
4. **CheckNewInclusionsRecorded(snowball_includes, includes_in_included, includes_in_candidates)**: Returns satisfied = true if snowball_includes == includes_in_included AND snowball_includes == includes_in_candidates. Returns (satisfied, failures).
5. **CheckPhase3All(max_depth_reached, saturation_below_threshold, max_depth, seed_count, seeds_with_forward, seeds_with_backward, truncated_count, truncated_with_counts, snowball_includes, includes_in_included, includes_in_candidates)**: Runs checks 1-4. Returns (satisfied, failures) where satisfied is true only if all four pass.

## Properties to Prove
- **Soundness**: If CheckPhase3All returns satisfied == true, then all four individual checks pass.
- **Completeness**: If any individual check fails, CheckPhase3All returns satisfied == false with non-empty failures.
- **Determinism**: Same inputs produce the same output.
- **All operations are read-only**: No operation modifies its inputs.
