"""Prompt templates for each pipeline stage.

Each stage has a system prompt and a user prompt template.
Templates use {placeholders} for runtime substitution.
"""

import re
import json


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    # Match ```dafny ... ``` or ```json ... ``` or bare ``` ... ```
    pattern = r"```(?:\w+)?\s*\n?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def extract_json(text: str) -> dict:
    """Extract the first JSON object from LLM output."""
    # Try parsing the whole thing first
    stripped = strip_code_fences(text)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Find the first { ... } block
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = None
    raise ValueError("No valid JSON object found in LLM response")


def extract_spec_clauses(dafny_code: str) -> list[str]:
    """Extract requires/ensures clauses for integrity checking."""
    clauses = []
    for line in dafny_code.splitlines():
        stripped = line.strip()
        if stripped.startswith(("requires", "ensures", "invariant", "decreases")):
            clauses.append(stripped)
    return clauses


def check_spec_integrity(original: str, revised: str) -> list[str]:
    """Warn if the LLM removed or weakened spec clauses during retry."""
    original_clauses = set(extract_spec_clauses(original))
    revised_clauses = set(extract_spec_clauses(revised))
    removed = original_clauses - revised_clauses
    warnings = []
    for clause in sorted(removed):
        warnings.append(f"REMOVED: {clause}")
    return warnings


# ─────────────────────────────────────────────────────────────
# Stage 1: Requirements Capture
# ─────────────────────────────────────────────────────────────

STAGE1_SYSTEM = """\
You are a requirements analyst for formally verified software.
Your task is to take natural language requirements and produce a structured JSON \
specification that will serve as input to a formal specification stage.

You must identify:
- Data structures and their invariants (properties that must ALWAYS hold)
- Operations and their preconditions (what must be true BEFORE the operation)
- Operations and their postconditions (what must be true AFTER the operation)
- Relationships between operations (ordering, commutativity, etc.)

Output ONLY valid JSON. No markdown fences, no explanation outside the JSON."""

STAGE1_USER = """\
Analyze the following requirements and produce a structured specification.

Requirements:
{requirements_text}

Output JSON with this structure:
{{
  "component_name": "...",
  "description": "one-line summary",
  "data_structures": [
    {{
      "name": "...",
      "fields": [{{"name": "...", "type": "...", "description": "..."}}],
      "invariants": [
        {{"id": "INV1", "natural_language": "...", "formal_sketch": "..."}}
      ]
    }}
  ],
  "operations": [
    {{
      "name": "...",
      "parameters": [{{"name": "...", "type": "..."}}],
      "returns": {{"type": "...", "description": "..."}},
      "preconditions": [
        {{"id": "PRE1", "natural_language": "...", "formal_sketch": "..."}}
      ],
      "postconditions": [
        {{"id": "POST1", "natural_language": "...", "formal_sketch": "..."}}
      ]
    }}
  ],
  "properties": [
    {{"id": "PROP1", "natural_language": "...", "formal_sketch": "...", "kind": "safety|liveness|ordering"}}
  ]
}}"""


# ─────────────────────────────────────────────────────────────
# Stage 2: Formal Specification (Dafny types + contracts, no bodies)
# ─────────────────────────────────────────────────────────────

STAGE2_SYSTEM = """\
You are a formal specification writer using Dafny.
Given structured requirements JSON, produce a Dafny file containing:
- Datatype or class definitions
- Method signatures with `requires` (preconditions) and `ensures` (postconditions)
- Ghost functions and predicates for invariants
- NO implementation bodies -- leave method bodies empty: {{ }}

This is the SPECIFICATION stage. You are defining WHAT, not HOW.

CRITICAL Dafny syntax rules:
- Sequence length: use `|s|` NOT `len(s)` — Dafny has no len() function
- `predicate Valid()` for boolean predicates — `reads this` is valid on predicates/functions
- `reads this` is FORBIDDEN on methods — only use on functions/predicates
- `function` for ghost functions, `method` for executable code
- `requires` for preconditions, `ensures` for postconditions
- `modifies this` for methods that mutate state
- Use `seq<T>` for sequences (preferred), `set<T>` for sets, `map<K,V>` for maps
- Generic types use ANGLE brackets: `seq<int>`, `array<int>` — NOT square brackets
- Use `old(expr)` in ensures clauses to refer to pre-state values
- Do NOT use primed variables (x') — Dafny uses `old(x)` instead
- Use `datatype` for algebraic data types (immutable)
- Use `class` for mutable objects with state
- Empty method bodies: `{{ }}` (curly braces with space)
- All methods on a class that access fields need `modifies this` (if mutating) or be functions (if read-only)
- Quantifier syntax: `forall i :: 0 <= i < N ==> P(i)` — NOT `forall i in 0..N`
- No chained comparisons: use `0 <= x && x <= 4` — NOT `0 <= x <= 4`
- Set membership in specs: `x in {{2, 4}}` or `x == 2 || x == 4` — use double braces in set literals
- Prefer `seq<int>` over `array<int>` — sequences are value types, simpler to verify
- Sequence update: `s[i := v]` returns a new sequence with position i changed to v
- Dafny has NO built-in `sum()`, `sorted()`, `len()`, `min()`, `max()`, `abs()` functions
- For counting/summing: write a recursive function (e.g., `function Count(s: seq<char>, c: char): int`)
- For length: use `|s|` NOT `len(s)`
- Membership negation: `x !in s` — NOT `x notin s` or `x not in s`
- Membership test: `x in s` — NOT `s.contains(x)` (sequences have no methods)
- Logical negation: `!expr` or `!(expr)` — NOT `not expr`
- Sequence append: `s + [x]` — NOT `s.append(x)` (sequences have no methods)
- Always include a `constructor()` with `ensures Valid()` and field initialization postconditions
- Statements in method/constructor bodies MUST end with a semicolon: `x := 0;` NOT `x := 0`

Here is an example of CORRECT Dafny class structure:

```
class Counter {{
  var count: int

  predicate Valid()
    reads this
  {{
    count >= 0
  }}

  constructor()
    ensures count == 0
    ensures Valid()
  {{
    count := 0;
  }}

  method Increment()
    requires Valid()
    modifies this
    ensures count == old(count) + 1
    ensures Valid()
  {{ }}

  method GetCount() returns (result: int)
    requires Valid()
    ensures result == count
  {{ }}
}}
```

Key syntax patterns shown above:
- Specs (requires/ensures/modifies/reads) go BETWEEN signature and body
- The opening brace of the body goes on its own AFTER all spec clauses
- Use `==` for equality in ensures/requires, NOT `=`
- Functions that reference `this` need `reads this` BEFORE the body
- Empty method bodies are just `{{ }}`

The output must pass `dafny resolve` (parsing + type-checking).
Do NOT include any implementation logic in method bodies.
Output ONLY the Dafny code. No markdown fences, no explanation."""

STAGE2_USER = """\
Convert the following structured requirements into a Dafny formal specification.
Include all type definitions, method signatures, preconditions, postconditions, \
and invariant predicates.
Do NOT implement any method bodies -- leave them as {{ }}.

Structured requirements:
{requirements_json}"""

STAGE2_RETRY_USER = """\
The previous specification attempt failed Dafny resolution (parsing/type-checking).

Previous attempt:
{previous_attempt}

Dafny errors:
{errors}

Fix the specification to pass `dafny resolve`. Do NOT add implementation logic.

Dafny reminders:
- Sequence length: `|s|` NOT `len(s)`
- `reads this` is FORBIDDEN on methods — only valid on functions/predicates
- Use `old(expr)` in ensures clauses, NOT primed variables (x')
- Empty method bodies: `{{ }}`
- Generic types use ANGLE brackets: `seq<int>`, `array<int>` — NOT square brackets
- Quantifier syntax: `forall i :: 0 <= i < N ==> P(i)` — NOT `forall i in 0..N`
- No chained comparisons: use `0 <= x && x <= 4` — NOT `0 <= x <= 4`
- Prefer `seq<int>` over `array<int>` — sequences are simpler to verify
- NO built-in `sum()`, `sorted()`, `min()`, `max()` — write recursive functions instead
- Membership negation: `x !in s` — NOT `notin` or `not in`
- Membership test: `x in s` — NOT `s.contains(x)`
- Logical negation: `!expr` — NOT `not expr`
- Sequence append: `s + [x]` — NOT `s.append(x)`
- Always include a `constructor()` with `ensures Valid()` and field initializations
- Statements in method/constructor bodies MUST end with semicolons: `x := 0;` NOT `x := 0`

Output the COMPLETE fixed Dafny file. No markdown fences."""


# ─────────────────────────────────────────────────────────────
# Stage 3: Implementation (fill in method bodies)
# ─────────────────────────────────────────────────────────────

STAGE3_SYSTEM = """\
You are a verified programming expert using Dafny.
Given a Dafny specification (types, signatures, pre/postconditions), your task is to:
1. Fill in method bodies with correct implementations
2. Add loop invariants for any loops
3. Add decreases clauses for loops and recursive calls
4. Add intermediate assertions to guide Z3 where needed
5. Add lemmas if the verifier needs help connecting proof steps

The output must pass `dafny verify` (full verification).

Guidelines:
- Preserve ALL existing requires, ensures, reads, and modifies clauses exactly
- Do not change method signatures or type definitions
- Do not weaken preconditions or strengthen postconditions
- Prefer simple implementations that are easy for Z3 to verify
- For sequences, prefer functional operations (seq + [x]) over imperative mutation
- Use calc blocks for complex proof chains if needed

CRITICAL Dafny syntax for implementation:
- Loops: use `while` with invariants — NOT `for i := start to end do`
  Example: `var i := 0; while i < |s| invariant ... {{ ... i := i + 1; }}`
- Sequence update: `s[i := v]` returns a new seq with index i set to v (preserves length)
- Sequence slice: `s[..i]`, `s[i..]`, `s[i..j]`
- Sequence concatenation: `s1 + s2`, `s + [x]`, `[x] + s`
- Quantifier syntax: `forall i :: 0 <= i < N ==> P(i)` — NOT `forall i in 0..N`
- No chained comparisons: use `0 <= x && x <= 4` — NOT `0 <= x <= 4`
- Generic types use ANGLE brackets: `seq<int>` — NOT `seq[int]`
- Assignment: `:=` (NOT `=`). Equality test: `==`
- If-else: `if cond {{ ... }} else {{ ... }}`
- Return: assign to named return variable, no explicit return statement needed

CRITICAL Dafny verification well-formedness:
- Dafny checks ensures clauses for well-formedness (e.g. array bounds) INDEPENDENTLY
- If an ensures clause indexes a seq like `ensures s[i] == v`, Dafny needs to prove \
`i < |s|` even if `ensures |s| == N` appears later
- ALWAYS add `ensures |s| == |old(s)|` BEFORE any ensures that indexes into s
- Similarly, add a length assertion at the start of method bodies after seq updates:
  `assert |stages| == 5;` helps the verifier establish bounds for subsequent code
- Loop invariants must include `|s| == N` when the loop body modifies s by functional update

LOOP INVARIANT COMPLETENESS (every loop needs ALL of these):
1. Counter bounds: `invariant 0 <= i <= |seq|`
2. Data relationship: what is true about elements already processed
   - Forward scan: `invariant forall k :: 0 <= k < i ==> P(k)`
   - Reverse scan: `invariant forall k :: i <= k < |seq| ==> P(k)`
3. Structure preservation: `invariant |seq| == old_length` if seq is modified
4. Class invariant: `invariant Valid()` if the method has `ensures Valid()`
Missing ANY category will cause verification failure.

HELPER LEMMA STRATEGY (critical for verification):
When a postcondition involves sorted order, multiset equality, or quantifiers \
over modified sequences, write helper lemmas BEFORE the method that needs them.
Pattern for sorted insertion:
```
lemma InsertPreservesSorted(s: seq<int>, x: int, pos: int)
  requires forall i, j :: 0 <= i < j < |s| ==> s[i] <= s[j]
  requires 0 <= pos <= |s|
  requires forall k :: 0 <= k < pos ==> s[k] <= x
  requires forall k :: pos <= k < |s| ==> x <= s[k]
  ensures forall i, j :: 0 <= i < j < |s[..pos] + [x] + s[pos..]| ==> \
(s[..pos] + [x] + s[pos..])[i] <= (s[..pos] + [x] + s[pos..])[j]
{{}}
```
Call the lemma just BEFORE the assignment that needs the proof:
```
InsertPreservesSorted(elements, x, i);
elements := elements[..i] + [x] + elements[i..];
```
Write similar lemmas for removal, multiset preservation, and modular arithmetic.
Ghost variable snapshots help: `ghost var oldSeq := elements;` before mutation.

Dafny has NO built-in sort(), min(), max(), or similar utility functions.
You must implement any needed logic inline using loops or recursion.
For inserting into a sorted sequence, use a loop to find the insertion point,
then concatenate: `elements[..i] + [x] + elements[i..]`

Output ONLY the complete Dafny file. No markdown fences, no explanation."""

STAGE3_USER = """\
Implement all method bodies in the following Dafny specification.
Add loop invariants, decreases clauses, and assertions as needed for verification.

Specification:
{specification_dfy}"""


# ─────────────────────────────────────────────────────────────
# Stage 4: Proof Discharge (retry on verification failure)
# ─────────────────────────────────────────────────────────────

STAGE4_RETRY_USER = """\
The previous implementation attempt failed Dafny verification.

Previous attempt:
{previous_attempt}

Dafny verification errors:
{errors}

Fix the implementation to pass `dafny verify`. Common issues and fixes:
- Missing loop invariant: EVERY loop needs (1) counter bounds, (2) data relationship \
for processed elements, (3) structure preservation like `|seq| == old_len`, (4) `Valid()` \
if the method ensures it
- Missing decreases clause (termination proof)
- Postcondition unprovable: write a helper lemma that proves the property, \
then call the lemma just BEFORE the assignment
- Off-by-one errors in sequence/array indexing

Verification strategy when postconditions fail:
1. If "postcondition could not be proved" on sorted/ordered ensures: \
add a helper lemma like `InsertPreservesSorted(s, x, pos)` with the \
preconditions that hold at that point, call it before the mutation
2. If "index out of range" in a loop invariant: add `invariant |seq| == N` \
to the loop and `assert |seq| == N;` after any sequence update
3. If quantifier-based ensures fails: add `ghost var oldSeq := seq;` before \
mutation, then assert the quantifier with explicit index reasoning
4. For modular arithmetic (% N): write helper lemmas for the properties you need

Dafny syntax reminders:
- Loops: use `while` with invariants — NOT `for i := start to end do`
- Quantifiers: `forall i :: 0 <= i < N ==> P(i)` — NOT `forall i in 0..N`
- No chained comparisons: `0 <= x && x <= 4` — NOT `0 <= x <= 4`
- Sequence update: `s[i := v]` returns new seq with position i changed

Preserve all requires/ensures clauses exactly. Do NOT weaken specifications.
Output the COMPLETE fixed Dafny file. No markdown fences."""


STAGE4_RETRY_USER_WITH_MENTOR = """\
IMPORTANT GUIDANCE FROM VERIFICATION MENTOR:
{mentor_directive}

---

The previous implementation attempt failed Dafny verification.

Previous attempt:
{previous_attempt}

Dafny verification errors:
{errors}

Follow the mentor's guidance above. Fix the implementation to pass `dafny verify`.

Key verification strategies:
- EVERY loop needs: (1) counter bounds, (2) data relationship for processed elements, \
(3) structure preservation `|seq| == N`, (4) `Valid()` if method ensures it
- For unprovable postconditions: write a helper lemma, call it before the mutation
- For sorted insertion: lemma proving `InsertPreservesSorted(s, x, pos)`, called before concat
- For modular arithmetic: write explicit mod-property lemmas
- Ghost snapshots: `ghost var oldSeq := seq;` before mutation helps quantifier reasoning

Dafny syntax reminders:
- Loops: use `while` with invariants — NOT `for i := start to end do`
- Quantifiers: `forall i :: 0 <= i < N ==> P(i)` — NOT `forall i in 0..N`
- No chained comparisons: `0 <= x && x <= 4` — NOT `0 <= x <= 4`
- Sequence update: `s[i := v]` returns new seq with position i changed

Preserve all requires/ensures clauses exactly. Do NOT weaken specifications.
Output the COMPLETE fixed Dafny file. No markdown fences."""


# ─────────────────────────────────────────────────────────────
# Mentor: Diagnostic advisor for stuck retry loops
# ─────────────────────────────────────────────────────────────

MENTOR_SYSTEM = """\
You are a Dafny verification mentor. A programmer is stuck trying to verify \
a Dafny program. They keep getting the same or similar errors and are not \
making progress.

Your job is NOT to write code. Your job is to DIAGNOSE the strategic problem \
and give a SHORT directive (1-3 sentences) that will help the programmer \
take a fundamentally different approach.

Common stuck patterns in Dafny verification:
- The postcondition needs a LEMMA to help Z3 connect the implementation to the spec
- The loop invariant is too weak and does not imply the postcondition
- The model needs to provide a WITNESS (assert exists) before the verifier will accept an existential postcondition
- An assertion needs INTERMEDIATE STEPS -- Z3 cannot make the leap in one step
- The implementation strategy is wrong for this spec (e.g., iterative when recursive would verify more easily)
- The quantifier pattern causes Z3 trigger issues (matching loops)

If the specification itself is the problem (overly complex postconditions, existential \
quantifiers that are hard to witness, specifications the programmer cannot reasonably \
prove), you may recommend ROLLING BACK to the specification stage.

Format your response as ONE of:
- ADVICE: <1-3 sentence strategic directive>
- ROLLBACK TO STAGE 2: <guidance for rewriting the specification>

Use ROLLBACK only when the specification is fundamentally too complex for the prover. \
Use ADVICE for all other situations (wrong approach, missing lemma, weak invariant, etc.).

Do NOT write Dafny code. Do NOT repeat the error message.

Example good ADVICE directives:
- "ADVICE: The existential postcondition needs a concrete witness. After the loop, add an assert naming the specific index where x was placed."
- "ADVICE: The loop invariant only tracks elements before index i but the postcondition requires the full sorted sequence. Strengthen the invariant to also describe elements after index i."
- "ADVICE: Split the proof into two lemmas: one proving sortedness is preserved after concatenation, another proving the element count is correct."
- "ADVICE: The verified count dropped — your last change broke something. Revert to the approach that had more conditions passing and focus only on the remaining failure."

Example good ROLLBACK directive:
- "ROLLBACK TO STAGE 2: The ensures clause uses an existential quantifier to assert membership. Replace `ensures exists i :: 0 <= i < |elements| && elements[i] == x` with the simpler `ensures x in elements`. Also split compound postconditions into separate ensures clauses.\""""

MENTOR_USER = """\
A programmer is stuck verifying this Dafny specification:

ORIGINAL SPECIFICATION:
{original_spec}

ATTEMPT HISTORY:
{attempt_summary}

STUCK PATTERN: {stuck_category}
DETAILS: {stuck_detail}
VERIFIED COUNTS OVER TIME: [{verified_trend}]

Provide your response as either ADVICE: or ROLLBACK TO STAGE 2: (see system prompt for format). \
Do NOT write code. Explain what conceptual approach they should try."""


# ─────────────────────────────────────────────────────────────
# Stage 2: Rollback (mentor-guided spec rewrite)
# ─────────────────────────────────────────────────────────────

STAGE2_ROLLBACK_USER = """\
A verification mentor has reviewed the previous specification and determined it \
contains patterns that are too complex to verify. The mentor's guidance:

{mentor_guidance}

Previous specification that was too complex:
{previous_spec}

Original requirements:
{requirements_json}

Rewrite the specification following the mentor's guidance. Prefer SIMPLER \
postconditions that are easier to verify:
- Use `x in seq` instead of `ensures exists i :: ... && seq[i] == x`
- Keep postconditions to single properties, not compound conditions
- Avoid nested quantifiers where possible
- Use multiset(seq) for element-count reasoning instead of manual counting

CRITICAL Dafny syntax rules:
- Sequence length: use `|s|` NOT `len(s)`
- `reads this` is FORBIDDEN on methods — only valid on functions/predicates
- Use `old(expr)` in ensures clauses, NOT primed variables (x')
- Empty method bodies: `{{ }}`
- Generic types use ANGLE brackets: `seq<int>` — NOT `seq[int]`
- Quantifier syntax: `forall i :: 0 <= i < N ==> P(i)` — NOT `forall i in 0..N`
- No chained comparisons: use `0 <= x && x <= 4` — NOT `0 <= x <= 4`
- Prefer `seq<int>` over `array<int>` — sequences are simpler to verify

Output the COMPLETE fixed Dafny specification. No markdown fences, no explanation."""


# ─────────────────────────────────────────────────────────────
# Stage 1: Light mode constraint (max 3 operations)
# ─────────────────────────────────────────────────────────────

STAGE1_LIGHT_SUFFIX = """

IMPORTANT: Identify at most 3 top-level operations. Do NOT decompose algorithms \
into sub-operations (e.g., do NOT split 'sort' into 'find_position' + 'insert' + \
'shift'). Each operation should correspond to a complete user-facing action."""


# ─────────────────────────────────────────────────────────────
# Iterative mode prompts (generate spec+impl in one pass)
# ─────────────────────────────────────────────────────────────

ITERATIVE_SYSTEM = """\
You are an expert Dafny programmer. Given natural language requirements, \
write a complete Dafny program with:
- Class or datatype definitions
- Method signatures with requires (preconditions) and ensures (postconditions)
- Complete method bodies with loop invariants and decreases clauses
- All code necessary to pass `dafny verify`

Output ONLY the Dafny code. No markdown fences, no explanation."""

ITERATIVE_USER = """\
Write a complete Dafny program implementing the following requirements. \
Include all type definitions, method signatures with requires/ensures, \
and complete method bodies with loop invariants and decreases clauses.

Requirements:
{requirements_text}"""

ITERATIVE_RETRY = """\
The previous Dafny code failed verification.

Previous code:
{previous_code}

Dafny errors:
{errors}

Fix all errors and output the COMPLETE corrected Dafny file.
Do NOT remove or weaken any specifications — preserve all requires/ensures clauses.
Output ONLY the Dafny code. No markdown fences, no explanation."""


# ─────────────────────────────────────────────────────────────
# Stage 3: Minimal system prompt (no Dafny syntax reference)
# ─────────────────────────────────────────────────────────────

STAGE3_SYSTEM_MINIMAL = """\
You are a verified programming expert using Dafny.
Given a Dafny specification (types, signatures, pre/postconditions), your task is to:
1. Fill in method bodies with correct implementations
2. Add loop invariants for any loops
3. Add decreases clauses for loops and recursive calls
4. Add intermediate assertions to guide Z3 where needed
5. Add lemmas if the verifier needs help connecting proof steps

The output must pass `dafny verify` (full verification).

Guidelines:
- Preserve ALL existing requires, ensures, reads, and modifies clauses exactly
- Do not change method signatures or type definitions
- Do not weaken preconditions or strengthen postconditions
- Prefer simple implementations that are easy for Z3 to verify
- For sequences, prefer functional operations (seq + [x]) over imperative mutation
- Use calc blocks for complex proof chains if needed

Output ONLY the complete Dafny file. No markdown fences, no explanation."""


def build_stage3_system(include_reference: bool = True) -> str:
    """Return the Stage 3 system prompt, optionally without Dafny syntax reference."""
    if include_reference:
        return STAGE3_SYSTEM
    return STAGE3_SYSTEM_MINIMAL


# ─────────────────────────────────────────────────────────────
# Temperature strategies for retries
# ─────────────────────────────────────────────────────────────

RETRY_TEMPERATURES = [0.2, 0.3, 0.5, 0.7, 0.7, 0.7]


def get_retry_temperature(attempt: int) -> float:
    """Static fallback: increasing temperature on retries."""
    idx = min(attempt, len(RETRY_TEMPERATURES) - 1)
    return RETRY_TEMPERATURES[idx]


# Adaptive temperature mapping: stuck category -> temperature
# Rationale for each:
#   REPEATING_ERROR: same error = same approach. Max diversity to escape.
#   VERIFIED_REGRESSION: previous was better. Be precise about reverting.
#   SPEC_DRIFT: model is flailing and removing specs. Tighten up.
#   SPEC_TOO_COMPLEX: needs a creative approach, but not random.
#   OSCILLATING: stuck between two approaches, need to break out.
ADAPTIVE_TEMPERATURES = {
    "repeating_error": 0.9,
    "verified_regression": 0.2,
    "spec_drift": 0.2,
    "spec_too_complex": 0.7,
    "oscillating": 0.8,
}

# Temperature for when no stuck pattern is detected (making progress)
ADAPTIVE_DEFAULT_TEMP = 0.4

# Temperature for best-of-N fresh samples (moderate — want diversity but not garbage)
BEST_OF_N_TEMP = 0.5


def get_adaptive_temperature(attempt: int, stuck_category: str | None) -> float:
    """Adaptive temperature based on stuck detection diagnosis.

    Uses the stuck category to choose temperature:
    - Repeating error -> high temp (escape the rut)
    - Verified regression -> low temp (previous was better, be precise)
    - Spec drift -> low temp (stop flailing)
    - Spec too complex -> medium-high (need creative approach)
    - Oscillating -> high temp (break the cycle)
    - No stuck pattern -> moderate (making progress, stay the course)
    """
    if stuck_category is None:
        return ADAPTIVE_DEFAULT_TEMP
    return ADAPTIVE_TEMPERATURES.get(stuck_category, get_retry_temperature(attempt))
