# Balanced Parentheses Checker

## Data Structure
A checker that determines whether a string of parentheses characters is balanced.
Uses a counter-based approach: increment on '(' and decrement on ')'.
The string is balanced if the counter never goes negative and ends at zero.

## Operations
1. **IsBalanced(s)**: Given a sequence of characters (where each is either '(' or ')'), return whether the parentheses are balanced.
2. **CountOpen(s)**: Return the number of '(' characters in the sequence.
3. **CountClose(s)**: Return the number of ')' characters in the sequence.

## Properties to Prove
- **Balanced definition**: A sequence is balanced if and only if CountOpen == CountClose and no prefix has more ')' than '('.
- **Empty is balanced**: An empty sequence is balanced.
- **Single open is not balanced**: A sequence containing only '(' is not balanced.
- **Single close is not balanced**: A sequence containing only ')' is not balanced.
- **Matched pair is balanced**: The sequence ['(', ')'] is balanced.
- **Termination**: IsBalanced always terminates.
- **All operations are pure**: No operation modifies any state.
