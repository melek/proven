# Binary Search

## Data Structure
A sorted array of integers with a binary search operation.
The array is immutable after construction; only search is performed.

## Operations
1. **Search(arr, key)**: Given a sorted integer array and a key, return the index where key is found, or -1 if not present. The array must be sorted in non-decreasing order.
2. **IsSorted(arr)**: Return whether the array is sorted in non-decreasing order.

## Properties to Prove
- **Found correctness**: If Search returns an index >= 0, then arr[index] == key.
- **Not-found correctness**: If Search returns -1, then key does not appear anywhere in arr.
- **Index bounds**: If Search returns an index >= 0, then 0 <= index < |arr|.
- **Sorted precondition**: Search requires the array to be sorted.
- **Termination**: Search always terminates (via a decreasing measure on the search range).
- **IsSorted is pure**: IsSorted does not modify any state.
