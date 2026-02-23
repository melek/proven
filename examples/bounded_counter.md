# Bounded Counter

## Data Structure
A counter that maintains an integer value within a fixed range [min, max].
The counter is initialized with min and max bounds, and the value starts at min.

## Operations
1. **Increment()**: Increase the counter value by 1. The counter must not be at its maximum.
2. **Decrement()**: Decrease the counter value by 1. The counter must not be at its minimum.
3. **GetValue()**: Return the current counter value.
4. **IsAtMin()**: Return whether the counter is at its minimum value.
5. **IsAtMax()**: Return whether the counter is at its maximum value.

## Properties to Prove
- **Bounded**: The counter value is always >= min and <= max.
- **Increment effect**: After Increment, value increases by exactly 1.
- **Decrement effect**: After Decrement, value decreases by exactly 1.
- **GetValue is read-only**: GetValue does not modify counter state.
- **Bounds are immutable**: min and max never change after initialization.
