"""Oracle tests for Stack.

Tests the public API only — works for both Dafny-compiled and TDD implementations.
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "stack"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    factory, _ = get_factory_for_condition(request, PROBLEM, request.param)
    return factory


# ── Basic operations ──────────────────────────────────────────────────────

def test_empty_on_creation(make):
    s = make()
    assert s.IsEmpty() is True
    assert s.Size() == 0


def test_push_then_pop(make):
    s = make()
    s.Push(42)
    assert s.Pop() == 42


def test_push_then_top(make):
    s = make()
    s.Push(99)
    assert s.Top() == 99


def test_lifo_order(make):
    s = make()
    s.Push(1)
    s.Push(2)
    s.Push(3)
    assert s.Pop() == 3
    assert s.Pop() == 2
    assert s.Pop() == 1


def test_size_increases(make):
    s = make()
    s.Push(10)
    assert s.Size() == 1
    s.Push(20)
    assert s.Size() == 2
    s.Push(30)
    assert s.Size() == 3


def test_size_decreases_on_pop(make):
    s = make()
    s.Push(1)
    s.Push(2)
    s.Pop()
    assert s.Size() == 1


def test_not_empty_after_push(make):
    s = make()
    s.Push(5)
    assert s.IsEmpty() is False


def test_empty_after_pop_all(make):
    s = make()
    s.Push(1)
    s.Push(2)
    s.Pop()
    s.Pop()
    assert s.IsEmpty() is True
    assert s.Size() == 0


# ── Top is nondestructive ────────────────────────────────────────────────

def test_top_does_not_remove(make):
    s = make()
    s.Push(7)
    assert s.Top() == 7
    assert s.Top() == 7
    assert s.Size() == 1


# ── Interleaved operations ───────────────────────────────────────────────

def test_push_pop_interleave(make):
    s = make()
    s.Push(1)
    s.Push(2)
    assert s.Pop() == 2
    s.Push(3)
    assert s.Pop() == 3
    assert s.Pop() == 1


def test_single_element(make):
    s = make()
    s.Push(100)
    assert s.Size() == 1
    assert s.Top() == 100
    assert s.Pop() == 100
    assert s.IsEmpty() is True


def test_negative_values(make):
    s = make()
    s.Push(-1)
    s.Push(-2)
    assert s.Top() == -2
    assert s.Pop() == -2
    assert s.Pop() == -1
