# Scholar Metrics Recount

## Data Structure
Pure counting functions over sequences of records. No mutable state.

Input sequences:
- `screening_log`: sequence of records, each with a `decision` field (string: "include", "exclude", or "flag_for_full_text")
- `candidates`: sequence of records, each with an `id` field (string)
- `included`: sequence of records, each with an `id` field (string)
- `snowball_log`: sequence of records, each with a `depth_level` field (non-negative integer)
- `extractions`: sequence of records, each with a `paper_id` field (string)
- `concepts`: sequence of records, each with a `concept_id` field (string)

Output: a metrics record with fields:
- `total_candidates`: non-negative integer
- `total_included`: non-negative integer
- `total_excluded`: non-negative integer
- `total_flagged`: non-negative integer
- `snowball_depth_reached`: non-negative integer
- `concepts_count`: non-negative integer
- `extraction_complete_count`: non-negative integer

## Operations
1. **CountExcluded(screening_log)**: Count entries where decision == "exclude". Returns non-negative integer.
2. **CountFlagged(screening_log)**: Count entries where decision == "flag_for_full_text". Returns non-negative integer.
3. **CountIncluded(included)**: Return length of the included sequence.
4. **CountCandidates(candidates)**: Return length of the candidates sequence.
5. **MaxSnowballDepth(snowball_log)**: Return the maximum depth_level value across all entries. If the sequence is empty, return 0.
6. **CountConcepts(concepts)**: Return length of the concepts sequence.
7. **CountExtractions(extractions)**: Count the number of unique paper_id values in the extractions sequence.
8. **RecomputeAll(screening_log, candidates, included, snowball_log, extractions, concepts)**: Call all above functions and return a metrics record.

## Properties to Prove
- **Non-negative**: All count results are >= 0.
- **Accounting identity**: For any screening_log, CountExcluded(screening_log) + CountFlagged(screening_log) + count_of_include_decisions(screening_log) == length(screening_log). That is, every entry is counted exactly once.
- **Included bounded by candidates**: CountIncluded(included) <= CountCandidates(candidates) when every included record id appears in candidates (this is a conditional property — holds when the caller maintains the subset invariant).
- **Idempotency**: RecomputeAll called twice with the same inputs returns the same metrics record.
- **MaxSnowballDepth bounds**: If snowball_log is non-empty, MaxSnowballDepth(snowball_log) >= 0 and MaxSnowballDepth(snowball_log) <= max(entry.depth_level for entry in snowball_log).
- **CountExtractions bounded**: CountExtractions(extractions) <= length(extractions). (Unique count never exceeds total count.)
- **All operations are read-only**: No operation modifies its input sequences.
