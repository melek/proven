# Sorted List

## Data Structure
A list of integers that maintains sorted (non-decreasing) order at all times.
Internally represented as a sequence.

## Operations
1. **Insert(x)**: Add integer element x into the correct sorted position.
2. **Remove(x)**: Remove one occurrence of x from the list. The element must be present.
3. **Contains(x)**: Return whether x is in the list.
4. **GetMin()**: Return the minimum element. List must not be empty.
5. **GetMax()**: Return the maximum element. List must not be empty.
6. **Size()**: Return the number of elements in the list.

## Properties to Prove
- **Sorted invariant**: The sequence is always in non-decreasing order.
- **Insert preserves sort**: After Insert(x), the list is still sorted and contains x.
- **Insert size**: After Insert, size increases by 1.
- **Remove preserves sort**: After Remove(x), the list is still sorted.
- **Remove size**: After Remove, size decreases by 1.
- **Min correctness**: GetMin returns the first element (smallest in a sorted list).
- **Max correctness**: GetMax returns the last element (largest in a sorted list).
- **Contains is read-only**: Contains does not modify the list.
