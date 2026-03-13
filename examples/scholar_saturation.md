# Scholar Saturation Metrics

## Data Structure
Pure functions computing saturation metrics over sequences. Uses exact rational arithmetic (not floating point).

Input types:
- `snowball_entry`: record with `depth_level` (non-negative integer), `screening_decision` (string: "include", "exclude", or null), `already_known` (boolean)
- `concept_entry`: record with `concept_id` (string), `first_seen_in` (string — a paper_id), `first_seen_at` (timestamp string for ordering)
- `paper_id_set`: a set of strings representing paper identifiers

A rational number is represented as a pair (numerator: int, denominator: int) where denominator > 0.

## Operations
1. **DiscoverySaturation(snowball_log, depth)**: Filter snowball_log to entries where depth_level == depth. Count entries where screening_decision == "include" AND already_known == false → numerator. Count all entries at that depth → denominator. If denominator == 0, return rational(0, 1). Otherwise return rational(numerator, denominator).
2. **ConceptualSaturation(concepts, last_k_paper_ids)**: Count concepts whose first_seen_in is in last_k_paper_ids → numerator. Total concept count → denominator. If denominator == 0, return rational(0, 1). Otherwise return rational(numerator, denominator).
3. **ShouldTerminateDiscovery(saturation, threshold)**: Return true if saturation < threshold. Both are rationals.
4. **ShouldFeedbackLoop(delta, theta_c, iterations, max_iterations)**: Return true if delta >= theta_c AND iterations < max_iterations. delta and theta_c are rationals; iterations and max_iterations are non-negative integers.

## Properties to Prove
- **Range**: DiscoverySaturation always returns a rational in [0, 1]. ConceptualSaturation always returns a rational in [0, 1].
- **Zero denominator safety**: When denominator is 0, both saturation functions return rational(0, 1), not division-by-zero.
- **Threshold correctness**: ShouldTerminateDiscovery returns true if and only if saturation < threshold.
- **Feedback bound**: ShouldFeedbackLoop returns false when iterations >= max_iterations, regardless of delta and theta_c values.
- **Monotonicity of discovery**: If the snowball_log at depth d has no entries with screening_decision == "include" and already_known == false, then DiscoverySaturation returns rational(0, 1) (which is <= any non-negative threshold, so discovery terminates).
- **All operations are read-only**: No operation modifies its input data.
