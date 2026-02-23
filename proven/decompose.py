"""Deterministic spec decomposition: rewrite hard-to-prove Dafny patterns.

Operates on the Dafny specification text *before* implementation (Stage 3).
Each rewrite is a pure function: code in, (code, changes) out.
No LLM calls — these are regex/AST-level transformations.
"""

from __future__ import annotations

import re


def fix_generic_brackets(code: str) -> tuple[str, list[str]]:
    """Fix square-bracket generic syntax to angle-bracket syntax.

    LLMs frequently write array[int], seq[int], map[int, string], set[int],
    multiset[int] etc. using square brackets (Java/Go style).
    Dafny requires angle brackets: array<int>, seq<int>, map<int, string>, etc.

    Only converts when the bracket content is a type name (int, nat, bool,
    string, char, real, object, or capitalized identifier), NOT when it looks
    like array indexing (e.g., seq[i], elements[0]).
    """
    changes: list[str] = []

    # Type argument: known Dafny base types or capitalized identifiers (type params/classes)
    _type = r'(?:int|nat|bool|real|string|char|object|ORDINAL|[A-Z]\w*)'
    _type_arg = rf'{_type}(?:\s*,\s*{_type})*'
    pattern = rf'\b(array|seq|map|set|multiset|imap|iset)\[({_type_arg})\]'

    def replacer(m: re.Match) -> str:
        type_name = m.group(1)
        type_args = m.group(2)
        changes.append(
            f"Fixed generic syntax: `{type_name}[{type_args}]` -> `{type_name}<{type_args}>`"
        )
        return f"{type_name}<{type_args}>"

    fixed = re.sub(pattern, replacer, code)
    return fixed, changes


def fix_quantifier_range(code: str) -> tuple[str, list[str]]:
    """Fix Python/Rust-style range quantifiers to Dafny syntax.

    LLMs write: forall i in 0..N :: P(i)
    Dafny needs: forall i :: 0 <= i < N ==> P(i)

    Also handles: forall i in 0..|seq| :: P(i)
    """
    changes: list[str] = []

    # Pattern: forall VAR in [START..END] or forall VAR in START..END
    # with :: or : or | separator before body
    # Handles: 0..4, 0..|seq|, 0..stage-1, [0..4], [0..|seq|]
    pattern = r'forall\s+(\w+)\s+in\s+\[?(\w+)\.\.([\w|+\-]+)\]?\s*(?:::|:|(?:\|))\s*(.+)'

    def replacer(m: re.Match) -> str:
        var = m.group(1)
        start = m.group(2)
        end = m.group(3)
        body = m.group(4)
        changes.append(
            f"Fixed quantifier range: `forall {var} in {start}..{end}` "
            f"-> `forall {var} :: {start} <= {var} < {end} ==> ...`"
        )
        return f"forall {var} :: {start} <= {var} < {end} ==> {body}"

    fixed = re.sub(pattern, replacer, code)
    return fixed, changes


def fix_sequence_append(code: str) -> tuple[str, list[str]]:
    """Fix Python-style .append(x) to Dafny sequence concatenation.

    LLMs write: seq.append(x), old(seq).append(x)
    Dafny needs: seq + [x], old(seq) + [x]

    Also handles: elements.append(x), elems.append(x), etc.
    """
    changes: list[str] = []

    # Match: identifier.append(expr) or old(identifier).append(expr)
    # Capture the receiver and the argument
    pattern = r'((?:old\([^)]+\)|\w+))\.append\(([^)]+)\)'

    def replacer(m: re.Match) -> str:
        receiver = m.group(1)
        arg = m.group(2)
        changes.append(
            f"Fixed sequence append: `{receiver}.append({arg})` -> `{receiver} + [{arg}]`"
        )
        return f"{receiver} + [{arg}]"

    fixed = re.sub(pattern, replacer, code)
    return fixed, changes


def fix_membership_negation(code: str) -> tuple[str, list[str]]:
    """Fix Python-style 'notin' and 'not in' to Dafny '!in'.

    LLMs write: x notin seq, x not in seq
    Dafny needs: x !in seq
    """
    changes: list[str] = []

    # 'notin' as a single keyword (no space)
    def replace_notin(m: re.Match) -> str:
        changes.append(f"Fixed membership negation: `notin` -> `!in`")
        return '!in'

    fixed = re.sub(r'\bnotin\b', replace_notin, code)

    # 'not in' as two words (but not inside 'cannot in' etc.)
    # Only match when preceded by a value expression (identifier, ), |, etc.)
    def replace_not_in(m: re.Match) -> str:
        changes.append(f"Fixed membership negation: `not in` -> `!in`")
        return '!in'

    fixed = re.sub(r'\bnot\s+in\b', replace_not_in, fixed)
    return fixed, changes


def fix_contains_method(code: str) -> tuple[str, list[str]]:
    """Fix Java/Python-style .contains(x) to Dafny membership operator.

    LLMs write: seq.contains(x), old(seq).contains(x)
    Dafny needs: x in seq, x in old(seq)
    """
    changes: list[str] = []

    # Match: receiver.contains(arg) where receiver is identifier or old(...)
    pattern = r'((?:old\([^)]+\)|\w+))\.contains\(([^)]+)\)'

    def replacer(m: re.Match) -> str:
        receiver = m.group(1)
        arg = m.group(2)
        changes.append(
            f"Fixed contains method: `{receiver}.contains({arg})` -> `{arg} in {receiver}`"
        )
        return f"{arg} in {receiver}"

    fixed = re.sub(pattern, replacer, code)
    return fixed, changes


def fix_logical_not(code: str) -> tuple[str, list[str]]:
    """Fix Python-style 'not' to Dafny '!' for logical negation.

    LLMs write: not expr, not (expr)
    Dafny needs: !expr, !(expr)

    Must run AFTER fix_membership_negation (which handles 'not in').
    """
    changes: list[str] = []

    # Pattern 1: not (expr) -> !(expr) — parenthesized, clear boundaries
    def replace_paren(m: re.Match) -> str:
        expr = m.group(1)
        changes.append(f"Fixed logical negation: `not {expr}` -> `!{expr}`")
        return f"!{expr}"

    fixed = re.sub(r'\bnot\s+(?!in\b)(\([^)]*\))', replace_paren, code)

    # Pattern 2: not expr OP ... -> !(expr) OP ... where OP is ==>, &&, ||, etc.
    def replace_before_op(m: re.Match) -> str:
        expr = m.group(1).strip()
        op = m.group(2)
        changes.append(f"Fixed logical negation: `not {expr}` -> `!({expr})`")
        return f"!({expr}){op}"

    fixed = re.sub(
        r'\bnot\s+(?!in\b)(.+?)(\s*(?:==>|<==|<==>|&&|\|\|))',
        replace_before_op, fixed
    )

    # Pattern 3: not expr$ -> !(expr) at end of line (no trailing operator)
    def replace_eol(m: re.Match) -> str:
        expr = m.group(1).strip()
        changes.append(f"Fixed logical negation: `not {expr}` -> `!({expr})`")
        return f"!({expr})"

    fixed = re.sub(r'\bnot\s+(?!in\b)(.+)$', replace_eol, fixed, flags=re.MULTILINE)

    return fixed, changes


def fix_builtin_functions(code: str) -> tuple[str, list[str]]:
    """Flag/fix Python built-in function calls that don't exist in Dafny.

    LLMs write: len(s), sorted(s), sum(...), abs(x), min(a,b), max(a,b)
    Dafny uses: |s| for length, and has no built-in sort/sum/min/max.

    - len(s) -> |s| (auto-fix)
    - Others: commented out with a TODO (can't auto-fix meaningfully)
    """
    changes: list[str] = []

    # len(expr) -> |expr| — safe auto-fix
    def replace_len(m: re.Match) -> str:
        arg = m.group(1)
        changes.append(f"Fixed length call: `len({arg})` -> `|{arg}|`")
        return f"|{arg}|"

    fixed = re.sub(r'\blen\(([^)]+)\)', replace_len, code)

    # Flag sum(), sorted(), abs(), min(), max() — can't auto-fix
    flagged_builtins = re.findall(
        r'\b(sum|sorted)\s*\(', fixed
    )
    for fn in flagged_builtins:
        changes.append(
            f"WARNING: `{fn}()` is not a Dafny built-in. "
            f"Needs manual rewrite as a recursive function or loop."
        )

    return fixed, changes


def fix_missing_semicolons(code: str) -> tuple[str, list[str]]:
    """Add missing semicolons to statements in Dafny 4.x.

    Dafny 4.x requires trailing semicolons on assignment statements,
    variable declarations, return, and print statements inside
    method/constructor/lemma bodies.

    LLMs trained on older Dafny or on pseudocode often omit them.
    This is safe to apply broadly — these statement patterns only
    appear in imperative contexts where semicolons are required.
    """
    changes: list[str] = []
    lines = code.splitlines()
    new_lines = []

    # Patterns for statements that need semicolons
    stmt_patterns = [
        # Assignment or var declaration with :=
        re.compile(r'^\s*(?:ghost\s+)?(?:var\s+)?\w[\w.]*(?:\s*,\s*\w[\w.]*)*\s*:='),
        # Return statement (with or without value)
        re.compile(r'^\s*return\b'),
        # Print statement
        re.compile(r'^\s*print\b'),
    ]

    # Characters that indicate the line continues onto the next line
    continuation_endings = ('(', ',', '+', '-', '&&', '||', '==>', '<==',
                            '<==>',  '==>>', '::', '|', '\\')

    for line in lines:
        stripped = line.rstrip()
        trimmed = stripped.strip()

        # Skip lines that don't need processing
        if (not trimmed or
                trimmed.startswith('//') or
                trimmed.startswith('/*') or
                trimmed.startswith('*') or
                trimmed.endswith(';') or
                trimmed.endswith('{') or
                trimmed.endswith('}')):
            new_lines.append(line)
            continue

        # Check if it matches a statement pattern
        needs_semi = any(p.match(trimmed) for p in stmt_patterns)
        if not needs_semi:
            new_lines.append(line)
            continue

        # Don't add if line ends with a continuation character
        if any(trimmed.endswith(c) for c in continuation_endings):
            new_lines.append(line)
            continue

        new_lines.append(stripped + ';')
        changes.append(f"Added missing semicolon: `{trimmed}`")

    return '\n'.join(new_lines), changes


def fix_dafny_syntax(code: str) -> tuple[str, list[str]]:
    """Run syntax-level fixes that apply before dafny resolve.

    These fix common LLM-generated syntax errors that prevent parsing.
    Safe to apply at Stage 2 (before resolve) unlike semantic rewrites
    which apply between Stage 2 and 3.
    """
    all_changes: list[str] = []

    code, changes = fix_generic_brackets(code)
    all_changes.extend(changes)

    code, changes = fix_quantifier_range(code)
    all_changes.extend(changes)

    code, changes = strip_invalid_reads(code)
    all_changes.extend(changes)

    code, changes = fix_sequence_append(code)
    all_changes.extend(changes)

    code, changes = fix_contains_method(code)
    all_changes.extend(changes)

    code, changes = fix_membership_negation(code)
    all_changes.extend(changes)

    code, changes = fix_logical_not(code)
    all_changes.extend(changes)

    code, changes = fix_builtin_functions(code)
    all_changes.extend(changes)

    code, changes = fix_missing_semicolons(code)
    all_changes.extend(changes)

    return code, all_changes


def add_quantifier_bounds(code: str) -> tuple[str, list[str]]:
    """Add missing index bounds to existentially quantified variables.

    When ``exists i :: ... collection[i] ...`` lacks ``0 <= i < |collection|``,
    Dafny reports index-out-of-range during well-formedness checking.

    Only applies to existential quantifiers — universals typically carry
    bounds as part of their implication antecedent already.
    """
    changes: list[str] = []
    lines = code.splitlines()
    new_lines = []

    for line in lines:
        # Match: ... exists VAR [: TYPE] :: BODY (single quantified variable)
        m = re.search(
            r'\bexists\s+(\w+)\s*(?::\s*\w+)?\s*::\s*(.+)',
            line,
        )
        if not m:
            new_lines.append(line)
            continue

        var = m.group(1)
        body = m.group(2)

        # Find collections indexed by this variable: IDENT[VAR] or IDENT[VAR+/-N]
        index_uses = re.findall(
            r'(\w+)\[' + re.escape(var) + r'(?:[+\-]\d+)?\]', body
        )
        collections = set(index_uses)

        if not collections:
            new_lines.append(line)
            continue

        # Check which collections lack explicit bounds
        target_coll = None
        for coll in collections:
            has_lower = re.search(rf'0\s*<=\s*{re.escape(var)}\b', body)
            has_upper = re.search(
                rf'\b{re.escape(var)}\s*<\s*\|{re.escape(coll)}\|', body
            )
            if not has_lower or not has_upper:
                target_coll = coll
                break

        if target_coll is None:
            new_lines.append(line)
            continue

        # Insert bounds at start of existential body
        bounds = f"0 <= {var} < |{target_coll}|"
        new_body = f"{bounds} && {body}"
        new_line = line[: m.start(2)] + new_body + line[m.end(2) :]

        new_lines.append(new_line)
        changes.append(
            f"Added missing index bounds `{bounds}` to existential "
            f"quantifier over `{target_coll}`"
        )

    return '\n'.join(new_lines), changes


def _normalize_quantifier_vars(expr: str) -> str:
    """Alpha-normalize quantified variable names for structural comparison.

    ``forall i, j :: P(i, j)`` becomes ``forall _q0, _q1 :: P(_q0, _q1)``
    so that two expressions differing only in variable names compare equal.
    """

    def replacer(m: re.Match) -> str:
        quant = m.group(1)
        vars_str = m.group(2)
        body = m.group(3)

        vars_list = [v.strip() for v in vars_str.split(',')]
        mapping = {v: f"_q{idx}" for idx, v in enumerate(vars_list)}

        new_vars = ', '.join(mapping.values())
        new_body = body
        # Replace longest variable names first to avoid partial substitution
        for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
            new_body = re.sub(rf'\b{re.escape(old)}\b', new, new_body)

        return f"{quant} {new_vars} :: {new_body}"

    return re.sub(
        r'\b(forall|exists)\s+([\w]+(?:\s*,\s*[\w]+)*)\s*::\s*(.+)',
        replacer,
        expr,
    )


def simplify_redundant_ensures(code: str) -> tuple[str, list[str]]:
    """Simplify ensures clauses that are redundant with Valid().

    Part 1: Remove ensures clauses whose body matches Valid()'s body
            (modulo quantifier variable renaming).
    Part 2: Replace compound existentials asserting sorted insertion position
            with simple membership, when Valid() already ensures sorted order.

    Both simplifications reduce proof burden without weakening the spec.
    """
    changes: list[str] = []

    # Extract Valid() predicate body
    valid_match = re.search(
        r'predicate\s+Valid\(\)\s*\n\s*reads\s+this\s*\n\s*\{([^}]+)\}',
        code,
        re.DOTALL,
    )
    if not valid_match:
        return code, []

    valid_body_raw = valid_match.group(1).strip()
    # Strip comments
    valid_body_clean = re.sub(r'//[^\n]*', '', valid_body_raw).strip()
    valid_normalized = ' '.join(_normalize_quantifier_vars(valid_body_clean).split())

    # --- Part 1: Remove ensures that duplicate Valid() body ---
    # Two-pass: first identify methods with ensures Valid(), then remove duplicates
    lines = code.splitlines()
    methods_with_valid_p1: set[int] = set()
    current_method_p1: int | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'\b(method|constructor|lemma)\b', stripped):
            current_method_p1 = i
        elif stripped.startswith('{') and current_method_p1 is not None:
            current_method_p1 = None
        if stripped == 'ensures Valid()' and current_method_p1 is not None:
            methods_with_valid_p1.add(current_method_p1)

    new_lines: list[str] = []
    current_method_p1 = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(r'\b(method|constructor|lemma)\b', stripped):
            current_method_p1 = i

        # Check if this ensures clause duplicates Valid()
        if current_method_p1 in methods_with_valid_p1:
            ensures_m = re.match(r'\s*ensures\s+(.*)', stripped)
            if ensures_m:
                ensures_body = ensures_m.group(1).strip()
                ensures_normalized = ' '.join(
                    _normalize_quantifier_vars(ensures_body).split()
                )
                if ensures_normalized == valid_normalized:
                    changes.append(
                        f"Removed ensures clause redundant with Valid(): "
                        f"`ensures {ensures_body[:70]}...`"
                    )
                    continue

        new_lines.append(line)

    code = '\n'.join(new_lines)

    # --- Part 2: Simplify compound existentials with adjacency checks ---
    # Only if Valid() asserts sorted order on some collection
    sort_match = re.search(
        r'forall\s+\w+\s*,\s*\w+\s*::\s*'
        r'0\s*<=\s*\w+\s*<\s*\w+\s*<\s*\|(\w+)\|\s*==>\s*'
        r'\1\[\w+\]\s*<=\s*\1\[\w+\]',
        valid_body_clean,
    )
    if not sort_match:
        return code, changes

    sorted_coll = sort_match.group(1)

    # Two-pass: first identify which methods have ensures Valid()
    # (can appear before or after the existential in ensures order)
    lines = code.splitlines()
    methods_with_valid: set[int] = set()  # line indices of method declarations
    current_method_line: int | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'\b(method|constructor|lemma)\b', stripped):
            current_method_line = i
        elif stripped.startswith('{') and current_method_line is not None:
            current_method_line = None
        if stripped == 'ensures Valid()' and current_method_line is not None:
            methods_with_valid.add(current_method_line)

    # Second pass: simplify existentials in methods that have ensures Valid()
    new_lines = []
    current_method_line = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(r'\b(method|constructor|lemma)\b', stripped):
            current_method_line = i

        # Detect existential with adjacency indexing (collection[var+/-N])
        if (
            current_method_line in methods_with_valid
            and 'exists' in stripped
            and stripped.startswith('ensures')
            and re.search(r'\w+\[\w+[+-]\d+\]', stripped)
        ):
            # Extract: collection[var] == val
            membership = re.search(
                rf'{re.escape(sorted_coll)}\[\w+\]\s*==\s*(\w+)', stripped
            )
            if membership:
                val = membership.group(1)
                indent = line[: len(line) - len(line.lstrip())]
                new_lines.append(f"{indent}ensures {val} in {sorted_coll}")
                changes.append(
                    f"Simplified compound existential to "
                    f"`{val} in {sorted_coll}` "
                    f"(adjacency checks implied by Valid() sorted order)"
                )
                continue

        new_lines.append(line)

    return '\n'.join(new_lines), changes


def augment_constructor_body(code: str) -> tuple[str, list[str]]:
    """Add missing field assignments to constructor bodies.

    When a constructor has ``ensures FIELD == VALUE`` but the body doesn't
    assign FIELD, add the missing assignment.  Handles simple patterns:
      - ensures field == LITERAL   (0, false, true, [], {}, multiset{})
      - ensures this.field == PARAM
    Skips dotted-path ensures like ``buffer.Length == capacity``.
    """
    changes: list[str] = []

    # Match constructor header + body: constructor(...) spec { body }
    ctor_pattern = re.compile(
        r'(\bconstructor\b[^{]*)'  # header: signature + spec clauses
        r'\{([^}]*)\}',  # body between first { }
        re.DOTALL,
    )

    def process_ctor(m: re.Match) -> str:
        header = m.group(1)
        body = m.group(2)

        # Extract ensures field == value pairs from header
        ensures_pairs: list[tuple[str, str]] = []
        for em in re.finditer(
            r'ensures\s+(this\.)?(\w+)\s*==\s*'
            r'(-?\d+|false|true|\w+|\[\]|\{\}|multiset\{\})',
            header,
        ):
            this_prefix = em.group(1) or ''
            field = em.group(2)
            value = em.group(3)
            ensures_pairs.append((this_prefix + field, value))

        # Check which fields are missing from body
        missing: list[tuple[str, str]] = []
        for field, value in ensures_pairs:
            field_base = field.replace('this.', '')
            if not re.search(
                rf'\b(?:this\.)?{re.escape(field_base)}\s*:=', body
            ):
                missing.append((field, value))

        if not missing:
            return m.group(0)

        # Determine indent from existing body lines
        indent = '    '  # default
        for bl in body.split('\n'):
            bl_stripped = bl.lstrip()
            if bl_stripped and not bl_stripped.startswith('//'):
                indent = bl[: len(bl) - len(bl_stripped)]
                break

        # Add missing assignments at end of body
        additions = []
        for field, value in missing:
            additions.append(f"{indent}{field} := {value};")
            changes.append(
                f"Added missing constructor assignment: `{field} := {value};`"
            )

        new_body = body.rstrip() + '\n' + '\n'.join(additions) + '\n'
        # Preserve indent of closing brace
        close_indent = indent[:-2] if len(indent) >= 2 else ''
        new_body += close_indent
        return f"{header}{{{new_body}}}"

    new_code = ctor_pattern.sub(process_ctor, code)
    return new_code, changes


def fix_array_class_spec(code: str) -> tuple[str, list[str]]:
    """Fix common array-class specification gaps.

    LLMs often forget two critical Dafny requirements for array-based classes:

    1. Valid() must include ``array.Length == capacity`` so methods can prove
       array accesses are in-bounds (e.g., ``tail < capacity`` + ``capacity ==
       buffer.Length`` implies ``tail < buffer.Length``).

    2. Methods that modify array contents need ``modifies this, array_field``
       not just ``modifies this`` (Dafny treats arrays as separate heap objects).

    Detects these patterns by finding classes with ``array<T>`` fields and an
    int/nat field used as the array capacity in Valid().
    """
    changes: list[str] = []

    # Detect array field and capacity field
    array_field_m = re.search(r'var\s+(\w+)\s*:\s*array<', code)
    if not array_field_m:
        return code, []
    array_field = array_field_m.group(1)

    # Find Valid() body
    valid_m = re.search(
        r'(predicate\s+Valid\(\)\s*\n\s*reads\s+this\s*\n\s*\{)([^}]+)(\})',
        code,
        re.DOTALL,
    )
    if not valid_m:
        return code, []
    valid_prefix = valid_m.group(1)
    valid_body = valid_m.group(2)
    valid_suffix = valid_m.group(3)

    # Find capacity field: a field used in Valid() as an upper bound
    # e.g., ``size <= capacity`` or ``head < capacity``
    capacity_candidates = re.findall(r'<\s*(\w+)', valid_body)
    capacity_candidates += re.findall(r'<=\s*(\w+)', valid_body)
    # Also check constructor ensures for array.Length == field
    ctor_cap_m = re.search(
        rf'{re.escape(array_field)}\.Length\s*==\s*(\w+)', code
    )
    if ctor_cap_m:
        capacity_candidates.append(ctor_cap_m.group(1))

    # Filter to actual class fields
    field_names = set(re.findall(r'var\s+(\w+)\s*:', code))
    capacity_field = None
    for c in capacity_candidates:
        if c in field_names:
            capacity_field = c
            break

    if not capacity_field:
        return code, []

    # --- Fix 1: Add array.Length == capacity to Valid() if missing ---
    length_check = f'{array_field}.Length == {capacity_field}'
    if length_check not in valid_body:
        # Also need reads this, array_field for Valid() to access array.Length
        valid_body_stripped = valid_body.rstrip()
        # Determine indent
        indent = '    '
        for line in valid_body.split('\n'):
            ls = line.lstrip()
            if ls:
                indent = line[: len(line) - len(ls)]
                break

        # Prepend the length check as first conjunct
        new_valid_body = f"\n{indent}{length_check} &&{valid_body_stripped}\n  "
        code = code.replace(
            valid_prefix + valid_body + valid_suffix,
            valid_prefix + new_valid_body + valid_suffix,
        )
        # Also add reads array_field to predicate
        code = code.replace(
            'reads this\n',
            f'reads this, {array_field}\n',
            1,  # only first occurrence (Valid predicate)
        )
        changes.append(
            f"Added `{length_check}` to Valid() predicate "
            f"and `reads {array_field}` for array access"
        )

    # --- Fix 2: Add array field to modifies clauses where needed ---
    lines = code.splitlines()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # If modifies this but not array_field, check if method references array
        if stripped == 'modifies this':
            # Look ahead in the method's ensures for array references
            idx = lines.index(line)
            method_refs_array = False
            for j in range(idx + 1, min(idx + 15, len(lines))):
                jstripped = lines[j].strip()
                if jstripped.startswith('{') or re.match(
                    r'\b(method|constructor)\b', jstripped
                ):
                    break
                if re.search(
                    rf'\b{re.escape(array_field)}\[', jstripped
                ):
                    method_refs_array = True
                    break

            if method_refs_array:
                indent = line[: len(line) - len(line.lstrip())]
                new_lines.append(
                    f"{indent}modifies this, {array_field}"
                )
                changes.append(
                    f"Added `{array_field}` to modifies clause "
                    f"(method accesses array contents)"
                )
                continue

        new_lines.append(line)

    return '\n'.join(new_lines), changes


def rewrite_existential_to_membership(code: str) -> tuple[str, list[str]]:
    """Replace simple existential membership patterns with `x in seq`.

    Matches:
      ensures exists i :: 0 <= i < |seq| && seq[i] == val
      ensures exists i: nat :: 0 <= i < |seq| && seq[i] == val

    Only rewrites when the existential is purely asserting membership
    (no additional conjuncts beyond bounds and equality).
    """
    changes: list[str] = []

    # Pattern: ensures exists i[: type] :: 0 <= i < |seq| && seq[i] == val [&& extra...]
    # We only rewrite when there's no extra conjuncts (simple membership).
    pattern = (
        r'(ensures\s+)exists\s+(\w+)\s*(?::\s*\w+)?\s*::\s*'
        r'0\s*<=\s*\2\s*<\s*\|(\w+)\|\s*&&\s*'
        r'\3\[(\2)\]\s*==\s*(\w+)\s*$'
    )

    lines = code.splitlines()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        m = re.match(pattern, stripped)
        if m:
            indent = line[:len(line) - len(line.lstrip())]
            seq_name = m.group(3)
            val_name = m.group(5)
            new_line = f"{indent}ensures {val_name} in {seq_name}"
            new_lines.append(new_line)
            changes.append(
                f"Simplified existential membership: "
                f"`exists {m.group(2)} :: ... && {seq_name}[{m.group(2)}] == {val_name}` "
                f"-> `{val_name} in {seq_name}`"
            )
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), changes


def strip_invalid_reads(code: str) -> tuple[str, list[str]]:
    """Remove `reads this` from method declarations.

    In Dafny, `reads this` is only valid on functions and predicates,
    not on methods. Methods that incorrectly have `reads this` will
    fail resolution.
    """
    changes: list[str] = []
    lines = code.splitlines()
    new_lines = []

    in_method = False
    in_function_or_predicate = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track what kind of declaration we're in
        if re.match(r'\b(method|constructor)\b', stripped):
            in_method = True
            in_function_or_predicate = False
        elif re.match(r'\b(function|predicate)\b', stripped):
            in_method = False
            in_function_or_predicate = True
        elif stripped.startswith('{') and not stripped.startswith('{{'):
            # Entering a body — reset tracking
            in_method = False
            in_function_or_predicate = False

        # Remove reads this from methods
        if in_method and stripped == 'reads this':
            changes.append(f"Removed invalid `reads this` from method (line {i + 1})")
            continue

        new_lines.append(line)

    return '\n'.join(new_lines), changes


def simplify_redundant_valid(code: str) -> tuple[str, list[str]]:
    """Remove redundant `ensures Valid()` from non-mutating methods.

    If a method has `requires Valid()` but NOT `modifies this`, then
    the Valid() predicate is trivially preserved (nothing changed).
    The `ensures Valid()` is redundant and adds a proof obligation for nothing.

    Conservative: only removes when we're confident it's safe.
    """
    changes: list[str] = []
    lines = code.splitlines()
    new_lines = []

    # First pass: identify method blocks and their properties
    method_blocks: list[dict] = []
    current_block: dict | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(r'\bmethod\b', stripped):
            if current_block:
                method_blocks.append(current_block)
            current_block = {
                'start': i,
                'has_requires_valid': False,
                'has_modifies_this': False,
                'ensures_valid_lines': [],
            }
        elif current_block is not None:
            if stripped == 'requires Valid()':
                current_block['has_requires_valid'] = True
            elif stripped.startswith('modifies') and 'this' in stripped:
                current_block['has_modifies_this'] = True
            elif stripped == 'ensures Valid()':
                current_block['ensures_valid_lines'].append(i)
            elif stripped.startswith('{') or stripped.startswith('method') or stripped.startswith('function') or stripped.startswith('predicate'):
                method_blocks.append(current_block)
                if stripped.startswith('method'):
                    current_block = {
                        'start': i,
                        'has_requires_valid': False,
                        'has_modifies_this': False,
                        'ensures_valid_lines': [],
                    }
                else:
                    current_block = None

    if current_block:
        method_blocks.append(current_block)

    # Find lines to remove
    remove_lines: set[int] = set()
    for block in method_blocks:
        if (block['has_requires_valid']
                and not block['has_modifies_this']
                and block['ensures_valid_lines']):
            for line_num in block['ensures_valid_lines']:
                remove_lines.add(line_num)
                changes.append(
                    f"Removed redundant `ensures Valid()` from non-mutating method (line {line_num + 1})"
                )

    for i, line in enumerate(lines):
        if i not in remove_lines:
            new_lines.append(line)

    return '\n'.join(new_lines), changes


def strip_unnecessary_modifies(code: str) -> tuple[str, list[str]]:
    """Remove `modifies this` from methods that don't actually mutate state.

    At the specification stage, method bodies are empty. We detect non-mutating
    methods by checking ensures clauses:
    - If ALL `old(...)` references are in preservation form (`ensures X == old(X)`),
      the method preserves state and `modifies this` is unnecessary.
    - If ANY `old(...)` reference indicates mutation (arithmetic on old, slicing,
      concatenation), keep `modifies this`.

    Removing false `modifies this` eliminates a spurious proof obligation
    and lets Dafny reason that fields are preserved without explicit proof.
    """
    changes: list[str] = []
    lines = code.splitlines()
    new_lines = []

    # Patterns indicating mutation via old()
    mutation_patterns = re.compile(
        r'\|old\(|old\([^)]+\)\s*\[|old\([^)]+\)\s*\+|'
        r'\+\s*old\(|old\([^)]+\)\s*-|-\s*old\('
    )
    # Pattern for preservation: ensures IDENT == old(IDENT) or old(IDENT) == IDENT
    preservation_pattern = re.compile(
        r'ensures\s+(\w+)\s*==\s*old\(\1\)|ensures\s+old\((\w+)\)\s*==\s*\2\b'
    )

    # Parse method blocks
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect method declaration
        if not re.match(r'\bmethod\b', stripped):
            new_lines.append(line)
            i += 1
            continue

        # Collect the method header (signature + spec clauses + opening brace)
        method_lines = [line]
        modifies_line_idx = None
        has_preservation = False
        has_mutation = False
        i += 1

        while i < len(lines):
            mline = lines[i]
            mstripped = mline.strip()

            # Stop at body opening or next declaration
            if mstripped.startswith('{') or re.match(r'\b(method|function|predicate|constructor|lemma)\b', mstripped):
                break

            if mstripped.startswith('modifies') and 'this' in mstripped:
                modifies_line_idx = len(method_lines)

            if 'old(' in mstripped:
                if mutation_patterns.search(mstripped):
                    has_mutation = True
                if preservation_pattern.match(mstripped):
                    has_preservation = True

            method_lines.append(mline)
            i += 1

        # Decide whether to remove modifies this
        if (modifies_line_idx is not None
                and has_preservation
                and not has_mutation):
            # Remove the modifies this line
            method_name_match = re.search(r'method\s+(\w+)', method_lines[0])
            method_name = method_name_match.group(1) if method_name_match else '?'
            del method_lines[modifies_line_idx]
            changes.append(
                f"Removed unnecessary `modifies this` from non-mutating method `{method_name}`"
            )

        new_lines.extend(method_lines)

    return '\n'.join(new_lines), changes


def reorder_ensures_clauses(code: str) -> tuple[str, list[str]]:
    """Move bounds-establishing ensures before indexing ensures.

    Dafny checks well-formedness of each ensures clause independently.
    If `ensures arr[result] == key` appears before `ensures 0 <= result < |arr|`,
    Dafny cannot prove the index is in range. Reordering fixes this.

    Priority rules (highest first):
    1. Contains `Valid()` — establishes class invariant
    2. Contains `|ident|` (sequence length) — establishes bounds
    3. Everything else — may index using bounds from (1) and (2)
    """
    changes: list[str] = []
    lines = code.splitlines()
    new_lines = []

    # Pattern: |identifier| anywhere in the clause (sequence/array length)
    length_pattern = re.compile(r'\|[\w.]+\|')
    # Pattern: identifier[expr] (indexing into sequence/array)
    index_pattern = re.compile(r'\w+\[(?![:=])')

    i = 0
    while i < len(lines):
        # Collect a block of ensures clauses
        ensures_block: list[str] = []
        block_start = i

        while i < len(lines) and lines[i].strip().startswith('ensures'):
            ensures_block.append(lines[i])
            i += 1

        if len(ensures_block) > 1:
            # Three-tier partition: validity, bounds, then indexing/rest
            tier1_valid = []    # ensures Valid()
            tier2_bounds = []   # contains |ident| (bounds-establishing)
            tier3_rest = []     # everything else

            for e in ensures_block:
                stripped = e.strip()
                if 'Valid()' in stripped:
                    tier1_valid.append(e)
                elif length_pattern.search(stripped):
                    tier2_bounds.append(e)
                else:
                    tier3_rest.append(e)

            reordered = tier1_valid + tier2_bounds + tier3_rest
            if reordered != ensures_block:
                new_lines.extend(reordered)
                changes.append(
                    f"Reordered ensures clauses: moved validity/bounds ensures "
                    f"before indexing ensures (lines {block_start + 1}-{block_start + len(ensures_block)})"
                )
                continue

        new_lines.extend(ensures_block)
        if i < len(lines):
            new_lines.append(lines[i])
            i += 1

    return '\n'.join(new_lines), changes


def inject_constructor(code: str) -> tuple[str, list[str]]:
    """Inject a constructor into classes that lack one.

    Without a constructor, Dafny cannot verify that objects start in a valid
    state. Every class needs a constructor with `ensures Valid()` and
    initialization postconditions for each field.

    Default initializations:
      seq<T> -> []    int/nat -> 0    bool -> false
      set<T> -> {}    array<T> -> not auto-initialized (skip)
    """
    changes: list[str] = []
    lines = code.splitlines()

    # Parse class blocks: find classes, their fields, and whether they have a constructor
    result_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect class declaration
        class_match = re.match(r'^(\s*)class\s+(\w+)', line)
        if not class_match:
            result_lines.append(line)
            i += 1
            continue

        indent = class_match.group(1)
        class_name = class_match.group(2)
        member_indent = indent + '  '

        # Collect the class body
        result_lines.append(line)
        i += 1

        # Find opening brace — may be on the class line itself
        if '{' not in line:
            while i < len(lines) and '{' not in lines[i]:
                result_lines.append(lines[i])
                i += 1
            if i < len(lines):
                result_lines.append(lines[i])
                i += 1

        # Scan class body for fields, constructor, and Valid() predicate
        fields: list[tuple[str, str]] = []  # (name, type)
        has_constructor = False
        has_valid = False
        brace_depth = 1
        body_start = len(result_lines)

        while i < len(lines) and brace_depth > 0:
            bodyline = lines[i]
            bodystripped = bodyline.strip()

            brace_depth += bodystripped.count('{') - bodystripped.count('}')

            if re.match(r'\bconstructor\b', bodystripped):
                has_constructor = True

            if re.match(r'\b(ghost\s+)?predicate\s+Valid\b', bodystripped):
                has_valid = True

            # Match field declarations: var name: type
            field_match = re.match(
                r'\s*(?:ghost\s+)?var\s+(\w+)\s*:\s*(.+)', bodystripped
            )
            if field_match and brace_depth == 1:
                fields.append((field_match.group(1), field_match.group(2).strip()))

            result_lines.append(bodyline)
            i += 1

        # Inject constructor if missing
        if not has_constructor and fields:
            # Build initialization postconditions
            ensures: list[str] = []
            inits: list[str] = []

            if has_valid:
                ensures.append(f'{member_indent}  ensures Valid()')

            for fname, ftype in fields:
                ftype_clean = ftype.rstrip(';').strip()
                if re.match(r'seq\s*<', ftype_clean):
                    ensures.append(f'{member_indent}  ensures {fname} == []')
                    inits.append(f'{member_indent}  {fname} := [];')
                elif re.match(r'set\s*<', ftype_clean):
                    ensures.append(f'{member_indent}  ensures {fname} == {{}}')
                    inits.append(f'{member_indent}  {fname} := {{}};')
                elif re.match(r'multiset\s*<', ftype_clean):
                    ensures.append(f'{member_indent}  ensures {fname} == multiset{{}}')
                    inits.append(f'{member_indent}  {fname} := multiset{{}};')
                elif ftype_clean in ('int', 'nat'):
                    ensures.append(f'{member_indent}  ensures {fname} == 0')
                    inits.append(f'{member_indent}  {fname} := 0;')
                elif ftype_clean == 'bool':
                    ensures.append(f'{member_indent}  ensures {fname} == false')
                    inits.append(f'{member_indent}  {fname} := false;')
                # Skip array<T> and other complex types — can't auto-initialize

            if inits:
                constructor_lines = [
                    '',
                    f'{member_indent}constructor()',
                ]
                constructor_lines.extend(ensures)
                constructor_lines.append(f'{member_indent}{{')
                constructor_lines.extend(inits)
                constructor_lines.append(f'{member_indent}}}')

                # Insert after fields, before first method/predicate/function
                insert_at = body_start
                for j in range(body_start, len(result_lines)):
                    jstripped = result_lines[j].strip()
                    if re.match(
                        r'\b(method|function|predicate|ghost\s+predicate|ghost\s+function|lemma)\b',
                        jstripped,
                    ):
                        insert_at = j
                        break
                else:
                    # Insert before closing brace
                    insert_at = len(result_lines) - 1

                for ci, cl in enumerate(constructor_lines):
                    result_lines.insert(insert_at + ci, cl)

                changes.append(
                    f"Injected constructor for class `{class_name}` "
                    f"with {len(inits)} field initializations"
                )

    return '\n'.join(result_lines), changes


def fix_postcondition_old_refs(code: str) -> tuple[str, list[str]]:
    """Fix postconditions that reference modified fields without old().

    In Dafny postconditions, unqualified names refer to the post-state.
    When a method has ``modifies this`` and a postcondition uses a class field
    as an array index, that field may have changed — making ``array[field]``
    refer to the *new* value and the postcondition unprovable.

    Detection: after ``strip_unnecessary_modifies`` has run, any method that
    still has ``modifies this`` is truly mutating.  A class field used as an
    array index in such a method needs ``old()`` unless it is explicitly
    preserved (``ensures field == old(field)``).

    Fixes two patterns:
      - ``ensures array[field] == val``  (write)
        -> ``ensures array[old(field)] == val``
      - ``ensures result == array[field]``  (read)
        -> ``ensures result == old(array[field])``

    Only applies to classes with ``array<T>`` fields.
    """
    changes: list[str] = []

    # Only applies to array-based classes
    array_field_m = re.search(r'var\s+(\w+)\s*:\s*array<', code)
    if not array_field_m:
        return code, []
    array_field = array_field_m.group(1)

    field_names = set(re.findall(r'var\s+(\w+)\s*:', code))
    lines = code.splitlines()

    # --- First pass: per-method, identify modifies status and preserved fields ---
    method_info: dict[int, dict] = {}  # line -> {has_modifies, preserved}
    current_method: int | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'\bmethod\b', stripped):
            current_method = i
            method_info[i] = {'has_modifies': False, 'preserved': set()}
        elif stripped.startswith('{') and current_method is not None:
            current_method = None
        elif current_method is not None:
            info = method_info[current_method]
            if stripped.startswith('modifies') and 'this' in stripped:
                info['has_modifies'] = True
            # Detect preserved fields: field == old(field) or old(field) == field
            # Works on compound ensures too (&&-separated conjuncts)
            for m in re.finditer(r'(\w+)\s*==\s*old\(\1\)', stripped):
                if m.group(1) in field_names:
                    info['preserved'].add(m.group(1))
            for m in re.finditer(r'old\((\w+)\)\s*==\s*\1\b', stripped):
                if m.group(1) in field_names:
                    info['preserved'].add(m.group(1))

    # Detect capacity field from Valid(): buffer.Length == FIELD
    capacity_field = None
    valid_m = re.search(
        rf'{re.escape(array_field)}\.Length\s*==\s*(\w+)', code
    )
    if valid_m and valid_m.group(1) in field_names:
        capacity_field = valid_m.group(1)

    # --- Second pass: fix ensures clauses in mutating methods ---
    new_lines = []
    current_method = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(r'\bmethod\b', stripped):
            current_method = i

        info = (
            method_info.get(current_method)
            if current_method is not None
            else None
        )

        if (
            not info
            or not info['has_modifies']
            or not stripped.startswith('ensures')
        ):
            new_lines.append(line)
            continue

        line_fixed = False
        for field in field_names:
            if field == array_field:
                continue
            if field in info['preserved']:
                continue

            # Skip if already wrapped in old()
            if re.search(
                rf'old\({re.escape(array_field)}\[{re.escape(field)}\]\)',
                stripped,
            ) or re.search(
                rf'{re.escape(array_field)}\[old\({re.escape(field)}\)\]',
                stripped,
            ):
                continue

            # Check for array[field] in this ensures clause
            if not re.search(
                rf'{re.escape(array_field)}\[{re.escape(field)}\]', stripped
            ):
                continue

            indent = line[: len(line) - len(line.lstrip())]

            # Inject capacity frame condition before the fixed ensures
            # so Dafny can prove old(index) < buffer.Length
            if capacity_field and capacity_field not in info['preserved']:
                cap_ensures = (
                    f"{indent}ensures {capacity_field} == "
                    f"old({capacity_field})"
                )
                # Check it's not already present in the method's ensures
                method_text = '\n'.join(
                    lines[current_method: i] if current_method else []
                )
                if f'{capacity_field} == old({capacity_field})' not in method_text:
                    new_lines.append(cap_ensures)
                    changes.append(
                        f"Added frame condition: `{capacity_field} == "
                        f"old({capacity_field})` "
                        f"(needed for old() array index well-formedness)"
                    )

            # Read pattern: result/var == array[field]
            is_read = re.match(
                rf'ensures\s+\w+\s*==\s*{re.escape(array_field)}'
                rf'\[{re.escape(field)}\]',
                stripped,
            )

            if is_read:
                new_ensures = stripped.replace(
                    f'{array_field}[{field}]',
                    f'old({array_field}[{field}])',
                )
                new_fragment = f'old({array_field}[{field}])'
            else:
                new_ensures = stripped.replace(
                    f'{array_field}[{field}]',
                    f'{array_field}[old({field})]',
                )
                new_fragment = f'{array_field}[old({field})]'

            new_lines.append(f"{indent}{new_ensures}")
            changes.append(
                f"Fixed postcondition: `{array_field}[{field}]` -> "
                f"`{new_fragment}` "
                f"({field} is modified by this method)"
            )
            line_fixed = True
            break

        if not line_fixed:
            new_lines.append(line)

    return '\n'.join(new_lines), changes


def decompose_spec(code: str) -> tuple[str, list[str]]:
    """Run all deterministic rewrites in sequence.

    Returns (simplified_code, all_changes).
    Each rewrite is independent — order doesn't matter for correctness,
    but we run them in a fixed order for reproducibility.
    """
    all_changes: list[str] = []

    code, changes = fix_array_class_spec(code)
    all_changes.extend(changes)

    code, changes = rewrite_existential_to_membership(code)
    all_changes.extend(changes)

    code, changes = strip_invalid_reads(code)
    all_changes.extend(changes)

    code, changes = simplify_redundant_valid(code)
    all_changes.extend(changes)

    code, changes = strip_unnecessary_modifies(code)
    all_changes.extend(changes)

    code, changes = add_quantifier_bounds(code)
    all_changes.extend(changes)

    code, changes = simplify_redundant_ensures(code)
    all_changes.extend(changes)

    code, changes = fix_postcondition_old_refs(code)
    all_changes.extend(changes)

    code, changes = reorder_ensures_clauses(code)
    all_changes.extend(changes)

    code, changes = inject_constructor(code)
    all_changes.extend(changes)

    code, changes = augment_constructor_body(code)
    all_changes.extend(changes)

    return code, all_changes
