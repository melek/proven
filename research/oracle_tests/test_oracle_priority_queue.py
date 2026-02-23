"""Oracle tests for MinPriorityQueue.

Tests the public API only — works for both Dafny-compiled and TDD implementations.
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "priority_queue"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    factory, _ = get_factory_for_condition(request, PROBLEM, request.param)
    return factory


# ── Basic operations ──────────────────────────────────────────────────────

def test_empty_on_creation(make):
    pq = make()
    assert pq.IsEmpty() is True
    assert pq.Size() == 0


def test_insert_and_extract(make):
    pq = make()
    pq.Insert(5)
    assert pq.ExtractMin() == 5


def test_min_ordering(make):
    pq = make()
    pq.Insert(5)
    pq.Insert(3)
    pq.Insert(7)
    assert pq.ExtractMin() == 3
    assert pq.ExtractMin() == 5
    assert pq.ExtractMin() == 7


def test_peek_returns_min(make):
    pq = make()
    pq.Insert(10)
    pq.Insert(2)
    pq.Insert(8)
    assert pq.Peek() == 2


def test_size_tracking(make):
    pq = make()
    pq.Insert(1)
    assert pq.Size() == 1
    pq.Insert(2)
    assert pq.Size() == 2
    pq.ExtractMin()
    assert pq.Size() == 1


def test_not_empty_after_insert(make):
    pq = make()
    pq.Insert(42)
    assert pq.IsEmpty() is False


def test_empty_after_extract_all(make):
    pq = make()
    pq.Insert(1)
    pq.Insert(2)
    pq.ExtractMin()
    pq.ExtractMin()
    assert pq.IsEmpty() is True


# ── Peek is nondestructive ────────────────────────────────────────────────

def test_peek_does_not_remove(make):
    pq = make()
    pq.Insert(5)
    pq.Insert(3)
    assert pq.Peek() == 3
    assert pq.Peek() == 3
    assert pq.Size() == 2


# ── Duplicates ────────────────────────────────────────────────────────────

def test_duplicate_values(make):
    pq = make()
    pq.Insert(5)
    pq.Insert(5)
    pq.Insert(5)
    assert pq.Size() == 3
    assert pq.ExtractMin() == 5
    assert pq.ExtractMin() == 5
    assert pq.ExtractMin() == 5


# ── Insertion order independence ──────────────────────────────────────────

def test_reverse_insertion(make):
    pq = make()
    pq.Insert(10)
    pq.Insert(9)
    pq.Insert(8)
    pq.Insert(7)
    assert pq.ExtractMin() == 7
    assert pq.ExtractMin() == 8
    assert pq.ExtractMin() == 9
    assert pq.ExtractMin() == 10


def test_interleaved_insert_extract(make):
    pq = make()
    pq.Insert(5)
    pq.Insert(3)
    assert pq.ExtractMin() == 3
    pq.Insert(1)
    assert pq.ExtractMin() == 1
    assert pq.ExtractMin() == 5


def test_negative_values(make):
    pq = make()
    pq.Insert(-1)
    pq.Insert(-5)
    pq.Insert(0)
    assert pq.ExtractMin() == -5
    assert pq.ExtractMin() == -1
    assert pq.ExtractMin() == 0


def test_single_element(make):
    pq = make()
    pq.Insert(42)
    assert pq.Peek() == 42
    assert pq.Size() == 1
    assert pq.ExtractMin() == 42
    assert pq.IsEmpty() is True
