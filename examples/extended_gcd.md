# Extended GCD

## Overview
The extended Euclidean algorithm computes the greatest common divisor of two integers along with Bezout coefficients — integers x and y such that a*x + b*y == gcd(a, b). The core challenge is maintaining the Bezout identity as a loop invariant through each iteration of the algorithm.

## Functions
1. **ExtendedGcd(a, b)**: Given two positive integers a and b, return a triple (g, x, y) where g is the greatest common divisor of a and b, and x and y satisfy a*x + b*y == g.

## Properties to Prove

### GCD properties
- **Divides both inputs**: The returned g divides both a and b.
- **Greatest**: No integer larger than g divides both a and b. Equivalently, for all d that divide both a and b, d <= g.
- **Positive result**: g > 0 when both inputs are positive.

### Bezout properties
- **Bezout identity**: a * x + b * y == g. This is the central invariant — it must hold at every iteration of the loop and be established as a postcondition.
- **Coefficient existence**: For any two positive integers, Bezout coefficients exist.

### Algorithm properties
- **Termination**: The algorithm terminates because the remainder strictly decreases toward zero.
- **Loop invariant**: At each step, the Bezout identity holds for the current values of the coefficients and the pair being reduced. Specifically, if the algorithm tracks (old_a, old_b) reducing to (r1, r2), then old_a * x1 + old_b * y1 == r1 and old_a * x2 + old_b * y2 == r2.
- **No mutation of inputs**: The original values of a and b are preserved (needed to state the postcondition).
