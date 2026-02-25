"""TDD agent — generate tests first, then implement to pass them.

Two-phase approach:
  Phase 1: Generate pytest tests from requirements (1 LLM call, no iteration)
  Phase 2: Implement Python class to pass tests (up to N iterations with pytest feedback)

Tests are written ONCE and never revised — prevents test weakening.

Usage:
    python research/tdd_agent.py examples/bounded_counter.md \
        --model qwen2.5-coder:14b \
        --base-url http://localhost:11434/v1 \
        --max-attempts 10 \
        --output-dir runs/tdd/local/bounded_counter
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path so we can import proven modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from proven.llm import LLMClient
from proven.prompts import strip_code_fences


# ── API contracts per benchmark ──────────────────────────────────────────
# Included in TDD prompts so both TDD and Dafny outputs share the same API.

API_CONTRACTS = {
    "bounded_counter": """\
class BoundedCounter:
    def __init__(self, min_val: int, max_val: int):
        '''Initialize with bounds [min_val, max_val]. Value starts at min_val.'''
    def Increment(self) -> None:
        '''Increase value by 1. Precondition: not at max.'''
    def Decrement(self) -> None:
        '''Decrease value by 1. Precondition: not at min.'''
    def GetValue(self) -> int:
        '''Return current value.'''
    def IsAtMin(self) -> bool:
        '''Return whether value equals min.'''
    def IsAtMax(self) -> bool:
        '''Return whether value equals max.'''""",

    "stack": """\
class Stack:
    def __init__(self):
        '''Initialize empty stack.'''
    def Push(self, x: int) -> None:
        '''Push x onto top of stack.'''
    def Pop(self) -> int:
        '''Remove and return top element. Precondition: not empty.'''
    def Top(self) -> int:
        '''Return top element without removing. Precondition: not empty.'''
    def Size(self) -> int:
        '''Return number of elements.'''
    def IsEmpty(self) -> bool:
        '''Return whether stack is empty.'''""",

    "priority_queue": """\
class MinPriorityQueue:
    def __init__(self):
        '''Initialize empty min-priority queue.'''
    def Insert(self, x: int) -> None:
        '''Add element to queue.'''
    def ExtractMin(self) -> int:
        '''Remove and return minimum element. Precondition: not empty.'''
    def Peek(self) -> int:
        '''Return minimum element without removing. Precondition: not empty.'''
    def Size(self) -> int:
        '''Return number of elements.'''
    def IsEmpty(self) -> bool:
        '''Return whether queue is empty.'''""",

    "sorted_list": """\
class SortedList:
    def __init__(self):
        '''Initialize empty sorted list.'''
    def Insert(self, x: int) -> None:
        '''Insert x at correct position to maintain non-decreasing sorted order.'''
    def Remove(self, x: int) -> None:
        '''Remove one occurrence of x. Precondition: x is present.'''
    def Contains(self, x: int) -> bool:
        '''Return whether x is in the list.'''
    def GetMin(self) -> int:
        '''Return minimum element. Precondition: not empty.'''
    def GetMax(self) -> int:
        '''Return maximum element. Precondition: not empty.'''
    def Size(self) -> int:
        '''Return number of elements.'''""",

    "unique_set": """\
class UniqueSet:
    def __init__(self):
        '''Initialize empty set.'''
    def Add(self, x: int) -> None:
        '''Add x to set. Idempotent — no effect if x already present.'''
    def Remove(self, x: int) -> None:
        '''Remove x from set. Precondition: x is present.'''
    def Contains(self, x: int) -> bool:
        '''Return whether x is in the set.'''
    def Size(self) -> int:
        '''Return number of elements.'''
    def IsEmpty(self) -> bool:
        '''Return whether set is empty.'''""",

    "pipeline_state": """\
class PipelineStateMachine:
    def __init__(self):
        '''Initialize 5-stage pipeline. All stages start as Pending (0).
        Status codes: 0=Pending, 1=InProgress, 2=Completed, 3=Failed, 4=Skipped.'''
    def Advance(self, stage: int) -> None:
        '''Set stage to InProgress (1).
        Precondition: stage is Pending AND all prior stages are Completed or Skipped.'''
    def Complete(self, stage: int) -> None:
        '''Set stage to Completed (2). Precondition: stage is InProgress.'''
    def Fail(self, stage: int) -> None:
        '''Set stage to Failed (3). Precondition: stage is InProgress.'''
    def Rollback(self, target: int) -> None:
        '''Reset target stage and all later stages to Pending (0). 0 <= target <= 4.'''
    def IsFinished(self) -> bool:
        '''Return whether all 5 stages are Completed (2) or Skipped (4).'''""",

    "binary_search": """\
class SortedArray:
    def __init__(self, elements: list[int]):
        '''Initialize with a sorted list of integers.'''
    def Search(self, key: int) -> int:
        '''Return index of key in elements, or -1 if not found.'''
    def IsSorted(self) -> bool:
        '''Return whether elements are in non-decreasing order.'''""",

    "ring_buffer": """\
class RingBuffer:
    def __init__(self, capacity: int):
        '''Initialize empty buffer with given capacity (capacity > 0).'''
    def Enqueue(self, x: int) -> None:
        '''Add x to back of buffer. Precondition: not full.'''
    def Dequeue(self) -> int:
        '''Remove and return front element. Precondition: not empty.'''
    def Peek(self) -> int:
        '''Return front element without removing. Precondition: not empty.'''
    def Size(self) -> int:
        '''Return number of elements currently in buffer.'''
    def IsFull(self) -> bool:
        '''Return whether buffer is at capacity.'''
    def IsEmpty(self) -> bool:
        '''Return whether buffer is empty.'''""",

    "balanced_parentheses": """\
class BalancedParentheses:
    @staticmethod
    def IsBalanced(s: str) -> bool:
        '''Return whether parentheses in s are balanced.
        Balanced means: equal '(' and ')' count, and no prefix has more ')' than '('.'''
    @staticmethod
    def CountOpen(s: str) -> int:
        '''Return count of '(' characters in s.'''
    @staticmethod
    def CountClose(s: str) -> int:
        '''Return count of ')' characters in s.'''""",

    "compositional_pipeline": """\
class CompositionalPipeline:
    @staticmethod
    def DigitSum(n: int) -> int:
        '''Return sum of decimal digits of n. Precondition: n >= 0.'''
    @staticmethod
    def ClassifyByDigitSum(values: list[int]) -> tuple[list[int], list[int]]:
        '''Partition values into (even_sum, odd_sum) based on digit sum parity.
        Precondition: all values >= 0.
        Returns (even_list, odd_list) where every input element appears in exactly one.'''""",

    "extended_gcd": """\
class ExtendedGcd:
    @staticmethod
    def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
        '''Return (g, x, y) where g = gcd(a, b) and a*x + b*y == g.
        Precondition: a > 0 and b > 0.'''""",

    "insertion_sort": """\
class InsertionSort:
    @staticmethod
    def sort(a: list[int]) -> list[int]:
        '''Return a new list containing the same elements as a, sorted in non-decreasing order.'''
    @staticmethod
    def is_sorted(a: list[int]) -> bool:
        '''Return whether a is sorted in non-decreasing order.'''""",

    "red_black_tree": """\
class RedBlackTree:
    def __init__(self):
        '''Initialize an empty red-black tree.'''
    def Insert(self, key: int) -> None:
        '''Insert key, maintaining all red-black invariants. No effect if key already present.'''
    def Contains(self, key: int) -> bool:
        '''Return whether key exists in the tree.'''
    def Valid(self) -> bool:
        '''Return whether the tree satisfies all red-black invariants:
        BST ordering, root is black, no red-red parent-child, uniform black-height.'''""",

    "compositional_triple": """\
class CompositionalTriple:
    @staticmethod
    def Frequencies(s: list[int]) -> dict[int, int]:
        '''Return map from each distinct value in s to its count.'''
    @staticmethod
    def FilterByFrequency(freq: dict[int, int], threshold: int) -> set[int]:
        '''Return set of keys in freq with count >= threshold. Precondition: threshold >= 1.'''
    @staticmethod
    def CollectFiltered(s: list[int], keep: set[int]) -> list[int]:
        '''Return subsequence of s containing only elements in keep, preserving order.'''""",

    "topological_sort": """\
class TopologicalSort:
    @staticmethod
    def topological_sort(graph: list[list[int]]) -> list[int]:
        '''Return vertices in topological order. graph[u] = list of vertices u has edges to.
        Precondition: graph is a DAG with valid vertex indices.'''
    @staticmethod
    def is_dag(graph: list[list[int]]) -> bool:
        '''Return whether graph has no directed cycles.'''""",
}


# ── System prompts ────────────────────────────────────────────────────────

TDD_TEST_SYSTEM = """\
You are an expert Python developer practicing TDD.
Given requirements and an API contract, write a comprehensive pytest test suite that covers:
- All operations (basic functionality for each method)
- Edge cases (empty, full, single element, boundary values)
- Invariant preservation across sequences of operations
- Error conditions and precondition boundaries
- The EXACT method signatures from the API contract below

Import the implementation class from the module using:
    from {module_name} import {class_name}

Output ONLY the Python test code. No explanation."""

TDD_IMPL_SYSTEM = """\
You are an expert Python developer.
Given requirements, an API contract, and a test suite, implement the class to pass all tests.
Use the EXACT class name, method names, and signatures from the API contract.

Output ONLY the Python implementation code. No explanation."""


TDD_RETRY = """\
The implementation failed some tests.

Previous implementation:
{previous_code}

Test failures:
{errors}

Fix the implementation to pass all tests. Preserve the exact class and method signatures.
Output ONLY the complete Python implementation. No explanation."""


# ── Module / class names per benchmark ────────────────────────────────────

CLASS_NAMES = {
    "bounded_counter": "BoundedCounter",
    "stack": "Stack",
    "priority_queue": "MinPriorityQueue",
    "sorted_list": "SortedList",
    "unique_set": "UniqueSet",
    "pipeline_state": "PipelineStateMachine",
    "binary_search": "SortedArray",
    "ring_buffer": "RingBuffer",
    "balanced_parentheses": "BalancedParentheses",
    "compositional_pipeline": "CompositionalPipeline",
    "extended_gcd": "ExtendedGcd",
    "insertion_sort": "InsertionSort",
    "red_black_tree": "RedBlackTree",
    "compositional_triple": "CompositionalTriple",
    "topological_sort": "TopologicalSort",
}


def run_tdd(
    requirements_file: Path,
    output_dir: Path,
    llm: LLMClient,
    max_attempts: int = 10,
    verbose: bool = False,
) -> dict:
    """Run the TDD generate-test-implement loop.

    Returns a results dict compatible with analyze_runs.py.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    attempts_dir = output_dir / "attempts"
    attempts_dir.mkdir(exist_ok=True)

    requirements_text = requirements_file.read_text(encoding="utf-8")
    problem = requirements_file.stem

    class_name = CLASS_NAMES.get(problem, problem.title().replace("_", ""))
    contract = API_CONTRACTS.get(problem, "")

    # Interaction log (same format as Proven pipeline)
    log_file = output_dir / "interaction_log.jsonl"
    log_entries: list[dict] = []

    def log_event(event: dict):
        event["ts"] = datetime.now(timezone.utc).isoformat()
        log_entries.append(event)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    start_time = time.time()
    total_tokens = 0
    llm_calls = 0
    tests_pass = False
    impl_exists = False

    # ── Phase 1: Generate tests (1 LLM call, no iteration) ──────────────
    if verbose:
        print(f"  Phase 1: Generating tests...")

    test_system = TDD_TEST_SYSTEM.format(
        module_name=problem,
        class_name=class_name,
    )
    test_prompt = (
        f"Write a comprehensive pytest test suite for the following requirements.\n\n"
        f"Requirements:\n{requirements_text}\n\n"
        f"API contract (use these EXACT class and method names):\n{contract}\n\n"
        f"Import the class with: from {problem} import {class_name}"
    )

    log_event({
        "event": "llm_request",
        "stage": "test_generation",
        "attempt": 0,
        "messages_count": 1,
    })

    try:
        test_resp = llm.complete(test_system, test_prompt, temperature=0.2)
    except Exception as e:
        print(f"  Test generation LLM call failed: {e}")
        log_event({"event": "llm_error", "error": str(e)})
        elapsed = time.time() - start_time
        return _make_result(problem, output_dir, requirements_file, llm,
                           False, False, 0, 0, elapsed)

    llm_calls += 1
    total_tokens += test_resp.usage.get("total_tokens", 0)

    log_event({
        "event": "llm_response",
        "stage": "test_generation",
        "attempt": 0,
        "content_length": len(test_resp.content),
        "usage": test_resp.usage,
    })

    test_code = strip_code_fences(test_resp.content)
    test_file = output_dir / f"test_{problem}.py"
    test_file.write_text(test_code, encoding="utf-8")

    if verbose:
        test_lines = len(test_code.splitlines())
        print(f"  Generated {test_lines} lines of tests")

    # ── Phase 2: Implement to pass tests (up to max_attempts iterations) ─
    if verbose:
        print(f"  Phase 2: Implementing to pass tests...")

    impl_system = TDD_IMPL_SYSTEM
    impl_prompt = (
        f"Implement the following class to pass the test suite below.\n\n"
        f"Requirements:\n{requirements_text}\n\n"
        f"API contract (use these EXACT class and method names):\n{contract}\n\n"
        f"Test suite:\n{test_code}"
    )

    conversation: list[dict] = [
        {"role": "user", "content": impl_prompt},
    ]

    current_code = ""
    impl_file = output_dir / f"{problem}.py"

    for attempt in range(max_attempts):
        temperature = 0.2 if attempt == 0 else min(0.2 + attempt * 0.1, 0.7)

        log_event({
            "event": "llm_request",
            "stage": "implementation",
            "attempt": attempt,
            "messages_count": len(conversation),
        })

        if verbose:
            print(f"  Attempt {attempt + 1}/{max_attempts} (temp={temperature:.1f})...")

        try:
            resp = llm.complete_with_history(
                impl_system, conversation, temperature=temperature,
            )
        except Exception as e:
            print(f"  LLM call failed: {e}")
            log_event({"event": "llm_error", "error": str(e)})
            break

        llm_calls += 1
        total_tokens += resp.usage.get("total_tokens", 0)

        log_event({
            "event": "llm_response",
            "stage": "implementation",
            "attempt": attempt,
            "content_length": len(resp.content),
            "usage": resp.usage,
        })

        current_code = strip_code_fences(resp.content)
        conversation.append({"role": "assistant", "content": current_code})

        # Save attempt
        attempt_file = attempts_dir / f"attempt_{attempt + 1:02d}.py"
        attempt_file.write_text(current_code, encoding="utf-8")
        impl_file.write_text(current_code, encoding="utf-8")
        impl_exists = True

        # Run pytest
        pytest_result = _run_pytest(test_file, impl_file, output_dir)

        log_event({
            "event": "tool_call",
            "stage": "implementation",
            "command": f"pytest {test_file.name}",
            "exit_code": pytest_result["exit_code"],
            "stdout": pytest_result["stdout"][:2000],
            "stderr": pytest_result["stderr"][:2000],
        })

        if pytest_result["exit_code"] == 0:
            tests_pass = True
            if verbose:
                print(f"  ALL TESTS PASS on attempt {attempt + 1}!")
            break

        # Failed — prepare retry
        errors = pytest_result["stdout"] + "\n" + pytest_result["stderr"]
        (attempts_dir / f"attempt_{attempt + 1:02d}_errors.txt").write_text(
            errors, encoding="utf-8"
        )

        if verbose:
            # Extract pass/fail counts
            for line in errors.splitlines():
                if "passed" in line or "failed" in line or "error" in line.lower():
                    print(f"  {line.strip()[:100]}")
                    break

        if attempt < max_attempts - 1:
            retry_prompt = TDD_RETRY.format(
                previous_code=current_code,
                errors=errors[:3000],
            )
            conversation.append({"role": "user", "content": retry_prompt})

    elapsed = time.time() - start_time

    # Write run_state.json (compatible with analyze_runs.py)
    run_state = {
        "run_id": output_dir.name,
        "workspace_path": str(output_dir),
        "current_stage": 5 if tests_pass else (3 if impl_exists else 0),
        "mode": "tdd",
        "stage_status": {
            "1": "completed",    # Requirements = read from file
            "2": "completed",    # Spec = test generation
            "3": "completed" if impl_exists else "pending",
            "4": "completed" if tests_pass else ("failed" if impl_exists else "pending"),
            "5": "completed" if tests_pass else "pending",
        },
        "retry_counts": {
            "1": 0,
            "2": 0,
            "3": 1,
            "4": max(0, llm_calls - 2),  # subtract test gen + first impl
            "5": 0,
        },
        "requirements_file": str(requirements_file),
        "config_snapshot": {
            "llm_model": llm.model,
            "target": "py",
            "max_retries": max_attempts,
            "condition": "tdd",
        },
    }
    (output_dir / "run_state.json").write_text(
        json.dumps(run_state, indent=2), encoding="utf-8"
    )

    # Write proof report (compatible with analyze_runs.py)
    proof_report = {
        "status": "verified" if tests_pass else "failed",
        "attempts": llm_calls,
        "last_errors": "" if tests_pass else "tests failed",
        "warnings": [],
        "mentor_interventions": 0,
    }
    (output_dir / "04_proof_report.json").write_text(
        json.dumps(proof_report, indent=2), encoding="utf-8"
    )

    status = "PASS" if tests_pass else "FAIL"
    print(f"\n  [{problem}] {status} — {llm_calls} LLM calls, "
          f"{total_tokens} tokens, {elapsed:.0f}s")

    return {
        "problem": problem,
        "tests_pass": tests_pass,
        "full_success": tests_pass,
        "verified": tests_pass,
        "attempts": llm_calls,
        "total_tokens": total_tokens,
        "wall_time_sec": round(elapsed, 1),
    }


def _run_pytest(test_file: Path, impl_file: Path, work_dir: Path) -> dict:
    """Run pytest on the test file, with impl_file's directory on PYTHONPATH."""
    env = os.environ.copy()
    # Add impl directory to PYTHONPATH so `from {problem} import {Class}` works
    impl_dir = str(impl_file.parent.resolve())
    env["PYTHONPATH"] = impl_dir + os.pathsep + env.get("PYTHONPATH", "")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file.name, "-v", "--tb=short", "--no-header"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(work_dir),
            env=env,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "TIMEOUT: pytest exceeded 60s",
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Failed to run pytest: {e}",
        }


def _make_result(problem, output_dir, req_file, llm, tests_pass, impl_exists,
                 llm_calls, total_tokens, elapsed):
    """Build result dict for early-exit cases."""
    run_state = {
        "run_id": output_dir.name,
        "workspace_path": str(output_dir),
        "current_stage": 0,
        "mode": "tdd",
        "stage_status": {"1": "failed", "2": "pending", "3": "pending",
                         "4": "pending", "5": "pending"},
        "retry_counts": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
        "requirements_file": str(req_file),
        "config_snapshot": {
            "llm_model": llm.model,
            "target": "py",
            "max_retries": 10,
            "condition": "tdd",
        },
    }
    (output_dir / "run_state.json").write_text(
        json.dumps(run_state, indent=2), encoding="utf-8"
    )
    return {
        "problem": problem,
        "tests_pass": False,
        "full_success": False,
        "verified": False,
        "attempts": llm_calls,
        "total_tokens": total_tokens,
        "wall_time_sec": round(elapsed, 1),
    }


def main():
    parser = argparse.ArgumentParser(
        description="TDD agent: generate tests, then implement to pass them",
    )
    parser.add_argument("requirements_file", type=Path, help="Path to requirements .md")
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--base-url", default=None, help="LLM API base URL")
    parser.add_argument("--api-key", default=None, help="LLM API key")
    parser.add_argument("--max-attempts", type=int, default=10,
                        help="Max implementation iterations")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    # Load .env for defaults
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    model = args.model or os.environ.get("LLM_MODEL", "qwen2.5-coder:14b")
    base_url = args.base_url or os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key = args.api_key or os.environ.get("LLM_API_KEY", "ollama")

    output_dir = args.output_dir or Path(
        f"runs/tdd/{model.replace(':', '-').replace('/', '-')}"
        f"/{args.requirements_file.stem}"
    )

    if not args.requirements_file.exists():
        print(f"Error: {args.requirements_file} not found")
        return 1

    print(f"TDD Agent — {model}")
    print(f"Problem: {args.requirements_file.stem}")
    print(f"Max attempts: {args.max_attempts}")
    print(f"Output: {output_dir}")

    llm = LLMClient(base_url, api_key, model)
    result = run_tdd(
        args.requirements_file,
        output_dir,
        llm,
        max_attempts=args.max_attempts,
        verbose=args.verbose,
    )

    return 0 if result["tests_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
