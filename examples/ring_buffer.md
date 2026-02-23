# Ring Buffer

## Data Structure
A fixed-capacity circular buffer storing integer elements.
Uses an array with head and tail pointers that wrap around using modular arithmetic.
The buffer has a fixed capacity set at creation time.

## Operations
1. **Enqueue(x)**: Add integer x to the back of the buffer. Buffer must not be full.
2. **Dequeue()**: Remove and return the element at the front. Buffer must not be empty.
3. **Peek()**: Return the front element without removing it. Buffer must not be empty.
4. **Size()**: Return the number of elements currently in the buffer.
5. **IsFull()**: Return whether the buffer is at capacity.
6. **IsEmpty()**: Return whether the buffer is empty.

## Properties to Prove
- **Capacity invariant**: The number of elements never exceeds the fixed capacity.
- **FIFO ordering**: Dequeue returns elements in the order they were enqueued.
- **Size tracking**: After Enqueue, size increases by 1. After Dequeue, size decreases by 1.
- **Pointer validity**: Head and tail pointers are always valid indices (0 <= ptr < capacity).
- **Wrap-around correctness**: Pointers correctly wrap from capacity-1 back to 0.
- **Peek consistency**: Peek returns the same value Dequeue would return.
- **Peek is read-only**: Peek does not modify buffer state.
