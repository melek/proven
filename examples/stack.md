# Stack (LIFO)

## Data Structure
A last-in-first-out stack storing integer elements.
Internally represented as a sequence where the top of the stack is the last element.

## Operations
1. **Push(x)**: Add integer element x to the top of the stack.
2. **Pop()**: Remove and return the top element. Stack must not be empty.
3. **Top()**: Return the top element without removing it. Stack must not be empty.
4. **Size()**: Return the number of elements in the stack.
5. **IsEmpty()**: Return whether the stack is empty.

## Properties to Prove
- **LIFO ordering**: Pop returns the most recently pushed element.
- **Size tracking**: After Push, size increases by 1. After Pop, size decreases by 1.
- **Top consistency**: Top returns the same value that Pop would return.
- **Top is read-only**: Top does not modify stack state.
- **Push-Pop inverse**: Pushing x then popping returns x and restores the original stack.
