# Unique Set

## Data Structure
A collection of integers with no duplicate elements.
Internally represented as a sequence where no element appears more than once.

## Operations
1. **Add(x)**: Add integer x to the set. If x is already present, the set is unchanged.
2. **Remove(x)**: Remove x from the set. The element must be present.
3. **Contains(x)**: Return whether x is in the set.
4. **Size()**: Return the number of elements in the set.
5. **IsEmpty()**: Return whether the set is empty.

## Properties to Prove
- **Uniqueness invariant**: No element appears more than once in the internal sequence.
- **Add effect**: After Add(x), x is in the set.
- **Add idempotent**: Adding an element that already exists does not change the set.
- **Add size**: If x was not present, size increases by 1. If x was present, size is unchanged.
- **Remove effect**: After Remove(x), x is not in the set.
- **Remove size**: After Remove, size decreases by 1.
- **Contains is read-only**: Contains does not modify the set.
