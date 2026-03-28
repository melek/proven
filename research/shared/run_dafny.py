"""Thin wrapper to run dafny commands. Loads DAFNY_PATH from .env.

Usage:
    python research/run_dafny.py verify path/to/file.dfy
    python research/run_dafny.py resolve path/to/file.dfy
    python research/run_dafny.py build path/to/file.dfy [--target:py] [--output dir/name]
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from proven.dafny import verify, resolve, build

def main():
    if len(sys.argv) < 3:
        print("Usage: python research/run_dafny.py <verify|resolve|build> <file.dfy> [args...]")
        sys.exit(1)

    command = sys.argv[1]
    dfy_file = Path(sys.argv[2])
    dafny_path = os.environ.get("DAFNY_PATH", "dafny")

    if command == "verify":
        result = verify(dfy_file, dafny_path=dafny_path)
    elif command == "resolve":
        result = resolve(dfy_file, dafny_path=dafny_path)
    elif command == "build":
        target = "py"
        output_dir = None
        for arg in sys.argv[3:]:
            if arg.startswith("--target:"):
                target = arg.split(":")[1]
            elif arg.startswith("--output"):
                # Next arg or =value
                pass
        # Check for --output as separate arg
        args = sys.argv[3:]
        for i, arg in enumerate(args):
            if arg == "--output" and i + 1 < len(args):
                output_dir = Path(args[i + 1])
        result = build(dfy_file, target=target, output_dir=output_dir, dafny_path=dafny_path)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    if result.stdout.strip():
        print(result.stdout)
    if result.stderr.strip():
        print(result.stderr, file=sys.stderr)
    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
