"""User interaction handling and mode switching."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class InteractionHandler:
    def __init__(self, mode: str, escalation_threshold: int = 2):
        self.mode = mode
        self.escalation_threshold = escalation_threshold

    def should_pause(self, outcome: str, attempts: int) -> bool:
        """Decide whether to pause for user input after a stage."""
        if self.mode == "assisted":
            return True
        elif self.mode == "autonomous":
            return False  # never pause in autonomous mode
        elif self.mode == "semi":
            return outcome == "failed" and attempts >= self.escalation_threshold
        return False

    def prompt_user(self, stage_num: int, stage_name: str, outcome: str, message: str, output_file: Path | None) -> str:
        """Show stage result and get user decision.

        Returns: "approve" | "retry" | "skip" | "abort" | "edit" | "switch_mode"
        """
        print(f"\n  Stage {stage_num} ({stage_name}): {outcome}")
        print(f"  {message}")
        if output_file and output_file.exists():
            print(f"  Output: {output_file}")
        print()
        print("  [a]pprove  - accept and continue")
        print("  [r]etry   - re-run this stage")
        print("  [e]dit    - open output file, then retry")
        print("  [s]kip    - skip to next stage")
        print("  [m]ode    - switch interaction mode")
        print("  [q]uit    - abort pipeline")
        print()

        while True:
            try:
                choice = input("  Choice: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return "abort"

            match choice:
                case "a" | "approve":
                    return "approve"
                case "r" | "retry":
                    return "retry"
                case "e" | "edit":
                    if output_file:
                        self._open_in_editor(output_file)
                    return "retry"
                case "s" | "skip":
                    return "skip"
                case "m" | "mode":
                    return "switch_mode"
                case "q" | "quit":
                    return "abort"
                case _:
                    print("  Invalid choice.")

    def get_new_mode(self) -> str:
        """Prompt user to select a new interaction mode."""
        print("\n  Switch to mode:")
        print("  [1] assisted  - pause after every stage")
        print("  [2] autonomous - run all stages automatically")
        print("  [3] semi      - auto with human escalation")
        print()
        try:
            choice = input("  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            return self.mode
        return {"1": "assisted", "2": "autonomous", "3": "semi"}.get(choice, self.mode)

    def _open_in_editor(self, file_path: Path) -> None:
        editor = os.environ.get("EDITOR", "notepad")
        try:
            subprocess.run([editor, str(file_path)])
        except FileNotFoundError:
            print(f"  Could not open editor '{editor}'. Edit the file manually:")
            print(f"  {file_path}")
            input("  Press Enter when done...")
