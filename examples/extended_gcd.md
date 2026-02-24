# Extended GCD

## Overview
The extended Euclidean algorithm computes the greatest common divisor of two integers along with Bezout coefficients — integers x and y such that a*x + b*y == gcd(a, b). The core challenge is maintaining the Bezout identity as a loop invariant through each iteration of the algorithm.

## Functions
1. **ExtendedGcd(a, b)**: Given two positive integers a and b, return a triple (g, x, y) where g is the greatest common divisor of a and b, and x and y satisfy a*x + b*y == g.

## Properties to Prove

### GCD properties
- **Divides both inputs**: The returned g divides both a and b.
- **Greatest**: For all positive integers d, if d divides both a and b, then d divides g. This divisibility-based formulation is more amenable to SMT solving than the maximality formulation (d <= g), which requires nonlinear reasoning.
- **Positive result**: g > 0 when both inputs are positive.

### Bezout properties
- **Bezout identity**: a * x + b * y == g. This is the central invariant — it must hold at every iteration of the loop and be established as a postcondition. Note that x and y may be negative.

**Feasibility note**: The Bezout identity involves nonlinear arithmetic (variable-variable multiplication), which Z3 handles with incomplete heuristics. This benchmark may require lemma functions or calc blocks to guide the solver.

### Algorithm properties
- **Termination**: The algorithm terminates because the remainder strictly decreases toward zero.
- **Loop invariant**: At each step, the Bezout identity holds for the current values of the coefficients and the pair being reduced. Specifically, if the algorithm tracks (old_a, old_b) reducing to (r1, r2), then old_a * x1 + old_b * y1 == r1 and old_a * x2 + old_b * y2 == r2.
- **No mutation of inputs**: The original values of a and b are preserved (needed to state the postcondition).
