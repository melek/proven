"""Oracle tests for BoundedCounter.

Tests the public API only — works for both Dafny-compiled and TDD implementations.
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "bounded_counter"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    factory, _ = get_factory_for_condition(request, PROBLEM, request.param)
    return factory


# ── Basic operations ──────────────────────────────────────────────────────

def test_initial_value(make):
    c = make(0, 10)
    assert c.GetValue() == 0


def test_initial_value_nonzero_min(make):
    c = make(5, 10)
    assert c.GetValue() == 5


def test_increment(make):
    c = make(0, 10)
    c.Increment()
    assert c.GetValue() == 1


def test_decrement(make):
    c = make(0, 10)
    c.Increment()
    c.Decrement()
    assert c.GetValue() == 0


def test_multiple_increments(make):
    c = make(0, 5)
    for _ in range(5):
        c.Increment()
    assert c.GetValue() == 5


def test_increment_then_decrement_sequence(make):
    c = make(0, 10)
    c.Increment()
    c.Increment()
    c.Increment()
    c.Decrement()
    assert c.GetValue() == 2


# ── Boundary checks ──────────────────────────────────────────────────────

def test_is_at_min_initially(make):
    c = make(0, 10)
    assert c.IsAtMin() is True


def test_is_at_min_after_increment(make):
    c = make(0, 10)
    c.Increment()
    assert c.IsAtMin() is False


def test_is_at_max_when_full(make):
    c = make(0, 3)
    c.Increment()
    c.Increment()
    c.Increment()
    assert c.IsAtMax() is True


def test_is_at_max_not_full(make):
    c = make(0, 3)
    c.Increment()
    assert c.IsAtMax() is False


def test_is_at_min_false_then_true(make):
    c = make(0, 5)
    c.Increment()
    assert c.IsAtMin() is False
    c.Decrement()
    assert c.IsAtMin() is True


# ── Edge cases ────────────────────────────────────────────────────────────

def test_single_range(make):
    """Counter with min == max - 1: can toggle between two values."""
    c = make(0, 1)
    assert c.GetValue() == 0
    assert c.IsAtMin() is True
    c.Increment()
    assert c.GetValue() == 1
    assert c.IsAtMax() is True
    c.Decrement()
    assert c.GetValue() == 0


def test_negative_bounds(make):
    c = make(-5, -1)
    assert c.GetValue() == -5
    c.Increment()
    assert c.GetValue() == -4


def test_getvalue_is_readonly(make):
    c = make(0, 10)
    c.Increment()
    c.Increment()
    val1 = c.GetValue()
    val2 = c.GetValue()
    assert val1 == val2 == 2
