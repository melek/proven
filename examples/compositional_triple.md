# Three-Function Compositional Chain

## Overview
Three pure functions composed in sequence, where each function's precondition depends on the previous function's postcondition. This is the full compositional verification challenge identified by DafnyComp (arXiv 2509.23061) where frontier LLMs achieve 3% or lower verification rates. The difficulty is not in any single function but in making the contracts strong enough to compose.

## Functions
1. **Frequencies(s)**: Given a sequence of integers, return a map from each distinct value to its count in the sequence. For example, Frequencies([1,2,1,3]) == map[1 := 2, 2 := 1, 3 := 1].
2. **FilterByFrequency(freq, threshold)**: Given a frequency map and a positive integer threshold (threshold >= 1), return the set of keys whose frequency is >= threshold.
3. **CollectFiltered(s, keep)**: Given the original sequence and a set of keys to keep, return a new sequence containing only the elements that are in the keep set, preserving their original order.

## Properties to Prove

### Frequencies properties
- **Complete**: Every distinct element of the input has an entry in the output map.
- **Accurate counts**: For each key k in the output, freq[k] equals the number of times k appears in s.
- **Positive counts**: All values in the frequency map are > 0.
- **Sum of counts**: The sum of all values in the frequency map equals |s|. Note: this property requires a recursive ghost function to sum over map values, which adds proof complexity.

### FilterByFrequency properties
- **Correctness**: A key is in the output set if and only if it appears in the frequency map with count >= threshold.
- **Subset**: The output set is a subset of the keys in the frequency map.

### CollectFiltered properties
- **Inclusion**: Every element in the output is a member of the keep set.
- **Subsequence**: The output is a subsequence of the input — it preserves relative order and contains no elements not in the input.
- **Completeness**: Every element of the input that is in the keep set appears in the output (including duplicates — if the input contains k copies of a value in the keep set, the output contains k copies).

### Compositional properties (the hard part)
- **End-to-end contract propagation**: Calling CollectFiltered(s, FilterByFrequency(Frequencies(s), k)) produces a subsequence of s containing exactly those elements that appear at least k times in s, preserving all occurrences (including duplicates).
- **Frequencies postcondition sufficiency**: The postcondition of Frequencies must be strong enough that FilterByFrequency can establish its own postcondition. Specifically, FilterByFrequency needs to know that every key in the map corresponds to an actual element of the original sequence.
- **FilterByFrequency postcondition sufficiency**: The postcondition of FilterByFrequency must be strong enough that CollectFiltered can establish that every kept element actually appeared with sufficient frequency. This requires the set membership guarantee to propagate through.
