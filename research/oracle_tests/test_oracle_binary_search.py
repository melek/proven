"""Oracle tests for SortedArray / BinarySearch.

Tests the public API only — works for both Dafny-compiled and TDD implementations.

Dafny-compiled versions vary:
  - Class pattern (SortedArray): ctor__ takes _dafny.Seq
  - Static pattern (default__): static Search(arr, key) takes _dafny.Array
The conftest adapter handles both, presenting a uniform instance API.
"""

import pytest
from conftest import get_factory_for_condition

PROBLEM = "binary_search"


@pytest.fixture(params=["formal", "tdd"])
def make(request):
    """Returns a factory: make(elements_list) -> object with .Search(key) and .IsSorted()."""
    factory, condition = get_factory_for_condition(request, PROBLEM, request.param)

    if condition == "formal":
        # Check if factory is already an adapter class (static pattern)
        # or a ctor__-based factory (class pattern)
        if isinstance(factory, type):
            # It's a class (adapter from _FORMAL_STATIC_ADAPTERS) — takes a list directly
            return factory
        else:
            # It's a ctor__-based factory — needs _dafny.Seq conversion
            def formal_make(elements: list[int]):
                import _dafny
                dafny_seq = _dafny.SeqWithoutIsStrInference(elements)
                return factory(dafny_seq)
            return formal_make
    else:
        return factory


# ── Basic search ──────────────────────────────────────────────────────────

def test_find_single_element(make):
    sa = make([5])
    assert sa.Search(5) == 0


def test_find_not_present(make):
    sa = make([1, 3, 5])
    assert sa.Search(4) == -1


def test_find_first_element(make):
    sa = make([1, 2, 3, 4, 5])
    assert sa.Search(1) == 0


def test_find_last_element(make):
    sa = make([1, 2, 3, 4, 5])
    assert sa.Search(5) == 4


def test_find_middle_element(make):
    sa = make([1, 2, 3, 4, 5])
    assert sa.Search(3) == 2


def test_find_in_two_elements(make):
    sa = make([10, 20])
    assert sa.Search(10) == 0
    assert sa.Search(20) == 1


# ── Not found cases ──────────────────────────────────────────────────────

def test_not_found_below_range(make):
    sa = make([5, 10, 15])
    assert sa.Search(1) == -1


def test_not_found_above_range(make):
    sa = make([5, 10, 15])
    assert sa.Search(20) == -1


def test_empty_array(make):
    sa = make([])
    assert sa.Search(1) == -1


# ── IsSorted ──────────────────────────────────────────────────────────────

def test_is_sorted_sorted(make):
    sa = make([1, 2, 3, 4, 5])
    assert sa.IsSorted() is True


def test_is_sorted_single(make):
    sa = make([42])
    assert sa.IsSorted() is True


def test_is_sorted_empty(make):
    sa = make([])
    assert sa.IsSorted() is True


def test_is_sorted_duplicates(make):
    sa = make([1, 1, 2, 2, 3])
    assert sa.IsSorted() is True


# ── Larger arrays ─────────────────────────────────────────────────────────

def test_search_large_sorted(make):
    elements = list(range(0, 100, 2))  # [0, 2, 4, ..., 98]
    sa = make(elements)
    assert sa.Search(50) == 25
    assert sa.Search(0) == 0
    assert sa.Search(98) == 49
    assert sa.Search(51) == -1


def test_search_with_negatives(make):
    sa = make([-10, -5, 0, 5, 10])
    assert sa.Search(-5) == 1
    assert sa.Search(0) == 2
    assert sa.Search(7) == -1
