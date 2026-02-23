"""Mentor module: diagnostic advisor for stuck retry loops.

The mentor is a perspective shift — same model, fresh context, different framing.
It classifies stuck patterns deterministically and generates strategic directives
via a separate LLM call when the coding context is going in circles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from .llm import LLMClient
from .workspace import InteractionLog
from .prompts import MENTOR_SYSTEM, MENTOR_USER


class StuckCategory(str, Enum):
    REPEATING_ERROR = "repeating_error"
    VERIFIED_REGRESSION = "verified_regression"
    SPEC_DRIFT = "spec_drift"
    SPEC_TOO_COMPLEX = "spec_too_complex"
    OSCILLATING = "oscillating"
    NOT_STUCK = "not_stuck"


@dataclass
class AttemptRecord:
    attempt_number: int
    error_text: str
    verified_count: int
    error_count: int
    error_signature: str
    spec_warnings: list[str]


@dataclass
class StuckPattern:
    category: StuckCategory
    detail: str
    consecutive_same: int
    verified_trend: list[int]


@dataclass
class MentorState:
    budget_remaining: int
    history: list[AttemptRecord] = field(default_factory=list)
    interventions: list[str] = field(default_factory=list)


@dataclass
class MentorDirective:
    action: str  # "advise" or "rollback"
    content: str  # The directive text
    rollback_target: int | None = None  # Stage to roll back to (e.g., 2)
    rollback_guidance: str | None = None  # Guidance for the target stage


# ─────────────────────────────────────────────────────────────
# Error normalization
# ─────────────────────────────────────────────────────────────

def _normalize_error(error_text: str) -> str:
    """Produce a stable fingerprint from Dafny error output.

    Strips file paths, line:col numbers, and visual pointer lines
    so that the same logical error at different positions compares equal.
    """
    normalized = re.sub(r'[^\s(]+\.dfy\(\d+,\d+\)', 'FILE:LOC', error_text)
    lines = []
    for line in normalized.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('|') and not stripped.startswith('^'):
            lines.append(stripped)
    return '\n'.join(lines)


def _parse_verified_count(error_text: str) -> tuple[int, int]:
    """Extract (verified, errors) from Dafny summary line."""
    match = re.search(r'(\d+)\s+verified,\s+(\d+)\s+error', error_text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def _first_error_line(error_text: str) -> str:
    """Extract the first 'Error: ...' line for display."""
    for line in error_text.splitlines():
        if 'Error:' in line:
            return line.strip()
    return error_text[:120]


# ─────────────────────────────────────────────────────────────
# Recording and detection
# ─────────────────────────────────────────────────────────────

def record_attempt(
    mentor_state: MentorState,
    attempt_number: int,
    error_text: str,
    spec_warnings: list[str],
) -> AttemptRecord:
    """Create an AttemptRecord and append it to mentor state."""
    verified, errors = _parse_verified_count(error_text)
    record = AttemptRecord(
        attempt_number=attempt_number,
        error_text=error_text,
        verified_count=verified,
        error_count=errors,
        error_signature=_normalize_error(error_text),
        spec_warnings=spec_warnings,
    )
    mentor_state.history.append(record)
    return record


def detect_stuck(mentor_state: MentorState, window: int = 2) -> StuckPattern | None:
    """Analyze attempt history and return a StuckPattern if stuck.

    Purely deterministic — no LLM call. Checks in priority order:
    spec drift → regression → repeating error → oscillation.
    """
    history = mentor_state.history
    if len(history) < 2:
        return None

    latest = history[-1]

    # Check 1: Spec drift (most dangerous)
    if latest.spec_warnings:
        return StuckPattern(
            category=StuckCategory.SPEC_DRIFT,
            detail=f"Model removed specification clauses: {'; '.join(latest.spec_warnings)}",
            consecutive_same=0,
            verified_trend=[r.verified_count for r in history],
        )

    # Check 2: Verified count regression
    prev = history[-2]
    if latest.verified_count < prev.verified_count and prev.verified_count > 0:
        return StuckPattern(
            category=StuckCategory.VERIFIED_REGRESSION,
            detail=(
                f"Verified count dropped from {prev.verified_count} to "
                f"{latest.verified_count} (lost {prev.verified_count - latest.verified_count} "
                f"previously-passing conditions)"
            ),
            consecutive_same=0,
            verified_trend=[r.verified_count for r in history],
        )

    # Check 3: Repeating identical error
    consecutive = 1
    for i in range(len(history) - 2, -1, -1):
        if history[i].error_signature == latest.error_signature:
            consecutive += 1
        else:
            break

    if consecutive >= window:
        return StuckPattern(
            category=StuckCategory.REPEATING_ERROR,
            detail=(
                f"Same error repeated {consecutive} times in a row. "
                f"Error: {_first_error_line(latest.error_text)}"
            ),
            consecutive_same=consecutive,
            verified_trend=[r.verified_count for r in history],
        )

    # Check 4: Spec too complex (verified stuck + postcondition errors + complex spec)
    if len(history) >= 3:
        recent = history[-3:]
        verified_stuck = all(r.verified_count == recent[0].verified_count for r in recent)
        has_postcondition_errors = any(
            'postcondition' in r.error_text.lower() for r in recent
        )
        if verified_stuck and has_postcondition_errors:
            return StuckPattern(
                category=StuckCategory.SPEC_TOO_COMPLEX,
                detail=(
                    f"Verified count stuck at {recent[0].verified_count} for "
                    f"{len(recent)} attempts with postcondition errors — "
                    f"the specification may be too complex to prove"
                ),
                consecutive_same=len(recent),
                verified_trend=[r.verified_count for r in history],
            )

    # Check 5: Oscillating between two error sets
    if len(history) >= 4:
        sigs = [r.error_signature for r in history[-4:]]
        if sigs[0] == sigs[2] and sigs[1] == sigs[3] and sigs[0] != sigs[1]:
            return StuckPattern(
                category=StuckCategory.OSCILLATING,
                detail="Model is alternating between two different error states",
                consecutive_same=0,
                verified_trend=[r.verified_count for r in history],
            )

    return None


# ─────────────────────────────────────────────────────────────
# Mentor LLM call
# ─────────────────────────────────────────────────────────────

def _build_attempt_summary(history: list[AttemptRecord]) -> str:
    """Build a concise summary of attempts for the mentor prompt."""
    lines = []
    for rec in history:
        first_error = _first_error_line(rec.error_text)
        warnings_str = f" SPEC WARNINGS: {rec.spec_warnings}" if rec.spec_warnings else ""
        lines.append(
            f"Attempt {rec.attempt_number}: "
            f"{rec.verified_count} verified, {rec.error_count} errors. "
            f"First error: {first_error}"
            f"{warnings_str}"
        )
    return '\n'.join(lines)


def parse_mentor_directive(raw_text: str) -> MentorDirective:
    """Parse raw mentor LLM output into a structured directive.

    Detects whether the response is advice or a rollback recommendation
    based on prefix matching. Falls back to advice if no prefix found.
    """
    text = raw_text.strip()

    # Check for rollback prefix
    rollback_match = re.match(
        r'ROLLBACK\s+TO\s+STAGE\s+(\d+)\s*:\s*(.*)',
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if rollback_match:
        target_stage = int(rollback_match.group(1))
        guidance = rollback_match.group(2).strip()
        return MentorDirective(
            action="rollback",
            content=text,
            rollback_target=target_stage,
            rollback_guidance=guidance,
        )

    # Check for advice prefix — strip it if present
    advice_match = re.match(r'ADVICE\s*:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
    if advice_match:
        return MentorDirective(
            action="advise",
            content=advice_match.group(1).strip(),
        )

    # No prefix — treat as advice (backward compatible)
    return MentorDirective(action="advise", content=text)


def get_mentor_directive(
    mentor_state: MentorState,
    pattern: StuckPattern,
    original_spec: str,
    llm: LLMClient,
    log: InteractionLog,
    verbose: bool = False,
) -> MentorDirective | None:
    """Call the LLM in mentor mode and return a structured directive.

    Consumes 1 unit of budget. Returns None if budget exhausted.
    The mentor never sees full code — only spec, attempt summaries, and the diagnosis.
    """
    if mentor_state.budget_remaining <= 0:
        if verbose:
            print("  [Mentor] Budget exhausted, skipping intervention")
        return None

    mentor_state.budget_remaining -= 1

    attempt_summary = _build_attempt_summary(mentor_state.history)

    user_prompt = MENTOR_USER.format(
        original_spec=original_spec,
        attempt_summary=attempt_summary,
        stuck_category=pattern.category.value,
        stuck_detail=pattern.detail,
        verified_trend=', '.join(str(v) for v in pattern.verified_trend),
    )

    log._append({
        "event": "mentor_intervention",
        "stuck_category": pattern.category.value,
        "stuck_detail": pattern.detail,
        "budget_remaining": mentor_state.budget_remaining,
        "attempt_count": len(mentor_state.history),
    })

    if verbose:
        print(f"  [Mentor] Stuck detected: {pattern.category.value}")
        print(f"  [Mentor] {pattern.detail}")
        print(f"  [Mentor] Calling LLM for strategic guidance (budget: {mentor_state.budget_remaining} remaining)...")

    resp = llm.complete(
        system_prompt=MENTOR_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=512,
    )

    raw_directive = resp.content.strip()
    directive = parse_mentor_directive(raw_directive)

    log._append({
        "event": "mentor_response",
        "action": directive.action,
        "directive": directive.content,
        "rollback_target": directive.rollback_target,
        "usage": resp.usage,
    })

    mentor_state.interventions.append(directive.content)

    if verbose:
        if directive.action == "rollback":
            print(f"  [Mentor] ROLLBACK to Stage {directive.rollback_target}: {directive.rollback_guidance}")
        else:
            print(f"  [Mentor] Directive: {directive.content}")

    return directive
