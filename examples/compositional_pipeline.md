# Compositional Pipeline

## Overview
Two pure functions composed in sequence, where the second function's precondition depends on the first function's postcondition. This tests whether the LLM can generate specifications and proofs that compose across function boundaries — the specific capability where frontier models collapse (DafnyComp benchmark: 3% verification rate for Claude Sonnet 4).

## Functions
1. **DigitSum(n)**: Given a non-negative integer, return the sum of its decimal digits. For example, DigitSum(123) == 6, DigitSum(0) == 0.
2. **ClassifyByDigitSum(values)**: Given a sequence of non-negative integers, return two sequences: one containing values whose digit sum is even, and one containing values whose digit sum is odd. Precondition: all elements of values are non-negative. Every element of the input must appear in exactly one of the two output sequences.

## Properties to Prove

### DigitSum properties
- **Non-negative result**: DigitSum always returns a value >= 0.
- **Zero case**: DigitSum(0) == 0.
- **Single digit**: For 0 <= n < 10, DigitSum(n) == n.
- **Decomposition**: For n >= 10, DigitSum(n) == DigitSum(n / 10) + n % 10. This prevents degenerate implementations that return 0 for all multi-digit inputs.
- **Termination**: DigitSum terminates (digits are finite).

### ClassifyByDigitSum properties
- **Partition completeness**: Every element of the input appears in either the even-sum or odd-sum output.
- **Partition correctness (even)**: Every element in the even-sum output has an even digit sum.
- **Partition correctness (odd)**: Every element in the odd-sum output has an odd digit sum.
- **No fabrication**: The multiset union of both outputs equals the multiset of the input. This is stronger than length equality — it proves no elements were swapped between partitions or fabricated.

### Compositional properties (the hard part)
- **Contract propagation**: ClassifyByDigitSum relies on DigitSum's postcondition (non-negative result) to establish that the digit sum modulo 2 is well-defined. The postcondition of DigitSum must be strong enough for ClassifyByDigitSum's proof to go through.
- **End-to-end correctness**: For any input sequence, calling ClassifyByDigitSum and then concatenating both outputs produces a permutation of the input.
