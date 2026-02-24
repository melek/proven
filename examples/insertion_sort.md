# Insertion Sort with Permutation Proof

## Overview
In-place insertion sort on an integer array, with a proof that the output is both sorted and a permutation of the input. The permutation proof requires ghost state (multiset tracking) — a specific capability that current benchmarks do not test and that LLMs consistently struggle with.

## Functions
1. **InsertionSort(a)**: Sort the array a in-place in non-decreasing order.
2. **IsSorted(a)**: Return whether the array is sorted in non-decreasing order.

## Properties to Prove

### Sorting correctness
- **Sorted output**: After InsertionSort, the array is sorted in non-decreasing order — for all valid indices i < j, a[i] <= a[j].
- **IsSorted agreement**: After InsertionSort, IsSorted(a) returns true.

### Permutation proof (the hard part)
- **Permutation invariant**: The multiset of elements in the array after sorting equals the multiset of elements before sorting. In Dafny terms: `multiset(a[..]) == multiset(old(a[..]))`. This proves no elements were fabricated, lost, or duplicated — only rearranged.
- **Inner loop permutation**: Each iteration of the inner loop (shifting elements right to make room for the key) preserves the multiset. This requires a loop invariant tracking the multiset through each swap.

### Algorithm properties
- **Termination**: Both the outer and inner loops terminate.
- **In-place**: The sort operates on the original array without allocating a new one.
- **Stability** (optional, harder): Equal elements retain their original relative order. This requires additional ghost state tracking original indices.
