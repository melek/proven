# Priority Queue with Proven Ordering Invariants

## Data Structure
A min-priority queue storing integer elements.
Internally represented as a sequence that maintains sorted order (smallest first).

## Operations
1. **Insert(x)**: Add integer element x to the queue.
2. **ExtractMin()**: Remove and return the minimum element. Queue must not be empty.
3. **Peek()**: Return the minimum element without removing it. Queue must not be empty.
4. **Size()**: Return the number of elements in the queue.
5. **IsEmpty()**: Return whether the queue is empty.

## Properties to Prove
- **Ordering**: ExtractMin and Peek always return the minimum element in the queue.
- **Size tracking**: After Insert, size increases by 1. After ExtractMin, size decreases by 1.
- **Sorted invariant**: The internal sequence is always in non-decreasing order.
- **Completeness**: No elements are lost — every inserted element can eventually be extracted.
- **Peek is read-only**: Peek does not modify the queue state.
