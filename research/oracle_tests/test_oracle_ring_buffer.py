"""Oracle tests for RingBuffer.

Tests the public API only — works for both Dafny-compiled and TDD implementations.
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "ring_buffer"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    factory, _ = get_factory_for_condition(request, PROBLEM, request.param)
    return factory


# ── Basic operations ──────────────────────────────────────────────────────

def test_empty_on_creation(make):
    rb = make(5)
    assert rb.IsEmpty() is True
    assert rb.Size() == 0


def test_enqueue_dequeue(make):
    rb = make(5)
    rb.Enqueue(42)
    assert rb.Dequeue() == 42


def test_fifo_order(make):
    rb = make(5)
    for i in range(5):
        rb.Enqueue(i)
    for i in range(5):
        assert rb.Dequeue() == i


def test_peek(make):
    rb = make(5)
    rb.Enqueue(10)
    rb.Enqueue(20)
    assert rb.Peek() == 10


def test_size_tracking(make):
    rb = make(5)
    rb.Enqueue(1)
    assert rb.Size() == 1
    rb.Enqueue(2)
    assert rb.Size() == 2
    rb.Dequeue()
    assert rb.Size() == 1


def test_is_full(make):
    rb = make(3)
    rb.Enqueue(1)
    rb.Enqueue(2)
    rb.Enqueue(3)
    assert rb.IsFull() is True


def test_not_full(make):
    rb = make(3)
    rb.Enqueue(1)
    assert rb.IsFull() is False


def test_not_empty_after_enqueue(make):
    rb = make(5)
    rb.Enqueue(1)
    assert rb.IsEmpty() is False


def test_empty_after_dequeue_all(make):
    rb = make(3)
    rb.Enqueue(1)
    rb.Enqueue(2)
    rb.Dequeue()
    rb.Dequeue()
    assert rb.IsEmpty() is True


# ── Peek is nondestructive ────────────────────────────────────────────────

def test_peek_nondestructive(make):
    rb = make(3)
    rb.Enqueue(42)
    assert rb.Peek() == 42
    assert rb.Peek() == 42
    assert rb.Size() == 1


# ── Wrap-around ───────────────────────────────────────────────────────────

def test_wrap_around(make):
    rb = make(3)
    rb.Enqueue(1)
    rb.Enqueue(2)
    rb.Enqueue(3)
    rb.Dequeue()       # removes 1
    rb.Enqueue(4)      # wraps around
    assert rb.Dequeue() == 2
    assert rb.Dequeue() == 3
    assert rb.Dequeue() == 4


def test_multiple_wrap_arounds(make):
    rb = make(2)
    # Fill and empty multiple times
    rb.Enqueue(1)
    rb.Enqueue(2)
    assert rb.Dequeue() == 1
    assert rb.Dequeue() == 2

    rb.Enqueue(3)
    rb.Enqueue(4)
    assert rb.Dequeue() == 3
    assert rb.Dequeue() == 4

    rb.Enqueue(5)
    rb.Enqueue(6)
    assert rb.Dequeue() == 5
    assert rb.Dequeue() == 6


def test_wrap_fifo_preserved(make):
    rb = make(3)
    # Enqueue 1,2,3 (full), dequeue 1, enqueue 4 (wraps), dequeue 2,3,4
    rb.Enqueue(1)
    rb.Enqueue(2)
    rb.Enqueue(3)
    assert rb.Dequeue() == 1
    rb.Enqueue(4)
    assert rb.Dequeue() == 2
    assert rb.Dequeue() == 3
    assert rb.Dequeue() == 4
    assert rb.IsEmpty() is True


# ── Capacity 1 ────────────────────────────────────────────────────────────

def test_capacity_one(make):
    rb = make(1)
    rb.Enqueue(99)
    assert rb.IsFull() is True
    assert rb.Size() == 1
    assert rb.Dequeue() == 99
    assert rb.IsEmpty() is True


def test_capacity_one_repeated(make):
    rb = make(1)
    for i in range(5):
        rb.Enqueue(i)
        assert rb.Dequeue() == i
