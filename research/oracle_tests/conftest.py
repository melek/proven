"""Oracle test infrastructure — adapters for Dafny-compiled and TDD outputs.

Provides fixtures that create instances through either:
  - Dafny-compiled: ClassName() then obj.ctor__(*args)
  - TDD (native Python): ClassName(*args) directly

Usage:
    pytest research/oracle_tests/ \
        --formal-dir runs/h2h/sonnet_freestyle \
        --tdd-dir runs/tdd/local \
        --problem ring_buffer

    # Or test a single condition:
    pytest research/oracle_tests/ -k "formal" --formal-dir ...
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


# ── Problem metadata ──────────────────────────────────────────────────────

PROBLEM_CONFIG = {
    "bounded_counter": {
        "formal_class": "BoundedCounter",
        "tdd_class": "BoundedCounter",
        "has_ctor_args": True,
    },
    "stack": {
        "formal_class": "Stack",
        "tdd_class": "Stack",
        "has_ctor_args": False,
    },
    "priority_queue": {
        "formal_class": "MinPriorityQueue",
        "tdd_class": "MinPriorityQueue",
        "has_ctor_args": False,
    },
    "sorted_list": {
        "formal_class": "SortedList",
        "tdd_class": "SortedList",
        "has_ctor_args": False,
    },
    "unique_set": {
        "formal_class": "UniqueSet",
        "tdd_class": "UniqueSet",
        "has_ctor_args": False,
    },
    "pipeline_state": {
        "formal_class": "PipelineStateMachine",
        "tdd_class": "PipelineStateMachine",
        "has_ctor_args": False,
    },
    "binary_search": {
        "formal_class": "SortedArray",
        "tdd_class": "SortedArray",
        "has_ctor_args": True,
    },
    "ring_buffer": {
        "formal_class": "RingBuffer",
        "tdd_class": "RingBuffer",
        "has_ctor_args": True,
    },
    "balanced_parentheses": {
        "formal_class": "default__",
        "tdd_class": "BalancedParentheses",
        "has_ctor_args": False,
        "static_only": True,
    },
}


# ── CLI options ───────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption("--formal-dir", default=None,
                     help="Root directory containing formal (Dafny-compiled) outputs")
    parser.addoption("--tdd-dir", default=None,
                     help="Root directory containing TDD outputs")
    parser.addoption("--problem", default=None,
                     help="Run oracle tests for a single problem only")


# ── Import helpers ────────────────────────────────────────────────────────

def import_module_from_path(module_path: Path, module_name: str = None) -> ModuleType:
    """Import a Python module from an arbitrary filesystem path."""
    module_path = module_path.resolve()
    if module_name is None:
        module_name = module_path.stem

    # Add the module's directory to sys.path so its sibling imports work
    # (Dafny-compiled modules import _dafny, System_, module_ from same dir)
    parent_dir = str(module_path.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ── Path discovery ────────────────────────────────────────────────────────

def find_formal_module(formal_dir: Path, problem: str) -> Path | None:
    """Find the Dafny-compiled module_.py for a problem.

    Searches patterns:
      {formal_dir}/{problem}/**/module_.py
      {formal_dir}/{problem}_v*/**/module_.py
    """
    # Direct match
    candidates = list(formal_dir.glob(f"{problem}/**/module_.py"))
    # Versioned match (pick highest version)
    candidates += list(formal_dir.glob(f"{problem}_v*/**/module_.py"))
    if not candidates:
        return None
    # Prefer the most recently modified
    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_tdd_module(tdd_dir: Path, problem: str) -> Path | None:
    """Find the TDD implementation for a problem.

    Searches patterns:
      {tdd_dir}/{problem}/{problem}.py
      {tdd_dir}/{problem}/implementation.py
    """
    direct = tdd_dir / problem / f"{problem}.py"
    if direct.exists():
        return direct
    alt = tdd_dir / problem / "implementation.py"
    if alt.exists():
        return alt
    return None


# ── Factory fixtures ──────────────────────────────────────────────────────

def make_formal_factory(module_path: Path, problem: str):
    """Create a factory that instantiates Dafny-compiled objects.

    Returns a callable: factory(*args) -> instance with ctor__ called.

    Handles two Dafny compilation patterns:
      - Class pattern: module has a named class with ctor__ and instance methods
      - Static pattern: module has default__ with static methods (binary_search, balanced_parentheses)
    """
    # Use a unique module name to avoid collisions between problems
    mod = import_module_from_path(module_path, f"formal_{problem}_module_")
    config = PROBLEM_CONFIG[problem]

    # Try primary class name first
    cls = getattr(mod, config["formal_class"], None)

    # Fallback: auto-detect the main class (any class with ctor__ or Init that isn't default__)
    if cls is None:
        _SKIP_CLASSES = {"default__", "Any", "Callable", "TypeVar", "count"}
        for name in dir(mod):
            if name in _SKIP_CLASSES or name.startswith("_"):
                continue
            obj = getattr(mod, name)
            if isinstance(obj, type) and (hasattr(obj, "ctor__") or hasattr(obj, "Init")):
                cls = obj
                break

    # Fallback: if class not found or lacks required methods,
    # check for default__ with static methods
    if cls is None or (problem in _FORMAL_STATIC_ADAPTERS and not _has_instance_methods(cls, problem)):
        default_cls = getattr(mod, "default__", None)
        if default_cls is not None and problem in _FORMAL_STATIC_ADAPTERS:
            return _FORMAL_STATIC_ADAPTERS[problem](mod, default_cls)
        if cls is None:
            raise AttributeError(
                f"Module {module_path} has no class with ctor__ "
                f"and no suitable fallback adapter for '{problem}'"
            )

    if config.get("static_only"):
        # balanced_parentheses: static methods, return the class itself
        return cls

    def factory(*args, **kwargs):
        obj = cls()
        if hasattr(obj, "ctor__"):
            obj.ctor__(*args, **kwargs)
        elif hasattr(obj, "Init"):
            obj.Init(*args, **kwargs)
        else:
            raise AttributeError(
                f"Class {cls.__name__} has neither ctor__ nor Init method"
            )
        return obj

    return factory


# ── Formal static adapters (for when Dafny compiles to default__ statics) ─

def _adapt_binary_search_static(mod, default_cls):
    """Wrap default__.Search(arr, key) and default__.IsSorted(arr) as an instance API.

    Returns a factory: factory(elements_list) -> adapter object with .Search(key) and .IsSorted()
    The adapter converts Python lists to _dafny.Array for the formal impl.
    """
    import _dafny

    class _BinarySearchAdapter:
        def __init__(self, elements):
            # Convert list to _dafny.Array (what the static methods expect)
            self._arr = _dafny.Array(None, len(elements))
            for i, v in enumerate(elements):
                self._arr[i] = v
            self._elements = elements

        def Search(self, key):
            return default_cls.Search(self._arr, key)

        def IsSorted(self):
            return default_cls.IsSorted(self._arr)

    return _BinarySearchAdapter


_FORMAL_STATIC_ADAPTERS = {
    "binary_search": _adapt_binary_search_static,
}

# Methods each adapter problem expects on instances (used to detect incomplete classes)
_EXPECTED_INSTANCE_METHODS = {
    "binary_search": ["Search", "IsSorted"],
}


def _has_instance_methods(cls, problem: str) -> bool:
    """Check if a class has the expected instance methods for a problem."""
    expected = _EXPECTED_INSTANCE_METHODS.get(problem, [])
    return all(hasattr(cls, m) for m in expected)


def make_tdd_factory(module_path: Path, problem: str):
    """Create a factory that instantiates TDD objects.

    Returns a callable: factory(*args) -> instance.
    """
    mod = import_module_from_path(module_path, f"tdd_{problem}_impl")
    config = PROBLEM_CONFIG[problem]
    cls = getattr(mod, config["tdd_class"])

    if config.get("static_only"):
        return cls

    return cls


# ── Dafny string conversion helpers (for balanced_parentheses) ────────────

def python_str_to_dafny_seq(s: str):
    """Convert a Python string to a Dafny sequence of CodePoints.

    Used by oracle tests for balanced_parentheses when testing formal output.
    """
    import _dafny
    return _dafny.SeqWithoutIsStrInference([_dafny.CodePoint(c) for c in s])


# ── Parametrized condition fixture ────────────────────────────────────────

def _get_active_conditions(config):
    """Determine which conditions (formal/tdd) have data available."""
    conditions = []
    if config.getoption("formal_dir"):
        conditions.append("formal")
    if config.getoption("tdd_dir"):
        conditions.append("tdd")
    return conditions


def get_factory_for_condition(request, problem: str, condition: str):
    """Get the implementation factory for a given condition and problem."""
    if condition == "formal":
        formal_dir_opt = request.config.getoption("formal_dir")
        if formal_dir_opt is None:
            pytest.skip("No --formal-dir provided")
        formal_dir = Path(formal_dir_opt)
        module_path = find_formal_module(formal_dir, problem)
        if module_path is None:
            pytest.skip(f"No formal output found for {problem}")
        return make_formal_factory(module_path, problem), "formal"
    else:
        tdd_dir_opt = request.config.getoption("tdd_dir")
        if tdd_dir_opt is None:
            pytest.skip("No --tdd-dir provided")
        tdd_dir = Path(tdd_dir_opt)
        module_path = find_tdd_module(tdd_dir, problem)
        if module_path is None:
            pytest.skip(f"No TDD output found for {problem}")
        return make_tdd_factory(module_path, problem), "tdd"
