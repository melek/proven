"""Oracle tests for SortedList.

Tests the public API only — works for both Dafny-compiled and TDD implementations.
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "sorted_list"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    factory, _ = get_factory_for_condition(request, PROBLEM, request.param)
    return factory


# ── Basic operations ──────────────────────────────────────────────────────

def test_empty_on_creation(make):
    sl = make()
    assert sl.Size() == 0


def test_insert_one(make):
    sl = make()
    sl.Insert(5)
    assert sl.Size() == 1
    assert sl.Contains(5) is True


def test_insert_maintains_sorted_order(make):
    sl = make()
    sl.Insert(3)
    sl.Insert(1)
    sl.Insert(2)
    assert sl.GetMin() == 1
    assert sl.GetMax() == 3
    assert sl.Size() == 3


def test_remove(make):
    sl = make()
    sl.Insert(1)
    sl.Insert(2)
    sl.Insert(3)
    sl.Remove(2)
    assert sl.Contains(2) is False
    assert sl.Size() == 2


def test_contains(make):
    sl = make()
    sl.Insert(10)
    assert sl.Contains(10) is True
    assert sl.Contains(20) is False


def test_get_min(make):
    sl = make()
    sl.Insert(5)
    sl.Insert(1)
    sl.Insert(9)
    assert sl.GetMin() == 1


def test_get_max(make):
    sl = make()
    sl.Insert(5)
    sl.Insert(1)
    sl.Insert(9)
    assert sl.GetMax() == 9


# ── Duplicate handling ────────────────────────────────────────────────────

def test_insert_duplicates(make):
    sl = make()
    sl.Insert(5)
    sl.Insert(5)
    sl.Insert(5)
    assert sl.Size() == 3
    assert sl.Contains(5) is True


def test_remove_one_duplicate(make):
    sl = make()
    sl.Insert(5)
    sl.Insert(5)
    sl.Remove(5)
    assert sl.Size() == 1
    assert sl.Contains(5) is True


# ── Sorted invariant after operations ─────────────────────────────────────

def test_sorted_after_mixed_inserts(make):
    sl = make()
    sl.Insert(10)
    sl.Insert(1)
    sl.Insert(5)
    sl.Insert(3)
    sl.Insert(8)
    assert sl.GetMin() == 1
    assert sl.GetMax() == 10
    assert sl.Size() == 5


def test_sorted_after_remove(make):
    sl = make()
    sl.Insert(1)
    sl.Insert(3)
    sl.Insert(5)
    sl.Remove(3)
    assert sl.GetMin() == 1
    assert sl.GetMax() == 5


def test_remove_min(make):
    sl = make()
    sl.Insert(1)
    sl.Insert(2)
    sl.Insert(3)
    sl.Remove(1)
    assert sl.GetMin() == 2


def test_remove_max(make):
    sl = make()
    sl.Insert(1)
    sl.Insert(2)
    sl.Insert(3)
    sl.Remove(3)
    assert sl.GetMax() == 2


# ── Edge cases ────────────────────────────────────────────────────────────

def test_single_element_min_max(make):
    sl = make()
    sl.Insert(42)
    assert sl.GetMin() == 42
    assert sl.GetMax() == 42


def test_negative_values(make):
    sl = make()
    sl.Insert(-5)
    sl.Insert(-1)
    sl.Insert(-3)
    assert sl.GetMin() == -5
    assert sl.GetMax() == -1


def test_insert_remove_all(make):
    sl = make()
    sl.Insert(1)
    sl.Insert(2)
    sl.Remove(1)
    sl.Remove(2)
    assert sl.Size() == 0
    assert sl.Contains(1) is False
    assert sl.Contains(2) is False
