"""Oracle tests for BalancedParentheses.

Tests the public API only — works for both Dafny-compiled and TDD implementations.

Special handling: Dafny-compiled version has static methods on `default__` that take
_dafny sequences of CodePoints. TDD version has static methods taking Python strings.
"""

import pytest
from conftest import get_factory_for_condition, PROBLEM_CONFIG

PROBLEM = "balanced_parentheses"


@pytest.fixture(params=["formal", "tdd"])
def checker(request):
    """Returns a (cls, convert) tuple.

    cls: the class with static IsBalanced/CountOpen/CountClose methods
    convert: function to convert Python strings to the expected input format
    """
    factory, condition = get_factory_for_condition(request, PROBLEM, request.param)

    if condition == "formal":
        # Dafny-compiled: static methods on default__ take _dafny sequences
        import _dafny

        def convert(s: str):
            return _dafny.SeqWithoutIsStrInference([_dafny.CodePoint(c) for c in s])

        return factory, convert
    else:
        # TDD: static methods take Python strings
        return factory, lambda s: s


# ── IsBalanced ────────────────────────────────────────────────────────────

def test_empty_is_balanced(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("")) is True


def test_single_pair(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("()")) is True


def test_nested(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("(())")) is True


def test_sequential(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("()()")) is True


def test_complex_balanced(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("(()())")) is True


def test_deeply_nested(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("(((())))")) is True


# ── Unbalanced cases ─────────────────────────────────────────────────────

def test_single_open(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("(")) is False


def test_single_close(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv(")")) is False


def test_close_before_open(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv(")(")) is False


def test_extra_open(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("(()")) is False


def test_extra_close(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv("())")) is False


def test_mismatched(checker):
    cls, conv = checker
    assert cls.IsBalanced(conv(")()(")) is False


# ── CountOpen ─────────────────────────────────────────────────────────────

def test_count_open_empty(checker):
    cls, conv = checker
    assert cls.CountOpen(conv("")) == 0


def test_count_open_pair(checker):
    cls, conv = checker
    assert cls.CountOpen(conv("()")) == 1


def test_count_open_multiple(checker):
    cls, conv = checker
    assert cls.CountOpen(conv("(()())")) == 3


def test_count_open_only_close(checker):
    cls, conv = checker
    assert cls.CountOpen(conv(")))")) == 0


# ── CountClose ────────────────────────────────────────────────────────────

def test_count_close_empty(checker):
    cls, conv = checker
    assert cls.CountClose(conv("")) == 0


def test_count_close_pair(checker):
    cls, conv = checker
    assert cls.CountClose(conv("()")) == 1


def test_count_close_multiple(checker):
    cls, conv = checker
    assert cls.CountClose(conv("(()())")) == 3


def test_count_close_only_open(checker):
    cls, conv = checker
    assert cls.CountClose(conv("(((")) == 0


# ── Consistency: balanced implies equal counts ────────────────────────────

def test_balanced_implies_equal_counts(checker):
    cls, conv = checker
    for s in ["", "()", "(())", "()()", "(()())", "(((())))"]:
        cs = conv(s)
        if cls.IsBalanced(cs):
            assert cls.CountOpen(cs) == cls.CountClose(cs)
