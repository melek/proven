"""Thin wrapper around the Dafny CLI."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DafnyResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    success: bool

    @property
    def error_message(self) -> str:
        """Combined output for feeding back to LLM."""
        parts = []
        if self.stderr.strip():
            parts.append(self.stderr.strip())
        if self.stdout.strip():
            parts.append(self.stdout.strip())
        return "\n".join(parts)


def _run_dafny(args: list[str], dafny_path: str, timeout: int) -> DafnyResult:
    """Execute a dafny subprocess and capture output."""
    cmd = [dafny_path] + args
    cmd_str = " ".join(cmd)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return DafnyResult(
            command=cmd_str,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            success=(result.returncode == 0),
        )
    except FileNotFoundError:
        return DafnyResult(
            command=cmd_str,
            exit_code=-1,
            stdout="",
            stderr=(
                f"Dafny not found at '{dafny_path}'.\n"
                "Install: dotnet tool install --global dafny\n"
                "Or download from https://github.com/dafny-lang/dafny/releases"
            ),
            success=False,
        )
    except subprocess.TimeoutExpired:
        return DafnyResult(
            command=cmd_str,
            exit_code=-2,
            stdout="",
            stderr=f"Dafny timed out after {timeout}s",
            success=False,
        )


def check_installed(dafny_path: str = "dafny") -> DafnyResult:
    """Check that Dafny is installed and reachable."""
    return _run_dafny(["--version"], dafny_path, timeout=30)


def resolve(dfy_file: Path, dafny_path: str = "dafny", timeout: int = 60) -> DafnyResult:
    """Parse and typecheck only (no verification). Used after Stage 2."""
    return _run_dafny(["resolve", str(dfy_file)], dafny_path, timeout)


def verify(dfy_file: Path, dafny_path: str = "dafny", timeout: int = 300) -> DafnyResult:
    """Full verification including pre/postconditions and invariants."""
    return _run_dafny(["verify", str(dfy_file)], dafny_path, timeout)


def build(
    dfy_file: Path,
    target: str = "py",
    output_dir: Path | None = None,
    dafny_path: str = "dafny",
    timeout: int = 120,
) -> DafnyResult:
    """Compile verified Dafny to target language."""
    args = ["build", f"--target:{target}", str(dfy_file)]
    if output_dir:
        args.extend(["--output", str(output_dir / dfy_file.stem)])
    return _run_dafny(args, dafny_path, timeout)
