"""Oracle tests for UniqueSet.

Tests the public API only — works for both Dafny-compiled and TDD implementations.
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "unique_set"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    factory, _ = get_factory_for_condition(request, PROBLEM, request.param)
    return factory


# ── Basic operations ──────────────────────────────────────────────────────

def test_empty_on_creation(make):
    s = make()
    assert s.IsEmpty() is True
    assert s.Size() == 0


def test_add_and_contains(make):
    s = make()
    s.Add(1)
    assert s.Contains(1) is True
    assert s.Size() == 1


def test_add_not_contains_other(make):
    s = make()
    s.Add(1)
    assert s.Contains(2) is False


def test_remove(make):
    s = make()
    s.Add(1)
    s.Remove(1)
    assert s.Contains(1) is False
    assert s.Size() == 0


def test_not_empty_after_add(make):
    s = make()
    s.Add(5)
    assert s.IsEmpty() is False


# ── Uniqueness (idempotent Add) ──────────────────────────────────────────

def test_add_idempotent(make):
    s = make()
    s.Add(1)
    s.Add(1)
    assert s.Size() == 1
    assert s.Contains(1) is True


def test_add_same_three_times(make):
    s = make()
    s.Add(5)
    s.Add(5)
    s.Add(5)
    assert s.Size() == 1


# ── Multiple elements ────────────────────────────────────────────────────

def test_multiple_adds(make):
    s = make()
    s.Add(1)
    s.Add(2)
    s.Add(3)
    assert s.Size() == 3
    assert s.Contains(1) is True
    assert s.Contains(2) is True
    assert s.Contains(3) is True


def test_remove_one_of_many(make):
    s = make()
    s.Add(1)
    s.Add(2)
    s.Add(3)
    s.Remove(2)
    assert s.Contains(1) is True
    assert s.Contains(2) is False
    assert s.Contains(3) is True
    assert s.Size() == 2


def test_remove_all(make):
    s = make()
    s.Add(1)
    s.Add(2)
    s.Remove(1)
    s.Remove(2)
    assert s.IsEmpty() is True
    assert s.Size() == 0


# ── Add after remove ─────────────────────────────────────────────────────

def test_add_after_remove(make):
    s = make()
    s.Add(1)
    s.Remove(1)
    s.Add(1)
    assert s.Contains(1) is True
    assert s.Size() == 1


# ── Edge cases ────────────────────────────────────────────────────────────

def test_negative_values(make):
    s = make()
    s.Add(-1)
    s.Add(-2)
    assert s.Contains(-1) is True
    assert s.Contains(-2) is True
    assert s.Size() == 2


def test_zero(make):
    s = make()
    s.Add(0)
    assert s.Contains(0) is True
    assert s.Size() == 1
