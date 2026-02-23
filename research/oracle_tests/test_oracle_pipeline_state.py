"""Oracle tests for PipelineStateMachine.

Tests the public API only — works for both Dafny-compiled and TDD implementations.

Status codes: 0=Pending, 1=InProgress, 2=Completed, 3=Failed, 4=Skipped
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "pipeline_state"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    factory, _ = get_factory_for_condition(request, PROBLEM, request.param)
    return factory


# ── Initial state ─────────────────────────────────────────────────────────

def test_not_finished_initially(make):
    p = make()
    assert p.IsFinished() is False


# ── Basic workflow: advance through all stages ────────────────────────────

def test_complete_all_stages(make):
    p = make()
    for stage in range(5):
        p.Advance(stage)
        p.Complete(stage)
    assert p.IsFinished() is True


def test_advance_then_complete(make):
    p = make()
    p.Advance(0)
    p.Complete(0)
    # Stage 0 is now completed; stage 1 should be advanceable
    p.Advance(1)
    p.Complete(1)


# ── Fail and rollback ────────────────────────────────────────────────────

def test_fail_stage(make):
    p = make()
    p.Advance(0)
    p.Fail(0)
    assert p.IsFinished() is False


def test_rollback_resets_to_pending(make):
    p = make()
    p.Advance(0)
    p.Complete(0)
    p.Advance(1)
    p.Complete(1)
    # Rollback stage 1 and later
    p.Rollback(1)
    # Stage 1 is now pending again; can re-advance
    p.Advance(1)
    p.Complete(1)


def test_rollback_all(make):
    p = make()
    p.Advance(0)
    p.Complete(0)
    p.Advance(1)
    p.Complete(1)
    p.Rollback(0)
    assert p.IsFinished() is False
    # Can restart from stage 0
    p.Advance(0)
    p.Complete(0)


def test_fail_then_rollback_and_retry(make):
    p = make()
    p.Advance(0)
    p.Complete(0)
    p.Advance(1)
    p.Fail(1)
    p.Rollback(1)
    p.Advance(1)
    p.Complete(1)


# ── Rollback preserves earlier stages ─────────────────────────────────────

def test_rollback_preserves_earlier(make):
    p = make()
    p.Advance(0)
    p.Complete(0)
    p.Advance(1)
    p.Complete(1)
    p.Advance(2)
    p.Complete(2)
    p.Rollback(2)
    # Stages 0 and 1 should still be completed; can advance stage 2 again
    p.Advance(2)
    p.Complete(2)


# ── Full pipeline with failure recovery ───────────────────────────────────

def test_full_pipeline_with_recovery(make):
    p = make()
    # Complete stages 0-2
    for i in range(3):
        p.Advance(i)
        p.Complete(i)
    # Stage 3 fails
    p.Advance(3)
    p.Fail(3)
    # Rollback and retry
    p.Rollback(3)
    p.Advance(3)
    p.Complete(3)
    # Complete stage 4
    p.Advance(4)
    p.Complete(4)
    assert p.IsFinished() is True


# ── Edge: rollback the very last stage ────────────────────────────────────

def test_rollback_last_stage(make):
    p = make()
    for i in range(5):
        p.Advance(i)
        p.Complete(i)
    assert p.IsFinished() is True
    p.Rollback(4)
    assert p.IsFinished() is False
    p.Advance(4)
    p.Complete(4)
    assert p.IsFinished() is True
